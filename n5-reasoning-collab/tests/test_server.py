import http.client
import ctypes
import io
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from server.app import LocalServer
from server.deepseek import load_key
from server import configure_key
from test_live import ScriptedModel


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        (root / "index.html").write_text("<!doctype html><title>N5 test</title>", encoding="utf-8")
        (root / "server").mkdir()
        (root / "server" / "secret.key").write_text("DO NOT SERVE")
        cls.server = LocalServer(0, root=root, credentials=False)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.directory.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        merged = {"Origin": self.server.origin, "Content-Type": "application/json"}
        merged.update(headers or {})
        connection.request(method, path, body=body, headers=merged)
        response = connection.getresponse()
        data = response.read()
        connection.close()
        return response.status, data

    def test_unconfigured_health_and_live_disabled(self):
        status, data = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(data)["available"])
        status, _ = self.request("POST", "/api/runs", '{"scenario":"react","weather":"rain","budget":300}')
        self.assertEqual(status, 503)

    def test_exact_static_whitelist_blocks_source_keys_traversal(self):
        self.assertEqual(self.request("GET", "/")[0], 200)
        for path in ("/server/secret.key", "/server/deepseek.py", "/README.md", "/.env", "/api/unknown",
                     "/../index.html", "/%2e%2e/index.html", "/assets/../../server/secret.key"):
            with self.subTest(path=path):
                self.assertIn(self.request("GET", path)[0], (400, 404))

    def test_origin_host_dns_rebinding_and_preflight_rejected(self):
        for headers in ({"Origin": "https://evil.example"}, {"Origin": "null"},
                        {"Host": "evil.example"}, {"Host": "localhost:" + str(self.server.server_port)},
                        {"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"}):
            self.assertEqual(self.request("GET", "/api/health", headers=headers)[0], 403)
        self.assertEqual(self.request("OPTIONS", "/api/runs")[0], 403)
        self.assertEqual(self.request("POST", "/api/runs", "{}", {"Origin": ""})[0], 403)

    def test_request_schema_size_and_content_type(self):
        for body in ('[]', '{}', '{"scenario":"react","weather":"rain","budget":true}',
                     '{"scenario":"react","weather":"rain","budget":300,"extra":1}',
                     '{"scenario":"react","scenario":"dual","weather":"rain","budget":300}'):
            self.assertEqual(self.request("POST", "/api/runs", body)[0], 400)
        self.assertEqual(self.request("POST", "/api/runs", "{}" * 9000)[0], 413)
        self.assertEqual(self.request("POST", "/api/runs", "{}", {"Content-Type": "text/plain"})[0], 415)

    def test_environment_key_has_priority(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "  test-only-key  ", "LOCALAPPDATA": self.directory.name}):
            self.assertEqual(load_key(), "test-only-key")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "", "LOCALAPPDATA": self.directory.name}):
            self.assertIsNone(load_key())


class ConfiguredHTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = LocalServer(0, client=ScriptedModel())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, value=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request(method, path, body=json.dumps(value) if value is not None else None,
                           headers={"Origin": self.server.origin, "Content-Type": "application/json"})
        response = connection.getresponse()
        status, data = response.status, json.loads(response.read())
        connection.close()
        return status, data

    def test_create_poll_snapshot_and_cancel_contract(self):
        status, health = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["available"])
        status, created = self.request("POST", "/api/runs", {"scenario": "dual", "weather": "rain", "budget": 300})
        self.assertEqual(status, 202)
        self.assertEqual(set(created), {"run_id"})
        run = self.server.manager.get(created["run_id"])
        run.task.result(timeout=5)
        status, snapshot = self.request("GET", "/api/runs/" + created["run_id"])
        self.assertEqual(status, 200)
        self.assertEqual(snapshot["status"], "completed")
        self.assertEqual(snapshot["events"][-1]["state_after"]["itinerary"]["total"], 210)
        self.assertEqual(snapshot["metrics"]["model_calls"], 5)
        status, cancelled = self.request("POST", "/api/runs/" + created["run_id"] + "/cancel", {})
        self.assertEqual(status, 200)
        self.assertEqual(cancelled["status"], "completed")
        self.assertEqual(self.request("POST", "/api/runs/" + created["run_id"] + "/cancel", {"extra": True})[0], 400)
        self.assertEqual(self.request("GET", "/api/runs/" + "0" * 32)[0], 404)

    def test_health_preserves_existing_manager_without_reloading_credentials(self):
        original = self.server.manager
        with patch("server.app.load_key", return_value="different-test-key") as loader, patch("server.app.RunManager") as factory:
            for _ in range(3):
                self.assertTrue(self.request("GET", "/api/health")[1]["available"])
            self.assertIs(self.server.manager, original)
            loader.assert_not_called()
            factory.assert_not_called()


class CredentialRefreshTests(unittest.TestCase):
    def read_health(self, server):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        connection.request("GET", "/api/health")
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        value = json.loads(response.read())
        connection.close()
        return value

    def test_health_can_activate_after_configuration_without_restarting(self):
        manager = MagicMock()
        with patch("server.app.load_key", side_effect=[None, None, "new-test-only-key"]) as loader, \
                patch("server.app.importlib.util.find_spec", return_value=object()), \
                patch("server.app.RunManager", return_value=manager) as factory:
            server = LocalServer(0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                self.assertFalse(self.read_health(server)["available"])
                self.assertTrue(self.read_health(server)["available"])
                self.assertIs(server.manager, manager)
                for _ in range(3):
                    health = self.read_health(server)
                    self.assertTrue(health["available"])
                    self.assertNotIn("new-test-only-key", json.dumps(health))
                self.assertEqual(loader.call_count, 3)
                factory.assert_called_once()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
        manager.close.assert_called_once()

    def test_parallel_health_only_constructs_one_manager(self):
        with patch("server.app.load_key", return_value=None) as loader, \
                patch("server.app.importlib.util.find_spec", return_value=object()), \
                patch("server.app.RunManager", return_value=MagicMock()) as factory:
            server = LocalServer(0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                loader.return_value = "parallel-test-only-key"
                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(lambda _: self.read_health(server), range(8)))
                self.assertTrue(all(result["available"] for result in results))
                factory.assert_called_once()
                self.assertEqual(loader.call_count, 2)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_disabled_credentials_never_read_local_store(self):
        with patch("server.app.load_key") as loader:
            server = LocalServer(0, credentials=False)
            try:
                self.assertFalse(server.refresh_credentials()["available"])
                loader.assert_not_called()
            finally:
                server.server_close()


class CredentialSetupTests(unittest.TestCase):
    def test_encrypted_save_uses_resolved_directory_for_both_atomic_paths(self):
        # Windows Store Python may redirect AppData from C: onto another drive.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            redirected = root / "redirected-appdata"
            redirected.mkdir()
            target = root / "virtual-appdata" / "deepseek.key.dpapi"
            original_resolve = Path.resolve
            def resolve(candidate, *args, **kwargs):
                if candidate == target.parent:
                    return redirected
                return original_resolve(candidate, *args, **kwargs)
            with patch.object(configure_key, "protect_key", return_value=b"test-encrypted-only"), \
                    patch.object(Path, "resolve", resolve):
                configure_key.save_key("test-not-a-real-key", target)
            self.assertEqual((redirected / target.name).read_bytes(), b"test-encrypted-only")
            self.assertFalse(target.exists())
            self.assertEqual([p.name for p in redirected.iterdir()], [target.name])

    def test_dpapi_uses_current_user_scope_without_touching_disk(self):
        encrypted = b"mock-dpapi-ciphertext"
        buffer = (ctypes.c_ubyte * len(encrypted)).from_buffer_copy(encrypted)
        crypt, kernel = MagicMock(), MagicMock()
        def encrypt(source, description, entropy, reserved, prompt, flags, destination):
            self.assertEqual(flags, 1)  # UI forbidden, not LOCAL_MACHINE (4).
            destination._obj.size = len(encrypted)
            destination._obj.data = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
            return 1
        crypt.CryptProtectData.side_effect = encrypt
        with patch.object(configure_key, "is_windows", return_value=True), \
                patch.object(configure_key.ctypes, "WinDLL", side_effect=[crypt, kernel], create=True):
            self.assertEqual(configure_key.protect_key("test-only-input"), encrypted)
        crypt.CryptProtectData.assert_called_once()
        kernel.LocalFree.assert_called_once()

    def test_new_key_uses_hidden_input_and_never_prints_value(self):
        output = io.StringIO()
        target = Path("unused-test-target.dpapi")
        with patch.object(configure_key, "is_windows", return_value=True), \
                patch.object(configure_key, "credential_path", return_value=target), \
                patch.object(Path, "exists", return_value=False), \
                patch.object(configure_key.getpass, "getpass", return_value="test-secret-value") as secret_input, \
                patch.object(configure_key, "save_key") as save, redirect_stdout(output):
            self.assertEqual(configure_key.main(), 0)
        secret_input.assert_called_once()
        save.assert_called_once_with("test-secret-value", target)
        self.assertNotIn("test-secret-value", output.getvalue())

    def test_overwrite_requires_local_yes_and_cancel_does_not_prompt_for_key(self):
        with patch.object(configure_key, "is_windows", return_value=True), \
                patch.object(configure_key, "credential_path", return_value=Path("unused-test-target.dpapi")), \
                patch.object(Path, "exists", return_value=True), \
                patch("builtins.input", return_value="no"), \
                patch.object(configure_key.getpass, "getpass") as secret_input, \
                patch.object(configure_key, "save_key") as save, redirect_stdout(io.StringIO()):
            self.assertEqual(configure_key.main(), 1)
            secret_input.assert_not_called()
            save.assert_not_called()

    def test_local_yes_allows_overwrite_and_invalid_key_never_saves(self):
        target = Path("unused-test-target.dpapi")
        for key, expected in (("test-only-key", 0), ("   ", 1), ("invalid key", 1)):
            with self.subTest(expected=expected), \
                    patch.object(configure_key, "is_windows", return_value=True), \
                    patch.object(configure_key, "credential_path", return_value=target), \
                    patch.object(Path, "exists", return_value=True), \
                    patch("builtins.input", return_value="yes"), \
                    patch.object(configure_key.getpass, "getpass", return_value=key), \
                    patch.object(configure_key, "save_key") as save, redirect_stdout(io.StringIO()):
                self.assertEqual(configure_key.main(), expected)
                if expected == 0:
                    save.assert_called_once_with(key, target)
                else:
                    save.assert_not_called()

    def test_no_plaintext_fallback_when_console_cannot_hide_input(self):
        with patch.object(configure_key, "is_windows", return_value=True), \
                patch.object(configure_key, "credential_path", return_value=Path("unused-test-target.dpapi")), \
                patch.object(Path, "exists", return_value=False), \
                patch.object(configure_key.getpass, "getpass", side_effect=configure_key.getpass.GetPassWarning), \
                patch.object(configure_key, "save_key") as save, redirect_stdout(io.StringIO()):
            self.assertEqual(configure_key.main(), 1)
            save.assert_not_called()

    def test_non_windows_uses_environment_guidance_without_prompt_or_file(self):
        with patch.object(configure_key, "is_windows", return_value=False), \
                patch.object(configure_key.getpass, "getpass") as secret_input, \
                patch.object(configure_key, "save_key") as save, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(configure_key.main(), 1)
            self.assertIn("DEEPSEEK_API_KEY", output.getvalue())
            secret_input.assert_not_called()
            save.assert_not_called()


if __name__ == "__main__":
    unittest.main()

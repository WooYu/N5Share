"""HTTP entrypoint: python server/app.py --port 8775. Binds only 127.0.0.1."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import mimetypes
from pathlib import Path
import re
import sys
import threading
from urllib.parse import urlsplit

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.deepseek import DeepSeekClient, MODEL, ModelError, load_key, parse_json
from server.runtime import RunManager, SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
STATIC_FILES = {
    "/": "index.html", "/index.html": "index.html",
    **{"/assets/" + f: "assets/" + f for f in (
        "theme.css", "player.js", "demo-player.js", "content-kit.js", "framework-handout.js")},
    **{"/slides/" + f: "slides/" + f for f in (
        "ch0-opening.js", "ch1-baseline.js", "ch2-react.js", "ch3-plan-reflexion.js",
        "ch4-multi-agent.js", "ch5-frameworks.js", "ch6-dual-agent.js", "ch7-code-review.js", "ch8-closing.js")},
    **{"/data/" + f: "data/" + f for f in (
        "outing-scripts.js", "dual-agent-script.js", "code-review-script.js")},
}
RUN_PATH = re.compile(r"^/api/runs/([0-9a-f]{32})(/cancel)?$")
MAX_BODY = 16384


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False
    request_queue_size = 16

    def __init__(self, port=8775, *, root=ROOT, client=None, credentials=True):
        self.root = Path(root).resolve()
        self.capacity = threading.BoundedSemaphore(16)
        self.credentials_enabled = credentials
        self.credentials_lock = threading.RLock()
        self.closed = False
        self.available, self.reason, self.manager = False, "未配置 DeepSeek 凭据，真实运行已禁用。", None
        super().__init__(("127.0.0.1", port), Handler)
        if client is not None:
            self.manager = RunManager(client)
            self.available, self.reason = True, "已配置测试模型。"
        else:
            self.refresh_credentials()

    def refresh_credentials(self):
        """Activate once credentials appear; preserve every existing run manager."""
        with self.credentials_lock:
            if self.manager is not None or not self.credentials_enabled or self.closed:
                return {"available": self.available, "reason": self.reason, "model": MODEL}
            try:
                if importlib.util.find_spec("httpx") is None:
                    self.reason = "未安装 httpx；请安装 server/requirements.txt。"
                else:
                    key = load_key()
                    if key:
                        self.manager = RunManager(DeepSeekClient(key))
                        self.available, self.reason = True, "已读取本机凭据；实际连通性将在运行时检查。"
                    else:
                        self.reason = "未配置 DeepSeek 凭据；请运行 configure-deepseek.cmd，保存后重新检测。"
            except (ModelError, OSError, UnicodeError):
                self.reason = "本机凭据不可读取；请检查环境变量或 Windows 账户。"
            return {"available": self.available, "reason": self.reason, "model": MODEL}

    @property
    def origin(self):
        return "http://127.0.0.1:" + str(self.server_port)

    def process_request(self, request, client_address):
        if not self.capacity.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.capacity.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            request.settimeout(8)
            super().process_request_thread(request, client_address)
        finally:
            self.capacity.release()

    def server_close(self):
        with self.credentials_lock:
            self.closed = True
            super().server_close()
            if self.manager:
                self.manager.close()
                self.manager = None
            self.available = False


class Handler(BaseHTTPRequestHandler):
    server_version = "N5Local/1"
    sys_version = ""
    protocol_version = "HTTP/1.0"

    def log_message(self, format, *args):
        # Do not print request paths, bodies, model responses or credentials.
        pass

    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        self.close_connection = True

    def fail(self, status, message):
        self.respond(status, {"error": message})

    def validate_origin(self, write=False):
        if self.client_address[0] != "127.0.0.1":
            self.fail(403, "仅允许本机访问。")
            return False
        hosts = self.headers.get_all("Host", [])
        if len(hosts) != 1 or hosts[0] != self.server.origin.removeprefix("http://"):
            self.fail(403, "Host 不在本机白名单中。")
            return False
        origins = self.headers.get_all("Origin", [])
        if len(origins) > 1 or (origins and origins[0] != self.server.origin):
            self.fail(403, "拒绝跨源请求。")
            return False
        if self.headers.get("Sec-Fetch-Site") in {"cross-site", "same-site"}:
            self.fail(403, "拒绝跨源请求。")
            return False
        if write and origins != [self.server.origin]:
            self.fail(403, "写请求必须声明本机同源 Origin。")
            return False
        return True

    def path_only(self):
        if len(self.path) > 2048 or "%" in self.path or "\\" in self.path:
            return None
        parts = urlsplit(self.path)
        if parts.scheme or parts.netloc or parts.fragment or ".." in parts.path.split("/"):
            return None
        return parts.path

    def read_json(self):
        if self.headers.get("Transfer-Encoding"):
            self.fail(400, "不支持分块请求。")
            return None
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isdigit():
            self.fail(411, "必须提供唯一 Content-Length。")
            return None
        size = int(lengths[0])
        if size < 2 or size > MAX_BODY:
            self.fail(413, "JSON 请求大小不在允许范围内。")
            return None
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            self.fail(415, "只接受 application/json。")
            return None
        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise ValueError()
            value = parse_json(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError()
            return value
        except (ValueError, UnicodeError, RecursionError):
            self.fail(400, "JSON 无效或存在重复字段。")
            return None

    def do_GET(self):
        if not self.validate_origin():
            return
        path = self.path_only()
        if path is None:
            return self.fail(400, "请求路径无效。")
        if path == "/api/health":
            return self.respond(200, self.server.refresh_credentials())
        match = RUN_PATH.fullmatch(path)
        if match and not match[2]:
            run = self.server.manager.get(match[1]) if self.server.manager else None
            return self.respond(200, run.snapshot()) if run else self.fail(404, "运行不存在或已过期。")
        relative = STATIC_FILES.get(path)
        if relative is None:
            return self.fail(404, "资源不在课件白名单内。")
        candidate = (self.server.root / relative).resolve()
        if not candidate.is_relative_to(self.server.root) or not candidate.is_file():
            return self.fail(404, "课件资源不存在。")
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if candidate.suffix == ".js":
            mime = "text/javascript"
        try:
            self.respond(200, candidate.read_bytes(), mime + "; charset=utf-8")
        except OSError:
            self.fail(500, "无法读取课件文件。")

    def do_POST(self):
        if not self.validate_origin(write=True):
            return
        path = self.path_only()
        if path is None:
            return self.fail(400, "请求路径无效。")
        match = RUN_PATH.fullmatch(path)
        if path != "/api/runs" and not (match and match[2]):
            return self.fail(404, "接口不存在。")
        body = self.read_json()
        if body is None:
            return
        if path == "/api/runs":
            if set(body) != {"scenario", "weather", "budget"} or not isinstance(body.get("scenario"), str) or body["scenario"] not in SCENARIOS or body.get("weather") not in ("sun", "rain") or type(body.get("budget")) is not int or body["budget"] not in (100, 200, 300):
                return self.fail(400, "参数必须为已知 scenario、sun/rain 和 100/200/300 整数预算。")
            if not self.server.available:
                return self.fail(503, self.server.reason)
            try:
                run = self.server.manager.start(body["scenario"], body["weather"], body["budget"])
            except ModelError as exc:
                return self.fail(429, str(exc))
            return self.respond(202, {"run_id": run.id})
        if body:
            return self.fail(400, "取消请求只能是空 JSON 对象。")
        run = self.server.manager.cancel(match[1]) if self.server.manager else None
        return self.respond(200, {"run_id": run.id, "status": run.status}) if run else self.fail(404, "运行不存在或已过期。")

    def do_OPTIONS(self):
        self.fail(403, "不允许跨源预检。")

    def do_HEAD(self):
        self.do_GET()

    def do_PUT(self):
        self.fail(405, "不支持该方法。")

    do_DELETE = do_PUT
    do_PATCH = do_PUT


def main():
    parser = argparse.ArgumentParser(description="N5 独立课件本地服务（仅 127.0.0.1）")
    parser.add_argument("--port", type=int, default=8775)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port 必须在 1024–65535 范围内")
    server = LocalServer(args.port)
    print("N5: " + server.origin, flush=True)
    print(server.reason, flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

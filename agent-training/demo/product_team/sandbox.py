"""Docker-only execution. No candidate imports, shell commands, or host fallback."""
import base64
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from uuid import uuid4
import queue
import threading

RUNTIME = Path(__file__).with_name('runtime')
DEFAULT_IMAGE = 'python:3.11-slim'


class SandboxError(RuntimeError):
    pass


def docker(*args, timeout=60, input=None):
    try:
        result = subprocess.run(['docker', *map(str, args)], input=input, capture_output=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SandboxError('Docker unavailable or timed out; host execution is disabled') from error
    if result.returncode:
        raise SandboxError(result.stderr[-3000:] or result.stdout[-3000:])
    return result.stdout.strip()


def resolve_image(image=DEFAULT_IMAGE):
    """Never pull implicitly; resolve an installed image to its immutable local ID."""
    server = json.loads(docker('info', '--format', '{{json .}}'))
    if server.get('OSType') != 'linux':
        raise SandboxError('A Linux Docker engine is required')
    info = json.loads(docker('image', 'inspect', image))[0]
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', info['Id']):
        raise SandboxError('Image has no immutable ID')
    # Do not inherit arbitrary image entrypoints, credentials or on-build hooks.
    if info['Config'].get('Entrypoint') or info['Config'].get('OnBuild'):
        raise SandboxError('Use the documented official Python runtime image')
    return info['Id']


class Sandbox:
    def __init__(self, source, image, *, legacy=False, data=None, timeout=30, expected_revision=None, contract=None):
        self.source = Path(source).resolve()
        self.image, self.legacy, self.timeout = image, legacy, timeout
        self.data = Path(data).resolve() if data else None
        self.name = 'training-product-' + uuid4().hex
        self.temp = None
        self.commands = []
        self.expected_revision, self.contract = expected_revision, contract
        self.transport = None
        self.transport_lock = threading.Lock()

    def command(self, *args, **kwargs):
        self.commands.append(['docker', *map(str, args)])
        return docker(*args, **kwargs)

    def __enter__(self):
        self.temp = tempfile.TemporaryDirectory(prefix='product-sandbox-')
        staging = Path(self.temp.name)
        try:
            # Copy before mounting. The executed snapshot cannot follow later source edits.
            from .workspace import read_sources
            files = read_sources(self.source)
            if self.expected_revision:
                from .workspace import digest
                if digest(files, self.contract) != self.expected_revision:
                    raise SandboxError('Snapshot changed before container startup')
            self.snapshot = staging / 'app'
            self.snapshot.mkdir()
            for name, content in files.items():
                target = self.snapshot / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding='utf-8')
            self.data = self.data or staging / 'data'
            self.data.mkdir(parents=True, exist_ok=True)
            self.data.chmod(0o777)
            for path in (self.snapshot, self.data, RUNTIME.resolve()):
                if ',' in str(path):
                    raise SandboxError('Docker mount paths cannot contain commas')
            entry = '/runtime/board_server.py' if self.legacy else '/app/app.py'
            self.command('run', '-d', '--name', self.name, '--pull', 'never',
                         '--network', 'none', '--read-only', '--user', '65534:65534',
                         '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true',
                         '--pids-limit', '64', '--memory', '256m', '--memory-swap', '256m', '--cpus', '1',
                         '--ulimit', 'nofile=256:256', '--log-driver', 'local',
                         '--log-opt', 'max-size=1m', '--log-opt', 'max-file=2',
                         '--tmpfs', '/tmp:rw,noexec,nosuid,size=32m',
                         '--mount', f'type=bind,src={self.snapshot},dst=/app,readonly',
                         '--mount', f'type=bind,src={RUNTIME.resolve()},dst=/runtime,readonly',
                         '--mount', f'type=bind,src={self.data},dst=/data',
                         '--workdir', '/app', '--env', 'APP_DATA=/data', '--env', 'PORT=8080',
                         '--env', 'PYTHONDONTWRITEBYTECODE=1', '--env', 'PYTHONUNBUFFERED=1',
                         '--entrypoint', '/usr/bin/env', self.image, '-i',
                         'PATH=/usr/local/bin:/usr/bin:/bin', 'APP_DATA=/data', 'PORT=8080',
                         'PYTHONDONTWRITEBYTECODE=1', 'PYTHONUNBUFFERED=1', '/usr/local/bin/python', '-B', entry)
            self.wait_ready()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def wait_ready(self):
        deadline = time.monotonic() + self.timeout
        error = None
        while time.monotonic() < deadline:
            try:
                self.request('/')
                return
            except (SandboxError, ValueError) as caught:
                error = caught
                running = self.command('inspect', '--format', '{{.State.Running}}', self.name)
                if running != 'true':
                    raise SandboxError('Candidate exited before serving HTTP: ' + self.logs()) from caught
                time.sleep(.2)
        raise SandboxError('Candidate did not start: ' + str(error))

    def request(self, path, method='GET', body=None, headers=None):
        if not isinstance(path, str) or not path.startswith('/') or path.startswith('//') or '\r' in path or '\n' in path:
            raise ValueError('Only local application paths are accepted')
        value = self.exchange({'path': path, 'method': method, 'body': body,
                               'headers': {'Content-Type': 'application/json', **(headers or {})}})
        return self.decode_response(value)

    @staticmethod
    def decode_response(value):
        try:
            if type(value['status']) is not int or not 100 <= value['status'] <= 599:
                raise ValueError('Invalid HTTP status')
            content = base64.b64decode(value['body'], validate=True)
            return {'status': value['status'], 'raw': content, 'content_type': value['content_type']}
        except (KeyError, TypeError, ValueError) as error:
            raise SandboxError('Invalid HTTP transport response') from error

    def parallel(self, requests):
        from .spec import validate_request
        for request in requests:
            validate_request(request)
        values = self.exchange({'requests': requests})
        if not isinstance(values, list) or len(values) != len(requests):
            raise SandboxError('Invalid parallel HTTP response')
        return [self.decode_response(value) for value in values]

    def exchange(self, request):
        # One persistent transport avoids a Docker CLI process for every browser asset.
        # Separate uid, isolated Python and read-only code; assertions remain on the host.
        with self.transport_lock:
            if self.transport is None:
                command = ['docker', 'exec', '-i', '--user', '0:0', self.name, '/usr/bin/env', '-i',
                           '/usr/local/bin/python', '-I', '/runtime/http_transport.py']
                self.commands.append(command)
                self.transport = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                                  stderr=subprocess.DEVNULL, text=True, encoding='utf-8', bufsize=1)
                self.responses = queue.Queue(maxsize=1)
                stream, responses = self.transport.stdout, self.responses
                def read():
                    while True:
                        line = stream.readline(12_000_000)
                        responses.put(line)
                        if not line:
                            return
                threading.Thread(target=read, daemon=True).start()
            try:
                self.transport.stdin.write(json.dumps(request) + '\n')
                self.transport.stdin.flush()
                raw = self.responses.get(timeout=20)
                value = json.loads(raw)
                if isinstance(value, dict) and 'transport_error' in value:
                    raise SandboxError(value['transport_error'])
                return value
            except (OSError, ValueError, queue.Empty) as error:
                self.stop_transport()
                raise SandboxError('HTTP transport failed or timed out') from error

    def stop_transport(self):
        process, self.transport = self.transport, None
        if process:
            try:
                process.stdin.close()
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=5)
            finally:
                process.stdout.close()

    def restart(self):
        self.stop_transport()
        self.command('restart', '--time', '2', self.name)
        self.wait_ready()

    def logs(self):
        return self.command('logs', '--tail', '60', self.name)[-8000:]

    def __exit__(self, *_):
        self.stop_transport()
        try:
            self.command('rm', '-f', self.name, timeout=15)
        except SandboxError:
            pass
        finally:
            if self.temp:
                self.temp.cleanup()

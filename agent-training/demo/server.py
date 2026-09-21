"""Loopback classroom API and a single explicitly allowed training HTML page."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
import json
import os
from pathlib import Path
import socket
import sys

from agents import GraphRun, PATTERNS, SCENARIOS, ToolBox, run, validate_options
from model_gateway import ModelError, model_status
from outing_live import RunManager, validate_payload

ROOT = Path(__file__).resolve().parents[1]
LIVE_RUNS = RunManager()


class TrainingHTTPServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR can route requests to a stale, second listener.
    allow_reuse_address = os.name != 'nt'

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def readiness():
    result = {'ready': False, 'schema_version': 2, 'engine': 'langgraph',
              'patterns': list(PATTERNS), 'scenarios': list(SCENARIOS),
              'modes': ['simulation'], 'interpreter': sys.executable}
    try:
        result['langgraph_version'] = version('langgraph')
        toolbox = ToolBox()
        GraphRun(toolbox, 30).compile('integrated')
        result['synthetic'] = toolbox.fixtures['synthetic']
        result['ready'] = True
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    return result


class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, content_type='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, status, value):
        self.send(status, json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8'))

    def local_request(self):
        expected = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
        hosts, origins = self.headers.get_all('Host', []), self.headers.get_all('Origin', [])
        if len(hosts) != 1 or hosts[0] not in expected or len(origins) > 1 or (origins and origins[0] not in {'http://' + host for host in expected}):
            # Closing a Windows socket with an unread POST body can reset the
            # connection before the client receives the rejection response.
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) == 1 and lengths[0].isascii() and lengths[0].isdecimal() and not self.headers.get('Transfer-Encoding'):
                length = int(lengths[0])
                if 0 < length <= 4096:
                    try:
                        self.connection.settimeout(1)
                        self.rfile.read(length)
                    except OSError:
                        pass
            self.send_json(403, {'error': 'Origin or Host rejected'})
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        if self.path == '/api/health':
            health = readiness()
            self.send_json(200 if health['ready'] else 503, health)
        elif self.path == '/api/outing/config':
            self.send_json(200, model_status())
        elif self.path.startswith('/api/outing/runs/'):
            trace = LIVE_RUNS.snapshot(self.path.removeprefix('/api/outing/runs/'))
            self.send_json(200 if trace else 404, trace or {'error': '运行不存在或已过期。'})
        elif self.path in ('/', '/index.html'):
            try:
                page = (ROOT / 'index.html').read_bytes()
            except OSError:
                self.send_json(503, {'error': 'Training page has not been built'})
                return
            self.send(200, page, 'text/html; charset=utf-8')
        else:
            self.send_json(404, {'error': 'Not found'})

    def do_POST(self):
        if not self.local_request():
            return
        if self.path not in ('/api/run', '/api/outing/start', '/api/outing/cancel'):
            self.send_json(404, {'error': 'Not found'})
            return
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal() or self.headers.get('Transfer-Encoding'):
                raise ValueError('Exactly one Content-Length required; no transfer encoding')
            length = int(lengths[0])
            if not 0 < length <= 4096 or self.headers.get_content_type() != 'application/json':
                raise ValueError('JSON request required, maximum 4096 bytes')
            self.connection.settimeout(5)
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError('Incomplete request body')

            def unique_object(pairs):
                value = {}
                for key, item in pairs:
                    if key in value:
                        raise ValueError('Duplicate JSON key')
                    value[key] = item
                return value

            payload = json.loads(raw, object_pairs_hook=unique_object)
            if self.path == '/api/outing/start':
                validate_payload(payload)
                try:
                    trace = LIVE_RUNS.start(payload)
                except ModelError as error:
                    self.send_json(503, {'error': str(error)})
                    return
                except ValueError as error:
                    self.send_json(409, {'error': str(error)})
                    return
                self.send_json(202, trace)
                return
            if self.path == '/api/outing/cancel':
                if not isinstance(payload, dict) or set(payload) != {'id'} or not isinstance(payload['id'], str):
                    raise ValueError('仅接受运行 id。')
                stopped = LIVE_RUNS.stop(payload['id'])
                self.send_json(200 if stopped else 404, {'accepted': stopped})
                return
            if not isinstance(payload, dict) or not {'pattern', 'scenario'} <= payload.keys() or not payload.keys() <= {'pattern', 'scenario', 'max_steps'}:
                raise ValueError('Expected pattern, scenario and optional max_steps only')
            validate_options(payload['pattern'], payload['scenario'], payload.get('max_steps', 30))
        except (ValueError, TypeError, OSError) as error:
            self.send_json(400, {'error': str(error)})
            return
        self.send_json(200, run(**payload))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    arguments = parser.parse_args()
    httpd = TrainingHTTPServer(('127.0.0.1', arguments.port), Handler)
    print(f'Agent training: http://127.0.0.1:{httpd.server_port}', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

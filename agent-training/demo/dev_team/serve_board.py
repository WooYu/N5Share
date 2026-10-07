"""Run the generated candidate locally; keep HTTP handling outside model edits."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import re


def handler(root):
    candidate = root / 'candidate'
    spec = importlib.util.spec_from_file_location('delivered_board', candidate / 'board.py')
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)

    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, value):
            body = json.dumps(value, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/':
                body = (candidate / 'index.html').read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif self.path == '/api/tasks':
                store = board.TaskStore(root / 'tasks.db')
                try:
                    self.respond(200, store.list_tasks())
                finally:
                    store.close()
            else:
                self.respond(404, {'error': '路径不存在'})

        def change(self):
            store = board.TaskStore(root / 'tasks.db')
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 1 <= length <= 4096:
                    raise ValueError('请求大小无效')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('需要JSON对象')
                if self.command == 'POST' and self.path == '/api/tasks':
                    if not isinstance(data.get('title'), str):
                        raise ValueError('标题必须是文本')
                    self.respond(201, store.create_task(data['title']))
                elif self.command == 'PATCH' and re.fullmatch(r'/api/tasks/\d+', self.path):
                    if not isinstance(data.get('status'), str):
                        raise ValueError('状态必须是文本')
                    self.respond(200, store.update_status(int(self.path.rsplit('/', 1)[1]), data['status']))
                else:
                    self.respond(404, {'error': '路径不存在'})
            except KeyError:
                self.respond(404, {'error': '任务不存在'})
            except (ValueError, TypeError):
                self.respond(400, {'error': '参数不符合需求契约'})
            finally:
                store.close()

        do_POST = change
        do_PATCH = change

    return Handler


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    print(f'任务看板：http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), handler(args.run_dir.resolve())).serve_forever()

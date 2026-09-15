"""Loopback-only classroom server. No dependency installation required."""
import argparse
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
from agents import run

ROOT=Path(__file__).resolve().parents[1]

class Handler(BaseHTTPRequestHandler):
    def send(self,status,data,content_type):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if urlsplit(self.path).path not in ('/','/index.html'):
            self.send(404,b'Not found','text/plain');return
        self.send(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')

    def do_POST(self):
        if self.path!='/api/run':
            self.send(404,b'Not found','text/plain');return
        host=self.headers.get('Host','')
        expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        origin=self.headers.get('Origin')
        if host not in expected or (origin and origin not in {'http://'+h for h in expected}):
            self.send(403,b'Origin rejected','text/plain');return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=4096 or self.headers.get('Content-Type','').split(';')[0]!='application/json':
                raise ValueError('JSON request required')
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload,dict) or set(payload)!={'inject_failure'} or type(payload['inject_failure']) is not bool:
                raise ValueError('Expected inject_failure boolean')
        except (ValueError,TypeError):
            self.send(400,b'Invalid request','text/plain');return
        state=run(inject_failure=payload['inject_failure'])
        self.send(200,json.dumps(state,ensure_ascii=False).encode('utf-8'),'application/json; charset=utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Agent training: http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

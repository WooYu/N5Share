"""Transport only. Assertions and acceptance results live outside the container."""
import base64
import json
import sys
from concurrent.futures import ThreadPoolExecutor
import threading
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def request_one(request, barrier=None):
    body = request.get('body')
    data = None if body is None else json.dumps(body).encode('utf-8')
    if barrier:
        barrier.wait(timeout=5)
    try:
        response = build_opener(ProxyHandler({}), NoRedirect()).open(Request('http://127.0.0.1:8080' + request['path'], data=data,
                                  method=request.get('method', 'GET'),
                                  headers={'Content-Type': 'application/json', **request.get('headers', {})}), timeout=5)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError('Response too large')
        return {'status': response.status, 'body': base64.b64encode(raw).decode(),
                'content_type': response.headers.get('Content-Type', '')}


for line in sys.stdin:
    try:
        value = json.loads(line)
        if 'requests' in value:
            requests = value['requests']
            if not 2 <= len(requests) <= 8:
                raise ValueError('Invalid parallel batch')
            barrier = threading.Barrier(len(requests))
            with ThreadPoolExecutor(max_workers=len(requests)) as pool:
                response = list(pool.map(lambda request: request_one(request, barrier), requests))
        else:
            response = request_one(value)
        print(json.dumps(response), flush=True)
    except Exception as error:
        print(json.dumps({'transport_error': str(error)}), flush=True)

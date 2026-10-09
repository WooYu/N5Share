"""External regression probes for the defects found in the two live product reviews.

This verifies generated examples; the product orchestrator has no domain branches.
"""
import argparse
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demo'))
from product_team.delivery import proxy_handler
from product_team.sandbox import Sandbox, resolve_image
from product_team.workspace import material, snapshot


def probe(root, output, kind):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    version, release = snapshot(root)
    contract = material(root)
    result = {'probe': kind, 'revision': version, 'passed': False}
    try:
        with Sandbox(release / 'candidate', resolve_image(contract['image']),
                     expected_revision=version, contract=contract) as box:
            if kind == 'booking-invalid-unicode':
                response = box.request('/api/bookings', 'POST', {
                    'room': '\ud800', 'start': '2030-01-01T10:00:00Z',
                    'end': '2030-01-01T11:00:00Z', 'owner': 'probe'})
                result['status'] = response['status']
                assert response['status'] == 400, response
                assert json.loads(box.request('/api/bookings')['raw']) == []
            else:
                keys = []
                class DropFirstResponse(proxy_handler(box)):
                    def do_POST(self):
                        if self.path == '/api/withdrawals':
                            keys.append(self.headers.get('Idempotency-Key'))
                            if len(keys) == 1:
                                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                                response = box.request(self.path, 'POST', body,
                                    {'Authorization': self.headers['Authorization'], 'Idempotency-Key': keys[0]})
                                assert response['status'] == 201
                                self.send_response(201)
                                self.send_header('Content-Type', 'application/json')
                                self.send_header('Content-Length', str(len(response['raw']) + 10))
                                self.end_headers()
                                self.wfile.write(response['raw'][:3])
                                self.close_connection = True
                                return
                        super().dispatch()
                with ThreadingHTTPServer(('127.0.0.1', 0), DropFirstResponse) as server:
                    thread = threading.Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    try:
                        from playwright.sync_api import sync_playwright, expect
                        with sync_playwright() as playwright:
                            browser = playwright.chromium.launch(headless=True, chromium_sandbox=True)
                            try:
                                context = browser.new_context(service_workers='block', accept_downloads=False)
                                origin = f'http://127.0.0.1:{server.server_port}'
                                context.route('**/*', lambda route: route.continue_()
                                              if route.request.url.startswith(origin + '/') else route.abort())
                                page = context.new_page()
                                page.goto(origin)
                                page.locator('#name').fill('响应中断探针')
                                page.locator('#stock').fill('5')
                                page.locator('#add').click()
                                expect(page.locator('#items')).to_contain_text('响应中断探针', timeout=20000)
                                item = json.loads(box.request('/api/items')['raw'])[0]
                                page.locator('#item-id').fill(str(item['id']))
                                page.locator('#quantity').fill('2')
                                page.locator('#withdraw').click()
                                expect(page.locator('#items')).to_contain_text('余量 3', timeout=20000)
                                expect(page.locator('#error')).to_have_text('')
                                assert len(keys) == 2 and keys[0] and keys[0] == keys[1], keys
                                assert json.loads(box.request('/api/items')['raw'])[0]['stock'] == 3
                                screenshot = output.with_suffix('.png')
                                page.screenshot(path=str(screenshot), full_page=True)
                                result.update(requests=2, same_idempotency_key=True, final_stock=3,
                                              screenshot=str(screenshot))
                            finally:
                                browser.close()
                    finally:
                        server.shutdown()
                        thread.join(5)
            result['passed'] = True
    except Exception as error:
        result['error'] = str(error)[:3000]
    output.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result['passed'] else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--probe', required=True, choices=['inventory-response-drop', 'booking-invalid-unicode'])
    args = parser.parse_args()
    raise SystemExit(probe(args.run_dir, args.output, args.probe))

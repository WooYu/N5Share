"""Real browser interaction against a loopback proxy; no external requests."""
from http.server import ThreadingHTTPServer
from pathlib import Path
import threading
import time


def execute_browser(box, cases, evidence_dir, deadline):
    from playwright.sync_api import sync_playwright, expect
    from .delivery import proxy_handler
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadingHTTPServer(('127.0.0.1', 0), proxy_handler(box)) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, chromium_sandbox=True)
                try:
                    context = browser.new_context(accept_downloads=False, service_workers='block')
                    context.route('**/*', lambda route: route.continue_()
                                  if route.request.url.startswith(origin + '/') else route.abort())
                    page = context.new_page()
                    page.set_default_timeout(15000)
                    browser_errors, http = [], []
                    page.on('pageerror', lambda error: browser_errors.append(str(error)[:1000]))
                    page.on('response', lambda response: http.append({'url': response.url, 'status': response.status}))
                    for case in cases:
                        browser_errors.clear()
                        http.clear()
                        try:
                            page.goto(origin + '/')
                            for step in case['steps']:
                                if time.monotonic() >= deadline:
                                    raise TimeoutError('Browser acceptance time budget exhausted')
                                if 'fill' in step:
                                    page.locator(step['fill']).fill(step['value'])
                                elif 'select' in step:
                                    page.locator(step['select']).select_option(step['value'])
                                elif 'click' in step:
                                    page.locator(step['click']).click()
                                elif 'reload' in step:
                                    page.reload()
                                else:
                                    expect(page.locator(step['text'])).to_contain_text(step['contains'], timeout=15000)
                            screenshot = evidence_dir / (case['id'] + '.png')
                            page.screenshot(path=str(screenshot), full_page=True)
                            results.append({'id': case['id'], 'passed': True, 'screenshot': str(screenshot),
                                            'steps': case['steps']})
                        except Exception as error:
                            failed = {'id': case['id'], 'passed': False, 'error': str(error)[:2000],
                                      'browser_errors': list(browser_errors), 'http': list(http)}
                            try:
                                screenshot = evidence_dir / (case['id'] + '-failed.png')
                                page.screenshot(path=str(screenshot), full_page=True, timeout=5000)
                                failed.update(screenshot=str(screenshot), page_text=page.locator('body').inner_text(timeout=2000)[:3000])
                            except Exception:
                                pass
                            results.append(failed)
                finally:
                    browser.close()
        finally:
            server.shutdown()
            thread.join(timeout=5)
    return results

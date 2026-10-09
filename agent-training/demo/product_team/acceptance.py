"""Trusted host-side business assertions. Candidate stdout is never test evidence."""
from concurrent.futures import ThreadPoolExecutor
import json
import time

from .sandbox import Sandbox, SandboxError, resolve_image
from .workspace import material, revision, snapshot


def lookup(value, path):
    for key in path.split('.') if path else []:
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def substitute(value, variables):
    if isinstance(value, str):
        for key, replacement in variables.items():
            token = '${' + key + '}'
            if value == token:
                return replacement
            value = value.replace(token, str(replacement))
        if '${' in value:
            raise ValueError('Unknown acceptance variable')
    elif isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    elif isinstance(value, list):
        return [substitute(v, variables) for v in value]
    return value


def assert_response(response, expected):
    if response['status'] != expected['status']:
        raise AssertionError(f"HTTP {response['status']} != {expected['status']}: {response['raw'][:600]!r}")
    raw = response['raw'].decode('utf-8')
    for text in expected.get('contains', []):
        if text not in raw:
            raise AssertionError('Missing response text: ' + text)
    if any(k in expected for k in ('equals', 'fields', 'types', 'length')):
        value = json.loads(raw)
        if 'equals' in expected and value != expected['equals']:
            raise AssertionError(f'Unexpected JSON: {value!r}')
        for path, wanted in expected.get('fields', {}).items():
            if lookup(value, path) != wanted:
                raise AssertionError(f'{path}: {lookup(value, path)!r} != {wanted!r}')
        types = {'string': str, 'integer': int, 'number': (int, float), 'boolean': bool, 'array': list, 'object': dict}
        for path, kind in expected.get('types', {}).items():
            actual = lookup(value, path)
            allowed = types[kind]
            if type(actual) not in (allowed if isinstance(allowed, tuple) else (allowed,)):
                raise AssertionError(f'{path}: expected {kind}')
        if 'length' in expected and len(value) != expected['length']:
            raise AssertionError('Unexpected result length')
    return raw


def execute_cases(box, cases, deadline=None):
    results, variables = [], {}
    for case in cases:
        evidence = []
        try:
            for original in case['steps']:
                if deadline is not None and time.monotonic() >= deadline:
                    raise SandboxError('Acceptance time budget exhausted')
                step = substitute(original, variables)
                if step.get('restart'):
                    box.restart()
                    evidence.append({'restart': True})
                    continue
                if 'parallel' in step:
                    responses = box.parallel(step['parallel'])
                    if sorted(r['status'] for r in responses) != sorted(step['statuses']):
                        raise AssertionError('Concurrent request statuses do not match: ' + str([r['status'] for r in responses]))
                    evidence.append({'parallel_statuses': [r['status'] for r in responses]})
                    continue
                response = box.request(step['path'], step.get('method', 'GET'), step.get('body'), step.get('headers'))
                raw = assert_response(response, step['expect'])
                evidence.append({'path': step['path'], 'method': step.get('method', 'GET'),
                                 'status': response['status'], 'response': raw[:1000]})
                for name, path in step.get('save', {}).items():
                    variables[name] = lookup(json.loads(raw), path)
            results.append({'id': case['id'], 'passed': True, 'evidence': evidence})
        except (AssertionError, ValueError, KeyError, IndexError, TypeError, SandboxError) as error:
            results.append({'id': case['id'], 'passed': False, 'error': str(error)[:3000], 'evidence': evidence})
    return results


def board_cases():
    """The original public contract, checked through actual HTTP and process restart."""
    return [
        {'id': 'test_frontend', 'steps': [{'path': '/', 'expect': {'status': 200, 'contains': ['<html', '/api/tasks']}}]},
        {'id': 'test_create_and_list', 'steps': [
            {'path': '/api/tasks', 'expect': {'status': 200, 'equals': []}},
            {'path': '/api/tasks', 'method': 'POST', 'body': {'title': '  第一项  '},
             'expect': {'status': 201, 'fields': {'title': '第一项', 'status': 'todo'}, 'types': {'id': 'integer'}}, 'save': {'task_id': 'id'}},
            {'path': '/api/tasks', 'method': 'POST', 'body': {'title': '第二项'},
             'expect': {'status': 201, 'fields': {'title': '第二项', 'status': 'todo'}, 'types': {'id': 'integer'}}},
            {'path': '/api/tasks', 'expect': {'status': 200, 'length': 2, 'fields': {'0.title': '第一项', '1.title': '第二项'}}}]},
        {'id': 'test_empty_and_long_titles_are_rejected', 'steps': [
            {'path': '/api/tasks', 'method': 'POST', 'body': {'title': title}, 'expect': {'status': 400}}
            for title in ('', '   ', 'x' * 121, None, 3)]},
        {'id': 'test_valid_status_survives_reopen', 'steps': [
            *[{'path': '/api/tasks/${task_id}', 'method': 'PATCH', 'body': {'status': status},
               'expect': {'status': 200, 'fields': {'id': '${task_id}', 'title': '第一项', 'status': status},
                          'types': {'id': 'integer', 'title': 'string', 'status': 'string'}}} for status in ('doing', 'done', 'todo')],
            {'restart': True},
            {'path': '/api/tasks', 'expect': {'status': 200, 'length': 2, 'fields': {'0.status': 'todo', '0.id': '${task_id}'}}}]},
        {'id': 'test_invalid_status_is_rejected', 'steps': [
            *[{'path': '/api/tasks/${task_id}', 'method': 'PATCH', 'body': {'status': status}, 'expect': {'status': 400}}
              for status in ('deleted', '', 'DONE', None)],
            {'path': '/api/tasks', 'expect': {'status': 200, 'fields': {'0.status': 'todo'}}}]},
        {'id': 'test_missing_task_is_rejected', 'steps': [
            {'path': '/api/tasks/999999', 'method': 'PATCH', 'body': {'status': 'done'}, 'expect': {'status': 404}}]}
    ]


def run_acceptance(root, timeout=180):
    current = revision(root)
    result = {'revision': current, 'passed': False, 'tool': 'external_http_acceptance',
              'executed': 0, 'cases': [], 'timeout': False, 'exit_code': None}
    start = time.monotonic()
    try:
        _, release = snapshot(root)
        contract = material(root)
        if not contract.get('legacy'):
            from .spec import validate_spec
            validate_spec(contract)
        image = resolve_image(contract.get('image', 'python:3.11-slim'))
        cases = board_cases() if contract.get('legacy') else contract['acceptance']
        if not cases:
            raise ValueError('Zero acceptance cases cannot pass')
        with Sandbox(release / 'candidate', image, legacy=bool(contract.get('legacy')), timeout=min(timeout, 30),
                     expected_revision=current, contract=contract) as box:
            result['cases'] = execute_cases(box, cases, start + timeout)
            if contract.get('browser'):
                from .browser import execute_browser
                result['cases'] += execute_browser(box, contract['browser'], release / 'browser-evidence', start + timeout)
            result['executed'] = len(result['cases'])
            result['commands'] = box.commands
            result['logs'] = box.logs()
        result['passed'] = all(item['passed'] for item in result['cases']) and result['executed'] == len(cases) + len(contract.get('browser', [])) and revision(root) == current
        result['exit_code'] = 0 if result['passed'] else 1
        result['image'] = image
    except Exception as error:
        result['error'] = str(error)
    result['duration_seconds'] = round(time.monotonic() - start, 2)
    result['output'] = json.dumps(result.get('cases') or {'error': result.get('error')}, ensure_ascii=False)
    return result

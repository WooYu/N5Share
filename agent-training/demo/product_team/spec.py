"""User-owned declarative HTTP acceptance; never executable test code."""
import json
from pathlib import Path
import re


def validate_spec(spec):
    required = {'name', 'requirements', 'unresolved', 'acceptance'}
    if not isinstance(spec, dict) or not required <= spec.keys():
        raise ValueError('需求 JSON 需要 name、requirements、unresolved、acceptance')
    if not set(spec) <= required | {'browser', 'image'}:
        raise ValueError('未知需求字段；legacy等内部运行标记不能作为新产品输入')
    if not isinstance(spec['name'], str) or not spec['name'].strip():
        raise ValueError('产品名称为空')
    if not isinstance(spec['requirements'], str) or not 30 <= len(spec['requirements']) <= 30000:
        raise ValueError('需要明确业务需求、角色、接口与持久化契约')
    if spec['unresolved'] != []:
        raise ValueError('核心规则尚未确认：' + str(spec['unresolved']))
    cases = spec['acceptance']
    if not isinstance(cases, list) or not 1 <= len(cases) <= 60:
        raise ValueError('至少需要一项真实业务验收，最多 60 项')
    seen, requests = set(), 0
    for case in cases:
        if not isinstance(case, dict) or set(case) != {'id', 'steps'} or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', case.get('id', '')) or case['id'] in seen:
            raise ValueError('验收 ID 必须唯一且可定位')
        seen.add(case['id'])
        if not isinstance(case['steps'], list) or not 1 <= len(case['steps']) <= 80:
            raise ValueError('验收步骤为空或过多')
        case_requests = 0
        for step in case['steps']:
            if step == {'restart': True}:
                continue
            if 'parallel' in step:
                if set(step) != {'parallel', 'statuses'} or not 2 <= len(step['parallel']) <= 8 or len(step['statuses']) != len(step['parallel']):
                    raise ValueError('并发验收需要 2–8 个请求及各响应的状态码')
                for request in step['parallel']:
                    validate_request(request)
                case_requests += len(step['parallel'])
                continue
            if not set(step) <= {'path', 'method', 'body', 'headers', 'expect', 'save'}:
                raise ValueError('未知验收步骤字段')
            validate_request(step)
            expected = step.get('expect', {})
            if not expected or not set(expected) <= {'status', 'equals', 'fields', 'types', 'length', 'contains'} or type(expected.get('status')) is not int:
                raise ValueError('每个请求必须有外部响应断言')
            if any(t not in ('string', 'integer', 'number', 'boolean', 'array', 'object') for t in expected.get('types', {}).values()):
                raise ValueError('未知响应字段类型')
            case_requests += 1
        if not case_requests:
            raise ValueError('只有重启的用例不能算业务验收')
        requests += case_requests
    if requests > 200:
        raise ValueError('验收请求超过预算')
    browser = spec.get('browser')
    if not isinstance(browser, list) or not 1 <= len(browser) <= 10:
        raise ValueError('新产品需要 1–10 项可操作前端验收 browser')
    for case in browser:
        if (not isinstance(case, dict) or set(case) != {'id', 'steps'}
                or not isinstance(case.get('id'), str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', case['id']) or case['id'] in seen):
            raise ValueError('浏览器验收 ID 无效或重复')
        seen.add(case['id'])
        if not isinstance(case['steps'], list) or not 1 <= len(case['steps']) <= 30:
            raise ValueError('浏览器步骤为空或过多')
        has_assertion = False
        for step in case['steps']:
            if step == {'reload': True}:
                continue
            keys = set(step)
            if keys not in ({'fill', 'value'}, {'click'}, {'text', 'contains'}, {'select', 'value'}):
                raise ValueError('未知浏览器操作')
            if any(not isinstance(v, str) or not v or len(v) > 500 for v in step.values()):
                raise ValueError('浏览器选择器或输入无效')
            has_assertion |= 'text' in step
        if not has_assertion:
            raise ValueError('浏览器用例必须包含可见结果断言')
    return spec


def validate_request(step):
    path = step.get('path')
    if not isinstance(path, str) or not path.startswith('/') or path.startswith('//') or any(c in path for c in '\r\n'):
        raise ValueError('验收只能请求应用内部路径')
    if step.get('method', 'GET') not in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
        raise ValueError('不支持的请求方法')
    if len(json.dumps(step)) > 20000:
        raise ValueError('请求过大')


def load_spec(path):
    path = Path(path)
    if path.stat().st_size > 200000:
        raise ValueError('需求文件过大')
    return validate_spec(json.loads(path.read_text(encoding='utf-8-sig')))

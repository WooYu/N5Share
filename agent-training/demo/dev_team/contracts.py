"""Structured evidence validation and deterministic delivery decisions."""
from .tools import fingerprint


class ContractError(ValueError):
    pass


FINDING_FIELDS = {'id', 'severity', 'file', 'line', 'end_line', 'title', 'evidence', 'impact', 'suggestion', 'test_name'}
REVIEW_SCHEMA = {'type': 'object', 'additionalProperties': False,
    'properties': {'verdict': {'type': 'string', 'enum': ['pass', 'request_changes', 'needs_context']},
        'summary': {'type': 'string'}, 'findings': {'type': 'array', 'items': {
            'type': 'object', 'additionalProperties': False,
            'properties': {**{key: {'type': 'string'} for key in FINDING_FIELDS - {'severity', 'line', 'end_line'}},
                'severity': {'type': 'string', 'enum': ['high', 'medium', 'low']},
                'line': {'type': 'integer'}, 'end_line': {'type': 'integer'}},
            'required': sorted(FINDING_FIELDS)}}}, 'required': ['verdict', 'summary', 'findings']}


def validate_review(report, context):
    if not isinstance(report, dict) or set(report) != {'verdict', 'summary', 'findings'}:
        raise ContractError('评审字段无效')
    if report['verdict'] not in ('pass', 'request_changes', 'needs_context'):
        raise ContractError('未知评审结论')
    if not isinstance(report['summary'], str) or not 1 <= len(report['summary']) <= 2000:
        raise ContractError('缺少有效评审摘要')
    if not isinstance(report['findings'], list) or len(report['findings']) > 12:
        raise ContractError('问题列表无效')
    if not context['complete'] and report['verdict'] != 'needs_context':
        raise ContractError('上下文不足不能给出完整评审结论')
    ids = set()
    for finding in report['findings']:
        if not isinstance(finding, dict) or set(finding) != FINDING_FIELDS:
            raise ContractError('问题字段无效')
        if any(not isinstance(finding[key], str) or not finding[key].strip() or not 1 <= len(finding[key]) <= 3000
               for key in FINDING_FIELDS - {'line', 'end_line'}):
            raise ContractError('问题文本为空或过长')
        if finding['id'] in ids or finding['severity'] not in ('high', 'medium', 'low'):
            raise ContractError('问题标识或严重度无效')
        ids.add(finding['id'])
        path = finding['file']
        if path not in context['files'] or path not in context['changed_files']:
            raise ContractError('问题必须定位到本轮变更文件')
        lines = context['files'][path].splitlines()
        start, end = finding['line'], finding['end_line']
        if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines) or end - start > 12:
            raise ContractError('问题行号超出文件范围')
        if finding['evidence'].strip() not in '\n'.join(lines[start - 1:end]):
            raise ContractError('问题证据不在声明的代码行中')
    blocking = any(item['severity'] in ('high', 'medium') for item in report['findings'])
    if report['verdict'] == 'pass' and blocking:
        raise ContractError('存在阻断问题不能通过')
    if report['verdict'] == 'request_changes' and not blocking:
        raise ContractError('退回修改须提供阻断问题及证据')
    return {**report, 'revision': context['revision']}


def delivery_gate(root, review, tests, decision=None, approved_revision=None):
    current = fingerprint(root)
    if review.get('revision') != current or tests.get('revision') != current:
        return {'status': 'stale', 'reason': '代码或验收材料已变化，必须重新评审和测试'}
    if review.get('verdict') == 'needs_context':
        return {'status': 'needs_context', 'reason': '补齐上下文后重新评审'}
    if review.get('verdict') != 'pass' or not tests.get('passed'):
        return {'status': 'needs_fix', 'reason': '评审或固定验收未通过'}
    if decision is None:
        return {'status': 'waiting_approval', 'reason': '评审与验收完成，等待人工批准当前版本'}
    if approved_revision != current:
        return {'status': 'stale', 'reason': '批准版本不匹配'}
    if decision == 'reject':
        return {'status': 'rejected', 'reason': '人工退回，保留材料'}
    if decision == 'approve':
        return {'status': 'completed', 'reason': '当前版本评审、验收及人工批准均已满足'}
    raise ContractError('未知人工决定')

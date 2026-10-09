"""Shared fail-closed policy, also shipped with standalone deliveries."""
from .workspace import material, revision


def delivery_gate(root, review, tests, decision=None, approved_revision=None):
    current = revision(root)
    if review.get('revision') != current or tests.get('revision') != current:
        return {'status': 'stale', 'reason': '源码、需求或验收器已变化，必须重新评审和测试'}
    if review.get('verdict') == 'needs_context':
        return {'status': 'needs_context', 'reason': '补齐上下文后重新评审'}
    contract = material(root)
    from .acceptance import board_cases
    required = contract['acceptance'] + contract.get('browser', []) if not contract.get('legacy') else board_cases()
    cases = tests.get('cases', [])
    if (review.get('verdict') != 'pass'
            or any(f.get('severity') in ('high', 'medium') for f in review.get('findings', []))
            or tests.get('passed') is not True or tests.get('tool') != 'external_http_acceptance'
            or type(tests.get('executed')) is not int or tests['executed'] < 1
            or tests['executed'] != len(cases)
            or [c.get('id') for c in cases] != [c['id'] for c in required]
            or not all(c.get('passed') is True for c in cases)
            or not tests.get('image', '').startswith('sha256:')):
        return {'status': 'needs_fix', 'reason': '评审或外部业务验收未通过'}
    if decision is None:
        return {'status': 'waiting_approval', 'reason': '评审与验收完成，等待人工批准当前版本'}
    if approved_revision != current:
        return {'status': 'stale', 'reason': '批准版本不匹配'}
    if decision == 'reject':
        return {'status': 'rejected', 'reason': '人工退回，保留材料'}
    if decision == 'approve':
        return {'status': 'completed', 'reason': '当前版本评审、业务验收及人工批准均已满足'}
    raise ValueError('未知人工决定')

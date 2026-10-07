"""Real Python tools over fixed classroom sources; no external venue service."""
from copy import deepcopy

VENUES = [
    dict(venue='城市博物馆', indoor=True, adult=50, child=20, transport=30, ref='VENUE-001'),
    dict(venue='互动科学馆', indoor=True, adult=80, child=40, transport=30, ref='VENUE-002'),
    dict(venue='滨河公园', indoor=False, adult=0, child=0, transport=60, ref='VENUE-003'),
]


def missing_fields(state):
    return [key for key in ('candidates', 'meal', 'meal_ref') if key not in state['evidence']]


def read_sources(state, scenario):
    """Only the first read is incomplete in the missing-data scenario."""
    rounds = state['research_rounds'] + 1
    evidence = {'candidates': deepcopy(VENUES)}
    if scenario == 'normal' or rounds > 1:
        evidence.update(meal=90, meal_ref='FOOD-001')
    return dict(evidence=evidence, research_rounds=rounds, research_done=True,
                needs_research=False, analysis=[], analyzed=False, proposal=None,
                approved=False, issues=missing_fields({'evidence': evidence}))


def calculate_costs(state):
    """Missing money is never interpreted as zero."""
    missing = missing_fields(state)
    if missing:
        return dict(analysis=[], analyzed=False, issues=missing, approved=False)
    rows = [dict(venue=venue['venue'], indoor=venue['indoor'], ref=venue['ref'],
                 tickets=2 * venue['adult'] + venue['child'], transport=venue['transport'],
                 meal=state['evidence']['meal'],
                 total=2 * venue['adult'] + venue['child'] + venue['transport'] + state['evidence']['meal'])
            for venue in state['evidence']['candidates']]
    return dict(analysis=rows, analyzed=True, issues=[], approved=False)


def validate_proposal(state):
    """Independently check the model draft from observed source values."""
    issues = missing_fields(state)
    if issues:
        return issues
    proposal = state.get('proposal')
    if not state.get('analyzed') or not proposal:
        return ['尚无完整核算或建议']
    rows = calculate_costs(state)['analysis']
    feasible = [row for row in rows if (state['weather'] == 'sun' or row['indoor']) and row['total'] <= state['budget']]
    selected = min(feasible, key=lambda row: row['total']) if feasible else None
    if (proposal['venue'], proposal['total']) != ((selected['venue'], selected['total']) if selected else ('', 0)):
        return ['模型建议与天气、完整费用或预算不一致']
    if not proposal.get('text'):
        return ['缺少建议正文']
    return []

"""VS Code entry: MetaGPT artifacts, real review/fix loop and explicit approval."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

# Import the model gateway only on live runs; approval/checks need no model or MetaGPT.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dev_team.contracts import delivery_gate
from dev_team.tools import fingerprint, run_tests, write_json


def decide(root, decision, revision):
    root = Path(root).resolve()
    state = json.loads((root / 'state.json').read_text(encoding='utf-8'))
    if state['status'] != 'waiting_approval':
        raise ValueError('当前任务没有等待审批；不能重复或跨阶段批准')
    if revision != fingerprint(root):
        raise ValueError('审批版本已变化，必须重新运行评审')
    current_tests = run_tests(root)
    gate = delivery_gate(root, state['review'], current_tests, decision, revision)
    state.update(gate, tests=current_tests, human_decision={'decision': decision, 'revision': revision})
    write_json(root / 'state.json', state)
    print(json.dumps(gate, ensure_ascii=False, indent=2))
    return 0 if gate['status'] in ('completed', 'rejected') else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=('buggy', 'clean', 'incomplete'), default='buggy')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--step', action='store_true')
    parser.add_argument('--max-repairs', type=int, default=2)
    parser.add_argument('--max-model-calls', type=int, default=12)
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--decision', choices=('approve', 'reject'))
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--revision')
    options = parser.parse_args()
    if options.decision:
        if not options.run_dir or not options.revision:
            parser.error('人工决定需要 --run-dir 与 --revision（见 state.json）')
        try:
            return decide(options.run_dir, options.decision, options.revision)
        except (ValueError, OSError, KeyError) as error:
            print('审批未执行：' + str(error))
            return 2
    if options.max_repairs < 0 or options.max_model_calls < 1 or options.max_seconds < 1:
        parser.error('修复次数须非负；模型次数和时间须为正整数')
    from dev_team.session import Session, new_run_directory
    from model_gateway import ModelError
    session = None
    try:
        session = Session(options.output or new_run_directory(), options.scenario, options.max_repairs,
                          options.max_model_calls, options.max_seconds, options.step)
        print('运行目录：' + str(session.root), flush=True)
        print('实际模型配置：' + json.dumps(session.model.metadata, ensure_ascii=False))
        from dev_team.bootstrap import prepare_runtime
        prepare_runtime(session.root)
        from dev_team.team import run_team
        asyncio.run(run_team(session))
    except Exception as error:
        if session:
            session.state['status'] = 'failed'
            session.emit('Host', 'failed', type(error).__name__ + '：' + str(error))
        else:
            print('无法启动：' + str(error))
        return 2
    print('运行目录：' + str(session.root))
    print('结果：' + session.state['status'])
    if session.state['status'] == 'waiting_approval':
        print('待批准版本：' + session.state['review']['revision'])
    return 0 if session.state['status'] == 'waiting_approval' else 2


if __name__ == '__main__':
    raise SystemExit(main())

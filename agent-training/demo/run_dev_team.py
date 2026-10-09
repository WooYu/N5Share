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
    from product_team.delivery import approve
    state = approve(root, decision, revision)
    print(json.dumps({'status': state['status'], 'revision': revision}, ensure_ascii=False, indent=2))
    return 0 if state['status'] in ('completed', 'rejected') else 2


def main(argv=None):
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
    parser.add_argument('--requirements', type=Path, help='业务需求与外部 HTTP 验收 JSON')
    parser.add_argument('--resume', action='store_true', help='从 --output 恢复；复用源码并重新评审与验收')
    parser.add_argument('--check', action='store_true', help='只校验需求与 Docker 环境，不调用模型')
    parser.add_argument('--serve', action='store_true', help='只启动已批准版本，需 --run-dir')
    parser.add_argument('--port', type=int, default=8766)
    options = parser.parse_args(argv)
    if options.serve:
        if not options.run_dir:
            parser.error('--serve 需要 --run-dir')
        from product_team.delivery import serve
        serve(options.run_dir, options.port)
        return 0
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
        from product_team.spec import load_spec
        from product_team.sandbox import resolve_image
        from product_team.delivery import run_lock
        product = load_spec(options.requirements) if options.requirements else None
        if options.resume:
            if not options.output or options.requirements:
                parser.error('--resume 需要 --output；不能替换原任务需求')
            saved = options.output / 'product.json'
            product = load_spec(saved) if saved.exists() else None
        image = resolve_image((product or {}).get('image', 'python:3.11-slim'))
        if product:
            product['image'] = image
        if options.check:
            print(json.dumps({'status': 'environment_ready', 'image': image,
                              'product': product['name'] if product else 'legacy-review', 'model_calls': 0}))
            return 0
        with run_lock(options.output or new_run_directory()) as locked_root:
            session = Session(locked_root, options.scenario, options.max_repairs,
                              options.max_model_calls, options.max_seconds, options.step,
                              product=product, resume=options.resume)
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

"""Model budget, explicit provider fallback and inspectable action artifacts."""
import asyncio
from datetime import datetime
import json
from pathlib import Path
import threading
import time

from model_gateway import create_model, ModelError, ModelUnavailable
from .contracts import ContractError
from .tools import write_json


class Session:
    def __init__(self, root, scenario='buggy', max_repairs=2, max_calls=12, max_seconds=600,
                 step=False, model=None, product=None, resume=False):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.resuming = resume
        if (self.root / 'state.json').exists() and not resume:
            raise ContractError('运行目录已存在，请使用 --resume 恢复或指定新目录')
        self.product = product
        self.scenario, self.step = scenario, step
        self.model = model or create_model()
        self.deadline = time.monotonic() + max_seconds
        self.cancel = threading.Event()
        self._checked = None
        self.state = {'schema_version': 1, 'scenario': scenario, 'status': 'running',
                      'repair_round': 0, 'max_repairs': max_repairs, 'calls': 0, 'max_calls': max_calls,
                      'events': [], 'review': {}, 'tests': {}, 'usage': {}, 'model': self.model.metadata}
        if resume:
            self.state = json.loads((self.root / 'state.json').read_text(encoding='utf-8'))
            if self.state['status'] == 'rejected':
                raise ContractError('已结束的任务不能恢复；请新建运行')
            self.state.update(status='running', review={}, tests={})
            self.state.pop('human_decision', None)
            self.state.pop('release', None)
            self.state['max_calls'] = max(self.state['max_calls'], max_calls)
            path = self.root / 'product.json'
            self.product = json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        elif product:
            write_json(self.root / 'product.json', product)

    def remaining_time(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ContractError('总运行时限已耗尽；未接受迟到结果')
        return remaining

    async def check_candidate(self):
        from .tools import run_tests, fingerprint
        current = fingerprint(self.root)
        if self._checked and self._checked['revision'] == current:
            return self._checked
        result = await asyncio.to_thread(run_tests, self.root, min(180, self.remaining_time()))
        self.remaining_time()
        self._checked = result
        return result

    def emit(self, actor, kind, message, **data):
        event = {'index': len(self.state['events']) + 1, 'actor': actor, 'kind': kind,
                 'message': message, **data}
        self.state['events'].append(event)
        self.state['model'] = self.model.metadata
        print(f"[{event['index']:02}] {actor} / {kind}: {message}", flush=True)
        write_json(self.root / 'state.json', self.state)

    async def ask(self, actor, instruction, context, schema, validator=None):
        """Actions call the existing gateway, on a worker thread, with JSON contracts."""
        for attempt in range(2):
            remaining = self.remaining_time()
            if self.state['calls'] >= self.state['max_calls']:
                raise ContractError('模型调用次数或总时限已耗尽')
            self.model.timeout = min(300 if actor == 'Developer' else 120, remaining)
            self.state['calls'] += 1
            self.emit(actor, 'model_request', f"第 {self.state['calls']} 次真实模型请求")
            try:
                answer, usage = await asyncio.to_thread(self.model.generate_json, instruction, context, self.cancel, schema)
            except ModelUnavailable:
                if not getattr(self.model, 'activate_fallback', lambda: False)():
                    raise
                self.emit(actor, 'provider_switch', '连接不可用，显式切换备用供应商')
                continue
            for key, value in usage.items():
                self.state['usage'][key] = self.state['usage'].get(key, 0) + value
            self.remaining_time()
            try:
                checked = validator(answer) if validator else answer
            except (ContractError, ValueError, TypeError, KeyError, SyntaxError) as error:
                self.artifact(f"invalid-output-{self.state['calls']}.json", answer)
                self.emit(actor, 'invalid_output', '输出契约不满足：' + str(error))
                if attempt:
                    raise ContractError('模型两次输出均未通过契约校验') from None
                instruction += '\n上一轮输出未被执行，请修正以下契约错误：' + str(error)
                continue
            self.emit(actor, 'model_result', '结构化输出已收到并完成程序校验')
            return checked
        raise ModelError('未取得有效模型输出')

    async def before_action(self, actor, action, causes):
        self.remaining_time()
        self.emit(actor, 'action', action, cause_by=causes)
        if self.step:
            await asyncio.to_thread(input, '在 VS Code 查看源码和当前消息后，按 Enter 执行此行动…')
            self.remaining_time()

    def artifact(self, name, value):
        path = self.root / name
        if isinstance(value, str):
            path.write_text(value, encoding='utf-8')
        else:
            write_json(path, value)
        return str(path)


def new_run_directory():
    from uuid import uuid4
    return Path(__file__).resolve().parents[1] / 'output' / 'dev-team' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid4().hex[:6])

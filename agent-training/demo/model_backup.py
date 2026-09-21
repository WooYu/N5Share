"""DeepSeek official API backup and explicit per-run provider selection."""
import asyncio
import json
import time

import httpx

from model_gateway import CodexModel, ModelError, ModelCancelled, ModelUnavailable, STEP_SCHEMA, check_step
from secret_store import load_deepseek_key


class DeepSeekModel:
    def __init__(self, api_key=None, transport=None):
        try:
            self._key = api_key or load_deepseek_key()
        except (OSError, ValueError):
            raise ModelUnavailable('无法解密本机 DeepSeek 备用凭据。') from None
        if not self._key:
            raise ModelUnavailable('尚未配置 DeepSeek 备用凭据。')
        self._transport = transport
        self.timeout = 90
        self.metadata = {'provider': 'DeepSeek', 'model': 'deepseek-flash', 'transport': 'deepseek-api',
                         'protocol': 'structured-action', 'credential_source': '本机受保护凭据或环境变量'}

    async def _request(self, instruction, context, cancel):
        example = {'summary': '简短决策摘要', 'calls': [], 'plan': [], 'reflection': '', 'next_actor': '', 'result': None}
        system = ('你是课堂模型。仅返回符合下列 schema 的 JSON 对象，必须包含全部字段。'
                  '使用简体中文，summary 不超过120字，只提供简短决策摘要，不输出内部思维过程。'
                  'calls 是交给宿主执行的工具请求，不得伪造实际观察。未使用的数组为空、字符串为空、result为null。'
                  'JSON示例：' + json.dumps(example, ensure_ascii=False) + '\nJSON schema：' + json.dumps(STEP_SCHEMA, ensure_ascii=False))
        payload = {'model': self.metadata['model'], 'stream': False, 'max_tokens': 2500,
                   'thinking': {'type': 'disabled'}, 'response_format': {'type': 'json_object'},
                   'messages': [{'role': 'system', 'content': system},
                                {'role': 'user', 'content': json.dumps({'instruction': instruction, 'context': context}, ensure_ascii=False)}]}
        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport, follow_redirects=False) as client:
            task = asyncio.create_task(client.post('https://api.deepseek.com/chat/completions',
                headers={'Authorization': 'Bearer ' + self._key}, json=payload))
            started = time.monotonic()
            try:
                while not task.done():
                    if cancel.is_set():
                        raise ModelCancelled('已停止 DeepSeek 请求。')
                    if time.monotonic() - started >= self.timeout:
                        raise ModelUnavailable('DeepSeek 请求超时。')
                    await asyncio.wait({task}, timeout=.1)
                response = await task
            except httpx.HTTPError:
                raise ModelUnavailable('DeepSeek 网络连接失败或请求超时。') from None
            finally:
                if not task.done():
                    task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        if cancel.is_set():
            raise ModelCancelled('已停止 DeepSeek 请求。')
        errors = {400: '请求参数不被接受', 401: '密钥无效', 402: '账户余额不足', 403: '访问被拒绝',
                  404: '模型或接口不存在', 429: '请求限流', 500: '服务内部错误', 503: '服务暂不可用'}
        if response.status_code != 200:
            raise ModelUnavailable(f'DeepSeek：{errors.get(response.status_code, "调用未完成")}（HTTP {response.status_code}）。')
        try:
            data = response.json()
            choice = data['choices'][0]
            if choice.get('finish_reason') != 'stop':
                raise ModelError('DeepSeek 输出未完整结束，未执行该轮工具。')
            answer = json.loads(choice['message']['content'])
            usage = data.get('usage', {})
            counts = {'input_tokens': usage.get('prompt_tokens', 0), 'output_tokens': usage.get('completion_tokens', 0)}
            if any(type(value) is not int or value < 0 for value in counts.values()):
                raise ValueError('Invalid usage')
        except (ValueError, KeyError, TypeError, IndexError):
            raise ModelError('DeepSeek 返回的 JSON 不完整或格式无效，未执行该轮工具。') from None
        return check_step(answer), counts

    def generate(self, instruction, context, cancel):
        if cancel.is_set():
            raise ModelCancelled('已停止 DeepSeek 请求。')
        return asyncio.run(self._request(instruction, context, cancel))


class ModelRouter:
    def __init__(self, primary, backup=None, startup_reason=None):
        self.active = primary
        self.backup = backup
        self.startup_fallback_reason = startup_reason
        self.switched = bool(startup_reason)

    @property
    def metadata(self):
        return {**self.active.metadata, 'fallback': self.backup.metadata if self.backup else None,
                'using_backup': self.switched}

    @property
    def timeout(self):
        return getattr(self.active, 'timeout', 90)

    @timeout.setter
    def timeout(self, value):
        self.active.timeout = value

    def activate_fallback(self):
        if not self.backup or self.switched:
            return False
        self.active = self.backup
        self.switched = True
        return True

    def generate(self, instruction, context, cancel):
        return self.active.generate(instruction, context, cancel)


def create_model():
    try:
        backup = DeepSeekModel()
    except ModelUnavailable:
        backup = None
    try:
        return ModelRouter(CodexModel(), backup)
    except ModelError as error:
        if backup:
            return ModelRouter(backup, startup_reason=str(error))
        raise

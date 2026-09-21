"""Read the selected CCSwitch provider and invoke the official Codex CLI.

Credentials stay in process memory and the child environment, never in a trace.
The upstream account used in this course permits official Codex clients only.
"""
from dataclasses import dataclass, field
from contextlib import closing
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from urllib.parse import urlsplit
from process_scope import ProcessScope


class ModelError(RuntimeError):
    pass


class ModelCancelled(ModelError):
    pass


class ModelUnavailable(ModelError):
    """Connection, credential, quota, or client availability failure."""
    pass


@dataclass
class Provider:
    name: str
    model: str
    base_url: str = field(repr=False)
    api_key: str = field(repr=False)


def load_provider(root=None):
    root = Path(root) if root else Path.home() / '.cc-switch'
    try:
        settings = json.loads((root / 'settings.json').read_text(encoding='utf-8'))
        selected = settings.get('currentProviderCodex')
        with closing(sqlite3.connect((root / 'cc-switch.db').resolve().as_uri() + '?mode=ro', uri=True)) as db:
            if selected:
                row = db.execute("SELECT name, settings_config FROM providers WHERE app_type='codex' AND id=?", (selected,)).fetchone()
            else:
                rows = db.execute("SELECT name, settings_config FROM providers WHERE app_type='codex' AND is_current=1").fetchall()
                row = rows[0] if len(rows) == 1 else None
        if not row:
            raise ModelError('请在 CCSwitch 中选择一个 Codex 供应商。')
        data = json.loads(row[1])
        config = tomllib.loads(data['config'])
        model = config['model']
        connection = config['model_providers'][config['model_provider']]
        endpoint = connection['base_url'].rstrip('/')
        key = data.get('auth', {}).get('OPENAI_API_KEY', '')
        parsed = urlsplit(endpoint)
        if not isinstance(key, str) or not key.strip():
            raise ModelError('当前 CCSwitch 配置没有 API 密钥。')
        if not isinstance(model, str) or not model or len(model) > 150:
            raise ModelError('当前 CCSwitch 配置没有有效模型名称。')
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ModelError('模型地址必须是没有内嵌凭据的 HTTPS 地址。')
        if connection.get('wire_api', 'responses') != 'responses':
            raise ModelError('本演示需要 CCSwitch 的 Codex Responses 配置。')
        return Provider(row[0], model, endpoint, key)
    except ModelError:
        raise
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        raise ModelError('无法读取 CCSwitch 当前配置，请确认已安装并选中 Codex 供应商。') from None


def codex_command():
    installed = shutil.which('codex')
    if installed:
        file = Path(installed)
        if file.suffix.lower() not in ('.cmd', '.ps1', '.bat'):
            return [str(file)]
        # Avoid shell=True and batch quoting: invoke npm's JS entry directly.
        entry = file.parent / 'node_modules' / '@openai' / 'codex' / 'bin' / 'codex.js'
        node = shutil.which('node')
        if entry.is_file() and node:
            native = entry.parents[1] / 'node_modules' / '@openai' / 'codex-win32-x64' / 'vendor' / 'x86_64-pc-windows-msvc' / 'bin' / 'codex.exe'
            return [str(native)] if native.is_file() else [node, str(entry)]
    raise ModelError('未找到官方 Codex CLI，请安装并确保 codex 命令可用。')


RESULT_SCHEMA = {'type': 'object', 'properties': {
    'status': {'type': 'string', 'enum': ['pending', 'recommended', 'no_solution']},
    'place_id': {'type': 'string', 'enum': ['', 'P01', 'P02', 'P03']},
    'total': {'type': 'integer'}, 'citations': {'type': 'array', 'items': {'type': 'string'}},
    'text': {'type': 'string'}},
    'required': ['status', 'place_id', 'total', 'citations', 'text'], 'additionalProperties': False}

STEP_SCHEMA = {'type': 'object', 'properties': {
    'summary': {'type': 'string'},
    'calls': {'type': 'array', 'items': {'type': 'object', 'properties': {
        'name': {'type': 'string', 'enum': ['read_weather', 'read_catalog', 'calculate_cost']},
        'place_id': {'type': 'string', 'enum': ['', 'P01', 'P02', 'P03']}},
        'required': ['name', 'place_id'], 'additionalProperties': False}},
    'plan': {'type': 'array', 'items': {'type': 'string'}},
    'reflection': {'type': 'string'},
    'next_actor': {'type': 'string', 'enum': ['', 'weather', 'cost', 'summary', 'outing_lead', 'budget_lead']},
    'result': {'anyOf': [RESULT_SCHEMA, {'type': 'null'}]}},
    'required': ['summary', 'calls', 'plan', 'reflection', 'next_actor', 'result'],
    'additionalProperties': False}


def check_step(value):
    if not isinstance(value, dict) or set(value) != set(STEP_SCHEMA['required']):
        raise ModelError('模型没有返回完整的结构化行动，运行已停止。')
    for key in ['summary', 'reflection']:
        if not isinstance(value[key], str) or len(value[key]) > 2500:
            raise ModelError('模型输出文字格式或长度无效。')
    if not isinstance(value['plan'], list) or len(value['plan']) > 10 or any(not isinstance(x, str) or len(x) > 500 for x in value['plan']):
        raise ModelError('模型计划格式无效。')
    if not isinstance(value['calls'], list) or len(value['calls']) > 5:
        raise ModelError('单轮工具请求过多或格式无效。')
    for call in value['calls']:
        if not isinstance(call, dict) or set(call) != {'name', 'place_id'} or call['name'] not in ['read_weather', 'read_catalog', 'calculate_cost'] or call['place_id'] not in ['', 'P01', 'P02', 'P03']:
            raise ModelError('模型提出了未获允许的工具或参数。')
    if value['next_actor'] not in STEP_SCHEMA['properties']['next_actor']['enum']:
        raise ModelError('模型提出了未知的协作角色。')
    result = value['result']
    if result is not None:
        if not isinstance(result, dict) or set(result) != set(RESULT_SCHEMA['required']):
            raise ModelError('模型结果格式无效。')
        if result['status'] not in ['pending', 'recommended', 'no_solution'] or result['place_id'] not in ['', 'P01', 'P02', 'P03'] or type(result['total']) is not int or not isinstance(result['text'], str) or len(result['text']) > 4000:
            raise ModelError('模型结果字段无效。')
        if not isinstance(result['citations'], list) or len(result['citations']) > 20 or any(not isinstance(x, str) or len(x) > 80 for x in result['citations']):
            raise ModelError('模型引用格式无效。')
    return value


class CodexModel:
    def __init__(self, provider=None, timeout=90):
        self.provider = provider or load_provider()
        self.command = codex_command()
        self.timeout = timeout
        self.metadata = {'provider': self.provider.name, 'model': self.provider.model,
                         'transport': 'codex-cli', 'protocol': 'structured-action',
                         'credential_source': 'CCSwitch 当前 Codex 配置'}

    def generate(self, instruction, context, cancel):
        if cancel.is_set():
            raise ModelCancelled('运行已停止。')
        # ASCII JSON also avoids console codepage corruption on Windows.
        prompt = json.dumps({'instruction': instruction, 'context': context}, ensure_ascii=True)
        prefix = ('You are a classroom model. Interpret Unicode escapes in the JSON below. '
                  'Return ONLY the requested JSON. Write human-facing text in Simplified Chinese. '
                  'Do not use any Codex tools, access files, execute commands, or browse. '
                  'Tool requests in calls are proposals for the classroom host to execute later. '
                  'Never invent observations. summary is a brief decision summary, not private reasoning. '
                  'Keep summary under 120 Chinese characters. Unused arrays must be empty.\n')
        with tempfile.TemporaryDirectory(prefix='agent-classroom-') as directory:
            root = Path(directory)
            schema, output = root / 'schema.json', root / 'answer.json'
            schema.write_text(json.dumps(STEP_SCHEMA), encoding='utf-8')
            args = self.command + ['exec', '--ignore-user-config', '--ephemeral', '--skip-git-repo-check',
                                   '--sandbox', 'read-only', '--json', '--color', 'never',
                                   '-m', self.provider.model, '-C', directory,
                                   '--output-schema', str(schema), '-o', str(output)]
            for setting in ['model_provider="classroom"', 'model_providers.classroom.name="Classroom"',
                            'model_providers.classroom.base_url=' + json.dumps(self.provider.base_url),
                            'model_providers.classroom.wire_api="responses"',
                            'model_providers.classroom.env_key="CODEX_API_KEY"',
                            'features.shell_tool=false', 'features.multi_agent=false',
                            'features.plugins=false', 'features.remote_plugin=false',
                            'features.skill_search=false', 'features.skill_mcp_dependency_install=false',
                            'features.shell_snapshot=false',
                            'web_search="disabled"', 'project_doc_max_bytes=0', 'model_reasoning_effort="low"']:
                args.extend(['-c', setting])
            env = os.environ.copy()
            env['CODEX_API_KEY'] = self.provider.api_key
            # Pipes are drained before cleaning temporary files. On Windows,
            # inherited output handles may outlive the initial CLI process.
            process = subprocess.Popen(args + ['-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       env=env, start_new_session=os.name != 'nt',
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            scope = None
            start = time.monotonic()
            first = True
            try:
                scope = ProcessScope(process)
                while True:
                    if cancel.is_set():
                        raise ModelCancelled('已停止当前模型请求。')
                    if time.monotonic() - start > self.timeout:
                        raise ModelUnavailable('主模型请求超时。')
                    try:
                        stdout_data, stderr_data = process.communicate((prefix + prompt).encode('ascii') if first else None, timeout=.2)
                        break
                    except subprocess.TimeoutExpired:
                        first = False
            finally:
                if scope:
                    scope.close()
                if process.poll() is None:
                    process.kill()
                process.wait()
                for pipe in (process.stdin, process.stdout, process.stderr):
                    if pipe and not pipe.closed:
                        pipe.close()
            if process.returncode != 0 or not output.is_file():
                # Upstream errors may contain secrets; only return known categories.
                log = stderr_data.decode('utf-8', errors='replace')
                if '401' in log:
                    raise ModelUnavailable('模型认证失败，请检查 CCSwitch 当前凭据。')
                if '403' in log:
                    raise ModelUnavailable('模型服务拒绝此客户端或账号请求（403）。请检查供应商权限。')
                if '429' in log:
                    raise ModelUnavailable('模型服务限流或额度不足（429），请稍后再试。')
                raise ModelUnavailable('官方 Codex 客户端调用未完成，请检查供应商连接、额度和 CLI 登录配置。')
            try:
                value = json.loads(output.read_text(encoding='utf-8'))
            except (ValueError, OSError):
                raise ModelError('模型返回了无法解析的结果，未执行后续工具。') from None
            usage = {}
            for line in stdout_data.decode('utf-8', errors='replace').splitlines():
                try:
                    event = json.loads(line)
                    if event.get('type') == 'turn.completed':
                        usage = {key: val for key, val in event.get('usage', {}).items() if type(val) is int}
                except ValueError:
                    continue
            return check_step(value), usage


def create_model():
    from model_backup import create_model as create
    return create()


def model_status():
    try:
        model = create_model()
        return {'configured': True, **model.metadata,
                'notice': '优先使用 CCSwitch 主模型；已配置时可自动切换 DeepSeek 备用，按实际供应商规则计费。'}
    except ModelError as error:
        return {'configured': False, 'error': str(error)}

import { readFileSync, mkdirSync, writeFileSync, existsSync, unlinkSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = dirname(fileURLToPath(import.meta.url));
const modes = ['sequential', 'supervisor', 'hierarchical', 'swarm', 'network', 'devteam', 'security'];
const corpus = JSON.parse(readFileSync(join(root, 'data', 'corpus.json'), 'utf8'));
const roles = {
  researcher: '研究员：阅读提供的本地资料，提取事实并保留source编号，禁止编造互联网搜索结果。',
  critic: '审查员：指出方案的风险与证据缺口，区分事实与建议。',
  analyst: '分析员：比较协作模式的控制流、开销与适用场景，不编造市场数据。',
  outline: '提纲编辑：根据输入资料给出三段式提纲。',
  draft: '作者：按提纲生成简短培训报告，保留source编号。',
  editor: '编辑：检查逻辑和事实，保留来源。',
  writer: '作者：综合已有成果，输出包含建议、风险和来源的简短中文报告。',
  seo: 'SEO编辑：输出最终报告，并提供关键词，不新增未经验证的事实。',
};

function options(argv) {
  const result = { mode: 'sequential', live: false, approve: false, maxSteps: 12,
    maxCalls: 24, output: join(root, 'outputs'), topic: 'AI Agent协作模式选型' };
  const values = { '--mode': 'mode', '--output': 'output', '--topic': 'topic',
    '--max-steps': 'maxSteps', '--max-calls': 'maxCalls', '--requirements': 'requirements',
    '--decision': 'decision', '--run-dir': 'runDir', '--revision': 'revision' };
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    if (flag in values) {
      if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Missing value: ${flag}`);
      result[values[flag]] = argv[++i];
    } else if (flag === '--live') result.live = true;
    else if (flag === '--approve') result.approve = true;
    else if (flag === '--check') result.check = true;
    else if (flag === '--resume') result.resume = true;
    else if (flag === '--force-cycle') result.forceCycle = true;
    else if (flag === '--help') result.help = true;
    else throw new Error(`Unknown option: ${flag}`);
  }
  if (!modes.includes(result.mode)) throw new Error(`Unknown mode: ${result.mode}`);
  for (const name of ['maxSteps', 'maxCalls']) {
    result[name] = Number(result[name]);
    if (!Number.isSafeInteger(result[name]) || result[name] < 1 || result[name] > 100)
      throw new Error(`${name} must be an integer between 1 and 100`);
  }
  if (result.forceCycle && (result.live || result.mode !== 'network'))
    throw new Error('--force-cycle is only available for offline network exercises');
  result.output = resolve(result.output);
  return result;
}

class LimitError extends Error {}

function offlineOutput(name, topic, previous) {
  const label = `[离线模拟 / ${name}] ${topic}\n`;
  const findings = corpus.map(item => `[${item.id}] ${item.title}：${item.text}`).join('\n');
  const report = `## 建议\n步骤明确时先用Sequential Chain；需要动态任务分发时采用Supervisor；需要自主交接时采用Swarm。[source-02][source-04][source-05]\n\n` +
    `## 工程约束\n为子团队设置唯一名称，合并消息时避免重复历史，给路由设置白名单和调用上限。[source-03][source-06]\n\n` +
    `## 验收\n核查输出来源与任务完成情况。人工审批前不继续执行后续测试；本地工具不能冒充互联网搜索。[source-01][source-07]\n\n` +
    `## 本地依据\n${findings}`;
  const templates = {
    researcher: `已读取${corpus.length}条本地资料；没有互联网搜索。\n${findings}`,
    analyst: '分析维度：固定流程、中央调度、自主交接。固定步骤优先流水线；上下文分工复杂且需要调度时再增加Agent。费用与效果需通过实测比较。[source-01][source-02][source-04][source-05]',
    critic: '审查意见：资料只能支持协作模式与工程讨论，不能支持市场预测。需验证路由的退出条件、工具是否真正执行、报告是否保留来源。[source-06][source-07]',
    outline: '一、任务步骤与协作模式；二、共享状态与工具边界；三、人工审批、调用预算和验收。[source-01][source-05][source-07]',
    draft: report,
    editor: '编辑结果：移除未经本地资料支持的市场数据，保留事实与建议的区分。\n' + report,
    writer: report,
    seo: (previous.at(-1)?.content || report) + '\n\n关键词：多Agent、Supervisor、Swarm、顺序流水线、消息状态、人工审批。',
  };
  return label + templates[name];
}

class Session {
  constructor(config) {
    this.config = config;
    this.events = [];
    this.contexts = new Map();
    this.completed = [];
    this.modelCalls = 0;
    this.tokens = { prompt: 0, completion: 0 };
  }
  async model(messages, json = false) {
    if (this.modelCalls >= this.config.maxCalls) throw new LimitError('Model call budget reached');
    this.modelCalls++;
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST', signal: AbortSignal.timeout(45000),
      headers: { Authorization: `Bearer ${process.env.DEEPSEEK_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: process.env.DEEPSEEK_MODEL || 'deepseek-chat',
        messages, max_tokens: 600, temperature: 0.2,
        ...(json ? { response_format: { type: 'json_object' } } : {}) }),
    });
    if (!response.ok) throw new Error(`DeepSeek HTTP ${response.status}; check key, quota and connectivity`);
    const body = await response.json();
    const content = body.choices?.[0]?.message?.content;
    if (typeof content !== 'string' || !content.trim()) throw new Error('DeepSeek returned no text');
    this.tokens.prompt += body.usage?.prompt_tokens || 0;
    this.tokens.completion += body.usage?.completion_tokens || 0;
    return content;
  }
  async worker(name) {
    if (this.completed.length >= this.config.maxSteps) throw new LimitError('Worker step limit reached');
    if (name === 'researcher') this.events.push({ kind: 'tool', agent: name,
      tool: 'local_search', sources: corpus.map(item => item.id) });
    const evidence = name === 'researcher' ? corpus : this.completed.slice(-5);
    const context = this.contexts.get(name) || [{ role: 'system', content: roles[name] }];
    context.push({ role: 'user', content: JSON.stringify({ task: this.config.topic, evidence }) });
    const content = this.config.live ? await this.model(context) :
      offlineOutput(name, this.config.topic, this.completed);
    context.push({ role: 'assistant', content });
    this.contexts.set(name, context);
    this.completed.push({ agent: name, content });
    this.events.push({ kind: 'worker', agent: name, step: this.completed.length });
    console.log(`${String(this.completed.length).padStart(2, '0')} worker: ${name}`);
    return content;
  }
  async route(owner, candidates, fallback) {
    let choice = fallback;
    if (this.config.live) {
      const raw = await this.model([
        { role: 'system', content: `你是${owner}。根据任务和已有成果选择下一步。只输出JSON对象，格式为 {"next":"名称"}。next必须为：${candidates.join(', ')}。` },
        { role: 'user', content: JSON.stringify({ task: this.config.topic, completed: this.completed.slice(-5) }) },
      ], true);
      choice = JSON.parse(raw).next;
    }
    if (!candidates.includes(choice)) throw new Error(`Invalid route from ${owner}; allowed: ${candidates.join(', ')}`);
    this.events.push({ kind: 'route', agent: owner, next: choice });
    console.log(`   ${owner} -> ${choice}`);
    return choice;
  }
  async supervised(owner, workers) {
    const remaining = [...workers];
    while (remaining.length) {
      const candidates = remaining.length > 1 ? remaining.filter(name => name !== 'writer') : remaining;
      const name = await this.route(owner, candidates, candidates[0]);
      await this.worker(name);
      remaining.splice(remaining.indexOf(name), 1);
    }
  }
}

function validateTask(receiver, tools, usage, budget) {
  const allowed = { researcher: ['local_search'], writer: ['write_report'] };
  if (!(receiver in allowed) || !Array.isArray(tools) || tools.some(tool => !allowed[receiver].includes(tool)))
    throw new Error('Unauthorized tool request');
  if (![usage, budget].every(value => Number.isSafeInteger(value) && value >= 0) || usage > budget)
    throw new Error('Token budget exceeded');
  return true;
}

async function main() {
  const config = options(process.argv.slice(2));
  if (config.help) {
    console.log(`node run.mjs --mode ${modes.join('|')} [--live]\n` +
      'Options: --topic TEXT --output PATH --max-steps 12 --max-calls 24\n' +
      'Product: --mode devteam --requirements JSON [--check] [--resume]\n' +
      'Product approval: --mode devteam --decision approve|reject --run-dir PATH --revision SHA\n' +
      'Offline failure exercise: --mode network --force-cycle --max-steps 4');
    return;
  }
  if (config.mode === 'devteam') {
    if (config.approve) throw new Error('--approve cannot approve future output; use --decision approve --run-dir PATH --revision SHA');
    if (!config.requirements && !config.resume && !config.decision && !config.check)
      throw new Error('devteam requires --requirements JSON with business and browser acceptance');
    const productRoot = resolve(root, '../agent-training');
    const python = process.env.TRAINING_PRODUCT_PYTHON || join(productRoot, '.venv-metagpt', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
    const args = ['-X', 'utf8', join(productRoot, 'demo/run_dev_team.py')];
    for (const [field, flag] of Object.entries({requirements:'--requirements', output:'--output', decision:'--decision', runDir:'--run-dir', revision:'--revision'}))
      if (config[field]) args.push(flag, ['requirements','output','runDir'].includes(field) ? resolve(config[field]) : config[field]);
    if (config.check) args.push('--check');
    if (config.resume) args.push('--resume');
    const result = spawnSync(python, args, {cwd: productRoot, stdio: 'inherit', shell: false});
    if (result.error) throw result.error;
    process.exitCode = result.status ?? 1;
    return;
  }
  if (config.live && !process.env.DEEPSEEK_API_KEY?.trim()) throw new Error('Set DEEPSEEK_API_KEY before using --live');
  if (config.live && config.mode === 'security') throw new Error('Security lab is local; remove --live');
  const session = new Session(config);
  const report = { mode: config.mode, backend: config.live ? 'deepseek-api' : 'offline-simulation',
    status: 'completed', topic: config.topic, events: session.events, content: '' };
  console.log(`Mode: ${config.mode} | Backend: ${report.backend}`);
  try {
    switch (config.mode) {
      case 'sequential':
        for (const name of ['researcher', 'outline', 'draft', 'editor', 'writer', 'seo']) await session.worker(name);
        break;
      case 'supervisor':
        await session.supervised('supervisor', ['researcher', 'analyst', 'writer']);
        break;
      case 'hierarchical': {
        const teams = { research_team: ['researcher', 'analyst'], editorial_team: ['critic', 'writer'] };
        const remaining = Object.keys(teams);
        while (remaining.length) {
          const team = await session.route('root_supervisor', remaining, remaining[0]);
          await session.supervised(team, teams[team]);
          remaining.splice(remaining.indexOf(team), 1);
        }
        if (session.completed.at(-1)?.agent !== 'writer') await session.worker('writer');
        break;
      }
      case 'swarm':
      case 'network': {
        let active = 'researcher';
        while (active !== 'END') {
          await session.worker(active);
          const visited = new Set(session.completed.map(item => item.agent));
          const canEnd = visited.has('researcher') && visited.has('writer');
          const candidates = config.mode === 'swarm' ?
            ({ researcher: ['critic'], critic: ['researcher', 'writer'], writer: ['END'] })[active] :
            ['researcher', 'critic', 'writer'].filter(name => name !== active).concat(canEnd ? ['END'] : []);
          const fallback = config.forceCycle ? (active === 'researcher' ? 'critic' : 'researcher') :
            ({ researcher: 'critic', critic: 'writer', writer: 'END' })[active];
          active = await session.route(active, candidates, fallback);
        }
        break;
      }
      case 'security': {
        const blocked = callback => { try { callback(); return false; } catch { return true; } };
        report.checks = {
          allowedTool: validateTask('researcher', ['local_search'], 50, 100),
          unauthorizedToolBlocked: blocked(() => validateTask('researcher', ['delete_files'], 50, 100)),
          budgetExceededBlocked: blocked(() => validateTask('researcher', ['local_search'], 101, 100)),
        };
        report.content = JSON.stringify(report.checks, null, 2);
        break;
      }
    }
  } catch (error) {
    if (!(error instanceof LimitError)) throw error;
    report.status = 'step_limit';
    report.reason = error.message;
    process.exitCode = 2;
    console.log(`STOPPED: ${error.message}`);
  }
  report.content ||= session.completed.at(-1)?.content || '';
  report.modelCalls = session.modelCalls;
  report.tokens = session.tokens;
  report.results = session.completed;
  mkdirSync(config.output, { recursive: true });
  writeFileSync(join(config.output, `${config.mode}.json`), JSON.stringify(report, null, 2), 'utf8');
  const markdown = join(config.output, `${config.mode}.md`);
  if (report.status === 'completed') writeFileSync(markdown,
    `# ${config.topic}\n\nBackend: ${report.backend}\n\n${report.content}\n`, 'utf8');
  else if (existsSync(markdown)) unlinkSync(markdown);
  console.log(`Status: ${report.status} | model calls: ${report.modelCalls}\nOutput: ${config.output}`);
}

main().catch(error => { console.error(`ERROR: ${error.message}`); process.exitCode = 1; });

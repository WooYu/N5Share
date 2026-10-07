/* Each architecture, scenario and collaboration pattern owns its live trace. */
(function () {
  const dialog = document.querySelector('#outingLiveDialog');
  const el = name => dialog.querySelector(`[data-live-${name}]`);
  const architectureNames = ['① 单 Agent · RAG + Tool', '② ReAct', '③ Plan & Execute + Reflexion', '④ 多 Agent', '⑤ Router + Skill', '⑥ Blackboard', '⑦ Graph / Workflow'];
  const patternNames = {supervisor: 'Supervisor', hierarchical: '层次化', swarm: 'Swarm'};
  const stateNames = {queued: '准备运行', running: '正在运行', completed: '运行完成', failed: '运行失败', stopped: '达到上限', cancelled: '已停止'};
  const sessions = new Map();
  const preferredPatterns = new WeakMap();
  let current = null;
  let activeRun = null;
  let viewGeneration = 0;

  const isRunning = trace => trace && ['queued', 'running'].includes(trace.status);
  const name = session => architectureNames[session.architecture - 1] + (session.config.stage === 7 ? ` · ${patternNames[session.config.pattern]}` : '');
  const key = config => [config.stage, config.weather, config.budget, config.pattern, config.intent || ''].join(':');

  function sessionFor(panel, pattern) {
    const config = {stage: Number(panel.dataset.outingStage), weather: panel.querySelector('[data-outing-weather]').value,
      budget: Number(panel.querySelector('[data-outing-budget]').value), pattern};
    if (config.stage === 8) config.intent = panel.querySelector('[data-outing-intent]').value;
    const id = key(config);
    if (!sessions.has(id)) sessions.set(id, {config, architecture: Number(panel.dataset.outingArchitecture), panel,
      trace: null, selected: -1, follow: true, generation: 0, connectionOK: false, connection: '', notice: ''});
    return sessions.get(id);
  }

  function updateTradeoffs() {
    if (!current) return;
    const {stage, pattern} = current.config;
    const item = stage === 7 && pattern !== 'supervisor' ? DEMO_TRADEOFFS.outing[pattern] : DEMO_TRADEOFFS.architecture[current.architecture];
    renderTradeoffs(el('tradeoffs'), item);
  }

  function modelLabel(info) {
    const channel = info.transport === 'deepseek-api' ? 'DeepSeek 官方接口' : '官方 Codex 客户端';
    const backup = info.fallback && !info.using_backup ? `；备用：${info.fallback.provider} / ${info.fallback.model}` : '';
    return `${info.provider} · ${info.model} · ${channel}${info.using_backup ? '（已启用备用）' : ''}${backup}`;
  }

  function controls() {
    el('run').disabled = Boolean(activeRun) || !current?.connectionOK;
    el('cancel').disabled = !activeRun?.id || activeRun.cancelPending;
    el('cancel').textContent = activeRun && activeRun.session !== current ? `停止 ${name(activeRun.session)} 的运行` : '停止运行';
    el('pattern').disabled = activeRun?.session === current || !current?.connectionOK;
    el('export').disabled = !current?.trace;
  }

  async function request(url, options = {}) {
    const response = await fetch(url, {...options, signal: AbortSignal.timeout(12000)});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `请求失败（${response.status}）`);
    return body;
  }

  function detail() {
    const event = current?.trace?.events[current.selected];
    el('detail').replaceChildren();
    if (!event) {
      el('detail').textContent = '本演示尚无运行步骤。开始后查看模型决策、工具结果和角色消息。';
      return;
    }
    const phase = document.createElement('span');
    phase.className = 'outing-phase';
    phase.textContent = `${event.phase} · ${event.actor}`;
    const title = document.createElement('h3');
    title.textContent = event.title;
    const text = document.createElement('p');
    text.textContent = event.detail;
    el('detail').append(phase, title, text);
    if (event.data != null) {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = '查看结构化记录';
      const pre = document.createElement('pre');
      pre.textContent = JSON.stringify(event.data, null, 2);
      details.append(summary, pre);
      el('detail').append(details);
    }
  }

  function render() {
    if (!current) return;
    const session = current;
    const {trace, config} = session;
    el('title').textContent = `真实模型演示 · ${name(session)}`;
    el('task').textContent = `两大一小，半日出游；合成天气：${config.weather === 'rain' ? '下雨' : '晴天'}；预算 ${config.budget} 元。`;
    if (config.stage === 8) el('task').textContent += ` 用户需求：${{outing: '安排出游', budget: '只核算费用', unclear: '帮我看看'}[config.intent]}。`;
    el('pattern-row').hidden = config.stage !== 7;
    el('pattern').value = config.pattern;
    el('follow').checked = session.follow;
    el('connection').textContent = trace?.model ? modelLabel(trace.model) : session.connection;
    updateTradeoffs();
    const events = trace?.events || [];
    if (session.follow || session.selected >= events.length) session.selected = events.length - 1;
    let status = session.notice || (trace ? `${stateNames[trace.status] || trace.status}${trace.verified ? (trace.result?.status === 'cost_checked' ? ' · 费用核算通过，未查天气' : ' · 程序验收通过') : trace.result?.status === 'needs_clarification' ? ' · 等待澄清，未执行工具' : trace.status === 'completed' ? ' · 仅生成回答，尚未事实验收' : ''}` : '本演示尚未运行，点击开始创建独立任务。');
    if (activeRun && activeRun.session !== session) status += ` ${name(activeRun.session)} 仍在后台运行；可先停止该任务，再开始当前演示。`;
    el('status').textContent = status;
    const metrics = trace?.metrics || {};
    el('metrics').textContent = trace ? `运行 ${trace.id}　模型调用 ${metrics.model_calls || 0} / 12　工具 ${metrics.tool_calls || 0}　Token ${(metrics.input_tokens || 0) + (metrics.output_tokens || 0)}　用时 ${Math.round((metrics.elapsed_ms || 0) / 1000)} 秒` : '';
    el('events').replaceChildren();
    events.forEach((event, index) => {
      const button = document.createElement('button');
      button.textContent = `${index + 1}. ${event.title}`;
      button.className = index === session.selected ? 'selected' : '';
      button.setAttribute('aria-current', String(index === session.selected));
      button.onclick = () => {session.selected = index; session.follow = false; render();};
      el('events').append(button);
    });
    if (session.follow) el('events').scrollTop = el('events').scrollHeight;
    detail();
    controls();
  }

  function receive(run, trace) {
    if (run.session.generation !== run.generation) return false;
    if (!trace?.id || (run.id && trace.id !== run.id) || key(trace.config || {}) !== key(run.session.config)) {
      throw new Error('返回轨迹的任务或配置与本演示不一致，未载入。');
    }
    run.id = trace.id;
    run.session.trace = trace;
    run.session.notice = '';
    if (!isRunning(trace) && activeRun === run) activeRun = null;
    render();
    return isRunning(trace);
  }

  async function poll(run) {
    if (run.session.generation !== run.generation) return;
    try {
      const trace = await request(`/api/outing/runs/${encodeURIComponent(run.id)}`);
      if (receive(run, trace)) run.timer = setTimeout(() => poll(run), 900);
    } catch (error) {
      if (run.session.generation !== run.generation) return;
      run.session.notice = `暂时无法获取进度：${error.message}。正在重连。`;
      render();
      run.timer = setTimeout(() => poll(run), 2500);
    }
  }

  async function open(panel) {
    current = sessionFor(panel, preferredPatterns.get(panel) || 'supervisor');
    const session = current;
    const view = ++viewGeneration;
    session.connectionOK = false;
    session.connection = '正在检查本地模型连接配置…';
    render();
    dialog.showModal();
    if (location.protocol === 'file:') {
      session.connection = '离线文件不能调用模型。请启动 start-demo.cmd，使用 http://127.0.0.1:8765 打开课件。';
      render();
      return;
    }
    try {
      const info = await request('/api/outing/config');
      if (view !== viewGeneration || session !== current) return;
      session.connectionOK = info.configured;
      session.connection = info.configured ? modelLabel(info) : info.error;
    } catch (error) {
      if (view !== viewGeneration || session !== current) return;
      session.connection = '连接失败：' + error.message;
    }
    render();
  }

  document.querySelectorAll('.outing-demo:has([data-outing-live])').forEach(panel => {
    panel.querySelector('[data-outing-live]').onclick = () => {
      panel.querySelector('.walk-more')?.close();
      open(panel);
    };
  });
  el('run').onclick = async () => {
    if (activeRun || !current?.connectionOK) return;
    const session = current;
    session.trace = null;
    session.selected = -1;
    session.follow = true;
    session.notice = '正在创建本演示的独立模型任务…';
    const run = {session, generation: ++session.generation, id: null, cancelPending: false, timer: null};
    activeRun = run;
    render();
    try {
      const trace = await request('/api/outing/start', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(session.config)});
      if (receive(run, trace)) poll(run);
    } catch (error) {
      if (session.generation !== run.generation) return;
      if (activeRun === run) activeRun = null;
      session.notice = '未能开始：' + error.message;
      render();
    }
  };
  el('cancel').onclick = async () => {
    const run = activeRun;
    if (!run?.id || run.cancelPending) return;
    run.cancelPending = true;
    run.session.notice = '已请求停止，等待当前模型调用结束…';
    render();
    try {
      await request('/api/outing/cancel', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: run.id})});
    } catch (error) {
      if (run.session.generation !== run.generation || activeRun !== run) return;
      run.cancelPending = false;
      run.session.notice = '停止请求未送达：' + error.message;
      render();
    }
  };
  el('follow').onchange = () => {if (current) {current.follow = el('follow').checked; render();}};
  el('pattern').onchange = () => {
    if (!current || activeRun?.session === current) return;
    const previous = current;
    preferredPatterns.set(previous.panel, el('pattern').value);
    current = sessionFor(previous.panel, el('pattern').value);
    current.connectionOK = previous.connectionOK;
    current.connection = previous.connection;
    render();
  };
  el('export').onclick = () => {
    if (!current?.trace) return;
    const trace = current.trace;
    const url = URL.createObjectURL(new Blob([JSON.stringify(trace, null, 2)], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = `outing-live-${trace.config.stage}-${trace.config.pattern}-${trace.id}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
})();

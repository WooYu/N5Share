/* Real model runs are explicit. Scripted demos remain available offline. */
(() => {
  const dialog = document.querySelector('#outingLiveDialog');
  const el = name => dialog.querySelector(`[data-live-${name}]`);
  const stageNames = ['LLM', 'RAG', 'Tool Calling', 'ReAct', 'Plan-and-Execute', 'Plan-and-Execute + Reflexion', 'Multi-Agent'];
  const stateNames = {queued: '准备运行', running: '正在运行', completed: '运行完成', failed: '运行失败', stopped: '达到上限', cancelled: '已停止'};
  let config = null;
  let currentTrace = null;
  let running = false;
  let selected = -1;
  let generation = 0;
  let pollTimer = null;
  let connectionOK = false;

  function modelLabel(info) {
    const channel = info.transport === 'deepseek-api' ? 'DeepSeek 官方接口' : '官方 Codex 客户端';
    const backup = info.fallback && !info.using_backup ? `；备用：${info.fallback.provider} / ${info.fallback.model}` : '';
    return `${info.provider} · ${info.model} · ${channel}${info.using_backup ? '（已启用备用）' : ''}${backup}`;
  }

  function controls() {
    el('run').disabled = running || !connectionOK || !config;
    el('cancel').disabled = !running || !currentTrace;
    el('pattern').disabled = running;
    el('export').disabled = !currentTrace;
  }

  async function request(url, options = {}) {
    const response = await fetch(url, {...options, signal: AbortSignal.timeout(12000)});
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || `请求失败（${response.status}）`);
    return body;
  }

  function detail() {
    const event = currentTrace?.events[selected];
    el('detail').replaceChildren();
    if (!event) {
      el('detail').textContent = '运行后可逐步查看模型决策、工具结果和角色消息。';
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

  function render(trace) {
    currentTrace = trace;
    if (trace.model) el('connection').textContent = modelLabel(trace.model);
    running = ['queued', 'running'].includes(trace.status);
    const events = trace.events || [];
    if (el('follow').checked || selected >= events.length) selected = events.length - 1;
    el('status').textContent = `${stateNames[trace.status] || trace.status}${trace.verified ? ' · 程序验收通过' : trace.status === 'completed' ? ' · 仅生成回答，尚未事实验收' : ''}`;
    const metrics = trace.metrics || {};
    el('metrics').textContent = `模型调用 ${metrics.model_calls || 0} / 12　工具 ${metrics.tool_calls || 0}　Token ${(metrics.input_tokens || 0) + (metrics.output_tokens || 0)}　用时 ${Math.round((metrics.elapsed_ms || 0) / 1000)} 秒`;
    el('events').replaceChildren();
    events.forEach((event, index) => {
      const button = document.createElement('button');
      button.textContent = `${index + 1}. ${event.title}`;
      button.className = index === selected ? 'selected' : '';
      button.setAttribute('aria-current', String(index === selected));
      button.onclick = () => {
        selected = index;
        el('follow').checked = false;
        render(currentTrace);
      };
      el('events').append(button);
    });
    if (el('follow').checked) el('events').scrollTop = el('events').scrollHeight;
    detail();
    controls();
  }

  async function poll(id, token) {
    if (token !== generation) return;
    try {
      const trace = await request(`/api/outing/runs/${encodeURIComponent(id)}`);
      if (token !== generation) return;
      render(trace);
      if (running) pollTimer = setTimeout(() => poll(id, token), 900);
    } catch (error) {
      if (token !== generation) return;
      el('status').textContent = `暂时无法获取进度：${error.message}。正在重连，本地任务可能仍在执行。`;
      pollTimer = setTimeout(() => poll(id, token), 2500);
    }
  }

  async function open(panel) {
    if (!running) {
      config = {stage: Number(panel.dataset.outingStage), weather: panel.querySelector('[data-outing-weather]').value,
                budget: Number(panel.querySelector('[data-outing-budget]').value), pattern: 'supervisor'};
      el('title').textContent = `真实模型演示 · ${stageNames[config.stage - 1]}`;
      el('task').textContent = `两大一小，半日出游；合成天气：${config.weather === 'rain' ? '下雨' : '晴天'}；预算 ${config.budget} 元。`;
      el('pattern-row').hidden = config.stage !== 7;
      el('pattern').value = 'supervisor';
      currentTrace = null;
      selected = -1;
      el('events').replaceChildren();
      el('metrics').textContent = '';
      el('status').textContent = '正在检查本地模型连接配置…';
      detail();
    }
    dialog.showModal();
    if (running) return;
    connectionOK = false;
    controls();
    if (location.protocol === 'file:') {
      el('connection').textContent = '离线文件不能调用模型。请启动 start-demo.cmd，使用 http://127.0.0.1:8765 打开课件。';
      el('status').textContent = '当前可继续使用页面中的离线示意。';
      return;
    }
    try {
      const info = await request('/api/outing/config');
      connectionOK = info.configured;
      el('connection').textContent = info.configured ? modelLabel(info) : info.error;
      el('status').textContent = info.configured ? '配置就绪；点击开始后才会调用模型并产生用量。' : '请先修复模型配置。';
    } catch (error) {
      el('connection').textContent = '连接失败：' + error.message;
      el('status').textContent = '请确认使用培训本地服务打开，而非普通静态服务器。';
    }
    controls();
  }

  document.querySelectorAll('.outing-demo').forEach(panel => {
    panel.querySelector('[data-outing-live]').onclick = () => open(panel);
  });
  el('run').onclick = async () => {
    if (running || !connectionOK) return;
    running = true;
    currentTrace = null;
    el('follow').checked = true;
    el('status').textContent = '正在创建真实模型任务…';
    controls();
    const token = ++generation;
    clearTimeout(pollTimer);
    try {
      const trace = await request('/api/outing/start', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({...config, pattern: el('pattern').value})});
      if (token !== generation) return;
      render(trace);
      poll(trace.id, token);
    } catch (error) {
      running = false;
      el('status').textContent = '未能开始：' + error.message;
      controls();
    }
  };
  el('cancel').onclick = async () => {
    if (!currentTrace || !running) return;
    el('cancel').disabled = true;
    try {
      await request('/api/outing/cancel', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: currentTrace.id})});
      el('status').textContent = '已请求停止，正在结束当前模型调用…';
    } catch (error) {
      el('status').textContent = '停止请求未送达：' + error.message;
      controls();
    }
  };
  el('follow').onchange = () => { if (currentTrace) render(currentTrace); };
  el('export').onclick = () => {
    if (!currentTrace) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(currentTrace, null, 2)], {type: 'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = `outing-live-${currentTrace.id}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
})();

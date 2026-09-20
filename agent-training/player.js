const select = selector => document.querySelector(selector);
const patterns = {workflow: '固定工作流（基线）', supervisor: '主管委派', parallel: '并行分析', review: '提案与评审', integrated: '综合四角色'};
const actors = {workflow: '程序流程', coordinator: '协调者', evidence: '证据分析', knowledge: '知识分析', reviewer: '评审者'};
const steps = {workflow: '载入固定流程', check_evidence: '检查补查条件', validate: '程序校验', read_telemetry: '读取检测记录', read_knowledge: '检索知识', read_supplemental: '补查资料', draft: '形成提案', review: '检查证据', reviewer: '检查证据', coordinator: '制定计划', evidence: '检测分析', knowledge: '知识分析', dispatch: '委派任务', assess: '核对完整性', revise: '调整方案', supplement: '补查资料'};
const fields = {voltage: '电压', dtc: '故障码', gateway: '网关记录', voltage_threshold: '知识阈值', incident_time: '事件时间'};
const eventNames = {Start: '接收工单', Decision: '进入执行步骤', Plan: '制定执行方案', Dispatch: '委派任务', Action: '请求工具', Observation: '获得工具反馈', Assessment: '核对证据', Revision: '修订方案', Draft: '提交提案', Review: '检查提案', Finish: '报告就绪', Stop: '停止执行'};
const flows = {workflow: '程序预设：读取 → 条件补查 → 生成 → 校验；没有模型选路', supervisor: '协调者 → 证据分析 → 委派知识分析 → 汇总与评审', parallel: '协调者 →〔证据分析 ∥ 知识分析〕→ 汇总 → 评审', review: '收集证据 → 提案 → 评审 → 必要时修订重提', integrated: '协调者 → 双路并行 → 核对与补查 → 提案 → 评审'};
const scenarios = {normal: '正常工单', missing: '资料缺失', conflict: '证据冲突', tool_failure: '工具失败', budget: '预算耗尽'};
const statuses = {completed: '报告就绪，待人工审核', needs_human: '需要人工介入', failed: '执行失败', stopped: '受控停止'};
let current = 0;
let trace = null;
let traceLabel = '';
let eventIndex = -1;
let playback = null;
let busy = false;
const labIndex = COURSE.findIndex(slide => slide.body.includes('__DIAGNOSIS_LAB__'));

function fit() {
  const bounds = select('#viewport').getBoundingClientRect();
  document.documentElement.style.setProperty('--stage-scale', Math.max(.1, Math.min((bounds.width - 24) / 1440, (bounds.height - 18) / 810)));
}

function stopPlayback() {
  if (playback) clearInterval(playback);
  playback = null;
  select('#playDemo').textContent = '自动播放';
}

function showSlide(index, updateHash = true) {
  current = Math.max(0, Math.min(COURSE.length - 1, index));
  document.querySelectorAll('.slide').forEach((slide, position) => {
    slide.classList.toggle('active', position === current);
    slide.setAttribute('aria-hidden', String(position !== current));
    slide.inert = position !== current;
  });
  select('#chapterLabel').textContent = COURSE[current].chapter;
  select('#pageNumber').textContent = `${current + 1} / ${COURSE.length}`;
  select('#progress').style.width = `${(current + 1) / COURSE.length * 100}%`;
  select('#prevBtn').disabled = current === 0;
  select('#nextBtn').disabled = current === COURSE.length - 1;
  document.title = `${current + 1}. ${COURSE[current].title} · Agent 开发者实战课`;
  if (updateHash) history.replaceState(null, '', `#${current + 1}`);
  document.querySelectorAll('#tocList button').forEach((button, position) => button.setAttribute('aria-current', String(position === current)));
  if (current !== labIndex) stopPlayback();
}

function openDialog(id) {
  const dialog = select(`#${id}`);
  if (dialog.open) dialog.close();
  else dialog.showModal();
}

function showNotes() {
  const slide = COURSE[current];
  select('#notesTitle').textContent = `${current + 1} / ${slide.title}`;
  select('#notesText').textContent = slide.notes;
  select('#notesSources').replaceChildren();
  slide.sources.forEach(source => {
    const link = document.createElement('a');
    link.href = source[1];
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = `${source[0]} ↗`;
    select('#notesSources').append(link);
  });
  openDialog('notesDialog');
}

async function fullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch { select('#fullBtn').textContent = '请使用浏览器全屏'; }
}

COURSE.forEach((slide, index) => {
  const button = document.createElement('button');
  button.textContent = `${String(index + 1).padStart(2, '0')}　${slide.title}`;
  button.onclick = () => { showSlide(index); select('#tocDialog').close(); };
  select('#tocList').append(button);
});
select('#prevBtn').onclick = () => showSlide(current - 1);
select('#nextBtn').onclick = () => showSlide(current + 1);
select('#tocBtn').onclick = () => openDialog('tocDialog');
select('#notesBtn').onclick = showNotes;
select('#fullBtn').onclick = fullscreen;
select('#helpBtn').onclick = () => openDialog('helpDialog');
document.querySelectorAll('[data-close]').forEach(button => button.onclick = () => select(`#${button.dataset.close}`).close());
document.addEventListener('keydown', event => {
  if (event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input,textarea,select')) return;
  if (document.querySelector('dialog[open]')) return;
  if (['BUTTON', 'A'].includes(event.target.tagName) && [' ', 'Enter'].includes(event.key)) return;
  const actions = {
    ArrowRight: () => showSlide(current + 1), ArrowDown: () => showSlide(current + 1), PageDown: () => showSlide(current + 1),
    ' ': () => showSlide(current + 1), ArrowLeft: () => showSlide(current - 1), ArrowUp: () => showSlide(current - 1),
    PageUp: () => showSlide(current - 1), Home: () => showSlide(0), End: () => showSlide(COURSE.length - 1),
    o: () => openDialog('tocDialog'), n: showNotes, f: fullscreen, '?': () => openDialog('helpDialog')
  };
  const action = actions[event.key] || actions[event.key.toLowerCase()];
  if (action) { event.preventDefault(); action(); }
});
window.addEventListener('resize', fit);
window.addEventListener('hashchange', () => showSlide((parseInt(location.hash.slice(1), 10) || 1) - 1, false));

document.querySelectorAll('.quiz[data-quiz]').forEach(quiz => {
  quiz.querySelectorAll('button').forEach(button => button.onclick = () => {
    quiz.querySelectorAll('button').forEach(option => option.classList.remove('correct', 'wrong'));
    button.classList.add(button.dataset.correct === 'true' ? 'correct' : 'wrong');
    quiz.querySelector('.quiz-feedback').textContent = button.dataset.feedback;
  });
});

function validTrace(value) {
  return value && value.schema_version === 2 && value.engine === 'langgraph'
    && value.mode === 'simulation' && typeof value.run_id === 'string'
    && Object.hasOwn(patterns, value.pattern) && Object.hasOwn(scenarios, value.scenario)
    && Object.hasOwn(statuses, value.status) && typeof value.verified === 'boolean'
    && typeof value.report === 'string' && value.shared_state && typeof value.shared_state === 'object'
    && value.metrics && ['tool_calls', 'revision_rounds', 'elapsed_ms', 'evidence_coverage'].every(key => Number.isFinite(value.metrics[key]) && value.metrics[key] >= 0)
    && Array.isArray(value.events) && value.events.length > 0 && value.events.length <= 500
    && value.events.every(event => event && typeof event.id === 'string' && typeof event.actor === 'string'
      && typeof event.kind === 'string' && event.payload && typeof event.payload === 'object'
      && (event.kind !== 'Plan' || (Array.isArray(event.payload.steps) && event.payload.steps.every(step => typeof step === 'string')
        && (event.payload.conditional_steps === undefined || Array.isArray(event.payload.conditional_steps))))
      && (event.kind !== 'Observation' || (typeof event.payload.ok === 'boolean' && Array.isArray(event.payload.records)
        && event.payload.records.every(record => record && typeof record.id === 'string' && typeof record.field === 'string')))
      && (event.kind !== 'Draft' || (Array.isArray(event.payload.claims)
        && event.payload.claims.every(claim => claim && typeof claim.field === 'string' && Array.isArray(claim.refs))))
      && ['errors', 'issues'].every(key => event.payload[key] === undefined || Array.isArray(event.payload[key])));
}

function describePlan(plan) {
  if (!plan) return '等待新计划';
  const payload = plan.payload;
  const labels = payload.steps.map(step => (steps[step] || step) + ((payload.conditional_steps || []).includes(step) ? '（仅条件满足时）' : ''));
  if (['parallel', 'integrated'].includes(trace.pattern) && payload.steps[0] === 'read_telemetry' && payload.steps[1] === 'read_knowledge') {
    labels.splice(0, 2, `〔${labels[0]} ∥ ${labels[1]}〕`);
  }
  return labels.join(' → ');
}

function describeEvent(event) {
  const payload = event.payload;
  const tool = steps[payload.tool] || payload.tool || '工具';
  const problems = payload.errors || payload.issues || payload.reason;
  const reason = Array.isArray(problems) ? problems.join('；') : String(problems || '');
  switch (event.kind) {
    case 'Start': return '接收合成工单，尚未读取任何检测证据。';
    case 'Decision': return `执行「${steps[payload.node] || payload.node}」。本节点由${trace.pattern === 'workflow' ? '预设程序' : '教学规则'}驱动。`;
    case 'Plan': return `计划安排：${describePlan(event)}。`;
    case 'Dispatch': return `将后续任务交给${actors[payload.next_actor] || payload.next_actor}；已有 ${payload.received_observations} 份工具反馈。`;
    case 'Action': return `请求${tool}，等待工具返回；此时不能使用尚未返回的数据。`;
    case 'Observation': return payload.ok ? `${tool}返回 ${(payload.records || []).length} 条资料，证据已可供后续步骤引用。` : `${tool}失败，未新增证据。失败结果进入后续检查；限定补查后仍不足则转人工。`;
    case 'Assessment': return (payload.issues || []).length ? `发现问题：${reason}。下一步补充读取。` : '已收到所需证据，进入提案生成。';
    case 'Revision': return `调整原因：${reason}。${payload.strategy || '按预设分支补查一次，再次校验。'}`;
    case 'Draft': return `提案包含 ${(payload.claims || []).length} 项证据陈述；${(payload.reconciliations || []).length ? '已按事件时间解释冲突来源；' : ''}等待检查，尚不能视为通过。`;
    case 'Review': return payload.accepted ? '证据与引用对应，检查通过；等待生成报告。' : `${trace.pattern === 'workflow' || trace.events.slice(0, eventIndex).some(item => item.kind === 'Revision') ? '检查失败，补查额度已用完，准备转人工' : '退回补充'}：${reason}。`;
    case 'Finish': return '报告已生成，进入人工审核；证据契约通过不等于确认故障原因。';
    case 'Stop': return `停止继续执行：${reason === 'Graph node budget exhausted' ? '达到执行步数上限' : reason}。保留已收到的资料，交给人工处理。`;
    default: return '查看事件 JSON 了解本步骤的完整消息。';
  }
}

function renderStory(event) {
  const prefix = trace.events.slice(0, eventIndex + 1);
  const records = new Map();
  prefix.filter(item => item.kind === 'Observation' && item.payload.ok).forEach(item => {
    (item.payload.records || []).forEach(record => records.set(record.id, record));
  });
  select('#roleMap').replaceChildren();
  const roleKeys = trace.pattern === 'workflow' ? ['workflow'] : ['coordinator', 'evidence', 'knowledge', 'reviewer'];
  roleKeys.forEach(actor => {
    const node = document.createElement('div');
    node.textContent = actors[actor];
    const active = trace.pattern === 'workflow' || actor === event.actor;
    node.classList.toggle('current', active);
    node.setAttribute('aria-current', String(active));
    const status = document.createElement('small');
    status.textContent = active ? '当前事件' : prefix.some(item => item.actor === actor) ? '已参与' : '尚未参与';
    node.append(status);
    select('#roleMap').append(node);
  });
  select('#flowCaption').textContent = flows[trace.pattern] + (['parallel', 'integrated'].includes(trace.pattern) ? '（逐事件回看不表示串行执行）' : '');
  select('#eventStory').textContent = describeEvent(event);
  select('#observedEvidence').textContent = `当前已见证据（${records.size}）：` + ([...records.values()].map(record => `${fields[record.field] || record.field} ${record.value === 'reachable' ? '可达' : record.value}${record.unit || ''} [${record.id}]`).join('；') || '无');
  const revisionIndex = prefix.findLastIndex(item => item.kind === 'Revision');
  if (revisionIndex >= 0) {
    const oldPlan = prefix.slice(0, revisionIndex).findLast(item => item.kind === 'Plan');
    const newPlan = prefix.slice(revisionIndex).findLast(item => item.kind === 'Plan');
    select('#revisionStory').textContent = `修订前：${describePlan(oldPlan)} ｜ 修订后：${describePlan(newPlan)}`;
  } else {
    const rejected = prefix.findLast(item => item.kind === 'Review' && !item.payload.accepted);
    select('#revisionStory').textContent = rejected ? (trace.pattern === 'workflow' ? '固定工作流未通过程序校验，准备交人工处理；不进入计划修订。' : '评审已退回，尚未收到修订方案。') : '截至当前事件，尚未发生方案修订。';
  }
  const drafts = prefix.filter(item => item.kind === 'Draft');
  if (drafts.length > 1) {
    const previous = drafts[drafts.length - 2].payload.claims;
    const latest = drafts[drafts.length - 1].payload.claims;
    const changes = latest.filter(claim => !previous.some(old => old.field === claim.field && JSON.stringify(old) === JSON.stringify(claim)));
    select('#revisionStory').textContent = `草稿修订：${previous.length} 项 → ${latest.length} 项；新增或更新：` + (changes.map(claim => `${fields[claim.field] || claim.field} [${claim.refs.join(', ')}]`).join('；') || '证据陈述未变化') + '。';
  }
  if (event.kind === 'Stop') select('#revisionStory').textContent = '本次执行已停止，不会继续修订；保留证据与停止原因供人工处理。';
}

function loadTrace(value, label) {
  if (!validTrace(value)) throw new Error('轨迹格式无效：需要新版诊断 Demo 导出的 JSON（schema_version=2）。');
  stopPlayback();
  trace = value;
  traceLabel = label;
  select('#eventList').replaceChildren();
  value.events.forEach((event, index) => {
    const button = document.createElement('button');
    button.textContent = `${event.id} · ${actors[event.actor] || event.actor} / ${eventNames[event.kind] || event.kind}`;
    button.onclick = () => selectEvent(index);
    select('#eventList').append(button);
  });
  const mode = value.pattern === 'workflow' ? '确定性程序 + LangGraph 执行' : '规则模拟决策 + LangGraph 实际编排';
  select('#demoStatus').textContent = `${label}｜${mode}｜${patterns[value.pattern]} / ${scenarios[value.scenario]}｜整次结果：${statuses[value.status]}`;
  const metricValues = [value.metrics.tool_calls, value.metrics.revision_rounds, `${value.metrics.elapsed_ms.toFixed(1)} ms`, `${Math.round(value.metrics.evidence_coverage * 100)}%`];
  document.querySelectorAll('#demoMetrics b').forEach((element, index) => element.textContent = metricValues[index]);
  ['stepDemo', 'playDemo', 'downloadTrace', 'showReport', 'showState', 'showEvent'].forEach(id => select(`#${id}`).disabled = false);
  selectEvent(0);
}

function selectEvent(index) {
  if (!trace) return;
  eventIndex = Math.min(trace.events.length - 1, Math.max(0, index));
  const event = trace.events[eventIndex];
  select('#eventHeading').textContent = `${event.id} · ${actors[event.actor] || event.actor} · ${eventNames[event.kind] || event.kind} · v${event.plan_version ?? 1}`;
  renderStory(event);
  document.querySelectorAll('#eventList button').forEach((button, position) => {
    button.classList.toggle('selected', position === eventIndex);
    button.setAttribute('aria-current', String(position === eventIndex));
    if (position === eventIndex) {
      const list = select('#eventList');
      list.scrollTop = button.offsetTop - list.offsetTop - list.clientHeight / 2 + button.offsetHeight / 2;
    }
  });
  select('#eventCounter').textContent = `${eventIndex + 1} / ${trace.events.length}`;
  select('#stepDemo').disabled = eventIndex === trace.events.length - 1;
  if (eventIndex === trace.events.length - 1) stopPlayback();
}

function loadReplay() {
  const key = `${select('#pattern').value}:${select('#scenario').value}`;
  loadTrace(REPLAY[key], '录制教学回放（非本次运行）');
}

function setBusy(value) {
  busy = value;
  ['runDemo', 'compareDemo', 'replayDemo', 'pattern', 'scenario', 'traceFile'].forEach(id => select(`#${id}`).disabled = value);
}

function clearTrace() {
  stopPlayback();
  trace = null;
  traceLabel = '';
  eventIndex = -1;
  select('#eventList').replaceChildren();
  select('#eventHeading').textContent = '等待本次运行结果';
  select('#roleMap').replaceChildren();
  select('#eventStory').textContent = 'LangGraph 正在执行；完成后可逐事件回看。';
  select('#flowCaption').textContent = '等待本次运行，尚无可展示的事件。';
  select('#observedEvidence').textContent = '当前已见证据：无';
  select('#revisionStory').textContent = '尚无修订记录。';
  select('#eventCounter').textContent = '0 / 0';
  document.querySelectorAll('#demoMetrics b').forEach(element => element.textContent = '—');
  ['stepDemo', 'playDemo', 'downloadTrace', 'showReport', 'showState', 'showEvent'].forEach(id => select(`#${id}`).disabled = true);
}

async function requestRun(pattern, scenario) {
  const response = await fetch('/api/run', {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({pattern, scenario}),
    signal: AbortSignal.timeout(30000)
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const value = await response.json();
  if (!validTrace(value)) throw new Error('服务返回的轨迹不符合新版协议');
  return value;
}

select('#runDemo').onclick = async () => {
  if (busy) return;
  if (!/^https?:$/.test(location.protocol)) {
    select('#demoStatus').textContent = '现场运行请先启动 demo/server.py，再访问 http://127.0.0.1:8765；离线可加载教学回放。';
    return;
  }
  clearTrace();
  setBusy(true);
  select('#demoStatus').textContent = 'LangGraph 正在执行；完成后展示本次运行轨迹。';
  try { loadTrace(await requestRun(select('#pattern').value, select('#scenario').value), '本次本地运行'); }
  catch (error) { select('#demoStatus').textContent = `运行未完成：${error.message}。请确认已安装依赖并启动 demo/server.py；可加载教学回放。`; }
  finally { setBusy(false); }
};

select('#replayDemo').onclick = loadReplay;
select('#stepDemo').onclick = () => selectEvent(eventIndex + 1);
select('#playDemo').onclick = () => {
  if (playback) { stopPlayback(); return; }
  if (!trace) return;
  if (eventIndex === trace.events.length - 1) selectEvent(0);
  select('#playDemo').textContent = '暂停播放';
  playback = setInterval(() => selectEvent(eventIndex + 1), 1300);
};
document.querySelectorAll('[data-demo-pattern]').forEach(button => button.onclick = () => {
  if (busy) return;
  select('#pattern').value = button.dataset.demoPattern;
  select('#scenario').value = button.dataset.demoScenario || 'normal';
  showSlide(labIndex);
  loadReplay();
});

function showResult(title, text) {
  stopPlayback();
  select('#resultTitle').textContent = title;
  select('#resultText').textContent = text;
  openDialog('resultDialog');
}
select('#showState').onclick = () => showResult('共享状态 · 运行结束时快照', JSON.stringify(trace.shared_state, null, 2));
select('#showEvent').onclick = () => showResult('当前事件 · 原始 JSON', JSON.stringify(trace.events[eventIndex], null, 2));
select('#showReport').onclick = () => showResult('报告与人工审核入口',
  `${traceLabel}\n${statuses[trace.status]}\n\n${trace.report || '本次未生成成功报告，请查看异常事件与交接信息。'}\n\n教学契约验证：${trace.verified ? '通过' : '未通过'}（不代表真实诊断结论正确）\n\n人工审核信息\n${JSON.stringify(trace.human_review || {status: 'pending'}, null, 2)}\n\n审核清单\n□ 证据与工单是否对应？\n□ 资料是否完整、时间是否匹配？\n□ 不确定性和待确认项是否保留？\n本课堂入口展示审核材料，不写入真实业务审批状态。`);
select('#compareDemo').onclick = async () => {
  if (busy) return;
  clearTrace();
  setBusy(true);
  const selectedScenario = select('#scenario').value;
  const live = /^https?:$/.test(location.protocol);
  select('#demoStatus').textContent = live ? '依次运行固定工作流和三种协作模式，使用同一情景与验收标准…' : '比较基线与三种模式的预录轨迹；未执行新任务。';
  try {
    const results = [];
    for (const pattern of ['workflow', 'supervisor', 'parallel', 'review']) {
      results.push(live ? await requestRun(pattern, selectedScenario) : REPLAY[`${pattern}:${selectedScenario}`]);
    }
    const lines = results.map(value => `${patterns[value.pattern]}\n  工具调用 ${value.metrics.tool_calls} 次 · 修订 ${value.metrics.revision_rounds} 轮\n  ${value.metrics.elapsed_ms.toFixed(1)} ms · 证据覆盖 ${Math.round(value.metrics.evidence_coverage * 100)}%\n  ${statuses[value.status]} · 契约验证 ${value.verified ? '通过' : '未通过'}`);
    showResult('同一任务 · 固定工作流与三种协作方式', `${live ? '本次本地实际运行' : '录制教学回放'} / ${scenarios[selectedScenario]}\n基线由程序分支决定；协作角色由规则模拟。使用相同仿真数据、工具和验收标准。\n\n${lines.join('\n\n')}\n\n本任务的路径可枚举，固定工作流已足够；多角色用于展示协作机制。\n耗时为本机单次测量，受调度与缓存影响；不代表真实模型成本或生产性能排名。证据覆盖率不等于诊断准确率。`);
    select('#demoStatus').textContent = `${live ? '本次运行' : '录制回放'}的基线与协作对比已完成；关闭窗口后可选择单个模式查看轨迹。`;
  } catch (error) { select('#demoStatus').textContent = `对比未完成：${error.message}。离线打开 HTML 可查看预录对比。`; }
  finally { setBusy(false); }
};
select('#traceFile').onchange = async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > 2_000_000) throw new Error('文件大于 2 MB');
    loadTrace(JSON.parse(await file.text()), '导入历史轨迹（内容由文件声明，未重新验收）');
  } catch (error) { select('#demoStatus').textContent = `导入失败：${error.message}`; }
  event.target.value = '';
};
select('#downloadTrace').onclick = () => {
  if (!trace) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(trace, null, 2)], {type: 'application/json'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = `${trace.run_id.replace(/[^a-zA-Z0-9_-]/g, '_')}-trace.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
showSlide((parseInt(location.hash.slice(1), 10) || 1) - 1);
fit();

/* Replay the Python runner's events, including their historical snapshots. */
(() => {
  const views = [...document.querySelectorAll('[data-ct-pattern]')].map(root => ({
    root, pattern: root.dataset.ctPattern,
    data: JSON.parse(root.querySelector('[data-ct-data]').textContent)
  }));
  const sessions = new Map(views.map(view => [view.pattern, {scenario: 'missing', position: -1}]));
  const names = {Researcher: '搜集者', Analyst: '费用专家', Writer: '撰写者', Critic: '审查者',
    Supervisor: '主管', CEO: '总负责人', ResearchLead: '资料负责人', DeliveryLead: '交付负责人',
    User: '用户', START: '开始', END: '结束', sequential: '顺序链', supervisor: '主管模式',
    hierarchical: '层次化', swarm: 'Swarm', network: 'Network'};
  const kinds = {work: '执行', dispatch: '分派', report: '汇报', escalate: '逐级反馈',
    handoff: '交接控制权', route: '选择下一跳', fixed_edge: '固定顺序', start: '进入', finish: '结束'};
  function render(view) {
    const {root, data, pattern} = view;
    const session = sessions.get(pattern);
    const trace = data.traces[session.scenario];
    const event = trace.events[session.position];
    const state = event?.state;
    root.dataset.ctPosition = String(session.position);
    root.dataset.ctScenario = session.scenario;
    root.querySelectorAll('[data-ct-scenario]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.ctScenario === session.scenario));
    });
    root.querySelector('[data-ct-action="back"]').disabled = session.position < 0;
    const next = root.querySelector('[data-ct-action="next"]');
    next.disabled = session.position === trace.events.length - 1;
    next.textContent = session.position < 0 ? '开始演示' : next.disabled ? '演示结束' : '下一步';
    root.querySelector('[data-ct-action="finish"]').disabled = next.disabled;
    root.querySelector('[data-ct-progress]').textContent = `${Math.max(0, session.position + 1)} / ${trace.events.length} 步`;
    const get = key => root.querySelector(`[data-ct-state="${key}"]`);
    get('evidence').textContent = state?.evidence?.candidates ? `${state.evidence.candidates.length} 个候选` : '未查询';
    const hasMeal = state && Object.hasOwn(state.evidence, 'meal');
    get('meal').textContent = hasMeal ? `${state.evidence.meal} 元 / 三人` : state?.evidence?.candidates ? '缺失，不能按 0 元' : '未查询';
    get('meal').classList.toggle('ct-missing', !!state?.evidence?.candidates && !hasMeal);
    get('analysis').textContent = state?.analyzed ? '全部费用已核算' : state?.issues?.length ? '缺资料，无法核算' : '未完成';
    get('proposal').textContent = state?.proposal ? state.proposal.venue ? `${state.proposal.venue} · ${state.proposal.total} 元` : '当前条件无可行方案' : '未生成';
    get('approved').textContent = state?.approved ? '通过' : event?.kind === 'finish' ? '等待补充资料' : '未通过';
    get('approved').classList.toggle('ct-approved', !!state?.approved);
    const label = role => names[role] || role;
    const title = event ? event.actor === event.target ? `${label(event.actor)} · ${kinds[event.kind] || event.kind}`
      : `${label(event.actor)} → ${label(event.target)} · ${kinds[event.kind] || event.kind}`
      : '先预测：缺餐费时，谁决定下一步？';
    root.querySelector('[data-ct-event-title]').textContent = title;
    root.querySelector('[data-ct-event-message]').textContent = event ? event.message || event.reason
      : '点击开始演示，观察控制权、消息与状态。';
    root.querySelectorAll('[data-ct-node]').forEach(node => {
      node.classList.toggle('ct-current', !!event && (node.dataset.ctNode === event.actor || node.dataset.ctNode === event.target));
    });
    root.querySelectorAll('[data-ct-edge]').forEach(edge => {
      const active = !!event && edge.dataset.ctEdge === `${event.actor}:${event.target}`;
      edge.classList.toggle('ct-current', active);
      if (active) edge.parentNode.append(edge); // Draw the active connection above gray connections.
    });
    // Keep nodes above the connections after bringing the current edge forward.
    root.querySelectorAll('[data-ct-node]').forEach(node => node.parentNode.append(node));
    const highlighted = data.highlights[session.scenario][session.position];
    root.querySelectorAll('[data-ct-line]').forEach(line => {
      line.classList.toggle('ct-current', highlighted === Number(line.dataset.ctLine));
    });
  }
  function refresh(pattern) { views.filter(view => view.pattern === pattern).forEach(render); }
  views.forEach(view => {
    view.root.addEventListener('click', event => {
      const scenario = event.target.closest('button[data-ct-scenario]');
      const action = event.target.closest('button[data-ct-action]');
      if (!scenario && !action) return;
      const session = sessions.get(view.pattern);
      if (scenario) {
        session.scenario = scenario.dataset.ctScenario;
        session.position = -1;
      } else {
        const last = view.data.traces[session.scenario].events.length - 1;
        switch (action.dataset.ctAction) {
          case 'next': session.position = Math.min(last, session.position + 1); break;
          case 'back': session.position = Math.max(-1, session.position - 1); break;
          case 'reset': session.position = -1; break;
          case 'finish': session.position = last; break;
        }
      }
      refresh(view.pattern);
    });
    render(view);
  });
})();

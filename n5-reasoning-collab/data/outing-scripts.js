(function () {
  'use strict';
  var N5 = window.N5;
  var clone = function (value) { return JSON.parse(JSON.stringify(value)); };
  function freeze(value) {
    if (value && typeof value === 'object') {
      Object.keys(value).forEach(function (key) { freeze(value[key]); });
      Object.freeze(value);
    }
    return value;
  }
  var venues = [
    { id: 'P01', name: '城市公园', type: 'outdoor', tickets: 0, transport: 40, meal: 80, total: 120 },
    { id: 'P02', name: '植物园', type: 'outdoor', tickets: 150, transport: 40, meal: 80, total: 270 },
    { id: 'P03', name: '科技馆', type: 'indoor', tickets: 90, transport: 40, meal: 80, total: 210 },
    { id: 'P04', name: '美术馆', type: 'indoor', tickets: 80, transport: 40, meal: 80, total: 200 }
  ];
  var documents = [
    { id: 'D01', text: '雨天优先选室内场馆；本教学案例将户外场馆视为雨天不可行。' },
    { id: 'D02', text: '费用必须包含两大一小的门票、交通与固定 80 元餐费。' }
  ];
  N5.outingData = freeze({ venues: venues, documents: documents, meal: 80, source: '课程内置合成数据；不联网、不预订' });

  function conditions(options) {
    options = options || {};
    var weather = options.weather === undefined ? 'rain' : options.weather;
    var budget = options.budget === undefined ? 300 : options.budget;
    if (['sun', 'rain'].indexOf(weather) === -1) throw new Error('weather 必须为 sun 或 rain');
    if ([300, 200, 100].indexOf(budget) === -1) throw new Error('budget 必须为 300、200 或 100');
    return { weather: weather, budget: budget };
  }
  function role(id, label) { return { id: id, label: label }; }
  var host = role('host', '宿主 · 工具与验收');
  function Tape(initial) {
    this.state = clone(initial);
    this.initialState = freeze(clone(initial));
    this.writers = {};
    Object.keys(initial).forEach(function (key) { this.writers[key] = 'host'; }, this);
    this.events = [];
  }
  Tape.prototype.emit = function (actor, kind, title, detail, payload, patch, highlight, writeAs) {
    var self = this;
    Object.keys(patch || {}).forEach(function (key) {
      self.state[key] = clone(patch[key]);
      self.writers[key] = writeAs || actor;
    });
    this.state.version += 1;
    this.writers.version = 'host';
    var event = freeze({
      id: 'e' + String(this.events.length + 1).padStart(3, '0'), actor: actor, kind: kind,
      title: title, detail: detail, payload: clone(payload || {}), state_after: clone(this.state),
      highlight: (highlight || [actor]).slice(), writers: clone(this.writers)
    });
    this.events.push(event);
    return event;
  };
  Tape.prototype.finish = function () { return freeze({ initialState: this.initialState, events: this.events.slice() }); };
  function outingTape(input, controller) {
    return new Tape({
      version: 0, control: controller, weather: null, venues: [], selected: null,
      costs: null, budget_used: null, itinerary: null,
      constraints: { weather_input: input.weather, budget: input.budget, adults: 2, children: 1, day: '周六半日', meal: 80 },
      plan: null, plan_version: 0, reports: {}, delegated_to: null,
      pending_tool: null, tool_calls: 0, budget_check: null, error: null, status: 'running'
    });
  }
  function tool(tape, actor, name, args, input) {
    var requestId = 't' + String(tape.state.tool_calls + 1).padStart(2, '0');
    tape.emit(actor, 'action', '请求工具 · ' + name,
      '角色提交结构化请求；结果由宿主根据合成资料计算。',
      { tool: name, args: args, request_id: requestId }, { pending_tool: { name: name, args: args, request_id: requestId } });
    var result, patch = { pending_tool: null, tool_calls: tape.state.tool_calls + 1 };
    if (name === 'get_weather') {
      result = { condition: input.weather, label: input.weather === 'rain' ? '周六有雨' : '周六晴天', source_id: 'WEATHER-SAT-SYNTHETIC' };
      patch.weather = result;
    } else if (name === 'search_venue') {
      result = venues.filter(function (v) { return args.type === 'all' || v.type === args.type; });
      patch.venues = result;
    } else if (name === 'calculate_cost') {
      var venue = venues.find(function (v) { return v.id === args.venue; });
      if (!venue) throw new Error('未知场馆');
      result = { venue: venue.id, tickets: venue.tickets, transport: venue.transport, meal: venue.meal, total: venue.tickets + venue.transport + venue.meal };
      patch.costs = result;
      patch.budget_used = result.total;
    } else if (name === 'check_budget') {
      result = { total: args.total, limit: input.budget, ok: args.total <= input.budget, remaining: input.budget - args.total };
      patch.budget_check = result;
    } else {
      throw new Error('未知工具：' + name);
    }
    tape.emit('host', 'observation', '工具返回 · ' + name,
      name === 'calculate_cost' ? result.tickets + ' 门票 + ' + result.transport + ' 交通 + ' + result.meal + ' 餐费 = ' + result.total + ' 元。' : '宿主读取课程资料后返回；此观察不是模型生成。',
      { source: 'synthetic_tool', tool: name, request_id: requestId, result: result }, patch, [actor, 'host']);
    return clone(result);
  }
  function dispatch(tape, from, to, title, detail, handoff) {
    var patch = { delegated_to: to };
    if (handoff) patch.control = to;
    return tape.emit(from, 'dispatch', title, detail,
      { from: from, to: to, intent: handoff ? 'handoff' : 'delegate', correlation_id: 'outing-01', expected_state_version: tape.state.version }, patch, [from, to]);
  }
  function report(tape, actor, to, title, data, detail) {
    var reports = clone(tape.state.reports);
    reports[actor] = data;
    tape.emit(actor, 'report', title, detail || '向上游交付结构化结果，保留工具观察的证据引用。',
      { from: actor, to: to, intent: 'report', data: data, expected_state_version: tape.state.version }, { reports: reports }, [actor, to]);
  }
  function preference(weather, weatherAware) {
    var ids = weatherAware && weather === 'rain' ? ['P03', 'P04'] : ['P02', 'P01', 'P03', 'P04'];
    return ids.map(function (id) { return venues.find(function (v) { return v.id === id; }); });
  }
  function selectWithinBudget(tape, actor, input, weatherAware) {
    var choices = preference(input.weather, weatherAware).filter(function (v) {
      return tape.state.venues.some(function (candidate) { return candidate.id === v.id; });
    });
    for (var i = 0; i < choices.length; i += 1) {
      var venue = choices[i];
      tape.emit(actor, 'thought', '评估候选 · ' + venue.name,
        '按课程预设的亲子活动偏好尝试候选；先核算全部费用，再决定是否采用。这里不把活动偏好声称为通用性价比结论。',
        { candidate: venue.id }, { selected: venue });
      var costs = tool(tape, actor, 'calculate_cost', { venue: venue.id }, input);
      var check = tool(tape, actor, 'check_budget', { total: costs.total }, input);
      if (check.ok) return venue;
      tape.emit(actor, 'thought', '超预算，尝试下一候选', venue.name + ' 共 ' + costs.total + ' 元，超过 ' + input.budget + ' 元；不丢掉餐费来凑预算。', { rejected: venue.id, excess: costs.total - input.budget }, {});
    }
    tape.emit(actor, 'report', '候选均不满足预算', '已按完整费用检查可选场馆；请求人工调整预算或任务条件。', { code: 'NO_FEASIBLE_VENUE' }, { selected: null, error: { code: 'NO_FEASIBLE_VENUE', message: '当前条件下无可行方案' } });
    return null;
  }
  function accept(tape, input, reason) {
    var selected = tape.state.selected;
    var fact = selected && venues.find(function (v) { return v.id === selected.id; });
    var acceptance = {
      selected_exists: Boolean(fact),
      cost_matches: Boolean(fact && tape.state.costs && tape.state.costs.venue === fact.id && tape.state.budget_used === fact.total && tape.state.costs.total === fact.total),
      weather_compatible: Boolean(fact && tape.state.weather && tape.state.weather.condition === input.weather && (input.weather === 'sun' || fact.type === 'indoor')),
      within_budget: Boolean(fact && fact.total <= input.budget && tape.state.budget_check && tape.state.budget_check.ok)
    };
    var ok = !reason && Object.keys(acceptance).every(function (key) { return acceptance[key]; });
    var itinerary = ok ? { venue_id: fact.id, venue: fact.name, when: '周六半日', people: '两大一小', total: fact.total, breakdown: { tickets: fact.tickets, transport: fact.transport, meal: fact.meal } } : null;
    tape.emit('host', 'done', ok ? '宿主验收通过' : '停止 · 需要人工处理',
      ok ? fact.name + '，总费用 ' + fact.total + ' 元；天气、费用明细和预算逐项通过。仅输出行程，不执行预订。' : reason || '现有场馆、天气与预算无法同时满足；未生成已通过的行程。',
      { status: ok ? 'completed' : 'needs_human', acceptance: acceptance, reason: reason || (ok ? null : 'NO_FEASIBLE_VENUE') },
      { status: ok ? 'completed' : 'needs_human', itinerary: itinerary, control: 'host', delegated_to: null, error: ok ? null : (tape.state.error || { code: 'ACCEPTANCE_FAILED', message: reason || '无可行方案' }) });
    return ok;
  }
  function weatherSearch(tape, actor, input) {
    tape.emit(actor, 'thought', '先确认天气', '场馆类型依赖天气，因此先取得天气观察。', {}, {});
    tool(tape, actor, 'get_weather', {}, input);
    var type = tape.state.weather.condition === 'rain' ? 'indoor' : 'all';
    tape.emit(actor, 'thought', type === 'indoor' ? '下雨，只保留室内场馆' : '晴天，可考虑室内与户外', '依据刚收到的天气观察选择检索条件，使用资料 D01。', { document: 'D01', type: type }, {});
    tool(tape, actor, 'search_venue', { type: type }, input);
  }
  var planV1 = ['按活动偏好选择场馆', '计算两大一小门票', '计算交通与餐费', '核对总预算', '确认可行性并输出行程'];
  var planV2 = ['查询天气', '按天气过滤场馆类型', '选择候选场馆', '计算两大一小门票', '计算交通与餐费', '核对预算与可行性并输出行程'];
  function publishPlan(tape, actor, version) {
    var plan = version === 1 ? planV1 : planV2;
    tape.emit(actor, version === 1 ? 'plan' : 'revision', '发布计划 v' + version,
      version === 1 ? '门票、交通、餐费均列入计划；先选场馆，末尾再做可行性确认。' : '结构修订：将天气查询前置，并在选择场馆前增加类型过滤。费用项沿用 v1。',
      { version: version, steps: plan, changed: version === 2 ? ['天气前置', '类型过滤'] : [] },
      { plan: plan, plan_version: version, error: null });
  }
  function runV1(tape, actor, input) {
    tool(tape, actor, 'search_venue', { type: 'all' }, input);
    var selected = selectWithinBudget(tape, actor, input, false);
    if (!selected) return 'NO_FEASIBLE_VENUE';
    tape.emit(actor, 'thought', '末尾进行可行性确认', '预算已经核对；此时才调用天气工具，检验场馆能否使用。', {}, {});
    tool(tape, actor, 'get_weather', {}, input);
    if (input.weather === 'rain' && selected.type === 'outdoor') {
      tape.emit(actor, 'finding', '计划受阻 · 雨天户外不可行',
        selected.name + '的费用齐全且在预算内，但与雨天条件冲突。工具执行正常，失败来自计划的依赖顺序。',
        { code: 'OUTDOOR_IN_RAIN', venue: selected.id, observed_weather: input.weather },
        { error: { code: 'OUTDOOR_IN_RAIN', message: '选场馆发生在查天气之前' } });
      return 'OUTDOOR_IN_RAIN';
    }
    return null;
  }

  N5.scenarios.react = {
    title: 'ReAct · 观察驱动下一步', roles: [role('executor', '出游 Agent'), host],
    create: function (options) {
      var input = conditions(options), tape = outingTape(input, 'executor');
      weatherSearch(tape, 'executor', input);
      selectWithinBudget(tape, 'executor', input, true);
      accept(tape, input);
      return tape.finish();
    }
  };
  N5.scenarios.plan = {
    title: 'Plan-and-Execute · 计划 v1', roles: [role('planner', '规划器'), role('executor', '执行器'), host],
    create: function (options) {
      var input = conditions(options), tape = outingTape(input, 'planner');
      publishPlan(tape, 'planner', 1);
      dispatch(tape, 'planner', 'executor', '下发计划 v1', '执行器按照既定顺序执行，未授权自行重排步骤。', true);
      var failure = runV1(tape, 'executor', input);
      accept(tape, input, failure === 'OUTDOOR_IN_RAIN' ? '计划 v1 未把天气放在选场馆之前；请修订计划后重新执行。' : failure);
      return tape.finish();
    }
  };
  N5.scenarios.supervisor = {
    title: 'Supervisor · 主管集中调度',
    roles: [role('supervisor', '主管'), role('weather', '天气 Agent'), role('venue', '场馆 Agent'), role('budget', '预算 Agent'), host],
    create: function (options) {
      var input = conditions(options), tape = outingTape(input, 'supervisor');
      dispatch(tape, 'supervisor', 'weather', '主管委派天气任务', '控制权保留在主管；天气角色只能执行工具并回报。');
      tool(tape, 'weather', 'get_weather', {}, input);
      report(tape, 'weather', 'supervisor', '天气报告返回主管', { weather: tape.state.weather.condition });
      dispatch(tape, 'supervisor', 'venue', '主管按天气派发场馆任务', input.weather === 'rain' ? '主管依据雨天观察，要求只查室内。' : '主管允许查询所有场馆。');
      tool(tape, 'venue', 'search_venue', { type: input.weather === 'rain' ? 'indoor' : 'all' }, input);
      report(tape, 'venue', 'supervisor', '候选报告返回主管', { candidates: tape.state.venues.map(function (v) { return v.id; }) });
      var choices = preference(input.weather, true).filter(function (v) {
        return tape.state.venues.some(function (candidate) { return candidate.id === v.id; });
      });
      var feasible = false;
      for (var i = 0; i < choices.length; i += 1) {
        var candidate = choices[i];
        tape.emit('supervisor', 'thought', '主管选择待核算候选 · ' + candidate.name,
          '根据场馆报告和已收到的预算结果选择下一候选；预算角色不能自行更换场馆。',
          { candidate: candidate.id }, { selected: candidate });
        dispatch(tape, 'supervisor', 'budget', '主管委派单个候选核算',
          '只核算 ' + candidate.name + ' 的全部费用与预算结果，然后回报主管。');
        var costs = tool(tape, 'budget', 'calculate_cost', { venue: candidate.id }, input);
        var check = tool(tape, 'budget', 'check_budget', { total: costs.total }, input);
        report(tape, 'budget', 'supervisor', '预算报告返回主管',
          { selected: candidate.id, total: costs.total, feasible: check.ok },
          check.ok ? '当前候选费用通过；由主管决定是否提交验收。' : '当前候选超预算；回报事实，由主管决定是否另派候选。');
        if (check.ok) { feasible = true; break; }
        tape.emit('supervisor', 'thought', '主管接收超额结果，决定继续查找',
          candidate.name + ' 共 ' + costs.total + ' 元，超过 ' + input.budget + ' 元。保留约束，按未尝试候选重新派发。',
          { rejected: candidate.id, excess: costs.total - input.budget }, { delegated_to: null });
      }
      if (!feasible) {
        tape.emit('supervisor', 'report', '主管确认候选耗尽',
          '各候选均已收到不通过报告；停止委派，请求人工调整约束。',
          { code: 'NO_FEASIBLE_VENUE', to: 'host' },
          { selected: null, error: { code: 'NO_FEASIBLE_VENUE', message: '当前条件下无可行方案' } });
      }
      tape.emit('supervisor', 'report', '主管合并三份报告', '执行角色之间没有直接通信。主管提交候选，最终停止由宿主验收决定。', { to: 'host' }, { delegated_to: null });
      accept(tape, input);
      return tape.finish();
    }
  };
  N5.scenarios.hierarchical = {
    title: '层次化 · 两个小组汇总',
    roles: [role('director', '总管'), role('info_lead', '信息组长'), role('weather', '天气 Agent'), role('venue', '场馆 Agent'), role('finance_lead', '财务组长'), role('budget', '预算 Agent'), role('ticket', '票务 Agent'), host],
    create: function (options) {
      var input = conditions(options), tape = outingTape(input, 'director');
      dispatch(tape, 'director', 'info_lead', '总管下发信息组任务', '组长负责天气与场馆的局部调度；总管只接收组报告。', true);
      dispatch(tape, 'info_lead', 'weather', '信息组长委派天气', '天气角色仅将观察摘要返回本组。');
      tool(tape, 'weather', 'get_weather', {}, input);
      report(tape, 'weather', 'info_lead', '天气回报信息组长', { weather: input.weather });
      dispatch(tape, 'info_lead', 'venue', '信息组长委派场馆', '按已确认的天气过滤场馆类型。');
      tool(tape, 'venue', 'search_venue', { type: input.weather === 'rain' ? 'indoor' : 'all' }, input);
      report(tape, 'venue', 'info_lead', '场馆回报信息组长', { candidates: tape.state.venues.map(function (v) { return v.id; }) });
      report(tape, 'info_lead', 'director', '信息组提交一份摘要', { weather: input.weather, candidates: tape.state.venues.map(function (v) { return v.id; }), evidence: ['D01'] });
      dispatch(tape, 'info_lead', 'director', '信息组归还控制权', '总管接收组合报告，无需重读组内对话。', true);
      dispatch(tape, 'director', 'finance_lead', '总管下发财务组任务', '传递候选和预算，财务组负责票价证据与预算决策。', true);
      dispatch(tape, 'finance_lead', 'ticket', '财务组长委派票务核对', '票务角色核对两大一小门票口径，不执行购票。');
      var ticketRows = tape.state.venues.map(function (v) { return { venue: v.id, family_tickets: v.tickets }; });
      report(tape, 'ticket', 'finance_lead', '票务回报财务组长', { tickets: ticketRows, source: 'search_venue 已验证返回值', booking: false });
      dispatch(tape, 'finance_lead', 'budget', '财务组长委派完整费用核算', '核算门票、交通和餐费；场馆超预算则尝试下一候选。');
      selectWithinBudget(tape, 'budget', input, true);
      report(tape, 'budget', 'finance_lead', '预算回报财务组长', { total: tape.state.budget_used, feasible: Boolean(tape.state.selected) });
      report(tape, 'finance_lead', 'director', '财务组提交一份摘要', { venue: tape.state.selected && tape.state.selected.id, total: tape.state.budget_used, within_budget: Boolean(tape.state.selected) });
      dispatch(tape, 'finance_lead', 'director', '财务组归还控制权', '总管依据两份组报告形成结果，提交宿主验收。', true);
      accept(tape, input);
      return tape.finish();
    }
  };
  N5.scenarios.swarm = {
    title: 'Swarm · 对等角色交接', roles: [role('weather', '天气 Agent'), role('venue', '场馆 Agent'), role('budget', '预算 Agent'), host],
    create: function (options) {
      var input = conditions(options), tape = outingTape(input, 'weather');
      tool(tape, 'weather', 'get_weather', {}, input);
      dispatch(tape, 'weather', 'venue', '天气角色直接交接给场馆角色', input.weather === 'rain' ? '携带雨天证据，场馆角色接管并筛选室内。没有中央主管。' : '携带晴天证据，场馆角色接管候选选择。没有中央主管。', true);
      tool(tape, 'venue', 'search_venue', { type: input.weather === 'rain' ? 'indoor' : 'all' }, input);
      var choices = preference(input.weather, true).filter(function (v) {
        return tape.state.venues.some(function (candidate) { return candidate.id === v.id; });
      });
      var feasible = false;
      for (var i = 0; i < choices.length; i += 1) {
        var candidate = choices[i];
        tape.emit('venue', 'thought', '场馆角色选择候选 · ' + candidate.name,
          '从天气兼容且尚未尝试的场馆中选择；费用不通过时由预算角色交还控制权。',
          { candidate: candidate.id }, { selected: candidate });
        var estimate = tool(tape, 'venue', 'calculate_cost', { venue: candidate.id }, input);
        dispatch(tape, 'venue', 'budget', estimate.total > input.budget ? '候选超额，交接预算角色核验' : '交接预算角色进行最终核验',
          candidate.name + ' 共 ' + estimate.total + ' 元；携带完整费用，预算角色负责检查上限。', true);
        var check = tool(tape, 'budget', 'check_budget', { total: estimate.total }, input);
        if (check.ok) {
          feasible = true;
          tape.emit('budget', 'report', '预算角色请求宿主结束',
            '对等 Agent 可以提出结束请求；宿主以统一的天气、费用与预算规则决定是否通过，不能仅靠 Agent 自称成功。',
            { to: 'host', intent: 'request_stop', candidate: candidate.id }, {});
          break;
        }
        report(tape, 'budget', 'venue', '预算不通过，回传候选与原因',
          { selected: candidate.id, total: estimate.total, budget: input.budget, feasible: false },
          '预算角色不自行换场馆，也不改票价；将完整核算结果交给场馆角色。');
        dispatch(tape, 'budget', 'venue', '预算角色直接交回场馆角色',
          '携带已拒绝的 ' + candidate.name + ' 和预算限制，请场馆角色选择下一候选；没有中央主管。', true);
      }
      if (!feasible) {
        tape.emit('venue', 'report', '场馆角色确认候选耗尽',
          '收到预算失败后已没有未尝试候选；向宿主请求结束，避免在角色之间无限交接。',
          { to: 'host', intent: 'request_stop', code: 'NO_FEASIBLE_VENUE' },
          { selected: null, error: { code: 'NO_FEASIBLE_VENUE', message: '当前条件下无可行方案' } });
      }
      accept(tape, input);
      return tape.finish();
    }
  };

  N5.scriptUtils = { clone: clone, freeze: freeze, Tape: Tape, role: role, host: host, conditions: conditions, outingTape: outingTape, tool: tool, dispatch: dispatch, report: report, selectWithinBudget: selectWithinBudget, accept: accept, weatherSearch: weatherSearch, publishPlan: publishPlan, runV1: runV1 };
}());

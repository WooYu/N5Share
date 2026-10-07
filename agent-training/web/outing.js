const outingPlaces = [
  {id: 'P01', name: '湖畔公园', indoor: false, ticket: 60, transport: 40, meal: 80},
  {id: 'P02', name: '自然馆', indoor: true, ticket: 150, transport: 60, meal: 100},
  {id: 'P03', name: '城市博物馆', indoor: true, ticket: 90, transport: 40, meal: 80}
];

const outingDocuments = [
  {id: 'D01', text: '雨天排除户外场馆。', keywords: ['出游', '天气', '雨天']},
  {id: 'D02', text: '两大一小的预算必须包含门票、交通和餐费。', keywords: ['出游', '费用', '预算']},
  {id: 'D03', text: '长途住宿行程需另核对酒店入住时间。', keywords: ['住宿', '酒店']}
];

function outingCost(place) {
  return place.ticket + place.transport + place.meal;
}

function outingPrice(place) {
  return `${place.name} [${place.id}]：门票 ${place.ticket} + 交通 ${place.transport} + 餐费 ${place.meal} = ${outingCost(place)} 元`;
}

function makeOutingTrace(stage, weather, budget) {
  const rainy = weather === 'rain';
  const weatherText = rainy ? '周六有雨' : '周六晴天';
  const suitable = outingPlaces.filter(place => !rainy || place.indoor);
  const affordable = suitable.filter(place => outingCost(place) <= budget);
  const chosen = affordable[0];
  const events = [];
  const emit = (phase, title, detail) => events.push({phase, title, detail});
  const forecast = () => emit('观察 Observation', '天气工具返回', `read_weather() → ${weatherText} [WX01]。这是本地仿真数据。`);
  const catalog = () => emit('观察 Observation', '场馆工具返回', outingPlaces.map(place => `${place.name} [${place.id}]：${place.indoor ? '室内' : '室外'}`).join('；'));
  const finish = () => {
    if (chosen) emit('结果 Result', '建议已就绪，等待用户确认', `${weatherText}；选择${chosen.name}，合计 ${outingCost(chosen)} 元 ≤ 预算 ${budget} 元。引用 [WX01 / ${chosen.id} / D01 / D02]。没有预约或付款。`);
    else emit('停止 Stop', '没有满足条件的方案', `${weatherText}；现有候选均不能同时满足天气条件和 ${budget} 元预算。请用户调整预算或目的地，停止继续尝试。`);
  };
  emit('目标 Goal', '同一个任务，逐步增加能力', `周六两大一小，安排半日出游，总预算 ${budget} 元。先给建议，不预约、不付款。`);
  if (stage === 1) {
    emit('示例回答 Sample', '只凭提示词给出一个想法', '“可以去湖畔公园散步、野餐，安排轻松的半日游。”这段是预写示例，没有调用模型。');
    emit('能力边界 Limit', '还没有事实依据', '未读取天气、场所资料或费用，不能断言可出行、营业或满足预算。');
  } else if (stage === 2) {
    emit('检索 Retrieval', '找到两条出游资料', '[D01] 雨天优先室内场所；[D02] 预算应包括两大一小的门票、交通与餐费。这两条是本地教学资料。');
    emit('增强回答 Grounded Answer', '回答开始有引用', '“先确认周六天气；雨天考虑室内 [D01]。再计算门票、交通和餐费 [D02]。”');
    emit('能力边界 Limit', '有资料不代表有当前数据', '检索规则没有提供本周天气和具体报价。固定检索后回答也可以是工作流。');
  } else if (stage === 3) {
    forecast();
    catalog();
    emit('计算工具 Tool', '程序实际计算本地报价', outingPlaces.map(outingPrice).join('\n'));
    emit('能力边界 Limit', '工具调用不等于自主决策', '已经拿到天气与报价；这些调用顺序由代码预设。下一页再观察如何依据反馈调整选择。');
  } else if (stage === 4) {
    emit('判断 Thought', '先确定天气条件', '先查询天气，决定应查看室内还是室外候选。以下决策均由教学规则模拟。');
    emit('行动 Action', '请求天气工具', 'read_weather()：宿主程序读取本地天气样本。');
    forecast();
    emit('判断 Thought', '读取场馆名单', '天气已返回，再读取候选场馆及室内外属性。');
    emit('行动 Action', '请求场馆工具', 'read_catalog()：宿主读取合成场馆名单。');
    catalog();
    emit('检索 Retrieval', '加载规则与候选', '[D01] 雨天选室内；[D02] 费用包括门票、交通、餐费。' + suitable.map(place => `${place.name} [${place.id}]`).join('；'));
    for (const place of suitable) {
      emit('判断 Thought', `检查${place.name}的费用`, `候选符合天气要求；还需确认总费用是否不超过 ${budget} 元。`);
      emit('行动 Action', '调用费用计算工具', `calculate_cost(place_id="${place.id}")`);
      emit('观察 Observation', outingCost(place) <= budget ? '费用满足预算' : '费用超出预算，需要换候选', outingPrice(place));
      if (outingCost(place) <= budget) break;
    }
    finish();
  } else if (stage === 5) {
    emit('计划 Plan', '先列任务和依赖', '① 查天气与候选；② 根据①计算可行方案；③ 检查天气与完整费用；④ 输出建议。只有完成前项才能验收后项。');
    emit('执行 Execute', '完成资料收集', `${weatherText} [WX01]；规则 [D01 / D02]；候选 [P01 / P02 / P03]。`);
    emit('执行 Execute', '按依赖计算费用', suitable.map(outingPrice).join('\n'));
    emit('验证 Validation', chosen ? '验收条件通过' : '验收条件未通过', chosen ? `符合天气要求；费用三项齐全；${outingCost(chosen)} ≤ ${budget}；有来源编号。` : `天气允许的候选中，没有总费用 ≤ ${budget} 元的方案。保留已查资料，请用户调整要求。`);
    finish();
  } else if (stage === 6) {
    emit('计划 v1 / 执行', '初次执行得到有问题的草稿', '“去湖畔公园，门票 60 + 交通 40 = 100 元。”初稿漏算餐费，也没有核对天气。');
    emit('反馈 Feedback', '依据工具结果检查初稿', `${weatherText} [WX01]；湖畔公园为室外 [P01]；[D02] 要求含餐费。完整费用应为 60 + 40 + 80 = 180 元。`);
    emit('反思 Reflection', '把问题变成具体修改动作', `补上 80 元餐费，再核对 ${budget} 元预算；${rainy ? '雨天排除公园，改查室内候选' : '晴天可保留公园，但仍须检查总费用'}。不只是把文字改得更自信。`);
    emit('计划 v2 / 再执行', '根据失败反馈修订计划', '核对天气、补齐三项费用、验收预算；保留已有天气证据。重新计算：' + suitable.map(place => `${place.name} ${outingCost(place)} 元 [${place.id}]`).join('；') + '。');
    emit('再次验收 Validation', chosen ? '修订后通过' : '修订后仍无可行方案', chosen ? '天气适配、三项费用齐全、预算内，且保留来源。' : '完整费用仍超预算；停止重试，请用户调整条件。');
    finish();
  } else if (stage === 7) {
    emit('模式 Patterns', '同一任务可以怎样组织协作', 'Supervisor：主管分派给天气与费用角色；层次化：总主管分派给出游组与预算组，组长再分派；Swarm：天气角色按需交接给费用角色，再交接给汇总角色。下面仅示意 Supervisor。');
    emit('分工 Delegation', '主管为两种资料设置独立分析角色', '天气角色负责天气与室内外条件；费用角色负责三项费用；协调者合并结果。这里只演示分工，原任务用一个工作流也足够。');
    emit('消息 Messages', '两份独立结果交给协调者', `天气角色 → ${weatherText} [WX01 / D01]，可选：${suitable.map(place => place.name).join('、')}。\n费用角色 → ${outingPlaces.map(place => `${place.name} ${outingCost(place)} 元 [${place.id}]`).join('；')} [D02]。`);
    emit('共享状态 Shared State', '协调者合并两份消息中的证据', `task_id=outing-1；plan_version=1；budget=${budget}；weather=${weather}；evidence_refs=[WX01,P01,P02,P03,D01,D02]；status=ready_to_review。消息包含 from/to/type 与证据引用；按来源合并，不互相覆盖。`);
    emit('汇总 Synthesis', '交叉检查天气和预算', `${suitable.map(place => `${place.name}：${outingCost(place) <= budget ? '满足' : '超过'} ${budget} 元预算`).join('；')}。合并独立结果需要统一字段、来源和完成条件。`);
    finish();
  }
  return events;
}

// Shared fixtures support a baseline trace and the slide-specific teaching events.
// Live model sessions use their own backend and the initial scenario parameters.
function makeArchitectureTrace(architecture, weather, budget, intent = 'outing', keyEvents = false) {
  const rainy = weather === 'rain';
  const suitable = outingPlaces.filter(p => !rainy || p.indoor);
  const chosen = suitable.find(p => outingCost(p) <= budget);
  const events = [];
  const emit = (phase, title, detail, data = {}) => events.push({phase, title, detail, ...data});
  const review = () => {
    const facts = {
      1: '一个角色先检索 D01 / D02，再执行天气、场馆和费用工具；规则与当前数据各有来源。',
      2: events.filter(e => e.phase === '观察 Observation' && e.title.startsWith('费用')).map(e => e.detail).join('\n') + '\n每轮费用观察决定继续或停止；满足条件后不再查询其余候选。',
      3: keyEvents ? '用户在执行中改预算；保留已查天气与名单，规划器只修订受影响的步骤，再执行与验收。' : '计划 v1 → 首次失败 → 具体反思 → 计划 v2 → 再执行；修订增加一轮执行与验收。',
      4: '天气与费用各交付一份消息；主管等待两份结果后取交集，增加消息与合并步骤。',
      5: keyEvents && intent === 'outing' ? '出游技能准备后，用户改成只算费用；重新路由到费用技能，原出游流程未执行，省去天气调用。' : intent === 'budget' ? '仅加载费用技能，省去天气调用；其输出不能作为出行建议。' : intent === 'unclear' ? '模糊输入未命中技能，停止并请求澄清。' : '输入意图命中出游技能，加载其流程与 Reference；不加载费用专用技能。',
      6: '场馆名单发布后费用角色才就绪；三类证据齐备后汇总才就绪；版本随写入递增。',
      7: `${rainy ? 'rain → indoor_filter' : 'sun → all_places'} → cost → validate → ${chosen ? 'recommend' : 'no_solution'} → END；每一步都由显式边决定。`
    };
    const item = typeof DEMO_TRADEOFFS !== 'undefined' ? DEMO_TRADEOFFS.architecture?.[architecture] : null;
    emit('机制复盘', '本次观察到的特点', facts[architecture]);
    if (item) emit('取舍复盘', '优势与局限如何对应本例', `优势：${item.advantage}\n局限：${item.limitation}\n本次为离线规则示意，未测量真实模型性能、并发冲突或生产恢复。`);
  };
  const finish = (selection = chosen, effectiveBudget = budget) => {
    review();
    const result = {status: selection ? 'recommended' : 'no_solution', place_id: selection?.id || '', total: selection ? outingCost(selection) : 0,
      budget: effectiveBudget, citations: ['WX01', 'D01', 'D02', ...(selection ? [selection.id] : suitable.map(p => p.id))]};
    emit(selection ? '结果 Result' : '停止 Stop', selection ? '建议待用户确认' : '没有满足条件的方案',
      selection ? `${rainy ? '雨天' : '晴天'}；${selection.name} [${selection.id}]，完整费用 ${result.total} 元 ≤ ${effectiveBudget} 元。依据 [WX01 / D01 / D02]；不订票、不付款。`
        : `现有候选不能同时满足天气和 ${effectiveBudget} 元预算。保留证据，请用户调整条件；停止运行。`, {result});
  };
  if (architecture === 1) {
    emit('目标 Goal', '同一 Agent 组合 RAG 与 Tool', `两大一小，半日出游，预算 ${budget} 元。接下来查看资料检索和工具请求；离线生成由规则示意。`);
    emit('LLM · 生成基础', '只有语言建议，还缺事实', '“可以去公园散步。”未查天气和完整费用，这个想法不能直接交付。');
    const query = '两大一小 半日出游 天气 预算';
    emit('RAG · 检索请求', '用问题查询本地资料库', `query="${query}" → 本地关键词检索；资料库包含 D01 天气、D02 费用、D03 住宿。`, {capability: 'rag'});
    const documents = outingDocuments.filter(d => d.keywords.some(term => query.includes(term)));
    emit('RAG · 检索结果', '命中 D01 / D02，排除无关 D03', documents.map(d => `[${d.id}] ${d.text}`).join('\n'),
      {capability: 'rag', retrieved_documents: documents});
    emit('RAG · 增强生成', '把命中文档放入回答上下文', '“雨天选室内 [D01]；总预算算门票、交通、餐费 [D02]。”规则有引用，但当天的天气和具体报价仍需工具核实。', {capability: 'rag'});
    const call = (name, args, response, detail) => {
      const call_id = `single-${events.length}`;
      const argumentsText = Object.entries(args).map(([key, value]) => `${key}="${value}"`).join(', ');
      const request = {call_id, name, arguments: args};
      emit('Tool · 调用请求', `${name}(${argumentsText})`, '同一 Agent 提出请求 → 宿主校验参数并执行。本页工具读取合成数据。', {capability: 'tool', request});
      emit('Tool · 工具返回', `${name} 返回`, detail, {capability: 'tool', observation: {call_id, ...response}});
    };
    call('read_weather', {}, {id: 'WX01', weather}, `weather="${weather}" [WX01]：${rainy ? '周六有雨' : '周六晴天'}。`);
    call('read_catalog', {}, {id: 'CAT01', places: outingPlaces}, outingPlaces.map(p => `${p.name} [${p.id}]：${p.indoor ? '室内' : '室外'}`).join('；'));
    for (const p of outingPlaces) {
      const total = outingCost(p);
      call('calculate_cost', {place_id: p.id}, {id: `COST:${p.id}`, place_id: p.id, total}, outingPrice(p));
    }
    emit('LLM · 汇总证据', '引用规则与工具结果，再给建议', `RAG 提供 [D01 / D02] 的规则；Tool 提供 [WX01 / P01 / P02 / P03] 的天气和费用。核对天气与 ${budget} 元预算后形成回答。`);
    finish();
    return events;
  }
  if (architecture === 3) {
    if (keyEvents) {
      const revisedBudget = Math.min(budget, 200);
      emit('目标 Goal', '先计划，执行中接收新要求', `半日出游，初始预算 ${budget} 元。预算变动为离线教学事件。`);
      emit('计划 v1', '规划器安排查询、核算与验收', '查天气 → 查场馆名单 → 核算完整费用 → 选预算内场馆 → 验收。');
      emit('执行查询', '执行器读取天气', `${rainy ? '有雨' : '晴天'} [WX01 / D01]。`, {tool: 'read_weather'});
      emit('执行查询', '执行器读取场馆名单', '三处场馆 [P01 / P02 / P03]。', {tool: 'read_catalog'});
      emit('执行 v1', '执行器给出初步选择', suitable.map(outingPrice).join('\n') + (chosen ? `\n初步选择${chosen.name}，还未交付。` : '\n初始预算下没有可选场馆。'), {proposed_place: chosen?.id || ''});
      emit('用户变更', budget > revisedBudget ? '用户降低预算' : '用户再次确认预算上限', `预算 ${budget} → ${revisedBudget} 元；天气与人数不变。`, {budget_change: {from: budget, to: revisedBudget}});
      emit('验收 v1', '按最新预算检查初步选择', chosen && outingCost(chosen) <= revisedBudget ? '原候选仍在最新预算内，需要重新确认。' : '原候选不能通过最新预算要求，不能按旧计划交付。');
      emit('反思 Reflection', '把新要求交给规划器', `只改预算相关步骤；已有天气、名单和完整价格继续使用，按 ${revisedBudget} 元重新筛选。`);
      emit('计划 v2', '规划器修订剩余步骤', `复用已有资料 → 按 ${revisedBudget} 元筛选 → 再验收 → 建议或无解。`, {active_budget: revisedBudget});
      const revised = suitable.find(p => outingCost(p) <= revisedBudget);
      emit('执行 v2', '执行器按新预算重新筛选', suitable.map(outingPrice).join('\n'), {active_budget: revisedBudget});
      emit('验收 v2', revised ? '外部事实验收通过' : '新预算下没有可行方案', revised ? '天气适配、费用完整，且不超过最新预算。' : '现有天气适配候选都超过最新预算。');
      finish(revised || null, revisedBudget);
      return events;
    }
    emit('目标 Goal', '同一个任务，一条规划与反馈闭环', `半日出游，预算 ${budget} 元。先计划、执行与验收，再决定怎样修订。`);
    emit('计划 v1', 'Planner 写明依赖和验收', '读取天气与场馆名单 → 核算候选费用 → 检查天气、三项费用和预算 → 输出。执行器只能在依赖齐备后交付。');
    emit('执行 v1', 'Executor 读取事实，注入教学错误草稿', `${rainy ? '有雨' : '晴天'} [WX01]；公园是室外 [P01]。错误草稿：“公园门票60 + 交通40 = 100元”。漏餐费80元，错误由教学样本注入。`);
    emit('验收 v1', '首次执行草稿被退回', `[D02] 要求三项费用，公园应为180元。${rainy ? '[D01] 雨天还应排除室外公园。' : budget < 180 ? '完整费用还超过预算。' : '即使在预算内，也必须补齐费用与引用。'}没有通过初次验收。`);
    emit('反思 Reflection', '把失败原因转成修订动作', '保留已读天气与场馆名单，补餐费，再筛天气适配候选并核对完整费用；避免只改措辞。反思记录进入任务上下文，不更新模型权重。');
    emit('计划 v2', 'Planner 修订受影响的步骤', `${rainy ? '排除公园，核算室内场馆' : '保留公园候选，补齐三项费用'} → 按 ${budget} 元预算验收 → 建议或无解出口。`);
    emit('执行 v2', 'Executor 按修订计划重新核算', suitable.map(outingPrice).join('\n'));
    emit('验收 v2', chosen ? '外部事实验收通过' : '修订后仍无可行方案', chosen ? '天气适配、三项费用齐全、预算内且保留引用。' : '反思不能改变客观价格；所有天气适配候选都超预算，停止并请用户调整条件。');
    finish();
    return events;
  }
  if (architecture === 4 && keyEvents) {
    const weatherChoice = suitable[0];
    const cheapest = outingPlaces.reduce((a, b) => outingCost(a) < outingCost(b) ? a : b);
    emit('目标 Goal', '独立判断，主管统一取舍', `半日出游，预算 ${budget} 元；各角色的局部建议为离线教学示例。`);
    emit('分工 Delegation', '主管分配独立职责', '天气 Agent 判断天气和室内外适配；费用 Agent 核算价格并给出最便宜候选。两者都不独自交付最终建议。');
    emit('角色消息', '天气 Agent 的局部建议', `${rainy ? '雨天，排除公园' : '晴天，全部场馆可考虑'}；先建议${weatherChoice.name}。这份判断没有检查预算。`, {actor: 'weather', proposed_place: weatherChoice.id});
    emit('角色消息', '费用 Agent 的局部建议', outingPlaces.map(outingPrice).join('\n') + `\n${cheapest.name}最便宜，先建议它；尚未检查天气。`, {actor: 'cost', proposed_place: cheapest.id});
    emit('汇总 Synthesis', '主管对照两份局部建议', `${rainy ? '公园便宜但雨天不能去；自然馆室内但310元' : '公园天气适合且180元'}，还需对照 ${budget} 元预算。主管结合两份证据，不能只听其中一个角色。`);
    finish();
    return events;
  }
  if (architecture <= 4) {
    const stages = {2: [4], 4: [7]}[architecture];
    for (const stage of stages) {
      const trace = makeOutingTrace(stage, weather, budget);
      events.push(...trace.filter(e => !['目标 Goal', '结果 Result', '停止 Stop', '能力边界 Limit'].includes(e.phase)));
    }
    events.unshift({phase: '目标 Goal', title: `架构 ${architecture} · 同一出游任务`, detail: `两大一小，半日出游，预算 ${budget} 元。离线角色与决策由教学规则模拟。`});
    finish();
    return events;
  }
  emit('目标 Goal', '同一案例，比较控制机制', `两大一小，半日出游，预算 ${budget} 元。以下是浏览器执行的规则示意，不调用模型。`);
  if (architecture === 5) {
    const requests = {outing: '帮我安排周六半日出游', budget: '只核算三个场馆的完整费用', unclear: '帮我看看'};
    const skills = [
      {id: 'outing_plan', matches: text => /出游/.test(text), reference: 'D01：雨天优先室内；D02：三项费用齐全', tools: ['read_weather', 'read_catalog', 'calculate_cost']},
      {id: 'budget_check', matches: text => /费用/.test(text), reference: 'D02：门票 + 交通 + 餐费；只做预算核算', tools: ['read_catalog', 'calculate_cost']}
    ];
    let request = requests[intent] || requests.unclear;
    emit('输入 Input', '用户意图', request);
    if (keyEvents && intent === 'outing') {
      emit('路由 Router', '先选择出游技能', '关键词“出游”命中 outing_plan。', {route: 'outing_plan'});
      emit('加载 Skill', '准备出游技能，尚未执行工具', '准备天气和费用规则 D01 / D02；等待执行。', {skill: 'outing_plan'});
      request = requests.budget;
      emit('输入变更', '用户改成只算费用', request, {intent_change: {from: 'outing', to: 'budget'}});
    }
    const matches = skills.filter(skill => skill.matches(request));
    emit('路由 Router', '识别意图，再选择技能', `规则路由命中：${matches.map(skill => skill.id).join('、') || '无'}。此处用关键词示意，真实语义路由需另行评估。`, {route: matches[0]?.id || 'clarify'});
    if (matches.length !== 1) {
      review();
      emit('澄清 Clarify', '意图不足，先澄清', '请说明要安排出游，还是只核算费用；未加载技能、未执行工具。', {result: {status: 'needs_clarification'}});
      return events;
    }
    const skill = matches[0];
    emit('加载 Skill', `按需加载 ${skill.id}`, `Reference：${skill.reference}\n执行流程与工具：${skill.tools.join(' → ')}。${keyEvents && intent === 'outing' ? '停止原出游流程，当前只执行费用技能。' : '另一技能不加载。'}`, {skill: skill.id});
    if (skill.tools.includes('read_weather')) emit('执行 Execute', '出游技能读取天气', `${rainy ? '有雨' : '晴天'} [WX01]；按 D01 筛选室内外。`, {tool: 'read_weather'});
    emit('执行 Execute', '读取场馆名单', '三处合成场馆 [P01 / P02 / P03]。', {tool: 'read_catalog'});
    emit('执行 Execute', '按技能口径计算完整费用', outingPlaces.map(outingPrice).join('\n'), {tool: 'calculate_cost'});
    if (skill.id === 'budget_check') {
      review();
      emit('结果 Result', '只交付费用核算', outingPlaces.map(p => `${p.name}：${outingCost(p)} 元，${outingCost(p) <= budget ? '预算内' : '超预算'}`).join('；') + '。未查天气，不作出行建议。', {result: {status: 'cost_checked', intent: 'budget', budget}});
    } else finish();
  } else if (architecture === 6) {
    const board = {version: 0, weather: null, catalog: null, costs: null, result: null};
    const snapshot = () => JSON.parse(JSON.stringify(board));
    const publish = (actor, patch, detail) => {
      Object.assign(board, patch);
      board.version++;
      emit('发布 Publish', `${actor} 写入黑板 v${board.version}`, detail, {actor, board: snapshot()});
    };
    emit('初始化 Blackboard', '黑板 v0：记录目标与缺失证据', `budget=${budget}；weather=null；catalog=null；costs=null；result=null。角色仅按就绪条件领取任务。`, {board: snapshot()});
    if (!board.catalog) emit('等待 Wait', '费用角色暂时不能工作', '黑板上还没有场馆名单，不知道要给哪些场馆算钱；费用角色等待，黑板版本不变。', {actor: 'cost', waiting: 'catalog', board: snapshot()});
    const roles = [
      {actor: 'summary', ready: () => board.weather && board.catalog && board.costs,
        work: () => {
          const selection = board.catalog.find(p => (board.weather !== 'rain' || p.indoor) && board.costs[p.id] <= budget);
          publish('summary', {result: selection?.id || 'no_solution'}, '天气、场馆名单、费用都已齐备，汇总角色才可触发。');
        }},
      {actor: 'cost', ready: () => board.catalog && !board.costs,
        work: () => publish('cost', {costs: Object.fromEntries(board.catalog.map(p => [p.id, outingCost(p)]))}, board.catalog.map(outingPrice).join('\n'))},
      {actor: 'weather', ready: () => !board.weather,
        work: () => publish('weather', {weather}, `${rainy ? '雨天' : '晴天'} [WX01 / D01]；费用尚未齐备，汇总角色继续等待。`)},
      {actor: 'catalog', ready: () => !board.catalog,
        work: () => publish('catalog', {catalog: outingPlaces}, '发布场馆 [P01 / P02 / P03] 后，费用角色满足就绪条件。')}
    ];
    const completed = new Set();
    while (!board.result) {
      const role = roles.find(r => !completed.has(r.actor) && r.ready());
      if (!role) {
        emit('停止 Stop', '没有就绪角色', '缺少必要证据，停止并请求补充。', {result: {status: 'missing_evidence'}});
        return events;
      }
      emit('触发 Trigger', `状态变化唤醒 ${role.actor}`, `调度器检查黑板 v${board.version}；按就绪条件触发，不由主管发送任务消息。`, {actor: role.actor});
      role.work();
      completed.add(role.actor);
    }
    finish(board.catalog.find(p => p.id === board.result) || null);
  } else if (architecture === 7) {
    const state = {};
    const nodes = {
      weather: {run: () => {state.weather = weather; return `天气：${weather} [WX01]`;}, next: () => 'catalog'},
      catalog: {run: () => {state.catalog = outingPlaces; return '场馆名单齐备 [P01 / P02 / P03]；读取天气选择分支';}, next: () => state.weather === 'rain' ? 'indoor_filter' : 'all_places'},
      indoor_filter: {run: () => {state.candidates = state.catalog.filter(p => p.indoor); return 'rain 边：只保留室内 [P02 / P03 / D01]';}, next: () => 'cost'},
      all_places: {run: () => {state.candidates = state.catalog; return 'sun 边：保留全部候选 [P01 / P02 / P03]';}, next: () => 'cost'},
      cost: {run: () => {state.affordable = state.candidates.filter(p => outingCost(p) <= budget); return state.candidates.map(outingPrice).join('\n');}, next: () => 'validate'},
      validate: {run: () => state.affordable.length ? '天气、三项费用、预算验收通过' : '所有天气适配候选均超预算', next: () => state.affordable.length ? 'recommend' : 'no_solution'},
      recommend: {run: () => '成功边：输出建议，等待用户确认', next: () => 'END'},
      no_solution: {run: () => '失败边：请求调整条件，有限停止', next: () => 'END'}
    };
    emit('图 Graph', '预先定义节点、边与出口', 'START → weather → catalog → [rain: indoor_filter / sun: all_places] → cost → validate → [recommend / no_solution] → END。');
    let node = 'weather';
    for (let step = 0; node !== 'END' && step < 10; step++) {
      const current = nodes[node];
      const detail = current.run();
      const next = current.next();
      emit('节点 Node', `${node} → ${next}`, detail, {node});
      node = next;
    }
    finish(state.affordable[0] || null);
  }
  return events;
}

// Project the executed trace onto the teaching diagram. The original detail is
// retained in More; short captions describe the component and information flow.
function makeArchitecturePresentation(architecture, weather, budget, intent = 'outing') {
  const trace = makeArchitectureTrace(architecture, weather, budget, intent, true);
  const steps = [];
  const push = (event, nodes, edges, caption, mechanism) => steps.push({
    ...event, nodes, edges, caption, mechanism,
  });
  const resultCaption = event => event.result?.status === 'recommended'
    ? `${weather === 'rain' ? '雨天' : '晴天'}建议去${outingPlaces.find(p => p.id === event.result.place_id).name}：总价 ${event.result.total} 元，在 ${event.result.budget ?? budget} 元预算内。`
    : event.result?.status === 'cost_checked' ? '只交付完整费用：公园 180 元、自然馆 310 元、博物馆 210 元。'
    : event.result?.status === 'needs_clarification' ? '还不知道用户想做什么，先澄清需求，不执行工具。'
    : `没有场馆同时符合天气要求和 ${event.result.budget ?? budget} 元预算，停止查找。`;
  for (const event of trace) {
    const {phase, title} = event;
    if (phase.includes('复盘')) continue;
    if (event.result) {
      const node = architecture === 2 ? 'decision' : architecture === 3 ? 'validate'
        : architecture === 4 ? 'merge' : architecture === 5 ? 'execute' : 'agent';
      const explanation = event.result.status === 'recommended' ? '天气合适、费用算全且没有超预算；这里只给建议，不订票。'
        : event.result.status === 'cost_checked' ? '还没有查天气，因此这份结果不能当作出游建议。'
        : '不能自行提高预算；请用户调整预算或出游条件。';
      if (architecture === 6) push(event, ['board', 'summary'], [], resultCaption(event), '汇总角色把结论写到黑板上，大家可以查看同一份结果。');
      else if (architecture === 7) push(event, ['END'], [], resultCaption(event), event.result.status === 'recommended' ? '按预设流程给出建议后，走到 END，结束本次任务。' : '按预设流程说明没有合适方案，然后走到 END，结束本次任务。');
      else if (event.result.status === 'needs_clarification') push(event, ['router', 'clarify'], ['router-clarify'], resultCaption(event), '先问清要安排出游还是只算费用，再决定使用哪个技能。');
      else push(event, [node, 'output'], [`${node}-output`], resultCaption(event), explanation);
      continue;
    }
    if (phase === '目标 Goal') {
      const target = {1: 'agent', 2: 'decision', 3: 'planner', 4: 'supervisor', 5: 'router'}[architecture];
      if (target) push(event, ['input', target], [`input-${target}`], `先弄清需求：两位成人和一名孩子，半日出游，预算 ${budget} 元。`, '后面的步骤都要遵守人数、天气和预算要求。');
      continue;
    }
    if (architecture === 1) {
      if (phase.startsWith('LLM')) {
        if (phase.includes('生成基础')) push(event, ['agent'], [], 'Agent 先想到“去公园散步”，但还没有查天气和费用。', '先把它当作一个待核实的想法，接下来查规则和实际数据。');
        if (phase.includes('汇总')) push(event, ['agent'], [], '把出游规则、查到的天气和各场馆总价放在一起比较。', '这些资料都交给同一个 Agent，由它选出符合要求的场馆。');
      } else if (phase.includes('检索请求')) push(event, ['agent', 'rag'], ['agent-rag'], '先查出游资料，找出天气和费用方面的要求。', 'Agent 把问题交给文档库，查找与这次出游有关的说明。');
      else if (phase.includes('检索结果')) push(event, ['rag', 'agent'], ['rag-agent'], '查到两条规则：雨天不去户外；费用要包含门票、交通和餐费。', '文档库把相关资料交给 Agent；无关的住宿资料不使用。');
      else if (phase.includes('增强生成')) push(event, ['agent'], [], '现在知道该按什么规则选场馆，但还不知道周六天气和实际费用。', '接下来要用工具查天气和价格，不能只凭资料就给出建议。');
      else if (event.request) {
        const request = event.request;
        const place = outingPlaces.find(p => p.id === request.arguments.place_id);
        const captions = {read_weather: '现在请天气工具查询周六的天气。', read_catalog: '现在请场馆工具列出可选场馆。', calculate_cost: `现在请费用工具核算${place?.name}的总价。`};
        push(event, ['agent', 'tool'], ['agent-tool'], captions[request.name], 'Agent 提出要查什么，程序负责检查参数并实际执行工具。');
      }
      else if (event.observation) {
        const value = event.observation;
        const caption = value.weather ? `天气查到了：周六${weather === 'rain' ? '有雨，不能选户外公园' : '晴天，可以考虑户外公园'}。`
          : value.places ? '场馆名单查到了：公园、自然馆、城市博物馆。'
          : `${outingPlaces.find(p => p.id === value.place_id).name}的总价算好了：${value.total} 元。`;
        push(event, ['tool', 'agent'], ['tool-agent'], caption, value.weather ? weather === 'rain' ? '刚才的公园想法不成立；同一个 Agent 根据查到的事实调整建议。' : '公园想法通过天气检查，但仍要核对完整费用。'
          : value.places ? '工具把名单交给 Agent，接下来逐个场馆核算费用。'
          : '这笔总价包含门票、交通和餐费；工具把结果交给 Agent。');
      }
    } else if (architecture === 2) {
      if (phase.startsWith('判断')) {
        const observed = steps.some(s => s.nodes.includes('observation'));
        const place = title.match(/^检查(.+)的费用$/)?.[1];
        const previous = steps.findLast(s => s.phase.startsWith('观察'));
        const previousCost = previous?.detail.match(/= (\d+) 元/);
        const caption = title === '读取场馆名单' ? '已经拿到天气，下一步读取场馆名单和室内外属性。' : !observed ? '先查周六的天气，才能判断能不能去户外。'
          : previousCost && Number(previousCost[1]) > budget ? `${previous.detail.split(' [')[0]}超预算，改查${place}的费用。`
          : `已经确认天气，接下来先查${place}要多少钱。`;
        push(event, ['decision'], observed ? ['observation-decision'] : [], caption, observed ? 'Agent 根据刚查到的结果决定下一步，工具不是一次全部查完。' : '先决定要查什么，再发出查询请求。');
      } else if (phase.startsWith('行动')) {
        const place = steps.findLast(s => s.phase.startsWith('判断'))?.title.match(/^检查(.+)的费用$/)?.[1];
        push(event, ['decision', 'tool'], ['decision-tool'], title.includes('天气') ? '请天气工具查询周六的天气。' : title.includes('场馆') ? '请场馆工具读取候选名单和室内外属性。' : `请费用工具计算${place}的总价。`, 'Agent 选择这一次要用的工具，程序执行后把结果交回来。');
      }
      else if (phase.startsWith('观察')) {
        const cost = event.detail.match(/= (\d+) 元/);
        const nextCandidate = trace[trace.indexOf(event) + 1]?.phase.startsWith('判断');
        push(event, ['tool', 'observation'], ['tool-observation'], cost ? `${event.detail.split(' [')[0]}要 ${cost[1]} 元，${Number(cost[1]) > budget ? `超过 ${budget} 元预算` : '没有超预算'}。`
          : title.includes('场馆') ? '场馆名单查到了：公园、自然馆、城市博物馆。' : `天气查到了：${weather === 'rain' ? '有雨，只考虑室内场馆' : '晴天，可以考虑公园'}。`, cost && Number(cost[1]) > budget ? nextCandidate ? '这个场馆太贵，Agent 根据价格换一个场馆继续查。' : '适合天气的候选已经查完，都太贵，接下来说明没有合适方案。'
          : cost ? 'Agent 已经拿到价格，可以检查是否符合要求并结束任务。' : '先把查到的天气交给 Agent，再决定去查哪些场馆。');
      } else if (phase.startsWith('检索')) push(event, ['decision'], [], '按天气列出可选场馆，并查看总费用应该包含哪些项目。', weather === 'rain' ? '雨天只看室内场馆；预算要算上门票、交通和餐费。' : '晴天可以保留全部场馆；预算要算上门票、交通和餐费。');
    } else if (architecture === 3) {
      const latestBudget = Math.min(budget, 200);
      const initial = outingPlaces.find(p => p.id === event.proposed_place);
      if (event.budget_change) push(event, ['input', 'planner'], ['input-planner'], budget > latestBudget ? `执行途中，用户把预算从 ${budget} 元降到 ${latestBudget} 元。` : `执行途中，用户再次确认：预算不能超过 ${latestBudget} 元。`, '新要求已经生效；还未交付的方案要按最新预算重新检查。');
      else if (phase.startsWith('计划')) push(event, ['planner'], phase.includes('v2') ? ['reflection-planner'] : [], phase.includes('v2') ? `修改剩余计划：按 ${latestBudget} 元重新选场馆，再验收。` : '规划器先排好步骤：查天气、查场馆、算费用，再验收。', phase.includes('v2') ? '已有天气、名单和完整价格继续使用，省去重复查询。' : '先安排完整步骤，执行器随后按计划做。');
      else if (phase === '执行查询') push(event, ['executor'], [], event.tool === 'read_weather' ? `执行器查到周六${weather === 'rain' ? '有雨，先排除公园' : '晴天，可以考虑公园'}。` : '执行器查到三处场馆，接下来核算完整费用。', '执行器照计划收集事实，供后面的选择与验收使用。');
      else if (phase.startsWith('执行')) push(event, ['planner', 'executor'], ['planner-executor'], phase.includes('v1') ? initial ? `执行器初步选${initial.name}，${outingCost(initial)} 元，在 ${budget} 元预算内。` : `执行器发现：适合当天的场馆都超过 ${budget} 元预算。` : `执行器按 ${latestBudget} 元重新筛选，沿用已经查到的价格。`, phase.includes('v1') ? '这只是第一版计划的执行结果，验收前还不能交付。' : '重做受预算影响的部分，再把结果交给验收步骤。');
      else if (phase.startsWith('验收')) push(event, ['executor', 'validate'], ['executor-validate'], phase.includes('v1') ? `按最新的 ${latestBudget} 元检查初步选择，不能继续用旧预算。` : title.includes('验收通过') ? '重新检查通过：天气合适，费用完整，也符合最新预算。' : '重新检查后仍无合适方案：现有候选都超过最新预算。', phase.includes('v1') ? '把预算变动及检查结果交回规划器，修改尚未完成的步骤。' : '重规划不能改变价格；没有符合要求的方案就停止。');
      else if (phase.startsWith('反思')) push(event, ['validate', 'reflection'], ['validate-reflection'], `明确修改要求：保留已有资料，按 ${latestBudget} 元重新选场馆。`, '这里的反馈来自用户改预算，用它修订剩余计划。');
    } else if (architecture === 4) {
      if (phase.startsWith('分工')) push(event, ['supervisor', 'weather', 'cost'], ['supervisor-weather', 'supervisor-cost'], '主管把任务分成两份：一个 Agent 查天气，另一个 Agent 算费用。', '两位专业 Agent 各做自己的部分，再把结果发回主管。');
      else if (phase === '角色消息') {
        const place = outingPlaces.find(p => p.id === event.proposed_place);
        push(event, [event.actor, 'merge'], [`${event.actor}-merge`], event.actor === 'weather' ? `天气 Agent 建议${place.name}：${weather === 'rain' ? '有雨，室内更合适' : '晴天，可以去公园'}。` : '费用 Agent 建议公园：180 元最便宜。', event.actor === 'weather' ? '它只检查了天气，还没判断价格是否在预算内。' : '它只比较了费用，还没判断这个场馆当天能不能去。');
      }
      else if (phase.startsWith('消息')) {
        const messages = event.detail.split('\n');
        push(event, ['weather', 'merge'], ['weather-merge'], `天气 Agent 告诉主管：${weather === 'rain' ? '周六有雨，公园不能去' : '周六晴天，三处场馆都可以考虑'}。`, '主管先拿到天气判断；还要等费用结果，才能选出最终场馆。');
        steps.at(-1).detail = messages[0];
        push(event, ['cost', 'merge'], ['cost-merge'], '费用 Agent 告诉主管：公园 180 元、自然馆 310 元、博物馆 210 元。', '费用都包含门票、交通和餐费；现在主管拿到了两份结果。');
        steps.at(-1).detail = messages[1];
      } else if (phase.startsWith('汇总')) push(event, ['merge'], [], weather === 'rain' ? `主管发现：公园怕雨，自然馆 310 元；再看博物馆 210 元。` : `主管发现：公园适合晴天、总价 180 元，再核对预算。`, `主管同时检查天气和 ${budget} 元预算，两个局部建议都不能直接当结论。`);
    } else if (architecture === 5) {
      if (event.intent_change) push(event, ['input', 'router'], ['input-router'], '用户改口：“先不安排出游了，只帮我算费用。”', '原出游流程还没执行；Router 要按新需求重新选择技能。');
      else if (phase.startsWith('输入')) push(event, ['input'], [], `用户说：“${event.detail}”。`, '先看用户要做什么，才能决定使用哪一套处理步骤。');
      else if (phase.startsWith('路由')) {
        const skill = event.route;
        push(event, ['router', skill], [`router-${skill}`], skill === 'clarify' ? '“帮我看看”没有说明要做什么，需要先问清楚。' : skill === 'budget_check' ? '用户只想算费用，所以选择“费用技能”。' : '用户想安排出游，所以选择“出游技能”。', 'Router 负责分流；这个示例用“出游”“费用”等关键词判断需求。');
      } else if (event.skill) push(event, [event.skill, 'execute'], [`${event.skill}-execute`], event.skill === 'budget_check' ? '准备费用技能：使用费用规则和算价步骤，不准备天气查询。' : '准备出游技能：使用天气、费用规则和对应的查询步骤。', '一个技能是一套处理方法，包含要用的资料、工具和执行顺序。');
      else if (phase.startsWith('执行')) push(event, ['execute'], [], event.tool === 'read_catalog' ? '费用技能查到三处场馆，接下来给它们算总价。' : '把门票、交通和餐费加起来，得到每处场馆的总价。', '用户现在只要费用，所以不查天气，也不推荐出游地点。');
    } else if (architecture === 6) {
      if (phase.startsWith('初始化')) push(event, ['board'], [], '先建一份大家共用的记录，记下预算和还没查到的资料。', '这份共享记录叫黑板；各角色把查到的结果写在这里。');
      else if (event.waiting) push(event, ['cost', 'board'], [], '费用角色想开始，但黑板上还没有场馆名单，只能等待。', '没有名单就不知道要给谁算钱；等待不会写入费用，也不增加版本。');
      else if (phase.startsWith('触发')) {
        const role = {weather: '天气', catalog: '场馆', cost: '费用', summary: '汇总'}[event.actor];
        const captions = {weather: '黑板上还没有天气，让天气角色开始查询。', catalog: '黑板上还没有场馆名单，让场馆角色开始查询。', cost: '场馆名单已经查到，现在让费用角色开始算钱。', summary: '天气、名单和费用都齐了，现在让汇总角色选方案。'};
        push(event, ['board', event.actor], [`board-${event.actor}`], captions[event.actor], event.actor === 'cost' ? '先有场馆名单，才知道要给哪些场馆算钱。'
          : event.actor === 'summary' ? '汇总需要三类资料；资料没齐时，这个角色要继续等待。'
          : `调度器查看缺什么资料，再让${role}角色做对应的工作。`);
      } else if (event.board) {
        const captions = {weather: `天气角色把“周六${weather === 'rain' ? '有雨' : '晴天'}”记到黑板上。`, catalog: '场馆角色把三处场馆记到黑板上，费用角色可以开始了。', cost: '费用角色把各场馆总价记到黑板上，汇总所需的资料齐了。', summary: '汇总角色根据黑板上的资料选方案，再把结论写回黑板。'};
        push(event, [event.actor, 'board'], [`${event.actor}-board`], captions[event.actor], `共享记录更新到第 ${event.board.version} 版；调度器据此判断哪个角色接下来能工作。`);
      }
    } else if (architecture === 7) {
      if (phase.startsWith('图')) push(event, ['START'], [], '先把处理顺序画好：查天气、查场馆、算费用，再检查并给结果。', '晴天怎么走、雨天怎么走、超预算怎么办，都已在流程里规定。');
      else if (event.node) {
        const next = title.split(' → ')[1];
        const edges = [`${event.node}-${next}`];
        if (event.node === 'weather') edges.unshift('START-weather');
        const captions = {
          weather: `查到周六${weather === 'rain' ? '有雨' : '晴天'}，接下来查询场馆名单。`,
          catalog: weather === 'rain' ? '场馆名单查到了；因为有雨，流程转到“只保留室内”。' : '场馆名单查到了；因为晴天，流程转到“保留全部场馆”。',
          indoor_filter: '排除户外公园，接下来计算两处室内场馆的费用。',
          all_places: '三处场馆都保留，接下来计算它们的费用。',
          cost: '门票、交通和餐费已经算全，接下来检查有没有超过预算。',
          validate: next === 'recommend' ? `有场馆符合天气要求，且总价不超过 ${budget} 元，进入建议步骤。` : `适合当天出游的场馆都超过 ${budget} 元，进入“没有合适方案”步骤。`,
          recommend: '向用户给出符合天气和预算要求的建议，然后结束流程。',
          no_solution: '告诉用户没有符合要求的方案，请用户调整条件，然后结束流程。',
        };
        const explanations = {
          weather: '这里按事先规定的顺序执行：先查天气，再查名单。',
          catalog: '程序根据天气选择流程中的分支，不需要模型临时决定走哪条路。',
          indoor_filter: '雨天走这条预设路线；晴天则走另一条，保留全部场馆。',
          all_places: '晴天走这条预设路线；雨天则走另一条，只保留室内场馆。',
          cost: '费用算好后，按预设顺序进入预算检查步骤。',
          validate: '检查结果决定下一条路线：有合适方案就给建议，否则说明无解。',
          recommend: '给出建议是预先设置的出口之一，接下来走到 END。',
          no_solution: '没有合适方案也是预先设置的出口，不会一直查下去。',
        };
        push(event, [event.node, next], edges, captions[event.node], explanations[event.node]);
      }
    }
  }
  return steps;
}

document.querySelectorAll('.outing-demo').forEach(panel => {
  const next = panel.querySelector('[data-outing-next]');
  const reset = panel.querySelector('[data-outing-reset]');
  const weather = panel.querySelector('[data-outing-weather]');
  const budget = panel.querySelector('[data-outing-budget]');
  const output = panel.querySelector('[data-outing-output]');
  const counter = panel.querySelector('[data-outing-counter]');
  const intent = panel.querySelector('[data-outing-intent]');
  const prev = panel.querySelector('[data-outing-prev]');
  const more = panel.querySelector('.walk-more');
  const architecture = Number(panel.dataset.outingArchitecture);
  const mechanisms = {
    1: '重点看：同一个 Agent 怎样查资料、用工具，再把结果整理成建议。',
    2: '重点看：查到一个结果后，Agent 怎样决定下一步要查什么。',
    3: '重点看：用户途中改预算，规划器如何调整剩余步骤并复用资料。',
    4: '重点看：两个角色各给局部建议，主管如何同时检查天气和费用。',
    5: '重点看：用户改成只算费用后，切换技能，并省去天气查询。',
    6: '重点看：费用角色先等待，名单写入后再被调度器触发。',
    7: '重点看：条件不满足时，沿预设的无解分支走到 END。',
  };
  let events = [];
  let position = -1;
  const render = () => {
    const event = events[position];
    const seen = events.slice(0, position + 1);
    panel.classList.toggle('is-playing', Boolean(event));
    for (const node of panel.querySelectorAll('[data-vis-node]')) {
      const id = node.dataset.visNode;
      node.classList.toggle('is-current', event?.nodes.includes(id) || false);
      node.classList.toggle('is-visited', seen.some(e => e.nodes.includes(id)));
    }
    for (const edge of panel.querySelectorAll('[data-vis-edge]')) {
      const id = edge.dataset.visEdge;
      edge.classList.toggle('is-current', event?.edges.includes(id) || false);
      edge.classList.toggle('is-visited', seen.some(e => e.edges.includes(id)));
    }
    if (architecture === 6) {
      const board = seen.findLast(e => e.board)?.board;
      const node = panel.querySelector('[data-vis-node="board"]');
      node.querySelector('.walk-title').textContent = board ? `共享黑板 v${board.version} + 调度器` : '共享黑板 + 调度器';
      node.querySelector('.walk-subtitle').textContent = board
        ? `天气${board.weather ? '✓' : '—'} / 场馆${board.catalog ? '✓' : '—'} / 费用${board.costs ? '✓' : '—'}` : '字段 · 版本 · 就绪条件';
    }
    output.replaceChildren();
    const title = document.createElement('strong');
    title.textContent = event?.caption || '点击“开始演示”，每一步都会说明谁在做什么，以及接下来做什么。';
    const mechanism = document.createElement('p');
    mechanism.textContent = event?.mechanism || mechanisms[architecture];
    output.append(title, mechanism);
    counter.textContent = event ? `${position + 1} / ${events.length}` : '结构总览';
    next.disabled = Boolean(event) && position === events.length - 1;
    next.textContent = next.disabled ? '演示结束' : event ? '下一步' : '开始演示';
    prev.disabled = position < 0;
    panel.querySelector('[data-outing-detail-title]').textContent = event ? `${event.phase} · ${event.title}` : '结构总览';
    panel.querySelector('[data-outing-detail]').textContent = event?.detail || mechanisms[architecture];
    const history = panel.querySelector('[data-outing-history]');
    history.replaceChildren();
    const raw = makeArchitectureTrace(architecture, weather.value, Number(budget.value), intent?.value || 'outing', true);
    for (const item of raw) {
      const li = document.createElement('li');
      li.textContent = `${item.phase} · ${item.title}\n${item.detail}`;
      history.append(li);
    }
    const changedBudget = seen.find(e => e.budget_change)?.budget_change;
    const changedIntent = seen.some(e => e.intent_change);
    const request = intent ? ` · ${changedIntent ? '只核算费用' : intent.selectedOptions[0].textContent}` : '';
    const budgetLabel = changedBudget && changedBudget.from !== changedBudget.to ? `${changedBudget.from} → ${changedBudget.to}` : budget.value;
    panel.querySelector('[data-outing-scenario]').textContent = `出游案例 · ${weather.value === 'rain' ? '雨天' : '晴天'} · ${budgetLabel} 元预算${request}`;
    const rainy = weather.value === 'rain';
    const summaries = {
      1: rainy ? '关键事件：先想到公园，查到下雨后改建议' : '关键事件：先想到公园，再查事实确认能不能去',
      2: rainy ? '关键事件：自然馆 310 元太贵，改查博物馆 210 元' : '关键事件：查到公园 180 元，再决定继续还是结束',
      3: Number(budget.value) > 200 ? '关键事件：执行途中，用户把预算从 300 元降到 200 元' : '关键事件：执行途中，用户再次确认预算上限',
      4: rainy ? '关键事件：天气角色选自然馆，费用角色选公园' : '关键事件：两个角色分别判断，主管核对两份建议',
      5: intent?.value === 'unclear' ? '关键事件：需求说不清，先澄清再选择技能' : intent?.value === 'budget' ? '关键事件：只算费用，跳过天气查询' : '关键事件：用户从“安排出游”改成“只算费用”',
      6: '关键事件：费用角色先等待，场馆名单写入后才开始',
      7: outingPlaces.some(p => (!rainy || p.indoor) && outingCost(p) <= Number(budget.value)) ? '关键事件：条件符合，沿预设建议分支结束' : '关键事件：现有场馆都不符合，沿预设无解分支结束',
    };
    panel.closest('.slide').querySelector('.walk-lead').textContent = summaries[architecture];
  };
  const clear = () => {
    events = [];
    position = -1;
    render();
  };
  next.onclick = () => {
    if (!events.length) events = makeArchitecturePresentation(architecture, weather.value, Number(budget.value), intent?.value || 'outing');
    if (position >= events.length - 1) return;
    position++;
    render();
  };
  prev.onclick = () => { if (position >= 0) {position--; render();} };
  reset.onclick = clear;
  panel.querySelector('[data-outing-more]').onclick = () => more.showModal();
  panel.querySelector('[data-outing-close]').onclick = () => more.close();
  panel.querySelectorAll('[data-outing-jump]').forEach(button => {
    button.onclick = () => {
      events = makeArchitecturePresentation(architecture, weather.value, Number(budget.value));
      position = events.findIndex(e => e.capability === button.dataset.outingJump) - 1;
      more.close();
      next.onclick();
    };
  });
  if (intent) intent.onchange = clear;
  const changeScenario = () => document.dispatchEvent(new CustomEvent('outing-config', {detail: {weather: weather.value, budget: budget.value}}));
  weather.onchange = changeScenario;
  budget.onchange = changeScenario;
  document.addEventListener('outing-config', event => {
    weather.value = event.detail.weather;
    budget.value = event.detail.budget;
    clear();
  });
  clear();
});

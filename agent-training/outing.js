const outingPlaces = [
  {id: 'P01', name: '湖畔公园', indoor: false, ticket: 60, transport: 40, meal: 80},
  {id: 'P02', name: '自然馆', indoor: true, ticket: 150, transport: 60, meal: 100},
  {id: 'P03', name: '城市博物馆', indoor: true, ticket: 90, transport: 40, meal: 80}
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
  const catalog = () => emit('观察 Observation', '场所工具返回', outingPlaces.map(place => `${place.name} [${place.id}]：${place.indoor ? '室内' : '室外'}`).join('；'));
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

document.querySelectorAll('.outing-demo').forEach(panel => {
  const next = panel.querySelector('[data-outing-next]');
  const reset = panel.querySelector('[data-outing-reset]');
  const weather = panel.querySelector('[data-outing-weather]');
  const budget = panel.querySelector('[data-outing-budget]');
  const output = panel.querySelector('[data-outing-output]');
  const counter = panel.querySelector('[data-outing-counter]');
  let events = [];
  let position = -1;
  const clear = () => {
    events = [];
    position = -1;
    output.replaceChildren();
    output.textContent = '点击“下一步演示”，观察新增能力解决了什么问题。更改天气或预算可重新比较。';
    counter.textContent = '尚未开始';
    next.disabled = false;
    next.textContent = '下一步演示';
  };
  next.onclick = () => {
    if (!events.length) events = makeOutingTrace(Number(panel.dataset.outingStage), weather.value, Number(budget.value));
    if (position >= events.length - 1) return;
    const event = events[++position];
    output.replaceChildren();
    const phase = document.createElement('span');
    phase.className = 'outing-phase';
    phase.textContent = event.phase;
    const title = document.createElement('strong');
    title.textContent = event.title;
    const detail = document.createElement('p');
    detail.textContent = event.detail;
    output.append(phase, title, detail);
    counter.textContent = `${position + 1} / ${events.length}`;
    next.disabled = position === events.length - 1;
    if (next.disabled) next.textContent = '演示结束';
  };
  reset.onclick = clear;
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

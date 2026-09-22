(function () {
  'use strict';
  var N5 = window.N5, U = N5.scriptUtils;
  N5.scenarios.dual = {
    title: '双 Agent · 失败回传与计划修订',
    roles: [U.role('planner', '规划 Agent'), U.role('executor', '执行 Agent'), U.host],
    create: function (options) {
      var input = U.conditions(options), tape = U.outingTape(input, 'planner');
      U.publishPlan(tape, 'planner', 1);
      U.dispatch(tape, 'planner', 'executor', '规划方交付计划 v1', '执行方获得工具权限与计划版本；计划修订权仍属于规划方。', true);
      var failure = U.runV1(tape, 'executor', input);
      if (failure === 'OUTDOOR_IN_RAIN') {
        tape.emit('executor', 'report', '执行方回传失败观察',
          '不擅自改成室内场馆。将天气事实、已选场馆、已核算费用与受阻步骤一起返回规划方。',
          { from: 'executor', to: 'planner', intent: 'replan_request', code: failure, correlation_id: 'outing-01', plan_version: 1, expected_state_version: tape.state.version,
            evidence: { weather: tape.state.weather, venue: tape.state.selected, costs: tape.state.costs }, blocked_step: '确认可行性并输出行程' },
          { status: 'replanning' }, ['executor', 'planner']);
        U.dispatch(tape, 'executor', 'planner', '执行方归还控制权', '由持有全局目标和验收标准的规划方决定如何修订。', true);
        tape.emit('planner', 'reflection', '反思产出可执行修正',
          '场馆类型依赖天气。应先查天气，再过滤场馆类型；费用项已经齐全，无需通过少算费用掩盖失败。',
          { cause: 'WEATHER_DEPENDENCY_AFTER_SELECTION', change: ['将 get_weather 前置', '在选择场馆前按天气过滤类型'], retry_same_plan: false }, {});
        U.publishPlan(tape, 'planner', 2);
        U.dispatch(tape, 'planner', 'executor', '规划方重新交付计划 v2', '版本从 1 升为 2；执行方采用天气前置的新顺序。', true);
        tape.emit('executor', 'report', '确认执行版本 2', '旧计划的候选仅作为失败证据保留；按新计划重新读取事实并计算费用。',
          { from: 'executor', to: 'planner', plan_version: 2, intent: 'ack' }, { status: 'running' });
        U.weatherSearch(tape, 'executor', input);
        U.selectWithinBudget(tape, 'executor', input, true);
        U.report(tape, 'executor', 'planner', '执行方提交修订后结果', { plan_version: 2, venue: tape.state.selected && tape.state.selected.id, total: tape.state.budget_used, feasible: Boolean(tape.state.selected) });
        U.dispatch(tape, 'executor', 'planner', '执行结果回到规划方', '规划方检查任务目标，宿主独立核验费用与天气。', true);
        U.accept(tape, input);
      } else if (failure) {
        tape.emit('executor', 'report', '回报无可行预算方案', '所有候选均超预算；不循环生成实际上无法执行的新计划。',
          { from: 'executor', to: 'planner', code: failure, plan_version: 1 }, {});
        U.accept(tape, input, '预算低于所有可行场馆的完整费用，请人工调整约束。');
      } else {
        U.report(tape, 'executor', 'planner', '计划 v1 本次执行成功', { plan_version: 1, weather: input.weather, venue: tape.state.selected.id, total: tape.state.budget_used },
          '晴天没有触发户外场馆失败；本次不人为制造失败，也不进行无必要的计划修订。');
        U.dispatch(tape, 'executor', 'planner', '正常结果回到规划方', '即使无需修订，结果仍回传规划方，再交由宿主验收。', true);
        U.accept(tape, input);
      }
      return tape.finish();
    }
  };
}());

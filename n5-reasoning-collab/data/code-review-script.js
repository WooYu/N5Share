(function () {
  'use strict';
  var N5 = window.N5, U = N5.scriptUtils;
  var originalDiff = [
    'diff --git a/OrderController.java b/OrderController.java',
    '--- a/OrderController.java', '+++ b/OrderController.java', '@@ -0,0 +1,14 @@',
    '+@GetMapping("/orders")',
    '+public List<OrderVO> list(@RequestParam BigDecimal minAmount,',
    '+                         @RequestParam BigDecimal maxAmount,',
    '+                         @RequestParam String userId) {',
    '+    log.info("query orders userId={} min={} max={}",',
    '+             userId, minAmount, maxAmount);',
    '+    List<Order> orders = orderMapper.selectByAmountRange(minAmount, maxAmount);',
    '+    List<OrderVO> result = new ArrayList<>();',
    '+    for (Order o : orders) {',
    '+        User u = userMapper.selectById(o.getUserId());',
    '+        result.add(OrderVO.of(o, u));',
    '+    }', '+    return result;', '+}'
  ].join('\n');
  var revisedDiff = [
    '// 教学示意：省略 DTO、异常映射与持久队列实现，未编译或执行测试。',
    'record AmountRange(BigDecimal min, BigDecimal max) {',
    '  AmountRange {',
    '    if (min == null || max == null || min.signum() < 0 || max.signum() < 0',
    '        || min.compareTo(max) > 0) throw new IllegalArgumentException("Invalid range");',
    '  }', '}',
    '@GetMapping("/orders")',
    'public Slice<OrderVO> list(@AuthenticationPrincipal AppPrincipal principal,',
    '    @RequestParam BigDecimal minAmount, @RequestParam BigDecimal maxAmount,',
    '    @RequestParam(defaultValue = "0") int page,',
    '    @RequestParam(defaultValue = "20") int size) {',
    '  return orderQueryService.list(principal.requireUserId(),',
    '      new AmountRange(minAmount, maxAmount), PageSpec.checked(page, size, 100));',
    '}',
    '// service: userId 来自受信任登录态，权限与输入校验失败立即拒绝。',
    'public Slice<OrderVO> list(String userId, AmountRange range, PageSpec page) {',
    '  authorization.requireOrderRead(userId);',
    '  // 确认已持久接收再返回；异步发送失败由持久本地队列重试。',
    '  // 若主队列与本地持久兜底均不可用，拒绝敏感数据访问并告警。',
    '  audit.acceptDurably(AuditEvent.orderSearch(userId, range, clock.instant()));',
    '  return orderMapper.selectOwnedAmountSlice(userId, range.min(), range.max(), page);',
    '}',
    '// 批量关联代替循环 N+1；按用户及金额范围过滤并限制返回条数。',
    'SELECT o.id, o.amount, u.display_name',
    'FROM orders o JOIN users u ON u.id = o.user_id',
    'WHERE o.user_id = :userId AND o.amount BETWEEN :min AND :max',
    'ORDER BY o.amount, o.id LIMIT :pageSizePlusOne OFFSET :offset;',
    'CREATE INDEX idx_orders_user_amount_id ON orders(user_id, amount, id);',
    '// 大页偏移与索引收益需 EXPLAIN / 压测验证，可继续评估游标分页。'
  ].join('\n');
  var permissions = {
    synthetic: true,
    endpoint: 'GET /orders', authentication: '登录必需', ownership_filter_in_current_query: false,
    user_id_origin: '当前代码来自请求参数，且没有进入查询条件',
    general_log_policy: '普通应用日志不得直接输出用户标识和金额范围。',
    audit_policy: '课程业务规则：敏感订单金额访问必须有可追踪审计。审计存储须限制权限、保护字段并设置保留期限。',
    security_reviewer: ['依赖清单', '权限配置', '日志规范'],
    performance_reviewer: ['调用链', '建表语句', '索引信息'],
    readability_reviewer: ['lint 配置', '编码规范'],
    test_reviewer: ['覆盖率报告', '用例清单'],
    supervisor: ['所有审查报告', '业务事实登记表'],
    executor: ['修订建议', '代码示意稿']
  };
  var schema = {
    synthetic: true,
    ddl: 'CREATE TABLE orders (id BIGINT PRIMARY KEY, user_id VARCHAR(64), amount DECIMAL(12,2));',
    existing_indexes: ['PRIMARY KEY (id)'],
    amount_index: false,
    call_chain: ['OrderController.list', 'orderMapper.selectByAmountRange', 'for each order: userMapper.selectById'],
    latency_measurement: null, allocation_measurement: null,
    query_count_formula: '1 + N（从示意代码静态推导；不是实测跟踪）'
  };
  var testCases = [
    { id: 'T01', case: '登录用户 A 不能通过参数查询用户 B 的订单', dimension: '安全', expected: '所有 SQL 强制当前用户过滤' },
    { id: 'T02', case: '未登录请求', dimension: '安全', expected: '拒绝访问，不返回订单' },
    { id: 'T03', case: 'min > max、负数、缺失金额参数', dimension: '边界', expected: '明确的 4xx 校验错误' },
    { id: 'T04', case: 'min = max 与空结果', dimension: '边界', expected: '正确包含相等边界，返回合法空页' },
    { id: 'T05', case: 'page < 0、size = 0、size > 100', dimension: '分页', expected: '校验拒绝；不允许无界返回' },
    { id: 'T06', case: '同页多条订单', dimension: '性能', expected: '查询次数不随页内订单数线性增长，EXPLAIN 验证索引' },
    { id: 'T07', case: '审计主通道不可用', dimension: '可靠性', expected: '写入持久本地兜底队列；重启后可重放，幂等去重' },
    { id: 'T08', case: '主通道与兜底持久化同时失败', dimension: '可靠性', expected: '敏感数据访问失败关闭并告警；不悄悄丢弃审计' },
    { id: 'T09', case: '普通日志与受限审计存储', dimension: '隐私', expected: '普通日志无原始用户/金额；审计字段有权限与保留策略' }
  ];
  var businessFacts = {
    source: '课程内置业务事实登记表，非真实合规证明',
    sensitive_order_amounts: true, audit_required: true,
    endpoint: '高频订单列表接口（无实测 QPS 与延迟数字）',
    durability_required_before_response: true,
    audit_failure_policy: '所有持久通道失效时拒绝访问并告警',
    tests_executed: false
  };
  N5.reviewData = U.freeze({
    originalDiff: originalDiff, revisedDiff: revisedDiff, permissions: permissions, schema: schema,
    testCases: testCases, businessFacts: businessFacts,
    coverage: { synthetic: true, scope: '新增金额区间查询分支', covered_cases: [], note: '课程预置的覆盖缺口，不是运行测试产生的报告' },
    lint: { synthetic: true, rules: ['控制器只做 HTTP 适配', '金额区间规则集中表达', '查询与组装职责分离'] },
    dependencies: { synthetic: true, frameworks: ['Java', 'Spring MVC', 'MyBatis'], vulnerability_scan_performed: false }
  });
  var reviewers = ['security_reviewer', 'performance_reviewer', 'readability_reviewer', 'test_reviewer'];
  var labels = { security_reviewer: '安全审查', performance_reviewer: '性能审查', readability_reviewer: '可读性审查', test_reviewer: '测试审查' };
  function readArtifact(tape, actor, name, data, patch) {
    var id = 'review-tool-' + (tape.state.tool_calls + 1);
    tape.emit(actor, 'action', '请求资料 · ' + name, '工具权限限定当前角色能读取的资料。',
      { tool: 'read_review_fixture', args: { artifact: name }, request_id: id }, { pending_tool: { request_id: id, artifact: name } });
    var update = { pending_tool: null, tool_calls: tape.state.tool_calls + 1 };
    Object.keys(patch || {}).forEach(function (key) { update[key] = patch[key]; });
    tape.emit('host', 'observation', '宿主返回合成资料 · ' + name, '资料随课程内置；既不是线上系统事实，也不是实际运行的测试报告。',
      { source: 'synthetic_tool', tool: 'read_review_fixture', request_id: id, result: data }, update, [actor, 'host']);
  }
  function addFindings(tape, actor, title, entries) {
    var tasks = U.clone(tape.state.parallel_tasks);
    tasks[actor] = 'reported';
    var reports = U.clone(tape.state.reports);
    reports[actor] = { stage: 1, finding_ids: entries.map(function (f) { return f.id; }) };
    tape.emit(actor, 'finding', title, entries.map(function (f) { return f.summary; }).join('；'),
      { findings: entries, to: 'supervisor', context_isolated: true },
      { findings: tape.state.findings.concat(entries), parallel_tasks: tasks, reports: reports });
  }
  function resolve(tape, conflictId, decision) {
    return tape.state.conflicts.map(function (conflict) {
      return conflict.id === conflictId ? Object.assign({}, conflict, { status: 'resolved', decision: decision }) : conflict;
    });
  }
  N5.scenarios.review = {
    title: '代码检视 · 并行审查、仲裁与复审',
    roles: [U.role('supervisor', '审查主管'), U.role('security_reviewer', '安全审查'), U.role('performance_reviewer', '性能审查'), U.role('readability_reviewer', '可读性审查'), U.role('test_reviewer', '测试审查'), U.role('executor', '修订角色'), U.host],
    create: function () {
      var tape = new U.Tape({
        version: 0, control: 'supervisor', status: 'running', source: '预设教学剧本',
        diff_version: 1, code_diff: originalDiff, findings: [], conflicts: [], decisions: [],
        business_facts: {}, parallel_tasks: {}, reports: {}, review_results: {},
        permissions: permissions, test_plan: [], tests_executed: false,
        pending_tool: null, tool_calls: 0, error: null
      });
      tape.emit('supervisor', 'plan', '检视目标与边界',
        '四名审查员各有独立上下文、资料权限和责任。所有资料为合成示例，修订代码与复审结论是预写教学剧本。',
        { flow: ['并行审查', '汇总', '冲突检测', '仲裁', '修订', '复审'], tests_executed: false }, {});
      var tasks = {};
      reviewers.forEach(function (id) { tasks[id] = 'running'; });
      tape.emit('supervisor', 'dispatch', 'Fan-out · 同时派发四项审查',
        '四项任务的依赖相互独立，逻辑上并行启动。离线播放器按顺序展示预写的回报事件，不代表真实模型并行运行。',
        { from: 'supervisor', to: reviewers, intent: 'fan_out', correlation_id: 'review-01', expected_state_version: tape.state.version, permission_scopes: permissions },
        { parallel_tasks: tasks }, reviewers);
      readArtifact(tape, 'security_reviewer', '权限配置 / 日志规范 / 依赖清单', { permissions: permissions, dependencies: N5.reviewData.dependencies });
      addFindings(tape, 'security_reviewer', '安全发现 · 归属校验与审计缺失', [
        { id: 'F-AUTHZ', severity: 'high', location: 'OrderController:4,7', summary: '请求 userId 不可信且根本未参与查询；查询缺少当前登录用户约束，可能返回他人订单' },
        { id: 'F-LOG', severity: 'high', location: 'OrderController:5-6', summary: '普通日志直接记录 userId 和金额区间，违反课程隐私规范' },
        { id: 'F-AUDIT', severity: 'high', location: 'OrderController:7', summary: '敏感金额访问缺少受限审计，建议在访问前保证审计可靠接收' }
      ]);
      readArtifact(tape, 'performance_reviewer', '调用链 / DDL / 索引', schema);
      addFindings(tape, 'performance_reviewer', '性能发现 · N+1 与无界查询', [
        { id: 'F-NPLUS1', severity: 'high', location: 'OrderController:9-10', summary: '循环逐条查询用户，静态结构为 1 + N 次数据库查询' },
        { id: 'F-INDEX', severity: 'medium', location: 'orders DDL', summary: '当前仅有主键索引；需结合用户归属与金额谓词评估复合索引' },
        { id: 'F-PAGE', severity: 'high', location: 'OrderController:7', summary: '没有分页上限，返回规模不受控' },
        { id: 'F-SYNC-AUDIT', severity: 'medium', location: '审计方案', summary: '如果同步写远程审计存储，可能增加高频接口等待；需保留可靠性同时控制主链路开销' }
      ]);
      readArtifact(tape, 'readability_reviewer', 'lint / 编码规范', N5.reviewData.lint);
      addFindings(tape, 'readability_reviewer', '可读性发现 · 职责与区间表达', [
        { id: 'F-RESPONSIBILITY', severity: 'medium', location: 'OrderController:1-14', summary: '控制器混合身份处理、查询与结果组装，应分离职责' },
        { id: 'F-RANGE', severity: 'medium', location: 'OrderController:2-3', summary: '用 AmountRange 表达区间并集中处理空值、负数和 min > max 校验' }
      ]);
      readArtifact(tape, 'test_reviewer', '覆盖缺口 / 用例清单', { coverage: N5.reviewData.coverage, proposed_cases: testCases });
      addFindings(tape, 'test_reviewer', '测试发现 · 新分支与边界缺口', [
        { id: 'F-TEST', severity: 'high', location: '新增查询分支', summary: '教学资料标注新增查询分支没有用例；应补越权、参数边界、空结果、分页及审计故障用例' }
      ]);
      tape.emit('supervisor', 'report', 'Fan-in · 等待并收齐四份报告',
        '只有全部审查角色回报，主管才进入冲突检测。共享发现列表以 ID 去重追加，各角色保留证据和责任；宿主按版本串行合并。',
        { intent: 'fan_in', from: reviewers, received: 4, merge_policy: 'append_by_finding_id; reject_stale_version' },
        { control: 'supervisor', test_plan: testCases });
      tape.emit('supervisor', 'conflict', '真冲突 · 必须审计，但同步写入影响响应',
        '安全审查要求敏感数据访问可追踪；性能审查反对在高频路径同步等待远程审计落库。这两项都有业务影响，需要查事实后综合裁决。',
        { id: 'C-AUDIT', references: ['F-AUDIT', 'F-SYNC-AUDIT'], participants: ['security_reviewer', 'performance_reviewer'] },
        { conflicts: [{ id: 'C-AUDIT', type: 'genuine', status: 'open', references: ['F-AUDIT', 'F-SYNC-AUDIT'] }] },
        ['supervisor', 'security_reviewer', 'performance_reviewer']);
      readArtifact(tape, 'supervisor', '业务事实登记表', businessFacts, { business_facts: businessFacts });
      var auditDecision = {
        audit: 'async_durable_fallback', preserve: '访问主体、时间、金额范围与关联 ID 进入受限审计存储',
        path: '先确认可靠接收，再异步写远程审计库；主通道异常写持久本地兜底队列',
        fallback: '有容量限制、失败告警、重试、重启恢复与幂等键；不是内存队列',
        total_failure: '全部持久接收路径失败时拒绝敏感查询并告警',
        performance: '确认持久接收仍有成本，必须测量延迟；这里不承诺零开销'
      };
      tape.emit('supervisor', 'arbitration', '裁决 · 保留审计，异步写入并提供持久兜底',
        '依据共享业务事实：订单金额敏感，且本案例要求访问审计。保留审计义务，将远程落库异步化，可靠本地队列兜底；普通日志不输出原始敏感字段。',
        { conflict_id: 'C-AUDIT', evidence: ['sensitive_order_amounts', 'audit_required', 'durability_required_before_response'], decision: auditDecision },
        { conflicts: resolve(tape, 'C-AUDIT', 'async_durable_fallback'), decisions: tape.state.decisions.concat([{ conflict: 'C-AUDIT', decision: auditDecision }]) },
        ['supervisor', 'security_reviewer', 'performance_reviewer']);
      tape.emit('performance_reviewer', 'conflict', '新增顾虑 · AmountRange 会多创建一个对象',
        '性能审查读到可读性建议后提出对象分配顾虑。这是审查结果之间发生的通信，而不是四份报告简单拼接。当前资料没有分配成本测量。',
        { id: 'C-RANGE', references: ['F-RANGE'], based_on_shared_state: true, measurement: null },
        { conflicts: tape.state.conflicts.concat([{ id: 'C-RANGE', type: 'unsubstantiated', status: 'open', references: ['F-RANGE'] }]) },
        ['performance_reviewer', 'readability_reviewer']);
      tape.emit('supervisor', 'arbitration', '裁决 · 驳回未经测量的对象开销异议',
        '证据支持优先修复 N+1、无分页与查询索引问题，但没有证据说明 AmountRange 是瓶颈。保留值对象集中校验；若压测证明分配热点再优化。不能用纳秒与毫秒单位直接推出固定性能倍数。',
        { conflict_id: 'C-RANGE', decision: 'reject_unmeasured_objection', evidence: ['F-NPLUS1', 'F-PAGE', 'F-INDEX'], allocation_benchmark: null, latency_benchmark: null },
        { conflicts: resolve(tape, 'C-RANGE', 'reject_unmeasured_objection'), decisions: tape.state.decisions.concat([{ conflict: 'C-RANGE', decision: 'reject_unmeasured_objection' }]) },
        ['supervisor', 'performance_reviewer', 'readability_reviewer']);
      tape.emit('supervisor', 'dispatch', '退回修订 · 传递统一方案与验收清单',
        '修订角色收到冲突已解决的清单：可信身份、归属过滤、范围校验、分页、批量关联、索引候选、可靠异步审计与边界用例。',
        { from: 'supervisor', to: 'executor', intent: 'revise', expected_state_version: tape.state.version, correlation_id: 'review-01' },
        { control: 'executor' }, ['supervisor', 'executor']);
      tape.emit('executor', 'revision', '提交修订示意稿 v2',
        '新版示意代码反映已裁决的方案。持久队列与授权组件需要真实项目实现；索引需要真实数据上的执行计划验证；代码没有编译和测试。',
        { diff_version: 2, illustrative: true, tests_executed: false, code: revisedDiff, test_plan: testCases },
        { diff_version: 2, code_diff: revisedDiff, test_plan: testCases, tests_executed: false }, ['executor']);
      var nextTasks = {};
      reviewers.forEach(function (id) { nextTasks[id] = 're_reviewing'; });
      tape.emit('supervisor', 'dispatch', '重新并行审查 · 共享修订与裁决',
        '所有审查员能读取修订版本与已合并的安全校验。性能审查因此重新判断热路径，而不是沿用不知道安全改动时的旧结论。',
        { from: 'supervisor', to: reviewers, intent: 'fan_out_re_review', diff_version: 2, expected_state_version: tape.state.version },
        { control: 'supervisor', parallel_tasks: nextTasks }, reviewers);
      var summaries = {
        security_reviewer: '教学复审：身份来自登录态，查询有用户归属过滤，普通日志不泄露敏感字段，审计保留且要求持久接收；生产实现仍须验证。',
        performance_reviewer: '教学复审：读到了共享的归属与范围校验；N+1 被批量关联替代，分页有上限，复合索引需 EXPLAIN。接受可靠异步审计；无实测延迟结论。',
        readability_reviewer: '教学复审：控制器委托服务，AmountRange 集中表达区间规则，职责更清楚。',
        test_reviewer: '教学复审：用例计划覆盖越权、负数、反向区间、空结果、分页及审计故障；这些只是待执行用例，不代表测试已通过。'
      };
      reviewers.forEach(function (actor) {
        var reviewResults = U.clone(tape.state.review_results);
        reviewResults[actor] = { result: 'scripted_design_acceptance', diff_version: 2, tests_executed: false };
        var completedTasks = U.clone(tape.state.parallel_tasks);
        completedTasks[actor] = 'reviewed';
        tape.emit(actor, 'review', labels[actor] + ' · v2 剧本复审', summaries[actor],
          { scripted: true, tests_executed: false, diff_version: 2, result: 'design_accepted_in_script' },
          { review_results: reviewResults, parallel_tasks: completedTasks });
      });
      tape.emit('host', 'done', '教学流程完成 · 四项设计复审已回报',
        '已演示并行、汇总、两类仲裁、修订与重新审查。完成的是离线教学流程；示意代码尚未编译或测试，不是生产发布批准。',
        { status: 'completed', scope: 'offline_teaching_workflow', tests_executed: false, acceptance: { all_reviewers_returned: true, conflicts_resolved: true, revised_version: 2 } },
        { status: 'completed', control: 'host', tests_executed: false });
      return tape.finish();
    }
  };
}());

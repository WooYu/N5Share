(function () {
  'use strict';
  const {callout, table, code, notes, slide} = N5.content;
  const handout = () => '<button type="button" data-handout="frameworks">打开完整用法手册</button>';
  const compactCode = source => code(source).replace('<pre class="code">', '<pre class="code" style="font-size:18px;line-height:1.45;margin:0;padding:18px 20px">');
  const compactTable = (heads, rows) => table(heads, rows)
    .replace('class="table"', 'class="table" style="font-size:20px;line-height:1.35;margin:12px 0"')
    .replace(/<td>/g, '<td style="padding:8px 12px">')
    .replace(/<th scope="col">/g, '<th scope="col" style="padding:8px 12px">');
  const example = (source, explanation) => '<div class="grid" style="grid-template-columns:1.3fr 1fr;align-items:start;margin:14px 0">' +
    compactCode(source) + '<article class="card" style="padding:20px 22px;font-size:21px;line-height:1.55">' + explanation + '</article></div>';
  const exampleFooter = () => '<p class="small" style="margin:12px 0"><span class="tag">关键节选 · 非完整程序</span><span class="tag">教学回放 · 非模型评测</span>' + handout() + '</p>';
  const graphCode = [
    'g = StateGraph(ReleaseState)',
    'for name, fn in [("collect", collect_findings),',
    '        ("block", mark_block), ("allow", mark_allow),',
    '        ("missing", mark_missing)]:',
    '    g.add_node(name, fn)',
    'g.add_edge(START, "collect")',
    'g.add_conditional_edges("collect", release_route, {',
    '    "BLOCK": "block", "NEEDS_EVIDENCE": "missing",',
    '    "READY_FOR_MANUAL_REVIEW": "allow"})',
    'for n in ("block", "allow", "missing"): g.add_edge(n, END)',
    'for u in g.compile().stream({"source": release_input},',
    '        stream_mode="updates"): show(u)'
  ].join('\n');
  const autogenCode = [
    'async def inspect() -> str:  # make_agent 内的闭包',
    '    return json.dumps(read_evidence(role, source))',
    'agent = AssistantAgent(role, model_client=replay,',
    '    tools=[inspect], reflect_on_tool_use=False)',
    '# make_agent 返回 agent 和 replay；完整实现见手册',
    'pairs = [make_agent(r, release_input) for r in ROLES]',
    'team = RoundRobinGroupChat([p[0] for p in pairs],',
    '    termination_condition=MaxMessageTermination(4))',
    'result = await team.run(task=json.dumps(release_input))',
    'for message in result.messages:',
    '    print(type(message).__name__, message.source)',
    '# 读取三份工具报告后，由 evaluate 独立验收'
  ].join('\n');
  const metagptCode = [
    'class CheckRelease(Action):',
    '    async def run(self, source):',
    '        return json.dumps({"source": source, "reports": collect_reports(source)})',
    'class ReleaseReviewer(Role):',
    '    def __init__(self, **kwargs):',
    '        super().__init__(**kwargs)',
    '        self.set_actions([CheckRelease])',
    '        self._watch([UserRequirement])',
    'team = Team()',
    'team.hire([ReleaseReviewer(), ReportWriter(target=release_input)])',
    'team.run_project(json.dumps(release_input))',
    'await team.run(n_round=3)'
  ].join('\n');

  N5.chapters.push({id: 5, title: '框架概览与选型', slides: [
    slide('P32', '同一份发布检查，分别用三个框架接起来', 120,
      '<p class="lead" style="font-size:25px;margin-bottom:15px!important">输入发布资料，检查兼容性、迁移风险与测试证据；只输出建议，不执行部署。</p>' +
      table(['共同输入：release-b','需要发现的事实'], [
        ['接口 diff：移除 totalAmount 字段','线上客户端仍读取该字段，存在兼容性阻断项'],
        ['数据库迁移：直接删除旧列','缺少兼容迁移方案，不能据此放行'],
        ['CI：passed，但报告属于 release-a','测试通过不代表待发布的 release-b 已验证']
      ]) +
      compactCode('预期结果：{ status: "COMPLETED", decision: "BLOCK" }\n证据：接口契约冲突 / 迁移方案不完整 / CI 提交版本不匹配') +
      '<p class="small" style="margin-top:16px">对照四件事：输入在哪传、工具在哪注册、如何启动、输出怎样接入应用。' + handout() + '</p>',
      notes('先读懂共同输入，后面三个框架才有可比较的对象。release-b 是待发布提交，CI 的绿色报告却属于 release-a，版本匹配应由普通程序明确检查。移除客户端仍在读取的字段、删除旧列缺少迁移方案，则要求证据定位与风险解释。发布建议是 BLOCK，任务状态仍可以是 COMPLETED：检查工作完成不等于发布被批准。三层地图仍成立：任务需要哪些判断、怎样分工、用什么实现；本章把第三层落实到调用入口和输出。共同资料为合成案例，默认示例用教学回放确认框架接线，不能据此评价真实模型的风险识别能力。',
        '看到 COMPLETED 会把发布按钮变绿吗？还必须检查独立的 decision 和证据是否对应同一提交。',
        '圈出 release-b、release-a 与 totalAmount，让学员先写一个阻断原因。打开手册时定位共同输入和最终输出定义。',
        '先把检查过程表达为能看见分支和状态更新的图。'), {coreSeconds:60}),

    slide('P33', 'LangGraph：写出节点、分支，再读状态更新', 180,
      example(graphCode,
        '<h3 style="font-size:24px">实测轨迹（无模型）</h3><p><code>START → collect → block → END</code></p>' +
        '<p class="small">collect 写 reports；release_route 按宿主规则选边；stream 输出节点更新，最终 decision=BLOCK。</p>' +
        '<h3 style="font-size:24px">适用与代价</h3><p class="small">适合分支、回路需要明确追踪的任务。State 类型、工具函数、验收条件与并行合并规则仍由你实现。</p>') +
      '<p class="small" style="margin:12px 0">LangGraph 1.2.12：三类样例回放通过，模型效果未测。持久恢复还需 checkpointer、thread_id 与副作用幂等。</p>' +
      exampleFooter(),
      notes('从入口讲起：release_input 是共同资料，ReleaseState 声明 source、reports、result；collect_findings 调用 collect_reports 读取事实并产出报告；release_route 用宿主 evaluate 规则选边，不让模型用一句“可以发布”直接决定终态。add_conditional_edges 明确三条分支：有阻断项进入 block，单纯缺证据进入 missing，证据齐备且无阻断项进入 allow。allow 分支输出 READY_FOR_MANUAL_REVIEW，仍不自动部署。stream_mode=updates 能观察每个节点返回的状态更新，不能理解成工具内部的全部日志。完整导入与辅助函数在手册中。默认教学回放确认接线，真实模型仍需证据校验。当前 compile() 没配置检查点，不能据此声称已有持久恢复。API 官方核对日期为 2026-09-23，实际执行证据以手册记录为准。',
        '如果模型遗漏 CI 的提交版本，哪个普通代码规则必须仍然阻断？release_route 或它调用的验收函数应检查证据的 commit。',
        '按入口、节点、条件边、输出四处读代码。指出 collect_findings 是业务函数，StateGraph 与 stream 是框架 API；默认回放不能证明模型发现问题的能力。',
        '下一种实现把审查角色组织为有顺序的消息团队。'), {coreSeconds:120}),

    slide('P34', 'AutoGen：注册角色工具，消费团队事件', 180,
      example(autogenCode,
        '<h3 style="font-size:24px">实测轨迹（无模型）</h3><p><code>compat → db → tests</code></p>' +
        '<p class="small">0.7.5 已回放三类样例。固定轮转，消息标明来源；宿主汇总工具证据，再计算发布建议。</p>' +
        '<h3 style="font-size:24px">适用与代价</h3><p class="small">适合角色消息与工具委派需求。RoundRobin 不额外调用模型选发言者；角色调用、等待和上下文仍有成本。</p>') +
      '<p class="small" style="margin:12px 0">stop_reason 不是发布结论。2026-09-23 官方仓库确认 AutoGen 维护模式；新项目评估 Microsoft Agent Framework。</p>' +
      exampleFooter(),
      notes('本页使用 AgentChat API。前四行是 make_agent 内部节选：inspect 闭包绑定 role 与 source，read_evidence 是业务工具；make_agent 返回 Agent 和回放客户端。replay 是 ReplayChatCompletionClient，按预置 FunctionCall 请求 inspect，并非真实模型。reflect_on_tool_use=False 使工具结果直接形成工具摘要，避免再添加一轮反思。RoundRobinGroupChat 固定顺序推进 compat、db、tests。默认停止条件计入用户任务与三个角色最终消息，共四条；工具事件默认不计入。run 返回的 messages 需要筛出三份 ToolCallSummaryMessage，再由 evaluate 检查完整性与版本，不能拿停止理由当发布许可。需要实时事件时可使用官方 run_stream API，完整示例此处采用 run。AutoGen 官方仓库已核对维护状态，新项目建议评估 Microsoft Agent Framework。模型接入步骤见手册，回放跑通不代表真实模型质量提升。',
        '因 MaxMessageTermination 停止时能把 decision 自动设为 READY_FOR_MANUAL_REVIEW 吗？不能，还需宿主核验发现和证据。',
        '指出 tools、固定轮转顺序与 result.messages 三处。将 tests 消息映射为 actor、kind、payload；make_agent 的完整闭包、回放客户端与报告筛选逻辑都在手册中。',
        '第三种实现把注意力放在动作产物如何触发下一角色。'), {coreSeconds:120}),

    slide('P35', 'MetaGPT：让动作产物触发下一角色', 120,
      example(metagptCode,
        '<h3 style="font-size:24px">预期轨迹（未运行）</h3><p><code>CheckRelease → Message → PublishReport</code></p>' +
        '<p class="small">审查动作产出内容；带 cause_by 的消息触发 ReportWriter，形成绑定版本的发布报告。</p>' +
        '<h3 style="font-size:24px">适用与代价</h3><p class="small">适合有明确 SOP 和产物交接的流程。角色与动作要自己写；多一份文档不等于少一个缺陷。</p>') +
      '<p class="small" style="margin:12px 0">README：Python ≥3.9 且 &lt;3.12。本机 3.13 不兼容，已核对 API、未实跑。ReportWriter / PublishReport 与导入见手册。</p>' +
      exampleFooter(),
      notes('CheckRelease.run 调用 collect_reports，生成含 source 和 reports 的 JSON 产物，不调用模型。ReleaseReviewer.set_actions 注册动作，_watch 声明关注 UserRequirement；Team.hire 招募两个角色，run_project 注入任务，run 启动轮次。页面省略的 _act 非可有可无：完整实现解析消息、调用当前动作，并返回 cause_by=type(self.rc.todo) 的 Message。ReportWriter 关注 CheckRelease，调用 PublishReport，后者用 evaluate 独立验收。文字报告不会自然保证可发布，产物必须引用同一提交的证据。官方 API 与 README 范围已核对，本机 Python 3.13 不满足该范围，因此示例未实跑；不以语法片段或文档核对代替运行证据。',
        'release-b 改了迁移脚本，却沿用 release-a 的评审报告，SOP 形式再完整也能放行吗？不能，旧产物需要失效并重新审查。',
        '指出 Action、Role、Team 各自连接点。提示页面省略了完整报告角色、导入和配置，只有手册中的完整程序才用于后续环境验证。',
        '无论内部采用哪种框架，应用侧都需要稳定的任务协议。'), {coreSeconds:60}),

    slide('P36', '接到 Java、Android 和前端：先稳定任务协议', 180,
      '<p class="small"><strong>教学接口设计</strong> · /api/release-checks 尚未在课件服务实现；不是出游演示的现有接口。</p>' +
      callout('Android / 前端 → Java 服务（鉴权、任务 DTO）→ 编排服务 → 框架与工具').replace('class="callout"', 'class="callout" style="font-size:21px;line-height:1.4;padding:12px 18px;margin:12px 0"') +
      compactTable(['接口','客户端可据此做什么'], [
        ['<code>POST /api/release-checks</code>','提交 headSha 与资料，202 返回 runId，初始状态 RUNNING'],
        ['<code>GET /api/release-checks/{id}</code>','轮询 status / findings / decision；需要增量推送时再扩展 SSE'],
        ['<code>POST /api/release-checks/{id}/cancel</code>','请求取消，显示“取消中”；服务端确认 CANCELLED 后才结束']
      ]) +
      compactCode('{ "runId":"r1", "headSha":"release-b",\n  "status":"COMPLETED", "decision":"BLOCK" }') +
      '<p class="small" style="margin-top:12px">RUNNING → COMPLETED / FAILED / CANCELLED；COMPLETED 仅表示检查结束。<br>Java 将 Python 的 run_id / head_sha 适配为 runId / headSha；关闭页面不会取消服务端任务。' + handout() + '</p>',
      notes('这是一份教学接口设计，不能让学员在本课 localhost 服务上调用 release-checks 路由并以为已经实现。现有出游演示使用 api/runs；这里说明自己的 Java 服务、Android 或前端应用怎样定发布检查协议。Java 可承担鉴权、资料授权与 DTO，编排实现在独立服务内，客户端不必理解框架消息对象。轮询是最小起点；SSE 还要事件序号、去重、断线续传与终态处理。运行与证据都绑定同一 commit，晚到事件不能覆盖新运行。取消是服务端确认的状态变化，停止 fetch 或卸载页面不代表模型和工具停止。status 与 decision 必须分开，检查完成且建议阻断是合法结果。',
        'status=COMPLETED、decision=BLOCK，Android 页面应显示什么？检查已完成，发布建议是阻断。',
        '让 Java 同学指出 DTO 与鉴权边界，前端或客户端同学指出轮询、取消中和终态渲染。手册包含事件字段与服务适配示例，仍不能混称已上线接口。',
        '接得起来之后，用公平的验证记录判断效果是否值得。'), {coreSeconds:120}),

    slide('P37', '看效果：找出风险了吗，付出了多少开销', 180,
      '<div class="grid cols-3" style="margin:12px 0">' +
        '<article class="card" style="padding:14px 17px"><h4>① 比什么</h4><p class="small">脚本 / 单 Agent / 框架编排<br>同一资料、模型与预算</p></article>' +
        '<article class="card" style="padding:14px 17px"><h4>② 记什么</h4><p class="small">漏报 / 误报 / 证据归属<br>耗时 / 调用次数 / token</p></article>' +
        '<article class="card" style="padding:14px 17px"><h4>③ 哪些已验证</h4><p class="small">前两框架无模型回放已通过<br>真实模型效果：尚未评测</p></article></div>' +
      '<p class="small" style="margin:12px 0">样例跑通不代表准确率更高；增加角色未改善质量时，应减少复杂度。' + handout() + '</p>',
      notes('先设普通程序基线：版本不匹配和确定的规则本来就可以由脚本检查。再比较同一模型、同一资料、同一预算下的单 Agent 与框架编排，才能分清新增价值。记录漏报、误报和证据错误时给出样例数与原始问题，不只写一个没有分母的准确率。延迟与 token 包括所有角色、重试和等待，人工复核时间可另行计时。API 核对、默认教学回放与真实模型效果是不同证据；本章没有评测三个框架下的真实模型质量，不用漂亮轨迹证明性能提升。题目要求把运行完成和发布结论分开，避免 UI 把正常完成的阻断报告渲染为可发布。',
        '加了三个审查角色，漏报没减少，延迟和费用却增加，应怎么调整？保留有证据价值的责任边界，回到更简单的实现。',
        '先答题，再解释 CI=passed 为何不足。打开评估记录模板，未测项保留“未测”，不能将预期填成实测。',
        '回到双 Agent 演示，以控制权、事实证据和明确终态检验一次实际运行。'), {
        coreSeconds:120,
        quiz:{
          question:'检查返回 COMPLETED / BLOCK，CI passed 却来自旧提交。正确解释是？',
          options:['检查已结束；测试证据版本不匹配，发布仍被阻断','COMPLETED 就代表可以发布','CI 为绿色即可忽略提交版本','换成多 Agent 框架就能自动放行'],
          answer:0,
          explanation:'运行状态与发布结论是两条独立信息；框架不能代替同一提交的证据校验。'
        }
      })
  ]});
})();

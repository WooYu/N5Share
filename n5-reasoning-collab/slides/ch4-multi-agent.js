(function () {
  'use strict';
  const {cards, callout, table, code, flow, notes, slide} = N5.content;
  const messageCode = value => code(value).replace('<pre class="code">', '<pre class="code" style="font-size:18px;line-height:1.4;padding:13px 16px;margin:8px 0">');
  const supervisorDiagram = '<svg class="diagram" viewBox="0 0 1200 250" role="img" aria-labelledby="sup-title sup-desc"><title id="sup-title">Supervisor 星形调度</title><desc id="sup-desc">主管在上方，天气、场馆、预算三个执行角色分别向主管回报，执行角色之间没有直接通信。</desc><g stroke="#215bea" stroke-width="3" fill="none"><path d="M600 76 V113 H205 V163"/><path d="M600 76 V163"/><path d="M600 113 H995 V163"/></g><rect x="440" y="10" width="320" height="70" rx="16" fill="#215bea"/><text x="600" y="54" text-anchor="middle" fill="white" font-size="27">Supervisor / 主管</text><g fill="#edf2ff" stroke="#215bea" stroke-width="2"><rect x="55" y="163" width="300" height="72" rx="16"/><rect x="450" y="163" width="300" height="72" rx="16"/><rect x="845" y="163" width="300" height="72" rx="16"/></g><g fill="#172c42" font-size="25" text-anchor="middle"><text x="205" y="209">天气 Agent</text><text x="600" y="209">场馆 Agent</text><text x="995" y="209">预算 Agent</text></g><text x="770" y="106" fill="#627286" font-size="18">派发 ↓ / 回报 ↑</text></svg>';
  const hierarchyDiagram = '<svg class="diagram" viewBox="0 0 1200 290" role="img" aria-labelledby="hier-title hier-desc"><title id="hier-title">两级主管的层次化协作</title><desc id="hier-desc">总管接收信息组长和财务组长两份报告。信息组长管理天气和场馆角色，财务组长管理预算和票务角色。</desc><g fill="none" stroke="#215bea" stroke-width="3"><path d="M600 58 V86 H300 V110 M600 86 H900 V110"/><path d="M300 162 V190 H150 V223 M300 190 H450 V223 M900 162 V190 H750 V223 M900 190 H1050 V223"/></g><rect x="460" y="5" width="280" height="57" rx="13" fill="#215bea"/><g fill="#e9f5f3" stroke="#087f79" stroke-width="2"><rect x="160" y="110" width="280" height="55" rx="13"/><rect x="760" y="110" width="280" height="55" rx="13"/></g><g fill="#edf2ff" stroke="#215bea" stroke-width="2"><rect x="35" y="223" width="230" height="55" rx="12"/><rect x="335" y="223" width="230" height="55" rx="12"/><rect x="635" y="223" width="230" height="55" rx="12"/><rect x="935" y="223" width="230" height="55" rx="12"/></g><g text-anchor="middle" font-size="24" fill="#172c42"><text x="600" y="42" fill="white">总管</text><text x="300" y="146">信息组长</text><text x="900" y="146">财务组长</text><text x="150" y="259">天气</text><text x="450" y="259">场馆</text><text x="750" y="259">预算</text><text x="1050" y="259">票务</text></g></svg>';
  N5.chapters.push({id: 4, title: '多 Agent 协作模式', slides: [
    slide('P21', '先说清楚：出游不需要四个 Agent', 120,
      '<p class="lead">这里拆角色，是为了看清协作机制。</p>' + cards([['简单任务，降低理解成本','所有人都知道天气、场馆和预算是什么，能把注意力放在控制权与状态上。'],['真实项目，先证明拆分价值','最后用代码检视讨论独立专业责任、冲突和复审，检验拆分是否值得。']],2) + callout('Agent 数量不是能力指标。每增加一个角色，就增加一份通信与一致性成本。'),
      notes('这一页不能删，避免学员误以为安排家庭出游就应该搭一个复杂团队。前面的固定工具加少量决策已经足够。接下来保留同一个任务，只改变调度拓扑，因此学员不必重新理解业务。工程选型应该问独立上下文、工具权限和专业责任是否有真实收益，而不是为展示框架而拆角色。', '如果一个普通函数能可靠核算费用，你会专门建立“算术 Agent”吗？通常没有必要，模型可以调用这个函数。', '暂不打开演示，先把角色数和能力强弱分开。提醒完整路线还有代码检视案例，核心路线也应保留本页。', '用三个标准判断何时值得拆。')),
    slide('P22', '拆 Agent，至少要有一个清楚的理由', 180,
      cards([['独立上下文','不同角色需要不同知识与历史；混在一起会干扰判断。'],['不同工具权限','查询资料、运行测试、修改文件应有不同的可执行边界。'],['独立专业责任','安全、性能、测试有各自验收目标，需要分别给出结论。']],3) + callout('三项都不成立：优先单 Agent 或普通工作流。拆分后还要衡量协调成本。'),
      notes('三条是设计判断标准，不是多 Agent 的形式化定义。角色可以调用同一个基础模型，是否需要独立进程也取决于实现。工具权限必须由宿主真正限制，不能只写在角色提示词中。独立责任意味着每个角色能为特定结论提供证据，最终仍然需要一个系统级验收入口。某个标准成立只是候选理由，还要考虑额外延迟、冲突和维护成本。', '把一个大 prompt 拆成四段，是否自然满足这三条？请同学给出一个真正需要工具隔离的场景。', '让大家把自己的任务快速标注为上下文、权限或责任中的一项；没有理由也可以明确“不拆”。', '为了观察机制，先给出游团队一份清晰的角色契约。')),
    slide('P23', '开始画契约：先填框，再连箭头', 180,
      '<p class="small">① 写目标与验收 → ② 填角色输入 / 工具 / 输出 → ③ 给箭头写消息 → ④ 补状态与失败出口</p>' +
      table(['角色框','收到什么','允许调用什么','必须交付什么'],[['天气','周六、地点设定','get_weather','rain + 工具来源'],['场馆','rain + 两大一小','search_venue','室内候选 P03 / P04'],['预算','指定 P03 + 上限 200','calculate_cost / check_budget','P03：210 元，超 10 元'],['主管','三份报告 + 原始约束','白名单派发、读取状态','改派 P04；预算保持 200']]) +
      callout('先画四个角色框，再给箭头写输入、回报和下一步条件。'),
      notes('先让听众动笔，而不是只读角色名。用雨天、200元这组约束：目标是取得天气兼容且完整费用不超200元的行程。第一分钟写目标并画四个框，第二分钟填表中输入、工具和输出，第三分钟画主管与执行角色的派发/回报双向箭头。这里按Supervisor权限配置，场馆只查候选；Swarm另授权场馆calculate_cost作费用估算，正式预算检查仍归预算角色。工具白名单由宿主执行。主管可以改派候选，不能修改用户预算。工程迁移时，把天气/场馆/预算换成兼容性/数据库/测试，仍按同一张表定义独立产物；不需要隔离时可保留普通函数。', '预算角色只返回“不可行”，主管能决定换场馆吗？还缺候选ID、总价、预算、失败原因与事实引用。请把这些补进输出栏。', '给出90秒让学员画四框，随后60秒核对每个框的输入/输出，最后30秒圈出需要写入共享状态的事实。保留这张草图，到P30填消息、P31补完整出口。', '框里的职责已经确定；接下来比较控制权怎样连接这些框。')),
    slide('P24', 'Supervisor：每次派发，都回到主管', 180,
      supervisorDiagram + cards([['控制权集中','主管决定先派谁、是否重试、是否换候选，以及何时结束。'],['执行角色专注','只处理收到的任务，带结构化报告回传；不直接指挥其他角色。']],2),
      notes('观察的是控制权，不只是画了几条线。天气完成之后不会自行启动场馆角色，而是主管读报告后派发下一项。优点是全局规则集中、流程易观察；代价是主管上下文可能膨胀，所有小决策都要经过同一个点。主管也可能被写成确定性状态机，不一定每一步都需要额外模型调用。', '主管收到“科技馆 210 元、预算 200 元”后，应该结束还是继续派发？仍有美术馆候选，因此应继续。', '用手指模拟天气向主管回报，再由主管向场馆派发；避免直接画天气到场馆的箭头。', '在演示里只盯住一个问题：此刻谁拥有调度权。')),
    slide('P25', 'Supervisor 演示：谁决定下一位执行者', 240,
      '<p class="small">观察“派发 → 执行 → 回报”。天气、场馆、预算之间的控制权经过主管。</p>',
      notes('先用雨天 300 元跑通基本流程。每次报告后暂停，要求学员预测主管下一次派发对象，再继续。切到雨天 200 元，重点看首个候选费用不通过后主管如何决定换候选。控制权高亮体现当前事件的角色，历史事件回看不应该混入未来状态。提醒这仍是确定性教学剧本，不代表模型在各种情况下都会可靠派发。', '如果主管把预算不通过的报告误当作通过，谁还应拦住输出？系统级验收函数必须独立复核。', '先单步到三次回报，再自动跑完。回看预算报告，核对当前共享状态的写入者；切换预算后确认旧运行清空。', '当主管被细节淹没时，可以增加一层局部汇总。'),{demo:'supervisor'}),
    slide('P26', '层次化：让组长消化局部细节', 180,
      hierarchyDiagram + callout('总管看两份组报告；组长负责组内委派、局部汇总与证据保留。'),
      notes('信息组负责天气与场馆兼容性，财务组负责预算与票价核对。总管并不是看不到原始证据，而是默认接收精炼报告，在冲突或不确定时再追溯。层次化适合任务有自然边界且子问题复杂的场景，小任务加组长只会增加开销。票务角色在本课仅核查课程门票数据，没有购票权限，也不会创建订单。', '如果组报告只写“可行”，总管能否验收？不能，至少需要结论、关键费用、约束和证据引用。', '从叶子节点向上追踪一份报告，说明信息组与财务组的结果在总管处合并。', '下面看汇总如何减少上层默认接收的细节。')),
    slide('P27', '层次化演示：两份报告，形成一个结论', 180,
      '<p class="small">追踪叶子事实如何进入组报告；留意总管何时接手，以及仍保留哪些证据。</p>',
      notes('把看点从每个工具动作移到每次汇总。信息组长先拿到天气与场馆候选，财务组长再拿到票价和完整费用，总管根据两份报告做最终决策。预算不足时组报告必须带失败事实，不能为了简洁而隐去问题。共享状态保持可追溯，报告是摘要，不是删除细节。', '增加组长是否保证更快？不保证；独立子任务可能并行，但更多调度也可能提高延迟。', '默认雨/300，单步到信息组报告、财务组报告和总管汇总三个位置。回看任一叶子事件，核对它如何被上层报告引用。', '也可以不设中央主管，让控制权沿角色直接交接。'),{demo:'hierarchical'}),
    slide('P28', 'Swarm：控制权在对等角色之间交接', 180,
      flow([['天气 Agent','雨 → 交给场馆'],['场馆 Agent','候选 → 交给预算'],['预算 Agent','通过 / 换候选 / 停止']], 'Swarm 的对等交接', '天气角色直接交接到场馆角色，场馆将候选交给预算角色；预算不足时回到场馆角色更换候选，达成验收或耗尽候选时退出。',{target:1,label:'预算不通过 → 回到场馆角色换候选；通过或候选耗尽时退出'}) + callout('每次 handoff 要带交接原因、最小必要上下文，以及下一位执行者。'),
      notes('本课的 Swarm 表示一种对等交接模式，不声称是某个产品的内部实现。虽然没有中央主管，仍有宿主维护运行状态和硬性额度，不能把“去中心化”误解成没有控制。交接规则要避免 A 到 B 再回 A 的空转，通常记录已尝试候选和失败原因。谁有权声明完成也必须写入契约，最终结果仍由统一验收函数检查。', '预算角色发现 210 元超限，应交回场馆还是自己发明一个更便宜的票价？只能按契约请求换候选。', '指向回路，说明它表达换候选，不表示预算角色可以修改天气或票价。', '演示里观察 handoff，而不是寻找不存在的中央主管。')),
    slide('P29', 'Swarm 演示：交接之后，谁来负责结束', 180,
      '<p class="small">先用雨天 / 200 元观察换候选，再用 100 元观察候选耗尽的退出状态。</p>',
      notes('选择雨天 200 元会让交接更明显：科技馆 210 元不通过后，预算角色请求继续寻找，场馆返回美术馆，最终 200 元通过。若实际剧本排序先给出美术馆，则以事件为准说明课程排序，仍须指出换候选回路的条件。预算 100 元时不能无限 handoff，应报告候选耗尽。无主管不代表任何角色都能无条件宣布成功。', '两个角色不断把任务交还给对方，系统凭什么知道没有进展？可以比较状态版本、已尝试候选和相同交接次数。', '运行雨/200，停在每个 dispatch 或 handoff 事件。再切100元自动运行到终态，指出状态区别。', '拓扑只是骨架，要让协作可实现，还需要消息与共享状态契约。'),{demo:'swarm'}),
    slide('P30', '把同一条消息走完：派发 → 回报 → 合并', 180,
      '<p class="small">同一任务 trip-1 · 子任务 cost-1 · planVersion=1。以下是可以照着设计的消息示例。</p>' +
      '<div class="compare" style="margin:12px 0">' +
      '<div><h4>Dispatch：主管 → 预算</h4>' + messageCode(`{ "runId":"trip-1", "taskId":"cost-1",
  "planVersion":1, "intent":"check_cost",
  "from":"supervisor", "to":"budget",
  "payload":{"venue":"P03","limit":200} }`) + '</div>' +
      '<div><h4>Report：预算 → 主管</h4>' + messageCode(`{ "messageId":"m-7", "taskId":"cost-1",
  "runId":"trip-1", "planVersion":1,
  "from":"budget", "to":"supervisor",
  "payload":{"total":210,"ok":false,
    "evidenceIds":["cost-P03"]} }`) + '</div></div>' +
      '<p class="small"><b>宿主合并：</b>核对任务 / 计划 / 工具证据 → 按 messageId 去重 → 写 reports.budget → 主管再派 P04。</p>' +
      callout('发布检查也一样：派发 release-b → 回报 CI 属于旧提交 → 合并“证据不足” → 补查，不计作通过。'),
      notes('将P23的预算箭头放大为一来一回。请求规定要查什么，回报说明查到什么，宿主才负责验证和合并；模型不能靠在payload自填210就改变可信费用。示例是教学契约，现有播放器事件名采用snake_case，字段含义可以对应，不声称界面逐字返回这段JSON。发布检查中，将runId换为release-1、taskId换为tests-1，任务固定headSha=release-b；测试角色发现CI证据属于release-a时，应返回INSUFFICIENT并引用CI元数据，不能作为目标提交的PASS证据。合法并行报告都可使用同一planVersion；其他角色先写入使全局stateVersion变化，不应因此丢掉当前报告。真正过期的是目标提交、计划或任务尝试已被替换；宿主按角色字段合并并做消息去重。', 'm-7重传一次，会不会再加210元？不会，重复消息返回原处理结果。三个角色同拿计划v1，第一份先到后，另外两份还是合法报告吗？只要任务/提交/计划未失效，就应继续合并。', '用60秒追踪左右JSON，再用60秒让学员在P23草图的预算箭头写入taskId、版本和回报字段。最后60秒代入“旧CI报告”检查是否会误判通过。', '把消息重新放回整张图，再补上状态所有者和每一种出口。')),
    slide('P31', '完整契约：箭头有数据，回路有出口', 120,
      '<svg class="diagram" viewBox="0 0 1200 330" role="img" aria-labelledby="contract-trip-title contract-trip-desc">' +
      '<title id="contract-trip-title">雨天200元出游的完整Supervisor契约</title><desc id="contract-trip-desc">输入锁定预算。主管向天气、场馆、预算派发任务，三个角色带事实回报。预算不通过时主管换候选重新派发。宿主合并可信状态并验收；可行则完成，无解或持续工具失败转人工，超限停止，取消结束。</desc>' +
      '<defs><marker id="contract-trip-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#215bea"/></marker><marker id="contract-trip-return" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7" fill="#087f79"/></marker></defs>' +
      '<g fill="#edf2ff" stroke="#215bea" stroke-width="2"><rect x="8" y="12" width="218" height="64" rx="12"/><rect x="326" y="12" width="340" height="64" rx="12"/><rect x="950" y="12" width="242" height="64" rx="12"/><rect x="28" y="143" width="244" height="62" rx="12"/><rect x="363" y="143" width="244" height="62" rx="12"/><rect x="698" y="143" width="244" height="62" rx="12"/></g>' +
      '<g fill="none" stroke="#215bea" stroke-width="2.5" marker-end="url(#contract-trip-arrow)"><path d="M228 44 H322"/><path d="M668 44 H946"/><path d="M496 76 V98 H130 V138"/><path d="M496 98 H465 V138"/><path d="M496 98 H800 V138"/><path d="M1071 76 V242"/></g>' +
      '<g fill="none" stroke="#087f79" stroke-width="2.5" marker-end="url(#contract-trip-return)"><path d="M170 143 V112 H514 V80"/><path d="M505 143 V116 H528 V80"/><path d="M840 143 V108 H542 V80"/></g>' +
      '<g fill="#172c42" text-anchor="middle" font-size="22"><text x="117" y="38">输入：trip-1 / 200 元</text><text x="117" y="62" font-size="18">两大一小；预算不可改</text><text x="496" y="38">主管：按报告决定下一任务</text><text x="496" y="62" font-size="18">taskId / planVersion / 工具白名单</text><text x="1071" y="38">宿主：独立验收</text><text x="1071" y="62" font-size="18">天气 ∧ 完整费用 ∧ 预算</text><text x="805" y="33" font-size="18">事实齐备，提交方案</text><text x="150" y="133" font-size="18">日期 ↓ / weather ↑</text><text x="485" y="133" font-size="18">rain ↓ / 候选 IDs ↑</text><text x="820" y="133" font-size="18">P03 ↓ / 210、false ↑</text><text x="150" y="167">天气角色</text><text x="150" y="191" font-size="18">get_weather</text><text x="485" y="167">场馆角色</text><text x="485" y="191" font-size="18">search_venue</text><text x="820" y="167">预算角色</text><text x="820" y="191" font-size="17">calculate_cost / check_budget</text></g>' +
      '<text x="486" y="229" text-anchor="middle" fill="#087f79" font-size="20">false 回报 → 主管改派 P04 → 200 元通过；不修改预算或票价</text>' +
      '<rect x="8" y="247" width="732" height="77" rx="10" fill="#e9f5f3"/><rect x="778" y="247" width="414" height="77" rx="10" fill="#f0f3f8"/>' +
      '<g fill="#172c42" font-size="18"><text x="23" y="270">状态所有者：输入锁定 constraints；工具写 weather / venues / costs</text><text x="23" y="294">主管维护计划；宿主校验并合并 reports，统一写 status / itinerary</text><text x="23" y="316">按任务和版本验收，按消息 ID 去重；失败事实保留，不覆盖成成功</text><text x="794" y="269">completed：可行行程；needs_human：无解 / 失败</text><text x="794" y="293">stopped：额度耗尽；cancelled：用户取消</text><text x="794" y="317">任何终态都保留依据与结束原因</text></g></svg>' +
      '<p class="small">照图检查：每个框有责任；每条箭头有输入 / 回报；状态有写入者；失败有条件和出口。</p>' +
      '<button type="button" class="primary" data-handout="contract">打开发布检查完整契约、DTO 与评分</button>',
      notes('用这张图完成P23开始的草图。蓝箭头是派发，青箭头是回报：天气、场馆、预算始终通过主管协调；rain和工具费用由宿主记录。预算报告false后主管换P04再派，场馆耗尽后不能回到起点无限重试。最终是否通过由宿主检查天气兼容、完整费用和预算，角色没有修改constraints的权力。图中四类出口是出游设计模板，现有离线剧本主要展示completed和needs_human，真实模式另有取消、失败和超限。打开发布检查参考契约，把同一方法映射为Java API、三角色报告和验收。发布检查独立区分status与decision：COMPLETED只代表检查结束，decision可能是BLOCK或NEEDS_EVIDENCE；READY_FOR_MANUAL_REVIEW也不是生产发布批准。发现已证实的兼容性问题，即使还缺测试证据，也应给BLOCK并保留缺口，不能将业务阻断写成技术运行失败。', '把预算改成100元，沿图指出最后的出口，不能新增“省略餐费”分支。发布检查已经查明阻断问题并完成报告，应写失败运行还是COMPLETED/BLOCK？后者。', '前60秒沿210元失败、改派200元通过的回路走一遍；后60秒请学员对照自己的图找缺失箭头或出口。展示参考契约入口，详细DTO和评分留给后续练习或课后，不在两分钟内逐项朗读。', '契约先固定。接下来比较不同框架怎样实现这同一份契约。'))
  ]});

  N5.handouts = N5.handouts || {};
  N5.handouts.contract = {
    title: '发布检查：完整参考契约',
    html: '<p class="lead">输入同一提交的变更，输出带证据的发布建议。</p>' +
      '<p>同三框架实验：<code>head_sha=release-b</code> 删除客户端仍使用的 <code>totalAmount</code>，迁移删列且无兼容方案，CI 属于 <code>release-a</code>。应交付 <code>COMPLETED / BLOCK</code>，保留 <code>missing_evidence</code>。所有工具与CI资料是教学样本；以下API和补查回路为应用设计参考，不自动部署。</p>' +
      flow([['Java API','鉴权并冻结提交'],['固定派发','兼容性 ∥ 数据库 ∥ 测试'],['宿主合并','任务 / 版本 / 引用'],['规则验收','BLOCK / 缺证据 / 可复核']], '发布检查参考契约', 'Java接口冻结目标提交，编排器固定派发三个独立审查任务。宿主按任务与版本合并报告。有已证实阻断项则BLOCK并保留缺口；没有阻断但证据仍不足则NEEDS_EVIDENCE；证据齐备且无阻断才可交人工复核。检查完成时status都是COMPLETED。', {target:1,label:'缺证据 → 可只补查对应角色一次；已知阻断仍给 BLOCK 并保留缺口'}) +
      callout('整体用固定编排；角色内部需要根据发现追查资料时才用局部 ReAct。步骤都已知时直接调用工具，不必增加 Planner。') +
      '<h3>1. 角色框：工具权限与交付物</h3>' +
      table(['角色','输入 / 允许工具','报告'],[['兼容性','同一 diff；read_api_schema / search_client_usage','受影响字段、客户端、证据引用'],['数据库','同一迁移；read_ddl / read_explain_fixture','迁移风险、依据、待验证项'],['测试','目标提交；read_ci_run / read_test_report','PASS / BLOCK / INSUFFICIENT + CI引用'],['编排器 / 宿主','任务清单、原始约束；白名单派发与验收','合并报告、补查次数、最终建议']]) +
      '<p>所有角色无生产写权限。工具返回事实；模型可以解释风险、提出补查请求，不能自行伪造测试结果或修改目标提交。</p>' +
      '<h3>2. 箭头：同一个任务的请求与回报</h3>' +
      code(`Dispatch: {runId:"release-1", taskId:"tests-1",
  headSha:"release-b", planVersion:1, to:"TEST",
  allowedTools:["read_ci_run","read_test_report"]}
Report: {messageId:"m-7", runId:"release-1", taskId:"tests-1",
  headSha:"release-b", planVersion:1, from:"TEST",
  verdict:"INSUFFICIENT", evidenceIds:["ci-old"],
  finding:"CI ci-old 对应 release-a，缺目标提交的测试证据"}`) +
      '<p>宿主核对 CI 元数据，保存 missingEvidence，可只补查 TEST 一次。本例已有兼容性/迁移阻断 → COMPLETED/BLOCK；若其他角色均无阻断而仅缺CI → COMPLETED/NEEDS_EVIDENCE。两种情况都不能 READY。</p>' +
      '<h3>3. 共享状态：按字段合并</h3>' +
      table(['字段','写入者与规则'],[['target','Java API 冻结提交；审查员不能改'],['planVersion / tasks','编排器写；计划改变才升版本'],['evidence[id]','工具适配器写事实，保留 sourceSha 与来源'],['reports[role] / processedMessageIds','宿主校验后按角色合并；重复消息返回原结果'],['attempts[role]','编排器计数；每角色最多补查一次'],['status / decision','宿主规则验收；状态与业务结论分开']]) +
      callout('三个并行角色可合法回报同一 planVersion。不能因另一角色先写入使全局 stateVersion 改变，就拒绝其余有效报告。提交、任务尝试或计划失效才是过期。') +
      '<h3>4. 终态：检查完成不等于可以发布</h3>' +
      table(['触发条件','status','decision'],[['已完成检查，有已证实阻断项；可同时缺CI','COMPLETED','BLOCK（仍列出缺口）'],['无阻断，但证据仍缺失 / 分歧未解','COMPLETED','NEEDS_EVIDENCE'],['同一提交必要证据齐备，无阻断','COMPLETED','READY_FOR_MANUAL_REVIEW'],['技术故障 / 额度耗尽；或用户取消','FAILED；或 CANCELLED','null，保留原因与部分结果']]) +
      '<p>运行中 status=RUNNING、decision=null。只有宿主允许状态转移；取消后晚到报告只留审计，不能再发布成功。</p>' +
      '<h3>5. Java DTO 与外部接口</h3>' +
      code(`record ReviewReport(String messageId, String runId, String taskId,
  String headSha, int planVersion, Role role, Verdict verdict,
  List<String> evidenceIds, List<Finding> findings) {}

POST /api/release-checks {repoId, baseSha, headSha}
  -> 202 {runId, status:"RUNNING", decision:null}
GET /api/release-checks/{runId}
  -> {status, decision, reports, missingEvidence}
POST /api/release-checks/{runId}/cancel -> {status:"CANCELLED"}`) +
      '<p>前端 / Android 展示进度、证据、缺口和取消；Java 负责认证、仓库权限与任务入口；编排服务负责角色运行。Java字段 <code>headSha / missingEvidence</code> 对应实验JSON的 <code>head_sha / missing_evidence</code>。完整可复制 DTO 和空白模板见 <code>notes/collaboration-workbook.md</code>。</p>' +
      '<h3>6. 10 分验收表</h3>' +
      table(['各 2 分','必须能验证'],[['选型','固定编排与局部 ReAct 的位置、理由明确'],['角色与权限','角色有输入 / 工具 / 输出，无生产写权限'],['消息','任务、提交、计划、消息 ID 与证据引用齐全'],['共享状态','同提交才能验收；并行按字段合并；重复去重'],['结束条件','区分 status 与 decision；缺证据、取消、超限有出口']]) +
      '<p><b>8 分通过。</b>合并不同提交的通过证据、把未运行测试当作通过、自动部署，任一出现都需修正后重评。现场用“旧 CI、重复报告、一个角色超时”逐项走图。</p>'
  };
})();

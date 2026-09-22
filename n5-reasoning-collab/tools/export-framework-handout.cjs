/* Export the same practical guide to the offline reader and Markdown notes. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sections = [
  {title:'先跑同一条发布检查，再比较编排方式', text:'这份手册面向已经会写服务、客户端和测试的开发者。目标是跑起一个最小例子，看见状态、消息和产物如何流转，然后决定项目是否值得引入框架。投影片 P33–35 是关键代码节选，下面的源文件是完整程序。'},
  {text:'所有示例默认读取同一份合成资料，不访问真实仓库、数据库、CI 或模型服务，也不需要密钥。LangGraph 使用普通函数节点；AutoGen 使用官方 ReplayChatCompletionClient 回放一次工具调用；MetaGPT 使用自定义确定性 Action。运行框架成功，只证明接口和编排接通，不能证明模型更聪明或缺陷检出率更高。'},
  {title:'1. 统一输入、输出和验收', code:'head_sha: release-b\n删除 totalAmount；线上客户端仍读取它\n迁移删列；缺少兼容迁移方案\nCI: passed=true，但 head_sha=release-a\n\n预期 status: COMPLETED\n预期 decision: BLOCK\nfindings: API_BREAK、DB_DROP\nmissing_evidence: release-b 的 CI 证据', language:'text'},
  {text:'status 描述检查任务是否执行完；decision 描述业务上是否建议发布。发现阻断项仍是一次正常完成的检查。已有明确阻断项且同时缺证据时，保留 BLOCK 和缺口。只有缺证据则 NEEDS_EVIDENCE；全齐且无阻断才 READY_FOR_MANUAL_REVIEW。模型或框架说“完成”不能越过这个规则函数。'},
  {title:'2. 在独立环境运行', text:'在课件目录打开终端。运行前两种示例时使用 Python 3.10+；这里的验证环境为 Python 3.13。首次安装需要网络；安装后以下回放不联网、不消耗模型 token。不要把框架依赖装进正在使用的真实演示服务环境。'},
  {code:'python -m venv .framework-venv\n.\\.framework-venv\\Scripts\\python.exe -m pip install -r labs/requirements.txt\n.\\.framework-venv\\Scripts\\python.exe labs/common.py\n.\\.framework-venv\\Scripts\\python.exe labs/langgraph_release.py blocked\n.\\.framework-venv\\Scripts\\python.exe labs/autogen_release.py blocked', language:'powershell'},
  {text:'把最后一个参数改为 missing 或 ready，分别验证“只有旧 CI”和“证据齐备”。程序把轨迹和结果输出到终端；需要留存时在命令末尾添加 > result.txt。直接运行 common.py 得到不用框架的基线。'},
  {title:'3. LangGraph：把分支写成可观察的状态图', text:'ReleaseState 是输入和运行状态；collect 节点读取三类资料并产出报告；release_route 调用宿主规则，选择 block、missing 或 allow 节点；stream(stream_mode="updates") 输出每一步增量。把 TypedDict 类比 DTO，把 node 类比处理函数，把 edge 类比状态机转移。'},
  {code:'blocked: collect → block → END\nmissing: collect → missing → END\nready:   collect → allow → END', language:'text'},
  {text:'适合：业务必须明确分支、回路、暂停与状态边界。这个示例没有配置 checkpointer，因此没有证明重启恢复。生产使用时要选存储、设置 thread_id、验证恢复与副作用幂等；普通函数完全能做好的检查，也无需为了框架而调用模型。'},
  {file:'labs/langgraph_release.py', label:'LangGraph 完整程序'},
  {title:'4. AutoGen：角色轮流发消息，工具交付证据', text:'make_agent 为每个角色建立独立工具闭包，传入对应职责的 evidence；AssistantAgent 注册 inspect 工具。回放客户端要求调用一次 inspect，由真实 AgentChat 运行时执行工具并发布 ToolCallSummaryMessage。RoundRobinGroupChat 按 compat → db → tests 发言。MaxMessageTermination(4) 包含用户任务加三份最终报告；工具事件默认不计入该消息数。'},
  {code:'TextMessage / user\ncompat: ToolCallRequest → ToolCallExecution → ToolCallSummary\ndb:     ToolCallRequest → ToolCallExecution → ToolCallSummary\ntests:  ToolCallRequest → ToolCallExecution → ToolCallSummary\nstop_reason: 达到消息上限\n宿主再 evaluate(reports, source) → COMPLETED / BLOCK', language:'text'},
  {text:'固定顺序不需要模型选择下一位角色。RoundRobinGroupChat 共享团队对话上下文；它不是隐私或权限隔离边界，真正的工具授权仍由服务检查。停止原因仅说明对话停止，不能直接映射为业务通过。官方仓库现为维护模式，新项目应同时评估 Microsoft Agent Framework；示例用于理解现有 AutoGen 系统。'},
  {file:'labs/autogen_release.py', label:'AutoGen 完整程序'},
  {title:'5. MetaGPT：用产物触发下一角色', text:'CheckRelease 把输入变成带版本的审查产物；ReleaseReviewer 关注 UserRequirement。ReportWriter 只关注 CheckRelease 产生的消息，调用 PublishReport 验收后发布结果。Message.cause_by 声明产物由哪种 Action 产生，_watch 决定下游是否响应。SOP 是“审查 → 汇总”，不是让有职位名的模型自由聊天。'},
  {code:'UserRequirement\n  → ReleaseReviewer / CheckRelease\n  → Message(cause_by=CheckRelease, source + reports)\n  → ReportWriter / PublishReport\n  → COMPLETED / BLOCK', language:'text'},
  {text:'本机是 Python 3.13；MetaGPT 官方 README 要求 Python ≥3.9 且 <3.12。这段示例核对了官方 Action、Role、Team 接口并做语法检查，但尚未在受支持环境运行。上面的轨迹是预期结果，不能称为实测。采用它前，应在独立 Python 3.11 环境完成依赖安装和下面的三情景回放。'},
  {code:'# 将第一行路径替换为你已安装的 Python 3.11 路径\nC:\\Python311\\python.exe -m venv .metagpt-venv\n.\\.metagpt-venv\\Scripts\\python.exe -m pip install metagpt==0.8.2\n.\\.metagpt-venv\\Scripts\\python.exe labs/metagpt_release.py blocked\n.\\.metagpt-venv\\Scripts\\python.exe labs/metagpt_release.py missing\n.\\.metagpt-venv\\Scripts\\python.exe labs/metagpt_release.py ready', language:'powershell'},
  {text:'MetaGPT 初始化可能读取其自身本机配置；此例 Action 不调用 _aask，不需要真实模型请求。若初始化仍要求模型配置，按官方配置指南设置后再运行，不能凭本例宣称开箱即用。复杂依赖、产物格式校验和失败重审都是选型成本。'},
  {file:'labs/metagpt_release.py', label:'MetaGPT 完整程序（未执行验证）'},
  {title:'6. 如何换成真实模型', text:'先保留 read_evidence 与 evaluate。LangGraph：把 collect 内一个报告函数换成“读取证据 → 调模型 → 校验 JSON → 返回报告”；控制图和宿主验收不变。AutoGen：把 ReplayChatCompletionClient 换成兼容的 ChatCompletionClient，为 inspect 提供原始证据，要求模型产出结构化 ReviewReport，再由宿主校验。MetaGPT：在 CheckRelease.run 中调用 _aask(prompt)，将响应校验成审查产物，保持 cause_by 与版本字段。不要直接把自然语言报告当作发布许可。'},
  {text:'模型连接配置由服务端管理。一次真实尝试至少限制总模型次数、总工具次数和墙钟时长，支持明确取消，完整记录重试成本。这里未对三框架做真实模型质量或速度评测；原课件的 DeepSeek 真实模式是自写运行时，不能当作三框架的测试结果。'},
  {title:'7. Java、Android、前端怎样接', text:'建议由 Java API 负责会话鉴权、仓库访问校验、冻结目标版本和任务记录，编排服务在内部运行框架。对客户端返回稳定 DTO。以下是发布检查助手的接口设计示例，未加入本课现有 /api/runs 出游接口。'},
  {code:'POST /api/release-checks\n  {repoId, baseSha, headSha, artifactSha256, variant}\n  → 202 {runId, status:"RUNNING"}\nGET /api/release-checks/{runId}\n  → {runId, status, decision, completedRoles, findings, missingEvidence}\nPOST /api/release-checks/{runId}/cancel\n  → {runId, status:"CANCELLED"} 或已先完成的实际终态', language:'text'},
  {text:'前端组件卸载、AbortController.abort()、Android Activity 重建或停止收集 Flow，都只改变客户端观察。需要业务取消时发送 cancel 请求，并读取服务端终态；超时只表示结果未知。保留 runId 以便重新订阅，丢弃旧任务响应；若需要跨进程恢复，必须设计客户端与服务端持久化。Android 同一提交也可能有不同变体或安装包，证据还应绑定 artifactSha256、variant 和约定设备/API 环境。'},
  {title:'8. 效果怎么评，不凭演示判断', text:'先比较三种方案：固定规则基线、单 Agent、必要分工的多 Agent。固定任务集、模型、资料、token/工具预算与验收规则，每个真实模型情景重复运行并保留失败，别只挑成功截图。框架主要提供组织与运行控制；查得更准依赖模型、工具资料和契约，不能从框架名推导。'},
  {code:'固定样本组：可通过、已知阻断、缺CI、错SHA、角色超时、重复报告、取消\n质量：命中已知阻断 / 漏报 / 误报；无证据的“通过”次数\n可靠性：是否正确终止；取消确认后新工具调用数；重复/旧报告是否被拒绝\n代价：总延迟 p50/p95、全部模型/工具次数、输入/输出token、人工复核分钟\n公平性：包含主管调度和重试开销；真实模型至少多次重复，报告样本量\n结论：质量未改善而代价增加，优先减少角色或回到工作流', language:'text'},
  {title:'9. 共享工具与宿主验收源码', text:'这份实现专门针对三个固定样本，不是通用风险识别引擎。生产实现还需要严格 schema、身份与任务绑定、消息去重、工具证据来源验证，以及取消和超限的终态保护。'},
  {file:'labs/common.py', label:'共享样本、三角色报告与 evaluate'},
  {title:'10. 官方依据（2026-09-23 核对）', links:[
    ['LangGraph Graph API','https://docs.langchain.com/oss/python/langgraph/graph-api'],
    ['AutoGen Teams','https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html'],
    ['AutoGen ReplayChatCompletionClient','https://microsoft.github.io/autogen/stable/reference/python/autogen_ext.models.replay.html'],
    ['AutoGen 维护声明','https://github.com/microsoft/autogen'],
    ['MetaGPT Multi Agent 101','https://docs.deepwisdom.ai/main/en/guide/tutorials/multi_agent_101.html'],
    ['MetaGPT Python 版本要求','https://github.com/FoundationAgents/MetaGPT']
  ]}
];
const validation = JSON.parse(fs.readFileSync(path.join(root,'labs/verification.json'),'utf8'));
sections.splice(8,0,{title:'本次验证记录',text:validation.summary});
let html='', markdown='# 三框架实操手册\n\n';
for (const s of sections) {
  if(s.title){html+=`<h3>${esc(s.title)}</h3>`;markdown+=`## ${s.title}\n\n`;}
  if(s.text){html+=`<p>${esc(s.text)}</p>`;markdown+=s.text+'\n\n';}
  if(s.code){html+=`<pre><code>${esc(s.code)}</code></pre>`;markdown+='```'+(s.language||'text')+'\n'+s.code+'\n```\n\n';}
  if(s.file){const source=fs.readFileSync(path.join(root,s.file),'utf8');html+=`<details><summary>${esc(s.label)} · ${esc(s.file)}</summary><pre><code>${esc(source)}</code></pre></details>`;markdown+=`### ${s.label}\n\n文件：${s.file}\n\n\`\`\`python\n${source}\n\`\`\`\n\n`;}
  if(s.links){html+='<ul>'+s.links.map(([label,url])=>`<li><a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}</a></li>`).join('')+'</ul>';markdown+=s.links.map(([label,url])=>`- [${label}](${url})`).join('\n')+'\n\n';}
}
fs.writeFileSync(path.join(root,'assets/framework-handout.js'),'/* Generated by tools/export-framework-handout.cjs; no fetch required. */\n(function(){N5.handouts=N5.handouts||{};N5.handouts.frameworks='+JSON.stringify({title:'三框架实操：完整代码、输出与效果验证',html})+';})();\n');
fs.writeFileSync(path.join(root,'notes/framework-lab.md'),markdown.trimEnd()+'\n');
console.log('Exported framework handout + notes with four complete source files.');

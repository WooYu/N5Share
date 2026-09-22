# N5 独立课件实施与接口约定

依据：桌面《高级推理框架与多 Agent 协作.md》，2026-09-22 设计。用户要求据此重构，成品独立放在本目录。

## 范围

- 51 页、九章页数 2/3/7/8/11/6/5/6/3；总时长 148 分钟，核心路线 120 分钟。
- 1440 × 810 固定舞台，离线普通 script 加载，无 CDN，无 file:// fetch。
- 不修改或引用 agent-training 代码；沿用配色、案例设定和凭据存放位置。
- 植物园总费用修正为 150 + 40 + 80 = 270；不把未经测量的性能数量级写成结论。
- 所有 thought 是公开的简短决策摘要，不是模型内部思维。

## 实施任务

- [x] 课程：slides/ch0-opening.js 至 ch8-closing.js；assets/content-kit.js；notes/outline.md、speaker-notes.md。51 页逐页讲稿、SVG 图、判断题、裁剪时间。
- [x] 剧本：data/outing-scripts.js、dual-agent-script.js、code-review-script.js。七种演示共用事件格式，检查晴/雨 × 300/200/100，雨天 300 元双 Agent 回传与修订、代码检视两类仲裁和复审。
- [x] 播放器：index.html、assets/theme.css、player.js、demo-player.js。翻页、目录、备注、全屏、核心路线、事件回看、角色控制权、共享状态写入者、取消与错误状态。
- [x] 本地服务：server/app.py、deepseek.py、tools.py 及单元测试。127.0.0.1、明确静态/接口白名单、跨源拒绝、结构化动作校验、工具事实、预算、取消、无凭据禁用。
- [x] 集成：README.md、启动脚本、独立 ZIP；核对源码与成稿数量/时长，桌面和手机浏览器截图，打印分页。DeepSeek 凭据已导入本机 Windows DPAPI 存储，本地服务下七个“真实运行”按钮均已启用。

真实模型验证：ReAct 与双 Agent 演示均已通过实际 DeepSeek 调用。双 Agent 本次运行状态为 `completed`，使用 5 次模型调用、8 次工具调用，最终方案为 P03 科技馆，总费用 210 元。其余五种演示已确认按钮启用，尚未记录实际供应商运行通过；按钮可用不等于全部场景均已验证。凭据内容不进入课件或验证记录。

## JS 契约

index.html 首先设置 window.N5 = {chapters: [], scenarios: {}}。
章节调用 N5.chapters.push({id:0,title:'开场与目标',slides:[{id:'P01',title:'...',seconds:180,coreSeconds:180,html:'...',notes:'...',demo:null,quiz:null}]}).
coreSeconds 为 0 表示核心路线跳过，其余合计 7200 秒；seconds 合计 8880 秒。
quiz 如有值：{question,options:[string],answer:0,explanation:string}。
demo 为 react / plan / supervisor / hierarchical / swarm / dual / review。
章节 HTML 不含整个 section/h2（由播放器添加）。公共布局类：lead, grid, cols-2, cols-3, card, callout, flow, small, tag, compare, code, diagram, table。

N5.scenarios[id] = {title,roles:[{id,label}],create({weather:'rain'|'sun',budget:300|200|100}) => ({initialState,events})}。
事件：{id,actor,kind,title,detail,payload,state_after,highlight:[actorId],writers:{stateField:actorId}}。
state_after/writers 是该时刻完整快照，不能引用后续可变对象。结束事件 done 的 payload 含 status:'completed'|'needs_human'|'stopped'。
角色标识：weather,venue,budget,supervisor,director,info_lead,finance_lead,ticket,planner,executor,security_reviewer,performance_reviewer,readability_reviewer,test_reviewer。

## HTTP 契约

- GET /api/health → {available:boolean,reason:string,model:'deepseek-flash'}，不包含密钥。
- POST /api/runs，JSON {scenario,weather,budget} → 202 {run_id}。
- GET /api/runs/{run_id} → {run_id,status:'running'|'completed'|'needs_human'|'failed'|'cancelled'|'stopped',events:[全部事件快照],error:null|string,metrics:{model_calls,tool_calls,elapsed_seconds,input_tokens,output_tokens}}。
- POST /api/runs/{run_id}/cancel，JSON {} → {run_id,status}。
- 请求失败：JSON {error:string} + 对应 HTTP 状态。
- 不从 file:// 探测服务。HTTP 模式只访问同源接口。工具最多20次、模型最多12次、墙钟最多480秒。取消、错误、无可行方案均不可声称验收通过。

## 重点验证

2026-09-23 听众视角修订：保持 51 页及 148 / 120 分钟；P02 改为选型卡和完整协作契约两份交付。P12 / P20 / P49 补 Java、Android、前端任务的判据；P23 / P30 / P31 连通角色、派发、回报、合并和验收；P50 以旧证据、页面重建、取消竞态练习边界，并提供完整参考答案与评分。实操内容以本地内嵌弹窗提供，不增加离线网络访问。

P32–37 改为同一发布资料的三框架用法和输出比较，配套 `labs/` 与 `notes/framework-lab.md`。LangGraph 1.2.12、AutoGen 0.7.5 已在独立 Python 3.13 环境通过阻断、缺证据和可复核三种回放；均与无框架基线一致，伪造空报告被拒绝。MetaGPT 只核对官方 API 和语法，本机 Python 版本不满足其 README 范围，未执行验证。所有回放无模型调用，真实模型质量与性能未测。官方 API、维护声明及 Python 版本范围于 2026-09-23 重新核对。

1. 100 元无可行方案、雨天200元可选美术馆200元，不能固定成功。
2. 回看旧事件不能显示未来状态，切换条件/模式须清空旧运行，取消后不能继续发布成功。
3. 工具观察由宿主生成，模型给出的费用/天气与证据不符必须拒绝。
4. 跨源、路径穿越、未知接口、非结构化模型输出、预算耗尽明确失败。
5. 51 页内容边界/移动缩放/键盘/打印；真实模型不可用须显式提示，不回退剧本冒充模型。

# 高级推理框架与多 Agent 协作 · 讲师讲稿

90 分钟，48 页。面向 Java 后端、前端、客户端开发者，不预设 Agent 开发经验。

备课：安装 requirements.txt 后运行 `python demo/server.py`。默认规则模拟决策，LangGraph 实际编排，工具只读合成资料。离线 HTML 内嵌的是预录轨迹；completed 仅表示报告生成，仍需人工审核。verified 仅表示证据契约通过。

## 01 · 高级推理框架与多 Agent 协作

开场与目标 · 50 秒

【50 秒】今天不要求 Python 熟练，也不要求做过模型微调。Agent 在难以预先枚举的任务路径中解释信息、选择工具；已知条件分支仍是工作流。后面用函数、状态对象和 HTTP 对照大家已有的开发经验。只有两个核心目标：面对复杂度能选择合适的推理与编排方案；能设计一个职责清楚、能够停止的简单多 Agent 系统。所有工单、诊断读数与知识条目均为合成教学样本，不连接真实车辆。最终输出是待人工确认的建议，演示通过也不代表完成维修。

## 02 · 90 分钟：手把手搭建多 Agent 系统

开场与目标 · 1 分 40 秒

【1 分 40 秒】七章总计 90 分钟，包含概念、演示、练习与讨论，不额外添加隐藏的实操时长。前 17 页通过能力演进认识推理机制；后半程连续讲流程概念、设计方法、协作模型和同一个远程诊断案例。请 Java 与后端同学关注权限、状态和错误恢复，前端与客户端同学关注事件、可见状态和人工确认入口。最后用运行轨迹复盘角色边界、消息契约和停止条件。

## 03 · 本课学习路线：会判断、懂协作、能搭建

Agent 基础 · 2 分 30 秒

【2 分 30 秒】按学习动作讲路线。第一步会判断：能力演进介绍检索、工具、ReAct、规划和反思。第二步懂协作：从多 Agent 生命周期进入任务依赖、角色接口、消息、状态和停止。第三步能搭建：比较协作模型，映射到 LangGraph，再用同一份远程诊断工单验证。推理策略回答一个角色怎样决策；协作流程回答多个角色怎样流转；开发框架回答代码怎样管理状态与执行。Java 业务服务负责权限，状态与消息可类比 DTO，前端呈现进度和人工确认。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)

## 04 · 概念 ①：LLM 根据上下文生成回答

能力演进 · 1 分钟

【1 分钟】先从左到右读图。用户提供同行人数、时间与预算，模型结合这些上下文生成建议。它可能利用训练中学到的知识，但没有自动获得今天的天气和实时价格。能生成自然语言不代表已完成查询，也不保证事实正确。用“先给一个想法，出发前还要核实”帮助零基础学员理解。下一页只观察回答及其对未知信息的说明，不把模型随机措辞作为好坏标准。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 05 · 演示 ①：大语言模型 LLM

能力演进 · 50 秒

【50 秒】七组概念与演示展示可以组合的能力，不是技术发展的历史时间线，也不是每个应用必须逐级升级。全程沿用两大一小、半日出游、预算300元、不订票；下拉预算可对照200或100元。LLM 是大语言模型 Large Language Model。本页的离线模式展示事先写好的回答，例如建议湖畔公园，并提示核对天气与费用；没有实际模型、检索或工具调用。改变天气或预算不会使固定答案获得新的事实依据。统一合成场馆：湖畔公园为户外，门票60、交通40、餐饮80，总计180元；自然馆为室内，150+60+100=310元；城市博物馆为室内，90+40+80=210元。金额均为本次两大一小的合计。下雨需要室内，但本页并未查证这一约束。本章节已接入真实模型，点击真实模型演示打开本地运行窗口，操作与提示词见 model-demo-guide.md。模型负责生成建议、提出结构化工具请求、规划或反思，宿主程序负责执行工具、保存状态与限制轮次。下一步演示按钮保留离线规则示意。这些场馆与价格不是现实推荐，后六页也同时提供离线规则示意与真实模型模式。固定流程足够完成这个已知例子，动画用于比较机制，不证明自主能力。

## 06 · 概念 ②：RAG 先查资料，再参考资料回答

能力演进 · 1 分钟

【1 分钟】RAG 可以类比开卷回答。问题先交给检索程序，从资料库选取相关片段；程序将片段、来源编号和原问题一并提供给模型，模型再回答。库大时不必把整库塞进提示词。解释两条课程资料D01和D02，特别区分规则资料与当下天气、具体费用。引用使依据可追踪，但检索可能漏掉资料，资料也可能过期，仍要检查来源是否支持结论。本课真实模式使用关键词检索，同样能演示“检索后生成”的机制，不要求一开始就讲向量数据库。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 07 · 演示 ②：检索增强生成 RAG

能力演进 · 1 分 40 秒

【1 分 40 秒】RAG 是检索增强生成 Retrieval-Augmented Generation，可理解为先查资料再回答，不是重新训练模型。预写检索片段 D01：下雨时选择室内场馆；D02：总成本必须包含门票、交通、餐饮。演示把 D01、D02 带入回答并保留引用。仅有规则，仍不能声称已查到真实天气或实时价格；合成场馆数据与资料规则是不同来源。两大一小、半日、预算300元、不订票保持一致。预算改成200或100时，成本口径仍不能省略交通和餐饮。离线模式的检索和回答均为脚本模拟；真实模式先执行本地关键词检索再调用模型；固定检索链也是工作流。

## 08 · 概念 ③：工具调用让模型请求程序办事

能力演进 · 1 分钟

【1 分钟】按上排从左到右、下排从右到左读图。模型不会凭一句话直接操作工具，它先返回工具名称和参数，宿主程序核验后执行，再回传数据或错误。模型得到Observation后才能据此继续。RAG侧重查找已有资料，工具可访问接口或执行计算；检索也可以封装成一种工具，两者可以组合。本课程所有工具只读合成数据，不订票不付款。已有接口也必须有参数校验、权限和调用上限。下一页重点找出请求、执行、返回三个位置，避免把模型输出工具JSON当作已经执行成功。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 09 · 演示 ③：工具调用 Tool Calling

能力演进 · 1 分 40 秒

【1 分 40 秒】工具调用 Tool Calling 区分提出请求、宿主校验执行、收到结果。这里 weather、catalog、sum 是概念伪代码，界面实际使用 read_weather、localcatalog、outingCost；均为浏览器预写步骤示意，无网络服务、真实模型或订票动作。weather 使用 rain/sun 选项；catalog 返回合成场馆：湖畔公园户外60+40+80=180，自然馆室内150+60+100=310，城市博物馆室内90+40+80=210。sum 按门票、交通、餐饮核算两大一小合计。300元下自然馆也超预算，不能只看门票150元就认为可行。下雨排除公园；200元下雨和100元任意天气都没有符合条件的候选。此页重点观察数据来源和计算返回，下一页再观察怎样利用反馈重选。工具返回事实或错误，不能凭一句已经查过认定调用成功；参数权限与预算由运行时负责。已知调用次序可以直接使用固定工作流。

## 10 · 概念 ④：ReAct 根据每次反馈决定下一步

能力演进 · 1 分钟

【1 分钟】Thought在课堂上只展示简短决策摘要，不要求也不展示模型内部完整思维。Action是模型提出的行动，经宿主实际执行；Observation是工具回传的证据。根据310元超预算这条观察，下一轮可以改查其他候选。满足条件后结束，没有候选、工具持续失败、预算或步数用完也必须结束。ReAct不要求每个任务都出现同样的调用顺序。这个小任务的固定规则也能写成工作流，课堂用它来展示观察怎样影响下一次判断。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 11 · 演示 ④：推理与行动交替 ReAct

能力演进 · 1 分 40 秒

【1 分 40 秒】ReAct 强调推理与行动交替：决定先查什么，执行查询，利用返回决定下一步。展示简短教学决策摘要，不展示模型完整内部思维；离线步骤为预写规则，真实模式的行动来自每轮模型返回。默认下雨、预算300元：先按 D01 排除户外湖畔公园；查询自然馆并按 D02 算出310元，观察超预算后换城市博物馆，总计210元，通过天气和预算检查，再请用户确认，不订票。预算改为200元且下雨，室内候选都超额，应保留已查价格并说明没有可行方案；100元同样停止。晴天时公园180元可作为候选。不能偷偷增预算、漏餐费或反复查询同一结果。成功、无可行候选、工具错误和无进展都应有明确出口，运行时还要限制步数与时长。单次工具调用不等于 ReAct；本页这种已知重选也可以由固定分支实现。

来源：[ReAct · ICLR 2023](https://arxiv.org/abs/2210.03629)

## 12 · 概念 ⑤：Plan-and-Execute 先规划，再执行

能力演进 · 1 分钟

【1 分钟】先指规划者，再沿四项任务读依赖。规划的产物是任务清单，不是最终答案。天气和目录可以独立查询，但筛选需要前面的结果，总价需要候选，最终建议需要经过验收。执行器可以是普通函数，也可以在子任务内部使用ReAct。规划与执行分开后，学员能先检查是否漏了费用或验收条件，再看执行进度。遇到失败时可以调整受影响步骤，保留仍有效的证据。下一页观察模型先生成了什么计划，再对照实际执行了哪些步骤。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)

## 13 · 演示 ⑤：规划执行 Plan-and-Execute

能力演进 · 1 分 40 秒

【1 分 40 秒】规划 Planning 把目标拆成有依赖和交付标准的任务，Plan-and-Execute 将规划与执行分开。出游计划是读取天气和场馆，再按晴雨筛选，计算门票加交通加餐饮，最后核对两大一小、半日、预算与不订票。天气查询和场馆目录可从同一需求独立启动；筛选依赖两者，总价依赖选中场馆，最终建议依赖筛选与成本检查。不能先写可行再补证据。默认300元雨天选城市博物馆210元；200元雨天无合适场馆，反馈回计划并停止或请用户调整条件，系统不能自行放宽条件。已经有效的天气和目录无需全部重查。执行器可以是普通函数或 ReAct 循环。离线模式为预写计划，真实模式先请求模型生成计划再执行；固定工作流能表达已知依赖，不必为了有计划而增加智能体。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)

## 14 · 概念 ⑥：Reflexion 把失败反馈变成改进动作

能力演进 · 1 分钟

【1 分钟】先说清初次失败草稿是教学主动注入的样本，不能声称模型必然犯这个错误。Reflexion把失败反馈整理为可执行的后续指令，例如先验证天气、费用必须包含餐费，再将它用于计划v2和新的执行。Reflexion不是重复问一次，也不是仅修改语气，更不是现场训练模型权重。这个简化演示强调反馈进入后续上下文，并由程序再次核对是否改好。没有新证据、同一错误反复出现或无可行候选时，应停止而非无限自我修改。

来源：[LangChain · Plan-and-Execute](https://blog.langchain.com/planning-agents/)；[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 15 · 演示 ⑥：Plan-and-Execute + Reflexion

能力演进 · 1 分 40 秒

【1 分 40 秒】反思 Reflection 将反馈转为下一次可执行的改进；Reflexion 用语言反馈影响后续尝试，更新任务上下文而非模型权重。本页是简化的预写机制演示，不是论文实验复现。初稿直接推荐湖畔公园但未引用天气或完整费用。评审指出缺天气依据与成本核算；默认雨天还违反 D01。反思应写成先核对 weather，再用 catalog 和 sum，引用 D01、D02 后重写并验收。默认雨天300元修订为城市博物馆210元；200或100元雨天应修订为无可行候选，不能把措辞改成可能适合就算通过。晴天若预算至少180元，公园可保留，但必须补上天气与费用证据。与上一页组成 Plan-and-Execute + Reflexion：计划v1执行后发现遗漏，反馈写成可执行的反思记录，生成计划v2，重跑受影响步骤并重新验收；已有效的天气证据继续保留。反思记录会作为后续尝试的上下文，不更新模型权重。反思本身可能出错，仍要外部检查；同一错误反复出现或没有新增证据时有限停止。程序审查规则覆盖本例。真实模式用明确标记的教学错误草稿触发模型反思，模型产生计划v2，再用真实工具结果验收。

来源：[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 16 · 概念 ⑦：多 Agent 按职责协作

能力演进 · 1 分钟

【1 分钟】先讲角色，不从模型数量讲起。天气角色和费用角色分别拥有职责与上下文，可以调用同一个底层模型。左图Supervisor集中分派和汇总，中图层次化增加组长层级，右图Swarm由当前角色按需要把任务和控制权交接给下一角色，不能随机无限转交。箭头表示任务或控制权的方向，结果通过消息交付。消息像一次交接单，写清发送方、接收方、任务、结果和来源；共享状态像共同维护的任务记录，保存预算、证据、计划版本和完成状态。主管模式也可以构成层次化中的一层；并行是执行方式，评审是反馈方式，可以组合在这些组织方式里。最后回到例子：天气和费用取交集，300元雨天可以得到博物馆210元。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 17 · 演示 ⑦：多智能体 Multi-Agent

能力演进 · 1 分 40 秒

【1 分 40 秒】Supervisor 由主管集中派发并汇总；层次化是在主管模式上增加团队层级，如总协调者管理出游组和预算组，组长再分派子任务；Swarm 由当前角色按专长动态交接给下一角色，并非随机群聊或无限互相调用。它们属于组织与控制方式；并行是执行方式，评审是质量反馈方式，可与三种模式组合。Agent 间通信使用 task_id、from、to、type、evidence_refs、plan_version 等明确字段；共享状态保存约束、证据、计划、草稿和完成状态。消息表示本次交付，状态记录当前共识。由协调器校验来源与版本、合并各角色结果，避免后写覆盖与旧版本污染。离线互动演示为 Supervisor 的通信和状态示意；真实模型窗口可切换 Supervisor、层次化和 Swarm，分别运行集中分派、组长分派和动态角色交接。多智能体 Multi-Agent 按职责组织协作。同一出游需求下，天气角色独立读取 weather 与 D01，提交天气和室内外约束；费用角色独立读取全部 catalog 与 D02，提交三个场馆的完整费用及预算判断，不等待天气结论。协调者拿到两份摘要后取交集：雨天排除湖畔公园，300元预算排除自然馆，留下城市博物馆210元。雨天200或100元无解；晴天200元可选公园180元。合并保留引用与限制，不能覆盖另一角色的证据。只有各自结果齐备才能交付，部分失败必须说明。界面把两份独立角色摘要放在同一事件展示，不代表后台真实并行；离线模式角色和摘要均由预写规则模拟；真实模式各角色分别调用同一个模型并使用独立上下文。七组概念与演示表示可组合的能力：角色内部仍可使用 RAG、工具、ReAct、规划或反思，并非历史先后或能力排名。这个已知小任务仍用固定工作流即可；后续有独立上下文、工具权限或专业责任时，才评估拆分收益。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 18 · 后半程：把能力组织成多 Agent 系统

多 Agent 流程概念 · 1 分 20 秒

【1 分 20 秒】上一页已经展示多 Agent 可以按职责协作。后半程不再重复能力清单，而是把问题收敛到系统怎样运行。先认识一条多 Agent 流程，再把它设计成角色和状态，随后比较协作模型，最后用同一张远程诊断工单验证。四段内容前后承接，案例中的字段会从概念页一直沿用到运行台。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 19 · 多 Agent 系统的六个组成部分

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】从系统视角看，多 Agent 不是多个聊天窗口。任务给出共同目标，角色承担不同职责，工具取得外部事实，状态保存当前进展，编排器决定执行顺序，约束负责限制权限和轮次。下一页把这六个组成部分放进一次完整运行，观察它们在什么时刻发生作用。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 20 · 一次运行的完整生命周期

多 Agent 流程概念 · 2 分 10 秒

【2 分 10 秒】一条运行以 run_id 贯穿。编排器先创建任务，再根据依赖分派角色；角色调用工具后把结果写回状态；必要分支完成后才汇合；审查决定交付、修订或转人工。这个生命周期是后面所有设计页的主线。下一页进一步区分两条同时发生但作用不同的路径：控制流和数据流。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 21 · 控制流与数据流

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】控制流描述执行顺序和控制权，数据流描述任务、证据和反馈怎样传递。两者必须分别设计：角色被调用不代表拿到了完整上下文，结果写回状态也不代表它能决定下一步。下一页用顺序、并行和反馈回路组合这两条路径。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 22 · 顺序、并行与反馈回路

多 Agent 流程概念 · 2 分钟

【2 分钟】顺序、并行和反馈回路是协作模型下面更基础的流程结构。先画依赖再选择结构，不能为了看起来像多 Agent 而强行并发。后面的 Supervisor、Parallel 和 Review 都只是对这些结构分配控制权的不同方式。下一页解释结构中的信息究竟放在哪里。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 23 · 消息、上下文、状态与记忆

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】上一页确定了流程结构，本页确定信息边界。消息是一次交付，上下文是当前角色看到的切片，状态是本次运行的共同记录，记忆才涉及跨步骤或跨运行保留。明确四者后，才能判断并行分支该读什么、写什么。下一页专门处理并行结束后的同步与合并。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 24 · 并行后的同步与合并

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】并行并不只是同时启动两个角色。系统还需要等待屏障和确定的合并规则。证据与知识可以独立读取，但报告必须等待双方；同一字段出现两个值时要保留时间、来源和适用条件。下一页完成生命周期的最后一部分：什么情况下结束，什么情况下交给人。

来源：[Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 25 · 停止、失败与人工介入

多 Agent 流程概念 · 1 分 50 秒

【1 分 50 秒】到这里，一次多 Agent 运行已经从创建走到出口。系统必须区分完成、转人工、受控停止和取消。人工介入表示由人复核或决定，不等于模型自动获得授权。下一章沿用这条生命周期，把抽象流程逐步设计成可实现的协作图。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 26 · 设计方法：从任务到可执行协作图

多 Agent 设计方法 · 1 分 30 秒

【1 分 30 秒】上一章回答系统怎样运行，本章回答怎样把一个业务任务设计成这样的系统。全章使用同一套九步方法：先定义结果，再分析任务依赖，随后划分角色、权限、消息和状态，最后用运行轨迹验证。下一页从第一步开始，先把最终交付和验收写清楚。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 27 · 第一步：定义目标与验收结果

多 Agent 设计方法 · 2 分钟

【2 分钟】先定义结果可以避免角色各自写出看似合理但无法汇合的文本。本案例只生成待专家复核的资料报告，不确认故障原因，也不控制真实车辆。验收标准决定后续需要哪些子任务。下一页把这些子任务画成依赖关系。

来源：[道通 Autel · 远程专家](https://www.auteltech.cn/cloud/3942.jhtml)

## 28 · 第二步：画出任务依赖

多 Agent 设计方法 · 2 分钟

【2 分钟】任务依赖先于角色数量。证据读取和知识检索可以从同一工单独立启动；资料适用性必须同时看到两类结果；报告草稿依赖汇合结果；审查可能产生回边。下一页依据这张依赖图判断哪些边界值得拆成角色。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 29 · 第三步：决定是否拆角色

多 Agent 设计方法 · 1 分 50 秒

【1 分 50 秒】依赖图说明任务怎么拆，角色边界还要看产物、上下文、权限和专业责任。仅仅希望得到不同意见，不足以证明要新增 Agent。角色是逻辑职责，不等于单独模型或服务。下一页把拆出的角色写成清晰接口。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 30 · 第四步：定义角色接口

多 Agent 设计方法 · 2 分钟

【2 分钟】角色接口要求输入、输出和禁止事项同时明确。协调者负责路由但不制造事实；证据角色读取本次记录；知识角色给出条件化资料；审查角色只按标准验收。下一页把这些边界落实到工具和权限。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 31 · 第五步：分配工具与权限

多 Agent 设计方法 · 2 分钟

【2 分钟】上一页的不得做什么必须转成运行时限制。工具适配器校验参数和访问范围，编排器限制角色、步数和预算，状态层限制可写字段。仅在提示词里写不要越权不能形成安全边界。下一页继续定义角色之间怎样交接。

## 32 · 第六步：设计消息契约

多 Agent 设计方法 · 2 分钟

【2 分钟】角色接口确定以后，消息契约负责可靠交接。run_id 和 task_id 解决归属，plan_version 防止旧结果覆盖新计划，status 和 missing 说明完整度，evidence_refs 让依据可查询。下一页把有效消息合并进共享状态。

## 33 · 第七步：设计共享状态

多 Agent 设计方法 · 2 分 10 秒

【2 分 10 秒】消息到达后，接收端按照字段所有权更新共享状态。事实不能被草稿覆盖，审查者不能修改证据，模型角色不能自行写入人工批准。并行写入同一字段时必须使用独立字段或明确 reducer。下一页处理状态更新中最容易出错的冲突、重试和版本。

来源：[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 34 · 第八步：处理冲突、重试与版本

多 Agent 设计方法 · 2 分 10 秒

【2 分 10 秒】共享状态需要可重复更新，也需要拒绝不合时宜的更新。去重解决重试，来源和时间解释冲突，计划版本隔离迟到结果，重试上限防止死循环。下一页用可观察轨迹检查前八步是否真的工作。

来源：[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)；[LangGraph · Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

## 35 · 第九步：用轨迹验证设计

多 Agent 设计方法 · 2 分钟

【2 分钟】设计完成后，不以一次成功回答作为验收。轨迹要能证明分派、工具调用、并行汇合、修订和停止都按契约发生。到这里，我们已经有了一张可执行协作图。下一章比较五种协作模型如何分配这张图中的控制权。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

## 36 · 协作模型：五种控制关系

协作模型与实现 · 1 分 40 秒

【1 分 40 秒】上一章已经确定任务依赖和角色接口，本章只改变控制权如何移动。五种协作模型不是互斥产品：Supervisor 可以在内部并行，生成结果可以再进入 Review，层次化系统的某一层也可以使用 Handoff。下一页从最容易建立统一出口的 Supervisor 开始。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 37 · Supervisor：集中分派与汇总

协作模型与实现 · 2 分 10 秒

【2 分 10 秒】Supervisor 每次收回控制权，根据最新状态选择下一位角色。专家角色不需要知道完整团队历史，只需要完成结构化子任务。协调者可以由规则或模型提出决策，但运行时仍校验白名单和预算。下一页保留同一任务图，把可独立的证据与知识分支改为并行。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)；[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)

## 38 · Parallel：独立执行与统一汇合

协作模型与实现 · 2 分钟

【2 分钟】Parallel 把前一页的两个独立子任务同时启动，但仍保留统一汇合和验收。一个分支成功不能掩盖另一个必要分支失败，逐步播放界面也不能证明后端并发。下一页讨论另一种控制方式：不回到中央，而由当前角色直接转交。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[Anthropic · Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

## 39 · Handoff、Swarm 与层次化

协作模型与实现 · 2 分钟

【2 分钟】Handoff 和 Swarm 都让控制权沿角色转移，层次化则增加协调层级。它们比集中式更依赖交接契约和无进展检测。本课综合案例不使用 Swarm 或多层团队，因为四个角色还不需要这种复杂度。下一页回到案例会实际使用的反馈模型 Review。

来源：[LangChain · Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)

## 40 · Review：独立评审与有限修订

协作模型与实现 · 2 分钟

【2 分钟】Review 不是再生成一遍答案，而是用明确标准检查草稿。反馈必须能触发补证据、删除越界表述或重新核对条件。修订次数受全局预算限制。现在五种控制关系已经建立，下一页把它们映射到开发框架，而不是重新讲一遍协作概念。

来源：[Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)；[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 41 · 从协作模型到开发框架

协作模型与实现 · 2 分 10 秒

【2 分 10 秒】框架选择发生在流程和角色设计之后。LangGraph 适合显式状态图；AutoGen 更强调消息和团队交互；MetaGPT 强调角色、动作和 SOP。框架不能替代领域工具、权限、验收或终止设计。本课只深入 LangGraph，其他框架保留为结构映射。下一页把前面的设计元素逐项对应到 StateGraph。

来源：[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)；[AutoGen · 官方仓库](https://github.com/microsoft/autogen)；[MetaGPT · 官方仓库](https://github.com/FoundationAgents/MetaGPT)

## 42 · LangGraph：把设计映射为状态图

协作模型与实现 · 2 分钟

【2 分钟】State 对应共享状态，Node 对应角色或确定性处理器，Edge 对应控制流，Reducer 负责并行结果合并，END 对应统一出口。代码片段只展示两个分支等待后进入审查。下一章不再增加新概念，而是沿用这张图进入同一份远程诊断工单。

来源：[LangGraph · 官方概览](https://docs.langchain.com/oss/python/langgraph/overview)；[LangGraph · Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)；[LangGraph · Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

## 43 · 案例起点：固定工作流基线

案例演示与复盘 · 2 分 20 秒

【2 分 20 秒】案例从固定工作流开始，沿用前面定义的输入、状态和验收标准。规则已经知道缺电压时调用 read_supplemental，因此不需要 Agent 决定下一步。先确认基线能够生成待人工复核的报告。后面三页只改变控制关系，证据、工具和验收口径保持不变。

来源：[道通 Autel · 远程专家](https://www.auteltech.cn/cloud/3942.jhtml)

## 44 · 案例演示 ①：Supervisor 重新分派

案例演示与复盘 · 2 分 40 秒

【2 分 40 秒】在同一工单上，Supervisor 把固定补读改成集中协调。先看初次分派，再停在协调者发现缺少 E-VOLTAGE 的事件；随后核对计划版本变为 v2，并把补充读取重新分派给证据角色。下一页仍使用同一工单，但观察两个独立分支怎样并行以及怎样合并冲突。

## 45 · 案例演示 ②：Parallel 冲突合并

案例演示与复盘 · 2 分 40 秒

【2 分 40 秒】本页把案例切换到 conflict 情景，角色和状态字段不变。证据与知识并行完成后，汇合节点看到 11.7 V 和较早缓存的 12.6 V；系统依据事件时间说明取舍，同时保留两份记录。下一页继续沿用缺失电压情景，观察问题在草稿之后才被审查者发现时会怎样回退。

## 46 · 案例演示 ③：Review 退回修订

案例演示与复盘 · 2 分 40 秒

【2 分 40 秒】与 Supervisor 页不同，这次协调者先形成草稿，审查者再发现缺少电压证据。反馈必须指出 E-VOLTAGE，而不是只给低分。系统补充证据后重写并重新审查，revision_rounds 记录实际修订次数。下一页把集中分派、并行取数和评审回路组合进同一条运行。

来源：[Reflexion · NeurIPS 2023](https://arxiv.org/abs/2303.11366)

## 47 · 综合运行：同一状态串起全部流程

案例演示与复盘 · 5 分 20 秒

【5 分 20 秒】综合运行台使用 integrated 模式和同一张 SYNTH-REMOTE-001 工单，把前面三种模型组合起来。先运行 normal，按时间线指出协调分派、并行证据与知识、汇合、草稿和审查。再运行 missing 或 conflict，观察 plan_version、observations 和 review 怎样连续变化。随后运行 tool_failure，确认系统保留错误和已有证据并进入 needs_human；最后运行 budget，确认 status=stopped 且没有伪造成功报告。界面优先看中文故事线、角色图、当前证据和修订前后对照，再展开事件 JSON 核对消息字段。运行台使用规则模拟角色决策和实际 LangGraph 编排，不连接真实车辆。服务不可用时使用预录轨迹，并明确说明是历史回放。完成演示后不要切换新主题，直接进入下一页，用刚才的同一条轨迹反推设计。

## 48 · 案例复盘：从运行轨迹回看设计

案例演示与复盘 · 3 分 10 秒

【3 分 10 秒】最后一页不再新增框架或接口，而是回到第 18 页的四个问题。请学员从刚才的 integrated 轨迹指出流程、角色、状态、模型和异常出口。练习把缺失电压改成等待客户端上传：保存 run_id、plan_version、observations、剩余预算和恢复节点；上传后检查请求版本与幂等键，再从待补充节点恢复。当前 Demo 没有实现跨进程暂停恢复，这一题只做设计。课程结论是先画清流程，再定义角色和状态，最后选择协作模型与框架。

来源：[LangGraph · Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)；[LangGraph · Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

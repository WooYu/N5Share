"""Official concept references for the imported collaboration slides."""

COLLABORATION_SOURCES = {
    'collab_multi': ('LangChain · 多 Agent', 'https://docs.langchain.com/oss/python/langchain/multi-agent'),
    'collab_patterns': ('Anthropic · Agent 模式', 'https://www.anthropic.com/engineering/building-effective-agents'),
    'collab_subagents': ('LangChain · 主管与子 Agent', 'https://docs.langchain.com/oss/python/langchain/multi-agent/subagents'),
    'collab_subgraphs': ('LangGraph · 子图', 'https://docs.langchain.com/oss/python/langgraph/use-subgraphs'),
    'collab_handoffs': ('LangChain · Agent 交接', 'https://docs.langchain.com/oss/python/langchain/multi-agent/handoffs'),
    'collab_swarm': ('AutoGen · Swarm 交接', 'https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/swarm.html'),
    'collab_teams': ('AutoGen · 团队协作', 'https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html'),
    'collab_chain': ('LangGraph · 顺序工作流', 'https://docs.langchain.com/oss/python/langgraph/workflows-agents#prompt-chaining'),
    'collab_structured': ('LangChain · 结构化输出', 'https://docs.langchain.com/oss/python/langchain/structured-output'),
    'collab_graph': ('LangGraph · 状态与路由', 'https://docs.langchain.com/oss/python/langgraph/graph-api'),
    'collab_interrupts': ('LangGraph · 人工审批', 'https://docs.langchain.com/oss/python/langgraph/interrupts'),
    'collab_persistence': ('LangGraph · 状态持久化', 'https://docs.langchain.com/oss/python/langgraph/persistence'),
    'collab_a2a': ('A2A · 协议规范', 'https://a2a-protocol.org/latest/specification/'),
    'collab_mcp': ('MCP · 架构', 'https://modelcontextprotocol.io/docs/learn/architecture'),
    'collab_mcp_server': ('MCP · 工具、资源与提示', 'https://modelcontextprotocol.io/docs/learn/server-concepts'),
    'collab_guardrails': ('LangChain · 安全防护', 'https://docs.langchain.com/oss/python/langchain/guardrails'),
    'collab_security': ('MCP · 安全实践', 'https://modelcontextprotocol.io/specification/draft/basic/security_best_practices'),
    'collab_fault': ('LangGraph · 重试与容错', 'https://docs.langchain.com/oss/python/langgraph/fault-tolerance'),
}

SECTION_REFERENCES = {
    'sec02': ('collab_multi', 'collab_patterns'),
    'sec03': ('collab_subagents', 'collab_multi'),
    'sec04': ('collab_subagents', 'collab_subgraphs'),
    'sec05': ('collab_handoffs', 'collab_swarm'),
    'sec06': ('collab_chain', 'collab_graph'),
    'sec07': ('collab_handoffs', 'collab_graph'),
    'sec08': ('collab_subagents', 'collab_interrupts'),
    'sec09': ('collab_a2a', 'collab_mcp'),
    'sec10': ('collab_guardrails', 'collab_security'),
    'sec11': ('collab_fault', 'collab_persistence'),
    'sec12': ('collab_multi', 'collab_a2a', 'collab_mcp'),
    'faq': ('collab_multi', 'collab_a2a', 'collab_mcp'),
}


def references_for(section_id, heading, page_index):
    """Narrow section references when a page focuses on a specific topic."""
    if section_id == 'sec02' and heading == '模式横向对比':
        return ['collab_multi', 'collab_fault']
    if section_id == 'sec07' and heading == '代码实现':
        return ['collab_graph', 'collab_structured']
    if section_id == 'sec08' and heading == '代码实现':
        return ['collab_interrupts', 'collab_persistence']
    if section_id == 'sec09':
        if heading == 'A2A核心概念':
            return ['collab_a2a']
        if heading == 'MCP三种能力':
            return ['collab_mcp_server', 'collab_mcp']
    if section_id == 'sec11':
        if heading == '何时使用多Agent：决策矩阵':
            return ['collab_multi', 'collab_patterns']
        if heading == '性能基准':
            return ['collab_multi']
    if section_id == 'faq' and page_index == 1:
        return ['collab_chain', 'collab_guardrails', 'collab_structured']
    return list(SECTION_REFERENCES[section_id])

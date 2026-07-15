'''
Author: shdjfkc shiwang6861@qq.com
Date: 2026-07-15 19:18:20
LastEditors: shdjfkc shiwang6861@qq.com
LastEditTime: 2026-07-15 19:23:43
FilePath: \langchain_demo\agent\graph.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
'''
Author: shdjfkc shiwang6861@qq.com
Date: 2026-07-15 19:18:20
LastEditors: shdjfkc shiwang6861@qq.com
LastEditTime: 2026-07-15 19:23:29
FilePath: \langchain_demo\agent\graph.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from langchain.agents import create_agent as _create_agent
from langgraph.checkpoint.memory import MemorySaver

from agent.guard import GuardMiddleware
from agent.tool import calculator, web_search, rag_search
from config.setting import llm

# 默认挂载的工具列表
DEFAULT_TOOLS = [calculator, web_search, rag_search]


def create_agent(use_llm_audit: bool = False, tools: list | None = None):
    """构建带记忆、审核和工具的 ReAct agent.

    Args:
        use_llm_audit: 启用 LLM 深度内容审核(更准确,更慢).
        tools: 自定义工具列表,默认使用 [calculator, web_search, rag_search].
    """
    guard = GuardMiddleware(use_llm_audit=use_llm_audit)
    return _create_agent(
        model=llm,
        tools=tools if tools is not None else DEFAULT_TOOLS,
        middleware=[guard],
        checkpointer=MemorySaver(),
    )

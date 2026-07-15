# region ═══════════════════════════════════════════════════════════════════
#  📘 agent/graph.py — Agent 工厂
# ═══════════════════════════════════════════════════════════════════════════
#  把 LLM + 内容审核 + 多轮记忆打包成一个可调用的 Agent。
#  当前为纯对话模式（无工具），后续可按需挂载。
# endregion

# region ── ① 导入依赖 ─────────────────────────────────────────────────────

# LangGraph 官方的 Agent 创建函数
from langchain.agents import create_agent as _create_agent

# MemorySaver：内存检查点，同一 thread_id 自动记住对话历史，实现多轮对话
from langgraph.checkpoint.memory import MemorySaver

# 内容审核中间件：用户输入和 AI 输出各拦截一次
from agent.guard import GuardMiddleware

# 预配置的 LLM 实例（DeepSeek）
from config.setting import llm
# endregion


# region ── ② Agent 工厂函数 ───────────────────────────────────────────────
def create_agent(use_llm_audit: bool = False):
    """构建带多轮记忆和内容审核的纯对话 Agent（无工具）。

    use_llm_audit: bool = False
      - False（默认）：只用关键词黑名单审核
      - True：额外调用 LLM 做深度语义审核（更安全但消耗 token）
    """
    guard = GuardMiddleware(use_llm_audit=use_llm_audit)
    return _create_agent(
        model=llm,
        tools=[],                    # 纯对话模式，暂不挂载工具
        middleware=[guard],          # 内容审核中间件
        checkpointer=MemorySaver(),  # 多轮对话记忆（进程内，重启丢失）
    )
# endregion

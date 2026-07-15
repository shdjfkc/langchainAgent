# region ═══════════════════════════════════════════════════════════════════
#  📘 agent/graph.py — Agent 工厂
# ═══════════════════════════════════════════════════════════════════════════
#  这个文件负责"拼装"一个 AI Agent.你没有直接跟大模型打交道,
#  而是调用这里的 create_agent(),它帮你把各个零件组装好,返回一个能用的 Agent.
#
#  一句话:把 LLM + 工具 + 审核 + 记忆打包成一个对象.
# endregion

# region ── ① 导入依赖 ─────────────────────────────────────────────────────

# LangGraph 官方提供的 Agent 创建函数,我们给它起了个别名 _create_agent
# 加下划线前缀表示"内部使用":外部只应该调我们自己的 create_agent,不直接碰这个
from langchain.agents import create_agent as _create_agent

# MemorySaver = "记忆保存器"
# LangGraph 内置的内存检查点机制:把每轮对话自动存到内存里,
# 下次同一个 thread_id 进来时自动加载历史消息,AI 就能"记住"之前聊过什么
from langgraph.checkpoint.memory import MemorySaver

# 内容审核中间件:在 AI 收到用户输入之前和输出回复之前各拦截一次
from agent.guard import GuardMiddleware

# 三个工具:安全计算器、网页搜索、本地知识库检索
from agent.tool import calculator, web_search, rag_search

# 预配置的 LLM 实例(来自 config/setting.py)_ 当前用的是 DeepSeek
from config.setting import llm
# endregion

# region ── ② 默认工具列表 ─────────────────────────────────────────────────
# 如果不传 tools 参数,Agent 默认挂这三个工具.
# 传了就用你传的(比如只想用 calculator,可以 create_agent(tools=[calculator]))
DEFAULT_TOOLS = [calculator, web_search, rag_search]
# endregion


# region ── ③ Agent 工厂函数 ───────────────────────────────────────────────
def create_agent(use_llm_audit: bool = False, tools: list | None = None):
    """构建带记忆、审核和工具的 ReAct agent.

    这个函数做的事(按顺序):
      1. 创建 GuardMiddleware _ 内容安全守门员
      2. 调用 LangGraph 的 create_agent() 把所有零件拼起来
      3. 返回一个可以 .invoke() 的 Agent 对象

    ReAct 是什么意思?
      Reasoning + Acting(推理 + 行动)
      AI 不是一口气生成答案,而是在"想"和"做"之间循环:
      思考"我需要搜索吗?" → 行动(调用工具) → 观察结果 → 继续思考 → ...
      直到它认为可以给出最终答案为止.

    你需要知道的参数:
      use_llm_audit: bool = False
        是否启用 LLM 深度内容审核.
        - False(默认):只做关键词匹配,快速免费
        - True:每条消息额外调一次 LLM 判断是否违规,更安全但更慢
        (每轮多消耗约 100-200 token,延迟约 1-2 秒)

      tools: list | None = None
        想给 Agent 挂哪些工具.不传就用 DEFAULT_TOOLS(三个全上).
        - [] 表示一个工具都不要(纯聊天模式)
        - [calculator] 表示只要计算器
        - 传 None(默认)就会用 DEFAULT_TOOLS

    返回值:
      一个 LangGraph StateGraph 对象,核心方法是 .invoke()
      调用 agent.invoke({"messages": [...]}, config=...) 就能跟 AI 对话

    示例:
      # 快速模式(只做关键词审核)
      agent = create_agent()
      agent.invoke({"messages": [HumanMessage("你好")]}, config=...)

      # 深度审核模式
      agent = create_agent(use_llm_audit=True)

      # 只要计算器,不要搜索
      agent = create_agent(tools=[calculator])
    """
    # 步骤 1:初始化审核中间件
    # GuardMiddleware 会在 agent/guard.py 里详述,这里你只需要知道:
    # 它像一个安检门_用户输入先过它,AI 输出也过它
    guard = GuardMiddleware(use_llm_audit=use_llm_audit)

    # 步骤 2:调用 LangGraph 的 create_agent() 完成拼装
    # 传入四个核心组件:
    #   model=llm            → 大模型(DeepSeek),负责"思考"
    #   tools=...            → 工具列表,负责"行动"
    #   middleware=[guard]   → 审核中间件,负责"安全"
    #   checkpointer=...     → 记忆保存器,负责"记住"
    #
    # tools 参数逻辑:
    #   - 如果调用者传了 tools(不是 None),就用调用者传的
    #   - 如果没传(None),就用 DEFAULT_TOOLS 三件套
    return _create_agent(
        model=llm,
        tools=tools if tools is not None else DEFAULT_TOOLS,
        middleware=[guard],
        checkpointer=MemorySaver(),
    )
# endregion

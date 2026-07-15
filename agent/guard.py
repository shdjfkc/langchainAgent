# region ═══════════════════════════════════════════════════════════════════
#  📘 agent/guard.py — 内容审核中间件
# ═══════════════════════════════════════════════════════════════════════════
#  这个文件实现了 Agent 的"安检门".每条用户输入和 AI 输出都会经过这里.
#
#  审核分两级:
#    第一级:关键词快筛(免费,零延迟)→ 命中直接拦截
#    第二级:LLM 深度审核(消耗 token,约 1-2 秒)→ 可选开启
#
#  工作流程:
#    用户输入 → [关键词检查] → [可选: LLM 审核] → AI 思考 → [关键词检查] → 输出给用户
#                ↑ 违规直接拒绝                                  ↑ 违规直接拦截
# endregion

# region ── ① 导入依赖 ─────────────────────────────────────────────────────

# AgentMiddleware:LangChain 定义的中间件基类
# 继承它并重写 wrap_model_call() 就能在 Agent 管道里插入自定义逻辑
from langchain.agents.middleware import AgentMiddleware

# ModelRequest  / ModelResponse:中间件管道的请求和响应类型
# 你的代码不需要直接创建它们,但看懂签名需要知道这两个类型
from langchain.agents.middleware.types import ModelRequest, ModelResponse

# AIMessage / HumanMessage:LangChain 的消息类型
# AIMessage = AI 生成的消息,HumanMessage = 用户输入的消息
from langchain_core.messages import AIMessage, HumanMessage
# endregion


# region ── ② GuardMiddleware 类定义 ───────────────────────────────────────
class GuardMiddleware(AgentMiddleware):
    """内容审核拦截器 _ 预检用户输入 + 复检模型输出.

    继承自 LangChain 的 AgentMiddleware,重写 wrap_model_call() 方法.
    这个方法的签名是固定的(LangChain 框架规定的),你只需要关心:
      - request.state["messages"]:当前的对话历史
      - handler(request):调用它才会继续往下执行(让 Agent 真正干活)
      - return:必须返回 ModelResponse
    """

    # region ── ②-a 类属性 ────────────────────────────────────────────────

    # === 关键词黑名单 ===
    # 第一道防线:如果用户输入或 AI 输出包含这些词,直接拒绝,不经过 LLM.
    # 只收录中文明确违规词,英文词容易误伤(比如 "kill" 可能是"kill process"),
    # 英文场景交给第二级的 LLM 审核处理.
    BLOCKED_KEYWORDS: list[str] = [
        "制作炸弹", "制作毒品", "贩卖枪支", "儿童色情",
        "自杀方法", "黑客入侵", "木马病毒", "刷单诈骗",
    ]

    # === LLM 审核提示词 ===
    # 第二道防线:把待审核的内容 + 这段提示词一起发给 LLM,
    # 让 LLM 判断是否违规.只有开启 use_llm_audit 时才走这一步.
    # 提示词末尾强调"只回答安全或违规"是为了让判断结果可解析:
    #   以"安全"开头 → 放行
    #   以"违规"开头 → 拦截
    AUDIT_PROMPT = """你是一个内容安全审核员.请判断以下内容是否包含违规信息.

违规类型包括但不限于:
- 暴力、恐怖主义内容
- 色情、低俗内容
- 赌博、毒品相关内容
- 恶意代码、黑客攻击教程
- 诈骗、钓鱼信息
- 歧视、仇恨言论

请只回答 "安全" 或 "违规: <原因>".不要输出其他内容."""
    # endregion

    # region ── ②-b 构造函数 ──────────────────────────────────────────────
    def __init__(self, use_llm_audit: bool = False):
        """初始化审核中间件.

        use_llm_audit: bool = False
          - False(默认):只用关键词黑名单,免费零延迟
          - True:关键词命中后,再调一次 LLM 做深度语义审核
            (每轮多消耗约 100-200 token,延迟约 1-2 秒)
        """
        # super().__init__() 调用父类 AgentMiddleware 的构造函数
        # 不做这一步 AgentMiddleware 内部状态不会初始化,后续调用会报错
        super().__init__()
        self.use_llm_audit = use_llm_audit
    # endregion

    # region ── ②-c 核心拦截方法(框架自动调用)───────────────────────────
    def wrap_model_call(self, request: ModelRequest, handler) -> ModelResponse:
        """Agent 管道的"安检入口",LangChain 框架在每次模型调用前后自动调用.

        这个方法做的事情分三步:
          第一步:预检 _ 拿最新用户消息做内容审核,违规就直接返回拒绝消息
          第二步:放行 _ 调用 handler(request) 让 Agent 正常执行
          第三步:复检 _ 拿 AI 生成的回复再做一次审核,违规就替换成拦截消息

        参数:
          request: ModelRequest
            框架传进来的请求对象,核心字段是:
              - request.state:对话状态字典,里面的 "messages" 是完整的消息历史
          handler: Callable
            一个"继续执行"的回调函数.调用 handler(request) 才会让 Agent 真正干活.
            不能漏掉这步,否则 Agent 永远不会响应.

        返回值:
          ModelResponse: 必须返回这个类型,LangChain 框架会读取其中的 result 作为最终输出.
        """
        # 读取当前对话状态
        state = request.state
        # state 是一个字典,"messages" 键存着对话历史(列表,HumanMessage/AIMessage 交替)
        messages = state.get("messages", [])

        # ==================================================================
        #  第一步:预检 _ 审查最新用户输入
        # ==================================================================
        # 从消息历史里找出最后一条用户消息(也就是用户刚刚说的那句话)
        last_user_msg = self._last_user_message(messages)
        # 如果找到了用户消息,且内容违规
        if last_user_msg and self._is_violation(last_user_msg.content):
            # 直接返回拒绝消息,不调用 handler,Agent 不会执行
            # 这意味着 LLM 根本没看到这条违规输入,省了一次 API 调用
            return ModelResponse(
                result=[AIMessage(content="⚠️ 您的输入包含违规内容,已被拦截.请修改后重试.")]
            )

        # ==================================================================
        #  第二步:放行 _ 让 Agent 正常执行
        # ==================================================================
        # handler(request) 内部会:
        #   1. 把消息发给 LLM
        #   2. LLM 可能会决定调用工具(搜索/计算/查知识库)
        #   3. 工具结果返回给 LLM
        #   4. LLM 生成最终回复
        #   5. 把结果包装成 ModelResponse
        response = handler(request)

        # ==================================================================
        #  第三步:复检 _ 审查 AI 输出
        # ==================================================================
        # response.result 是 AI 生成的消息列表(通常只有一条 AIMessage)
        if response.result:
            # 取第一条(也是唯一一条)AI 消息的文本内容
            ai_content = response.result[0].content
            # isinstance 检查确保内容是字符串(有些情况下可能是其他类型,比如工具调用)
            if isinstance(ai_content, str) and self._is_violation(ai_content):
                # AI 输出了违规内容,替换成拦截提示
                return ModelResponse(
                    result=[AIMessage(content="⚠️ 回答包含不当内容,已被拦截.")]
                )

        # 两关都过了,返回 AI 的正常回复
        return response
    # endregion

    # region ── ②-d 内部辅助方法 ──────────────────────────────────────────

    def _last_user_message(self, messages: list) -> HumanMessage | None:
        """从消息列表中取出最后一条用户消息.

        从后往前遍历消息列表(reversed),找到第一个 HumanMessage 就返回.
        因为消息列表是 [Human, AI, Human, AI, ...] 交错排列的,
        从尾部倒着找能最快定位到"用户刚刚说的那句话".

        返回 None 表示消息列表里没有用户消息(比如刚初始化还没对话).
        """
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg
        return None

    def _is_violation(self, text: str) -> bool:
        """两级内容审核:关键词快筛 + 可选 LLM 深度审核.

        审核顺序是固定的(先快后慢):
          1. 关键词匹配 _ 遍历 BLOCKED_KEYWORDS 黑名单
             命中 → 立即返回 True(违规),不走第二步
          2. LLM 深度审核 _ 仅当 use_llm_audit=True 时执行
             把文本发给 LLM,用 AUDIT_PROMPT 做语义判断

        这种"先便宜后贵"的策略很重要:绝大多数违规是明显的关键词,
        关键词就能拦住 90% 的问题,省掉 LLM 审核的 token 消耗.

        返回 True 表示违规,False 表示安全.
        """
        # 统一转小写,避免大小写绕过(比如 "Suicide" vs "suicide")
        text_lower = text.lower()

        # --- 第一级:关键词快筛 ---
        # 把每个黑名单词转小写后在文本里搜索
        # Python 的 in 操作符做子串匹配,比如 "木马病毒" in "如何编写木马病毒程序" → True
        for kw in self.BLOCKED_KEYWORDS:
            if kw.lower() in text_lower:
                return True  # 命中黑名单,直接返回违规

        # --- 第二级:LLM 深度审核 ---
        # 只有用户启动时加了 --audit 参数才会走到这里
        # 因为 LLM 调用有成本(token 消耗)和延迟(网络请求)
        if self.use_llm_audit:
            return self._llm_audit(text)

        # 两级都没命中 → 内容安全
        return False

    def _llm_audit(self, text: str) -> bool:
        """调用 LLM 对单条文本做深度语义审核.

        这里会发起一次真实的 LLM API 调用:
          1. 把 AUDIT_PROMPT(审核员人设)作为第一条消息
          2. 把待审核文本作为第二条消息
          3. LLM 返回 "安全" 或 "违规: <原因>"
          4. 我们检查是否以"违规"开头来判断

        返回 True 表示违规,False 表示安全.

        为什么 import 写在这里而不是文件顶部?
          这是延迟导入:只在真正需要调 LLM 时才 import.
          如果用户没用 --audit 模式,llm 对象永远不会被加载,
          节省了导入 DeepSeek 相关库的开销.
        """
        from config.setting import llm

        # llm.invoke() 是 LangChain 统一的 LLM 调用接口
        # 传入一个消息列表,返回一个 AIMessage 对象
        # 第一条消息 (system prompt) 设定 LLM 的人设:"你是审核员"
        # 第二条消息 (user prompt) 是待审核的实际内容
        result = llm.invoke(
            [
                HumanMessage(content=self.AUDIT_PROMPT),
                HumanMessage(content=f"待审核内容:\n{text}"),
            ]
        )
        # result.content 是 LLM 返回的文本,比如:
        #   "安全"          → .startswith("违规") = False → 放行
        #   "违规: 包含暴力内容" → .startswith("违规") = True  → 拦截
        return result.content.strip().startswith("违规")
    # endregion
# endregion

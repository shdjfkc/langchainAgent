from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage


class GuardMiddleware(AgentMiddleware):
    """内容审核拦截器 — 预检用户输入 + 复检模型输出."""

    # 违规关键词 — 仅中文明确违规词(英文词太容易误伤,交给 LLM 审核)
    BLOCKED_KEYWORDS: list[str] = [
        "制作炸弹", "制作毒品", "贩卖枪支", "儿童色情",
        "自杀方法", "黑客入侵", "木马病毒", "刷单诈骗",
    ]

    # 系统提示词 — 用于 LLM 深度审核
    AUDIT_PROMPT = """你是一个内容安全审核员.请判断以下内容是否包含违规信息.

违规类型包括但不限于:
- 暴力、恐怖主义内容
- 色情、低俗内容
- 赌博、毒品相关内容
- 恶意代码、黑客攻击教程
- 诈骗、钓鱼信息
- 歧视、仇恨言论

请只回答 "安全" 或 "违规: <原因>".不要输出其他内容."""

    def __init__(self, use_llm_audit: bool = False):
        """use_llm_audit=True 会额外调用 LLM 深度审核,更准确但更慢."""
        super().__init__()
        self.use_llm_audit = use_llm_audit

    def wrap_model_call(self, request, handler):
        state = request.state
        messages = state.get("messages", [])

        # 1. 预检:审查最新用户输入
        last_user_msg = self._last_user_message(messages)
        if last_user_msg and self._is_violation(last_user_msg.content):
            return ModelResponse(
                result=[AIMessage(content="⚠️ 您的输入包含违规内容,已被拦截.请修改后重试.")]
            )

        # 2. 执行模型
        response = handler(request)

        # 3. 复检:审查模型输出
        if response.result:
            ai_content = response.result[0].content
            if isinstance(ai_content, str) and self._is_violation(ai_content):
                return ModelResponse(
                    result=[AIMessage(content="⚠️ 回答包含不当内容,已被拦截.")]
                )

        return response

    # ── 内部方法 ──────────────────────────────────────────

    def _last_user_message(self, messages: list) -> HumanMessage | None:
        """取消息列表中最后一条用户消息."""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg
        return None

    def _is_violation(self, text: str) -> bool:
        """两级审核:关键词快筛 + 可选 LLM 深度审核."""
        text_lower = text.lower()

        # 关键词快筛
        for kw in self.BLOCKED_KEYWORDS:
            if kw.lower() in text_lower:
                return True

        # LLM 深度审核
        if self.use_llm_audit:
            return self._llm_audit(text)

        return False

    def _llm_audit(self, text: str) -> bool:
        """调用 LLM 进行深度内容审核."""
        from config.setting import llm

        result = llm.invoke(
            [
                HumanMessage(content=self.AUDIT_PROMPT),
                HumanMessage(content=f"待审核内容:\n{text}"),
            ]
        )
        return result.content.strip().startswith("违规")

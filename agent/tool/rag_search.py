"""知识库检索工具 — 基于本地向量库的 RAG 查询。"""

from langchain_core.tools import tool

_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        from agent.rag.retriever import get_retriever
        _retriever = get_retriever()
    return _retriever


@tool
def rag_search(query: str) -> str:
    """在本地知识库中搜索相关文档片段。适用于需要参考内部资料的问题。"""
    try:
        r = _get_retriever()
        docs = r.invoke(query)
        if not docs:
            return "知识库中未找到相关内容。"
        parts = []
        for i, doc in enumerate(docs[:5], 1):
            src = doc.metadata.get("source", "未知")
            parts.append(f"[{i}] ({src})\n{doc.page_content}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"知识库检索失败: {e}"

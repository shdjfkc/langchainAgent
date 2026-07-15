"""DuckDuckGo 网页搜索工具 — 通过 langchain_community 封装。"""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool


_ddg = DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """搜索互联网获取最新信息。返回相关网页摘要。"""
    try:
        return _ddg.invoke(query)
    except Exception as e:
        return f"搜索失败: {e}"

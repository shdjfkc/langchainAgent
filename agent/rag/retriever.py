"""向量检索引擎 — FAISS + 本地 embedding，懒加载单例。"""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config.setting import ROOT

INDEX_DIR = ROOT / "knowledge_base" / ".faiss_index"

# 轻量中文 embedding 模型，首次使用自动下载 (~400MB)
_EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"


_retriever = None


def _build_index() -> FAISS:
    from agent.rag.loader import load_documents

    docs = load_documents()
    embeddings = HuggingFaceEmbeddings(model_name=_EMBEDDING_MODEL)
    if not docs:
        raise RuntimeError("knowledge_base/ 中没有文档，无法构建索引")
    index = FAISS.from_documents(docs, embeddings)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index.save_local(str(INDEX_DIR))
    return index


def get_retriever():
    """获取 retriever 单例。有缓存索引用缓存，否则从文档构建。"""
    global _retriever

    if _retriever is not None:
        return _retriever

    embeddings = HuggingFaceEmbeddings(model_name=_EMBEDDING_MODEL)

    if (INDEX_DIR / "index.faiss").exists():
        index = FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)
    else:
        index = _build_index()

    _retriever = index.as_retriever(search_kwargs={"k": 5})
    return _retriever

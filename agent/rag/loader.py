"""文档加载器 — 加载 knowledge_base/ 下的 txt/md/pdf 文件。"""

from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.setting import ROOT

KB_DIR = ROOT / "knowledge_base"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def _load_file(path: Path) -> list:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")
    return loader.load()


def load_documents() -> list:
    """加载 knowledge_base/ 下所有支持的文档并切分。"""
    docs = []
    for path in KB_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in (".txt", ".md", ".pdf"):
            docs.extend(_load_file(path))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", ".", " ", ""],
    )
    return splitter.split_documents(docs) if docs else []

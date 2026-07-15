import os
from pathlib import Path
from types import SimpleNamespace

import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# 加载 .env 到环境变量
load_dotenv()

# 加载 config.yaml
ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "config.yaml", encoding="utf-8") as f:
    config: dict = yaml.safe_load(f)

# 注入 .env 中的敏感信息
config["db"]["user"] = os.getenv("DB_USER")
config["db"]["password"] = os.getenv("DB_PASSWORD")
config["llm"]["api_key"] = os.getenv("DEEPSEEK_API_KEY")


def _dict_to_ns(d: dict) -> SimpleNamespace:
    """递归将 dict 转为 SimpleNamespace,支持 dot 访问."""
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = _dict_to_ns(v)
    return SimpleNamespace(**d)


setting = _dict_to_ns(config)

# 预配置的 LLM 实例,main.py 直接 import 用
llm = ChatOpenAI(
    api_key=setting.llm.api_key,
    base_url=setting.llm.base_url,
    model=setting.llm.model,
    temperature=setting.llm.temperature,
    max_tokens=setting.llm.max_tokens,
)

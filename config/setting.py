# region ═══════════════════════════════════════════════════════════════════
#  📘 config/setting.py — 全局配置中心
# ═══════════════════════════════════════════════════════════════════════════
#  整个项目的配置都从这里来.它做了三件事:
#    1. 读 config.yaml(数据库地址、模型参数、端口等)
#    2. 读 .env(密钥、密码等敏感信息)
#    3. 把两者合并成一个 setting 对象 + 创建一个现成的 llm 实例
#
#  config.yaml 和 .env 分离的原因:
#    - config.yaml:不敏感、可提交 git,团队共享
#    - .env:密钥密码,永不提交 git(.gitignore 已排除)
# endregion

# region ── ① 导入依赖 ─────────────────────────────────────────────────────

import os                          # 读写环境变量(os.getenv)
from pathlib import Path            # 面向对象的文件路径(比字符串拼接更安全)
from types import SimpleNamespace   # 把字典变对象,支持 config.db.host 而不是 config["db"]["host"]

import yaml                         # 解析 YAML 配置文件
from dotenv import load_dotenv      # 把 .env 文件的内容加载到环境变量里
from langchain_openai import ChatOpenAI  # LangChain 对 OpenAI API 的封装(DeepSeek 兼容此接口)
# endregion

# region ── ② 加载 .env 文件 ───────────────────────────────────────────────
# load_dotenv() 会找到项目根目录下的 .env 文件,把里面的 KEY=VALUE 写入系统环境变量.
# 之后就可以用 os.getenv("KEY") 读取了.
# 放在文件最前面是为了确保后续代码(包括 config.yaml 的处理)都能读到环境变量.
load_dotenv()
# endregion

# region ── ③ 加载 config.yaml ─────────────────────────────────────────────
# __file__ = 当前文件的绝对路径 = D:\...\config\setting.py
# .resolve() 确保是绝对路径
# .parents[1] 往上跳两级:setting.py → config/ → 项目根目录
ROOT = Path(__file__).resolve().parents[1]

# 用 UTF-8 编码打开 config.yaml,读取所有配置到 config 字典
with open(ROOT / "config.yaml", encoding="utf-8") as f:
    config: dict = yaml.safe_load(f)  # safe_load 比 load 安全,不会执行任意 Python 代码
# endregion

# region ── ④ 注入 .env 敏感信息 ───────────────────────────────────────────
# config.yaml 只有配置结构,真正的密码/密钥写在 .env 里.
# 这里把 .env 的值"注入"到对应的 config 字段中,完成合并.

# 数据库账号密码(不提交 git)
config["db"]["user"] = os.getenv("DB_USER")          # .env 里的 DB_USER=root
config["db"]["password"] = os.getenv("DB_PASSWORD")  # .env 里的 DB_PASSWORD=root

# DeepSeek API 密钥(不提交 git)
config["llm"]["api_key"] = os.getenv("DEEPSEEK_API_KEY")
# endregion

# region ── ⑤ 字典 → 对象转换 ─────────────────────────────────────────────
def _dict_to_ns(d: dict) -> SimpleNamespace:
    """递归将嵌套字典转为 SimpleNamespace,支持点号访问.

    为什么需要这个转换?
      字典访问:setting["db"]["host"]  _ 写起来啰嗦,IDE 不补全
      对象访问:setting.db.host         _ 简洁,IDE 有自动补全提示

    递归是什么意思?
      如果字典的值本身也是字典(比如 config["db"]),
      就递归调用自己把它也转成 SimpleNamespace,嵌套多少层都能转.

    示例:
      输入:{"db": {"host": "127.0.0.1", "port": 3306}}
      输出:一个对象,可以用 setting.db.host 和 setting.db.port 访问

    这个函数名前加 _ 表示"模块内部使用",外部代码不应该直接调用它.
    """
    # 遍历字典的每一项
    for k, v in d.items():
        # 如果值本身也是个字典,递归转换它
        # isinstance 判断类型:v 是不是 dict?
        if isinstance(v, dict):
            d[k] = _dict_to_ns(v)
    # SimpleNamespace(**d) 把字典的键值对"展开"成对象的属性
    # 比如 SimpleNamespace(host="127.0.0.1", port=3306) → 对象.host、对象.port
    return SimpleNamespace(**d)


# 全局单例 _ 整个项目 import 这一个 setting 就够了
# 它是 config.yaml + .env 合并后的完整配置,支持点号访问
setting = _dict_to_ns(config)
# endregion

# region ── ⑥ 创建 LLM 实例 ────────────────────────────────────────────────
# 基于刚刚读到的配置,创建一个现成的 LLM 实例.
# 其他模块只需要 `from config.setting import llm`,不用重复配置.

# DeepSeek 兼容 OpenAI 的 API 格式,所以用 ChatOpenAI 类即可.
# base_url 指向 DeepSeek 的地址而不是 OpenAI 的,这是关键.
llm = ChatOpenAI(
    api_key=setting.llm.api_key,      # 从 .env 读的密钥
    base_url=setting.llm.base_url,    # "https://api.deepseek.com/v1"
    model=setting.llm.model,          # "deepseek-chat"
    temperature=setting.llm.temperature,  # 0.7,越高回答越随机,越低越确定
    max_tokens=setting.llm.max_tokens,    # 2048,单次回复最长长度
)
# endregion

# region ═══════════════════════════════════════════════════════════════════
#  📘 文件头:这是什么 · 怎么跑 · 整体流程
# ═══════════════════════════════════════════════════════════════════════════
#  这是整个项目的启动文件.直接运行 `python main.py` 就能在终端里跟 AI 对话.
#
#  一句话解释整个流程:
#    用户打字 → 安全检查 → AI 思考(可能会调工具) → 输出检查 → 显示回复 → 存记忆 → 循环
#
#  运行方式:
#    python main.py           普通模式(关键词审核,免费快速)
#    python main.py --audit   LLM 深度审核模式(更安全但消耗 token,约慢 1-2 秒)
#
#  特殊命令(在对话中输入):
#    /exit   退出程序
#    /clear  清空对话历史,相当于"换个新话题"
# endregion

# region ── ① 导入依赖 ─────────────────────────────────────────────────────
#  把其他文件写好的功能"拿过来用",Python 里叫 import(导入)

import sys              # sys = system,用来读取命令行参数(比如 --audit)、控制终端输出
import uuid             # uuid = 通用唯一标识,用来生成随机 ID,比如每次 /clear 时的新会话 ID

# langchain_core 是 LangChain 框架的核心库
# HumanMessage = "人类消息",代表你在对话框里输入的每一句话
from langchain_core.messages import HumanMessage

# 从我们自己的 agent/graph.py 文件里导入创建 Agent 的函数
# create_agent 就像一个"工厂函数"_调用它,返回一个配置好的 AI 助手
from agent.graph import create_agent
# endregion

# region ── ② Windows 终端中文兼容 ─────────────────────────────────────────
#  Windows 的命令行默认编码有时候不是 UTF-8,导致中文乱码或报错.
#  这行代码强制把标准输出(stdout)的编码改成 UTF-8,确保中文正常显示.
#  如果你的系统已经是 UTF-8,这行不会产生任何负面影响.
sys.stdout.reconfigure(encoding="utf-8")
# endregion


# region ── ③ 主函数 main() 定义 ───────────────────────────────────────────
#  Python 程序的入口习惯上叫 main().下面的 if __name__ == "__main__" 会调用它.
#  把所有逻辑放在 main() 里而不是直接写在外面,是一个好习惯_
#  这样别的文件导入这个文件时不会自动执行代码.

def main():
    """
    程序的入口函数:初始化 Agent → 进入对话循环 → 处理每条用户输入.
    """

    # region ── 步骤 1:解析命令行参数 ──────────────────────────────────────
    # sys.argv 是一个列表,包含了运行命令的所有参数.
    # 比如你输入:python main.py --audit
    #   sys.argv = ["main.py", "--audit"]
    # 这行就是在问:参数列表里有 "--audit" 这个字符串吗?
    #   有 → use_llm_audit = True(开启 LLM 深度审核)
    #   没有 → use_llm_audit = False(只用关键词快筛)
    use_llm_audit = "--audit" in sys.argv
    # endregion

    # region ── 步骤 2:创建 Agent 实例 ─────────────────────────────────────
    # create_agent() 会做这些事情(去看 agent/graph.py 了解细节):
    #   1. 创建 GuardMiddleware _ 内容审核中间件
    #   2. 连接到 DeepSeek 大模型
    #   3. 挂载 MemorySaver _ 自动记住对话历史
    #   4. 返回一个配置好的 LangGraph Agent 图
    agent = create_agent(use_llm_audit=use_llm_audit)
    # endregion

    # region ── 步骤 3:配置会话参数 ────────────────────────────────────────
    # config 是传给 Agent 的"元数据",目前只有一个作用:
    #   thread_id = "default"  →  同一 thread_id 共享对话历史
    #
    # 举例:
    #   如果你和两个人聊天,给每人分配不同的 thread_id,他们的对话就互不干扰.
    #   当前写死为 "default" 意味着整个程序只有一个会话.
    #
    # 格式是 LangGraph 规定的嵌套字典:
    #   {"configurable": {"thread_id": "xxx"}}
    # configurable 是 LangGraph 的关键词,表示"可配置项"
    config = {"configurable": {"thread_id": "default"}}
    # endregion

    # region ── 步骤 4:打印启动信息 ────────────────────────────────────────
    # 根据审核模式显示不同提示,让用户知道他当前用的是哪种安全策略
    mode = "LLM+关键词审核" if use_llm_audit else "关键词审核"
    print(f"Agent 已启动 ({mode})")
    print("输入 /exit 退出, /clear 清空历史\n")
    # endregion

    # region ── 步骤 5:对话主循环(程序的核心!)───────────────────────────
    # while True 意味着"一直循环,直到遇到 break 才退出".
    # 每次循环 = 一轮对话:你输入一句话 → AI 回复一句话
    while True:

        # --- 5a: 读取用户输入 ---
        # input("You: ") 会在屏幕上显示 "You: ",然后等待你打字,按回车后把内容存到 user_input
        # .strip() 去掉首尾空格(防止你不小心多打空格导致判断失败)
        # try/except 是异常处理:如果用户按 Ctrl+C 或 Ctrl+D,不会报错而是优雅退出
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            # EOFError: Unix 下按 Ctrl+D 触发(表示输入结束)
            # KeyboardInterrupt: 按 Ctrl+C 触发(中断信号)
            # 两都会直接退出循环,程序结束
            break

        # --- 5b: 空输入处理 ---
        # 如果用户什么都没输入直接按回车,跳过本轮循环,回到 while True 重新等待
        # continue = "本轮到此结束,开始下一轮循环"
        if not user_input:
            continue

        # --- 5c: 特殊命令 ---
        # 用户输入 "/exit" → break 跳出循环,程序结束
        if user_input == "/exit":
            break

        # 用户输入 "/clear" → 生成一个新的 thread_id 替换旧的
        # uuid.uuid4() 生成一个随机 UUID,比如 "a1b2c3d4e5f6g7h8"
        # .hex[:8] 取其十六进制字符串的前 8 位,既够用又短(碰撞概率极低)
        # 换了 thread_id 后,AI 就"忘记"之前的对话了,因为新 ID 查不到旧记录
        if user_input == "/clear":
            config["configurable"]["thread_id"] = uuid.uuid4().hex[:8]
            print("[历史已清空]")
            continue  # 跳过本轮(/clear 不是对话,不需要 AI 回复)

        # --- 5d: 调用 Agent(核心中的核心) ---
        # agent.invoke() 把用户消息送给 Agent,Agent 内部会:
        #   1. GuardMiddleware 预检(关键词 + 可选 LLM 审核)_ 拦截违规输入
        #   2. 大模型思考(可能调用工具:搜索/计算/查知识库)
        #   3. GuardMiddleware 复检 _ 拦截违规输出
        #   4. MemorySaver 自动保存本轮对话到内存
        #   5. 返回完整的消息列表(包含所有历史消息 + 新回复)
        #
        # 参数解释:
        #   第一个参数 {"messages": [...]} 是本轮新增的消息
        #     HumanMessage(content=user_input) 把用户输入的纯文本包装成"人类消息"对象
        #   第二个参数 config 告诉 Agent 用哪个 thread_id 存取历史
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )

        # --- 5e: 打印 AI 回复 ---
        # result["messages"] 是完整的消息历史列表(人类消息 + AI 消息交错排列)
        # [-1] 表示取列表最后一个元素 = 最新一条消息 = AI 刚刚生成的回复
        # .content 从 AI 消息对象里取出纯文本内容
        # \n 是换行符,让下一次 "You: " 前空一行,阅读更清晰
        print(f"Agent: {result['messages'][-1].content}\n")
    # endregion
# endregion


# region ── ④ Python 程序入口:__name__ 魔法变量 ────────────────────────────
#  __name__ 是 Python 的内置变量,表示"当前模块的名字".
#
#  当你直接运行 `python main.py` 时:
#    Python 会把 main.py 的 __name__ 设为 "__main__"
#    于是这个 if 条件成立 → 执行 main() → 程序启动
#
#  当别的文件 import main 时(比如测试文件):
#    此时 __name__ = "main"(不是 "__main__")
#    条件不成立 → main() 不会自动执行
#    这样别人就可以引用你的函数而不会意外启动对话循环
#
#  这是一种 Python 最佳实践,几乎每个 Python 脚本末尾都有这行.
if __name__ == "__main__":
    main()
# endregion

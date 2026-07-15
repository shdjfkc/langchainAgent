import sys
import uuid

from langchain_core.messages import HumanMessage

from agent.graph import create_agent

sys.stdout.reconfigure(encoding="utf-8")


def main():
    use_llm_audit = "--audit" in sys.argv
    agent = create_agent(use_llm_audit=use_llm_audit)
    config = {"configurable": {"thread_id": "default"}}

    mode = "LLM+关键词审核" if use_llm_audit else "关键词审核"
    print(f"Agent 已启动 ({mode})")
    print("输入 /exit 退出, /clear 清空历史\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue
        if user_input == "/exit":
            break
        if user_input == "/clear":
            config["configurable"]["thread_id"] = uuid.uuid4().hex[:8]
            print("[历史已清空]")
            continue

        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
        )
        print(f"Agent: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    main()

# 项目状态

## ✅ 已完成

- **LLM 配置**: DeepSeek API，config.yaml + .env 分离
- **Agent 骨架**: LangGraph 纯对话 Agent + MemorySaver（多轮记忆）
- **内容审核**: GuardMiddleware，关键词快筛 + 可选 LLM 深度审核

## ⬜ 待实现（骨架已就位，代码已清空）

| # | 模块 | 说明 |
|---|------|------|
| 1 | 工具系统 | calculator / web_search / rag_search 待重新实现 |
| 2 | 记忆三层存储 | Redis(热) / MySQL(温) / Disk(冷) 待重新实现 |
| 3 | RAG 检索 | 文档加载 → Embedding → FAISS 待重新实现 |

## 🟢 当前可运行

```bash
python main.py          # 关键词审核 + 多轮对话
python main.py --audit  # LLM 深度审核 + 多轮对话
```

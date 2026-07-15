# 项目状态

## ✅ 已完成

- **LLM 配置**: DeepSeek API，config.yaml + .env 分离
- **Agent 骨架**: LangGraph ReAct agent + MemorySaver + GuardMiddleware
- **内容审核**: 关键词快筛 + 可选 LLM 深度审核
- **3 个工具**: calculator / web_search / rag_search
- **RAG pipeline**: 文档加载 → 切分 → embedding → FAISS 索引
- **记忆三层存储**: Redis(热) / MySQL(温) / Disk(冷)，promote/demote 升降级，冷超 30 天删除
- **Git 仓库**: 本地已初始化，.gitignore 已配置

## ❌ 待完成

| # | 事项 | 说明 |
|---|------|------|
| 1 | tools 接入 agent | `graph.py:13` `tools=[]` 为空，三个工具未接入 |
| 2 | GC 定时触发 | `manager.gc()` 已实现但无人调用，热数据永不过期 |
| 3 | MemoryManager 注入 agent | 三层存储未接入 agent，agent 仍用内置 MemorySaver |
| 4 | thread_id 动态化 | `main.py` 写死 `"default"`，多会话不隔离 |
| 5 | knowledge_base 文档 | 目录为空，RAG 需先放文档建索引 |
| 6 | HTTP 服务端 | config.yaml 配了端口但只有 CLI |

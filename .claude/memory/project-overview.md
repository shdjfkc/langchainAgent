---
name: project-overview
description: langchain_demo 项目整体结构和当前状态
metadata: 
  node_type: memory
  type: project
  originSessionId: ac6d9647-1c82-43b4-89ea-a45090c4efce
---

# langchain_demo 项目

## 目录结构
```
agent/
├── graph.py          # ReAct agent，MemorySaver + GuardMiddleware，tools=[]
├── guard.py          # 内容审核中间件（关键词 + 可选 LLM 审计）
├── memory/           # 多后端记忆模块
│   ├── manager.py    # 记忆管理器
│   ├── db_store.py   # 数据库后端
│   ├── disk_store.py # 磁盘后端
│   ├── redis_store.py# Redis 后端
│   └── migration.py  # 后端间数据迁移
├── rag/              # RAG 检索增强生成
│   ├── loader.py     # 文档加载器
│   └── retriever.py  # 检索器
└── tool/             # Agent 工具集
    ├── calculator.py # 计算器
    ├── rag_search.py # RAG 搜索
    └── web_search.py # 网页搜索（DuckDuckGo）
config/
├── setting.py        # LLM 配置（从 config.yaml 读取）
└── config.yaml
main.py               # 入口
```

## 当前状态（2026-07-15）
- Agent 已创建，使用 langchain `create_agent` + MemorySaver
- GuardMiddleware 实现内容审核
- 三个工具已实现但 `graph.py:13` 的 `tools=[]` 为空，尚未接入 agent
- 记忆模块支持 DB/磁盘/Redis 三种后端 + 数据迁移
- RAG 模块有 loader 和 retriever

## 待处理
- [ ] 将 calculator/web_search/rag_search 接入 agent 的 tools 参数
- [ ] 完善 RAG pipeline（文档加载 → 向量化 → 检索 → 生成）
- [ ] 记忆模块后端选择/切换逻辑

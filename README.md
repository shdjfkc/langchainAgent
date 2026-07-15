# langchainAgent

基于 LangChain + LangGraph 构建的智能 Agent 框架，具备**多层记忆**、**内容安全**和**知识检索**能力。

## 愿景

打造一个开箱即用的智能 Agent 底座——接入 LLM 即可获得带记忆、会搜索、懂安全、能推理的对话智能体。

## 架构

```
main.py (CLI / 未来 → HTTP API)
    │
    ▼
Agent (LangGraph ReAct)
    ├── GuardMiddleware      ← 输入/输出双向内容审核
    ├── Tools                 ← calculator · web_search · rag_search
    ├── Memory (三层存储)     ← 热(Redis) → 温(MySQL) → 冷(Disk)
    └── RAG                   ← 文档加载 → Embedding → FAISS 检索
```

## 核心特性

| 模块 | 说明 |
|------|------|
| **ReAct Agent** | LangGraph 构建，支持工具调用 + 状态持久化 |
| **内容安全** | 关键词快筛 + 可选 LLM 深度审核，拦截违规输入/输出 |
| **三层记忆** | 热层 Redis (1h) → 温层 MySQL (7d) → 冷层 Disk (30d)，自动沉降与提升 |
| **RAG 检索** | 本地文档加载 → HuggingFace Embedding → FAISS 向量检索 |
| **安全计算器** | AST 白名单求值，杜绝代码注入 |
| **联网搜索** | DuckDuckGo 搜索，无需 API Key |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env（填入密钥）
DEEPSEEK_API_KEY=your_key
DB_USER=root
DB_PASSWORD=root

# 3. 放入知识库文档 (可选)
mkdir -p knowledge_base
cp your-docs/*.md knowledge_base/

# 4. 启动
python main.py                # 关键词审核模式
python main.py --audit        # LLM 深度审核模式
```

## 技术栈

- **LLM**: DeepSeek (兼容 OpenAI API)
- **Agent 框架**: LangChain 1.x + LangGraph
- **向量检索**: FAISS + HuggingFace text2vec-base-chinese
- **存储**: Redis + MySQL + 本地 JSON
- **搜索**: DuckDuckGo

## 路线图

- [x] Agent 骨架 + GuardMiddleware
- [x] 工具系统 (calculator / web_search / rag_search)
- [x] RAG 文档加载 + FAISS 索引
- [x] 三层记忆存储 + TTL 自动沉降
- [ ] 工具接入 Agent graph
- [ ] GC 定时调度
- [ ] 自定义 MemoryManager 注入 Agent
- [ ] HTTP API 服务端
- [ ] 多会话并发隔离

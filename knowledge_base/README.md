# LangChain Demo 知识库

这是一个示例知识库文档，用于测试 RAG 检索功能。

## 关于本项目

本项目是一个基于 LangChain 的智能 Agent 示例，集成了：
- 工具调用（计算器、网页搜索、知识库检索）
- 内容审核（关键词 + LLM 双重审核）
- 多层记忆存储（Redis / MySQL / 磁盘）

## DeepSeek API

本项目使用 DeepSeek 作为底层大模型。DeepSeek 提供兼容 OpenAI 接口的 API 服务。
配置信息在 `.env` 文件中设置 `DEEPSEEK_API_KEY`。

## 使用方式

```bash
pip install -r requirements.txt
python main.py          # 关键词审核模式
python main.py --audit  # LLM 深度审核模式
```

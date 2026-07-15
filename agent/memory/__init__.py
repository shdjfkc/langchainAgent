# 记忆模块 — 多后端会话存储（待实现）
#
# 规划的后端：
#   RedisStore  — 热层，活跃会话，TTL 1h
#   DBStore     — 温层，近期会话，TTL 7d
#   DiskStore   — 冷层，归档会话，TTL 30d
#
# 使用方式：from agent.memory import MemoryManager
__all__: list = []

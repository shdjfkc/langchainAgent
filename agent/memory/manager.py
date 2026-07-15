"""记忆管理器 — 三层存储统一接口,热 → 温 → 冷自动降级."""

import uuid
import time
from typing import Any

from agent.memory.redis_store import RedisStore
from agent.memory.db_store import DBStore
from agent.memory.disk_store import DiskStore
from agent.memory.migration import MigrationPolicy


class MemoryManager:
    """对外统一接口,自动协调三层存储.

    读取: 热 → 温 → 冷 逐级查找,命中后提升.
    写入: 写入热层 + 温层(兜底),冷层异步写入.
    """

    def __init__(self):
        self.hot = RedisStore()
        self.warm = DBStore()
        self.disk = DiskStore()
        self.migration = MigrationPolicy()

    # ── 公共接口 ──────────────────────────────────────────

    def load(self, thread_id: str) -> dict[str, Any]:
        """加载会话状态,没有则返回空模版."""
        state = self.migration.promote(thread_id, self.hot, self.warm, self.disk)
        if state:
            return state
        return {"thread_id": thread_id, "messages": [], "created_at": time.time()}

    def save(self, thread_id: str, state: dict[str, Any]) -> None:
        """保存会话状态到热层 + 温层(冷层兜底)."""
        stamped = self.migration.stamp(state)
        if not self.hot.save(thread_id, stamped):
            if not self.warm.save(thread_id, stamped):
                self.disk.save(thread_id, stamped)

    def delete(self, thread_id: str) -> None:
        self.hot.delete(thread_id)
        self.warm.delete(thread_id)
        self.disk.delete(thread_id)

    def gc(self) -> None:
        """扫描三层所有会话,执行 TTL 沉降 + 冷数据过期删除."""
        # 热层
        for tid in self.hot.list_keys():
            self.migration.demote(tid, self.hot, self.warm, self.disk)
        # 温层(可能热层已清但温层仍有)
        for tid in self.warm.list_keys():
            self.migration.demote(tid, self.hot, self.warm, self.disk)
        # 冷层
        for tid in self.disk.list_keys():
            self.migration.demote(tid, self.hot, self.warm, self.disk)

    def new_thread_id(self) -> str:
        return uuid.uuid4().hex[:16]

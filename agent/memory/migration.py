"""数据迁移策略 — TTL 过期 → 热升冷降 → 归档/删除.

热层 (Redis)  ←  当前活跃会话,读写命中
温层 (MySQL)  ←  近期完成会话,可查询
冷层 (Disk)   ←  长期归档,兜底存储

迁移方向: 冷 → 温 → 热 (升温,被访问时逐级提升)
         热 → 温 → 冷 (降温,TTL 超时后逐级沉降)
"""

import time
from typing import Any


class MigrationPolicy:
    """控制三层之间的数据流转."""

    # ponytail: 硬编码 TTL,需要可配时从 config.yaml 读
    HOT_TTL = 3600          # Redis 1 小时
    WARM_TTL = 86400 * 7    # MySQL 7 天
    COLD_TTL = 86400 * 30   # Disk 30 天

    @staticmethod
    def is_expired(record: dict[str, Any], ttl: int) -> bool:
        ts = record.get("_saved_at", 0)
        return (time.time() - ts) > ttl

    @staticmethod
    def stamp(record: dict[str, Any]) -> dict[str, Any]:
        record["_saved_at"] = time.time()
        return record

    @classmethod
    def promote(cls, thread_id: str, hot, warm, disk) -> dict[str, Any] | None:
        """逐级查找会话:热 → 温 → 冷,找到后提升到热层."""
        # 热层命中
        state = hot.get(thread_id)
        if state:
            return state

        # 温层命中 → 提升到热层
        state = warm.get(thread_id)
        if state:
            hot.save(thread_id, cls.stamp(state))
            return state

        # 冷层命中 → 提升到温层
        state = disk.get(thread_id)
        if state:
            warm.save(thread_id, cls.stamp(state))
            hot.save(thread_id, cls.stamp(state))
            return state

        return None

    @classmethod
    def demote(cls, thread_id: str, hot, warm, disk) -> None:
        """TTL 过期逐级沉降:热超时 → 温,温超时 → 冷,冷超时 → 删除."""
        state = hot.get(thread_id)
        if state and cls.is_expired(state, cls.HOT_TTL):
            hot.delete(thread_id)
            if not cls.is_expired(state, cls.WARM_TTL):
                warm.save(thread_id, cls.stamp(state))
            else:
                disk.save(thread_id, cls.stamp(state))

        state = warm.get(thread_id)
        if state and cls.is_expired(state, cls.WARM_TTL):
            warm.delete(thread_id)
            disk.save(thread_id, cls.stamp(state))

        state = disk.get(thread_id)
        if state and cls.is_expired(state, cls.COLD_TTL):
            disk.delete(thread_id)

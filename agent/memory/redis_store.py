"""Redis 热数据存储 — 活跃会话即时读写，不可用时自动降级。"""

import json
from typing import Any

try:
    import redis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

from config.setting import setting


class RedisStore:
    """Redis 会话存储，TTL 从 config.yaml 读取。连接失败静默降级为空操作。"""

    def __init__(self):
        cfg = getattr(setting, "redis", None)
        host = cfg.host if cfg else "127.0.0.1"
        port = cfg.port if cfg else 6379
        db = cfg.db if cfg else 0
        self.ttl = cfg.ttl if cfg else 3600
        self._client = None
        if _HAS_REDIS:
            try:
                self._client = redis.Redis(host=host, port=port, db=db,
                                           socket_connect_timeout=2)
                self._client.ping()
            except Exception:
                self._client = None

    @property
    def available(self) -> bool:
        return self._client is not None

    def get(self, thread_id: str) -> dict[str, Any] | None:
        if not self._client:
            return None
        try:
            data = self._client.get(f"session:{thread_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    def save(self, thread_id: str, state: dict[str, Any]) -> bool:
        if not self._client:
            return False
        try:
            self._client.setex(f"session:{thread_id}", self.ttl, json.dumps(state, default=str))
            return True
        except Exception:
            return False

    def delete(self, thread_id: str) -> bool:
        if not self._client:
            return False
        try:
            self._client.delete(f"session:{thread_id}")
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """列出所有会话 key（去掉前缀）。"""
        if not self._client:
            return []
        try:
            keys = self._client.keys("session:*")
            return [k.decode().removeprefix("session:") for k in keys]
        except Exception:
            return []

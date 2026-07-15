"""磁盘冷归档 — JSON 文件存储,始终可用."""

import json
from pathlib import Path
from typing import Any

from config.setting import ROOT

ARCHIVE_DIR = ROOT / "data" / "sessions"


class DiskStore:
    """本地 JSON 文件存储,兜底方案."""

    def __init__(self):
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _path(thread_id: str) -> Path:
        # 防止路径穿越
        safe = thread_id.replace("\\", "_").replace("/", "_")
        return ARCHIVE_DIR / f"{safe}.json"

    @property
    def available(self) -> bool:
        return True

    def get(self, thread_id: str) -> dict[str, Any] | None:
        path = self._path(thread_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def save(self, thread_id: str, state: dict[str, Any]) -> bool:
        try:
            self._path(thread_id).write_text(json.dumps(state, default=str, ensure_ascii=False, indent=2),
                                             encoding="utf-8")
            return True
        except Exception:
            return False

    def delete(self, thread_id: str) -> bool:
        try:
            path = self._path(thread_id)
            if path.exists():
                path.unlink()
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """列出所有归档的 thread_id."""
        try:
            return [p.stem for p in ARCHIVE_DIR.glob("*.json")]
        except Exception:
            return []

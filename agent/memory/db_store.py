"""MySQL 温数据存储 — 近期已完成会话,不可用时自动降级."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base

from config.setting import setting

Base = declarative_base()


class SessionRecord(Base):
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(64), unique=True, nullable=False, index=True)
    state_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class DBStore:
    """MySQL 会话存储,连接失败静默降级."""

    def __init__(self):
        self._engine = None
        try:
            db = setting.db
            url = f"mysql+pymysql://{db.user}:{db.password}@{db.host}:{db.port}/{db.database}?charset={db.charset}"
            self._engine = create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
            Base.metadata.create_all(self._engine)
        except Exception:
            self._engine = None

    @property
    def available(self) -> bool:
        return self._engine is not None

    def get(self, thread_id: str) -> dict[str, Any] | None:
        if not self._engine:
            return None
        try:
            with Session(self._engine) as session:
                record = session.query(SessionRecord).filter_by(thread_id=thread_id).first()
                return json.loads(record.state_json) if record else None
        except Exception:
            return None

    def save(self, thread_id: str, state: dict[str, Any]) -> bool:
        if not self._engine:
            return False
        try:
            with Session(self._engine) as session:
                record = session.query(SessionRecord).filter_by(thread_id=thread_id).first()
                payload = json.dumps(state, default=str)
                if record:
                    record.state_json = payload
                    record.updated_at = datetime.now(timezone.utc)
                else:
                    session.add(SessionRecord(thread_id=thread_id, state_json=payload))
                session.commit()
            return True
        except Exception:
            return False

    def delete(self, thread_id: str) -> bool:
        if not self._engine:
            return False
        try:
            with Session(self._engine) as session:
                session.query(SessionRecord).filter_by(thread_id=thread_id).delete()
                session.commit()
            return True
        except Exception:
            return False

    def list_keys(self) -> list[str]:
        """列出所有已存储的 thread_id."""
        if not self._engine:
            return []
        try:
            with Session(self._engine) as session:
                return [r.thread_id for r in session.query(SessionRecord.thread_id).all()]
        except Exception:
            return []

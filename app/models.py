from sqlalchemy import Column, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid, os
from enum import Enum as PyEnum

from .database import Base


class TaskStatus(str, PyEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Task(Base):
    __tablename__ = "tasks"

    if os.getenv("TESTING") or not os.getenv("DATABASE_HOST"):
        # Режим тестирования или разработки без PostgreSQL - используем String
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    else:
        # Продакшен с PostgreSQL - используем UUID
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus, name="task_status"), default=TaskStatus.CREATED, nullable=False, index=True)

    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"
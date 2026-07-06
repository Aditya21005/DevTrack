from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from devtrack_ai_db.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KanbanEventType(str, enum.Enum):
    task_moved = "task_moved"
    task_status_updated = "task_status_updated"
    board_reordered = "board_reordered"


class KanbanEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Transactional event record for realtime Kanban broadcasting.

    API writes this row in the same transaction as the board mutation. A future
    WebSocket/SSE publisher can poll unprocessed events and broadcast payloads
    to board subscribers without coupling realtime delivery to the request path.
    """

    __tablename__ = "kanban_events"
    __table_args__ = (
        Index("ix_kanban_events_board_created", "board_id", "created_at"),
        Index("ix_kanban_events_org_processed", "organization_id", "processed_at"),
        Index("uq_kanban_events_board_event_key", "board_id", "event_key", unique=True),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    board_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("boards.id", ondelete="RESTRICT"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    task_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[KanbanEventType] = mapped_column(Enum(KanbanEventType, name="kanban_event_type"), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    event_key: Mapped[str] = mapped_column(String(200), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)



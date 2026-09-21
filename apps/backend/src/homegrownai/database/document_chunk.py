from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import UUID, DateTime, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from homegrownai.database.db import Base

if TYPE_CHECKING:
    from homegrownai.database.document import Document


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    index: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        unique=True,
    )

    content: Mapped[str] = mapped_column(Text)

    line: Mapped[int] = mapped_column(Integer)

    column: Mapped[int] = mapped_column(Integer)

    offset: Mapped[int] = mapped_column(Integer)

    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[Document] = relationship(
        back_populates="embeddings",
    )

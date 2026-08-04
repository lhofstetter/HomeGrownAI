from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy import select, Engine, insert, update
from sqlalchemy.dialects.postgresql import UUID

from .db import Base, DB, DBSession

class Model(Base):
    """
    AI Model Class 
        id: unique UUID used for indexing the model.
        original_model_id: the original string used for the model on the hub it was retrieved from. Example: Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF
        provider: provider who supplied the model (e.g., Hugging Face).
        original_url: Link to the model page. 
        precision: precision of stored model. 
        quantization: quantization used.
        quantization_lib: library used for quantization (e.g., bitsandbytes).
        type: what kind of model is in use (e.g. text-to-text, text-to-image, text-to-video, etc.)
    """
    __tablename__ = "models"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    original_model_id: Mapped[str]
    provider: Mapped[str]
    original_url: Mapped[str]
    precision: Mapped[int]
    quantization: Mapped[str]
    quantization_lib: Mapped[str]
    type: Mapped[str]
    

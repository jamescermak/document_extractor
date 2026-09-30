from .db import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, Numeric, DateTime, func
from datetime import datetime
from decimal import Decimal

class Document(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str]
    file_path: Mapped[str] = mapped_column(unique=True)
    doc_type: Mapped[str]
    status: Mapped[str]
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    extracted_JSON: Mapped[dict] = mapped_column(JSON, nullable=True)
    flags_JSON: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(nullable=True)
    input_tokens: Mapped[int] = mapped_column(nullable=True)
    output_tokens: Mapped[int] = mapped_column(nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric, nullable=True)
    latency_ms: Mapped[float] = mapped_column(nullable=True)
    

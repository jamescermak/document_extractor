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
    corrected_JSON: Mapped[dict] = mapped_column(JSON, nullable=True)
    flags_JSON: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    model_name: Mapped[str] = mapped_column(nullable=True)
    input_tokens: Mapped[int] = mapped_column(nullable=True)
    output_tokens: Mapped[int] = mapped_column(nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=4), nullable=True)
    latency_ms: Mapped[float] = mapped_column(nullable=True)
    
    def __repr__(self):
        return(f'Document(id={self.id}, original_filename={self.original_filename}, '
               f'file_path={self.file_path}, doc_type={self.doc_type}, status={self.status}, '
               f'timestamp={self.timestamp}, extracted_JSON={self.extracted_JSON}, flags_json={self.flags_JSON}, '
               f'model_name={self.model_name}, input_tokens={self.input_tokens}, output_tokens={self.output_tokens}, '
               f'cost={self.cost}, latency_ms={self.latency_ms}')
    
    def to_dict(self):
        return {
            'doc_type': self.doc_type,
            'id': self.id,
            'status': self.status,
            'flags': self.flags_JSON,
            'data': self.corrected_JSON if self.corrected_JSON else self.extracted_JSON,
            'usage': {
                'model_name': self.model_name,
                'input_tokens': self.input_tokens,
                'output_tokens': self.output_tokens,
                'cost': self.cost,
                'latency': self.latency_ms
            }
        }
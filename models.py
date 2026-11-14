"""Tabelas do banco de dados."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    categoria: Mapped[str] = mapped_column(String(60), index=True, default="geral")
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

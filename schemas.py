"""Schemas: definem e validam os dados que entram e saem da API."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProdutoBase(BaseModel):
    nome: str = Field(min_length=2, max_length=120, examples=["Camiseta preta"])
    categoria: str = Field(default="geral", max_length=60, examples=["roupas"])
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=["79.90"])
    quantidade: int = Field(default=0, ge=0, examples=[10])


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    """Todos os campos são opcionais: envie só o que quer mudar."""

    nome: Optional[str] = Field(default=None, min_length=2, max_length=120)
    categoria: Optional[str] = Field(default=None, max_length=60)
    preco: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    quantidade: Optional[int] = Field(default=None, ge=0)


class ProdutoOut(ProdutoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    atualizado_em: datetime


class AjusteEstoque(BaseModel):
    quantidade: int = Field(
        description="Positivo = entrada de estoque. Negativo = saída.",
        examples=[5, -2],
    )


class ResumoEstoque(BaseModel):
    total_produtos: int
    itens_em_estoque: int
    valor_total_estoque: Decimal
    produtos_com_estoque_baixo: int

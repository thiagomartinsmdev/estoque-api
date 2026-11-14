"""Operações no banco (criar, ler, atualizar, apagar)."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas

LIMITE_ESTOQUE_BAIXO = 5


class EstoqueInsuficiente(Exception):
    """Levantada quando uma saída deixaria o estoque negativo."""


def listar(
    db: Session,
    categoria: Optional[str] = None,
    busca: Optional[str] = None,
    baixo_estoque: bool = False,
    skip: int = 0,
    limit: int = 50,
):
    stmt = select(models.Produto)
    if categoria:
        stmt = stmt.where(models.Produto.categoria == categoria)
    if busca:
        stmt = stmt.where(models.Produto.nome.ilike(f"%{busca}%"))
    if baixo_estoque:
        stmt = stmt.where(models.Produto.quantidade <= LIMITE_ESTOQUE_BAIXO)
    stmt = stmt.order_by(models.Produto.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()


def obter(db: Session, produto_id: int):
    return db.get(models.Produto, produto_id)


def criar(db: Session, dados: schemas.ProdutoCreate):
    produto = models.Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


def atualizar(db: Session, produto: models.Produto, dados: schemas.ProdutoUpdate):
    for campo, valor in dados.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return produto


def apagar(db: Session, produto: models.Produto):
    db.delete(produto)
    db.commit()


def ajustar_estoque(db: Session, produto: models.Produto, delta: int):
    novo_valor = produto.quantidade + delta
    if novo_valor < 0:
        raise EstoqueInsuficiente(
            f"Estoque insuficiente: há {produto.quantidade} unidade(s) e a saída é de {abs(delta)}."
        )
    produto.quantidade = novo_valor
    db.commit()
    db.refresh(produto)
    return produto


def resumo(db: Session) -> schemas.ResumoEstoque:
    total, itens, valor = db.execute(
        select(
            func.count(models.Produto.id),
            func.coalesce(func.sum(models.Produto.quantidade), 0),
            func.coalesce(func.sum(models.Produto.preco * models.Produto.quantidade), 0),
        )
    ).one()
    baixo = db.scalar(
        select(func.count(models.Produto.id)).where(
            models.Produto.quantidade <= LIMITE_ESTOQUE_BAIXO
        )
    )
    return schemas.ResumoEstoque(
        total_produtos=total,
        itens_em_estoque=int(itens),
        valor_total_estoque=Decimal(str(valor)).quantize(Decimal("0.01")),
        produtos_com_estoque_baixo=baixo or 0,
    )

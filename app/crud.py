"""Operações no banco (criar, ler, atualizar, apagar)."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas, security

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


# ---------- Usuários ----------


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


def contar_usuarios(db: Session) -> int:
    return db.scalar(select(func.count(models.Usuario.id))) or 0


def obter_usuario_por_email(db: Session, email: str) -> Optional[models.Usuario]:
    return db.scalar(
        select(models.Usuario).where(models.Usuario.email == _normalizar_email(email))
    )


def criar_usuario(db: Session, dados: schemas.UsuarioCreate) -> models.Usuario:
    usuario = models.Usuario(
        nome=dados.nome.strip(),
        email=_normalizar_email(dados.email),
        senha_hash=security.hash_senha(dados.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar(db: Session, email: str, senha: str) -> Optional[models.Usuario]:
    """Devolve o usuário se e-mail e senha estiverem certos; senão None.

    A senha é sempre verificada (com um hash falso se o e-mail não existir),
    para o tempo de resposta ser parecido nos dois casos.
    """
    usuario = obter_usuario_por_email(db, email)
    guardado = usuario.senha_hash if usuario else security.HASH_FALSO
    senha_ok = security.verificar_senha(senha, guardado)
    if usuario is None or not senha_ok or not usuario.ativo:
        return None
    return usuario

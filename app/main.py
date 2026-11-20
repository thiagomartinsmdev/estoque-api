"""API de Estoque: ponto de entrada da aplicação."""
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import auth, crud, models, schemas
from .database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas que ainda não existem (produtos e usuarios).
    # create_all nunca altera nem apaga tabelas que já existem.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Estoque",
    description="API REST para controle de produtos e estoque, feita com FastAPI e PostgreSQL.",
    version="1.1.0",
    lifespan=lifespan,
)


# CORS: permite que o painel web (outro endereço) converse com a API pelo navegador.
# Em desenvolvimento aceita qualquer origem. Para restringir, defina no .env:
# CORS_ORIGINS=http://127.0.0.1:5500,https://thiagomartinsmdev.github.io
origens = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rotas de autenticação (/auth/status, /auth/registro, /auth/login, /auth/eu).
app.include_router(auth.router)

# Todas as rotas deste grupo exigem login (token JWT no cabeçalho Authorization).
protegido = APIRouter(dependencies=[Depends(auth.usuario_atual)])


def _produto_ou_404(db: Session, produto_id: int) -> models.Produto:
    produto = crud.obter(db, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@app.get("/", tags=["Geral"])
def raiz():
    return {"mensagem": "API de Estoque no ar.", "documentacao": "/docs"}


@protegido.post(
    "/produtos",
    response_model=schemas.ProdutoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Produtos"],
)
def criar_produto(dados: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@protegido.get("/produtos", response_model=List[schemas.ProdutoOut], tags=["Produtos"])
def listar_produtos(
    categoria: Optional[str] = Query(None, description="Filtra por categoria"),
    busca: Optional[str] = Query(None, description="Busca pelo nome"),
    baixo_estoque: bool = Query(False, description="Só produtos com estoque baixo (5 ou menos)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.listar(db, categoria, busca, baixo_estoque, skip, limit)


@protegido.get("/produtos/{produto_id}", response_model=schemas.ProdutoOut, tags=["Produtos"])
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    return _produto_ou_404(db, produto_id)


@protegido.patch("/produtos/{produto_id}", response_model=schemas.ProdutoOut, tags=["Produtos"])
def atualizar_produto(
    produto_id: int, dados: schemas.ProdutoUpdate, db: Session = Depends(get_db)
):
    produto = _produto_ou_404(db, produto_id)
    return crud.atualizar(db, produto, dados)


@protegido.delete(
    "/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Produtos"]
)
def apagar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = _produto_ou_404(db, produto_id)
    crud.apagar(db, produto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@protegido.post(
    "/produtos/{produto_id}/estoque", response_model=schemas.ProdutoOut, tags=["Estoque"]
)
def ajustar_estoque(
    produto_id: int, ajuste: schemas.AjusteEstoque, db: Session = Depends(get_db)
):
    produto = _produto_ou_404(db, produto_id)
    try:
        return crud.ajustar_estoque(db, produto, ajuste.quantidade)
    except crud.EstoqueInsuficiente as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@protegido.get("/relatorios/resumo", response_model=schemas.ResumoEstoque, tags=["Relatórios"])
def resumo_estoque(db: Session = Depends(get_db)):
    return crud.resumo(db)


# Registra as rotas protegidas na aplicação (precisa vir depois delas).
app.include_router(protegido)

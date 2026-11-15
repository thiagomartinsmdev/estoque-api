"""API de Estoque: ponto de entrada da aplicação."""
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import Base, engine, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas na primeira execução.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Estoque",
    description="API REST para controle de produtos e estoque, feita com FastAPI e PostgreSQL.",
    version="1.0.0",
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


def _produto_ou_404(db: Session, produto_id: int) -> models.Produto:
    produto = crud.obter(db, produto_id)
    if produto is None:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


@app.get("/", tags=["Geral"])
def raiz():
    return {"mensagem": "API de Estoque no ar.", "documentacao": "/docs"}


@app.post(
    "/produtos",
    response_model=schemas.ProdutoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Produtos"],
)
def criar_produto(dados: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    return crud.criar(db, dados)


@app.get("/produtos", response_model=List[schemas.ProdutoOut], tags=["Produtos"])
def listar_produtos(
    categoria: Optional[str] = Query(None, description="Filtra por categoria"),
    busca: Optional[str] = Query(None, description="Busca pelo nome"),
    baixo_estoque: bool = Query(False, description="Só produtos com estoque baixo (5 ou menos)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return crud.listar(db, categoria, busca, baixo_estoque, skip, limit)


@app.get("/produtos/{produto_id}", response_model=schemas.ProdutoOut, tags=["Produtos"])
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    return _produto_ou_404(db, produto_id)


@app.patch("/produtos/{produto_id}", response_model=schemas.ProdutoOut, tags=["Produtos"])
def atualizar_produto(
    produto_id: int, dados: schemas.ProdutoUpdate, db: Session = Depends(get_db)
):
    produto = _produto_ou_404(db, produto_id)
    return crud.atualizar(db, produto, dados)


@app.delete(
    "/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Produtos"]
)
def apagar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = _produto_ou_404(db, produto_id)
    crud.apagar(db, produto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
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


@app.get("/relatorios/resumo", response_model=schemas.ResumoEstoque, tags=["Relatórios"])
def resumo_estoque(db: Session = Depends(get_db)):
    return crud.resumo(db)

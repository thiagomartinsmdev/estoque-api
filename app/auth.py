"""Rotas de autenticação (/auth) e a dependência que exige login."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import crud, models, schemas, security
from .database import get_db

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# auto_error=False: nós mesmos devolvemos o 401 com a mensagem em português.
bearer = HTTPBearer(auto_error=False)


def _nao_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado. Faça login.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def usuario_atual(
    credenciais: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """Exige o cabeçalho 'Authorization: Bearer <token>' válido."""
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise _nao_autenticado()
    usuario_id = security.ler_token(credenciais.credentials)
    if usuario_id is None:
        raise _nao_autenticado()
    usuario = db.get(models.Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise _nao_autenticado()
    return usuario


@router.get("/status", response_model=schemas.StatusAuth)
def status_auth(db: Session = Depends(get_db)):
    """Público: diz se já existe algum usuário (o painel usa para o 1º cadastro)."""
    return schemas.StatusAuth(tem_usuarios=crud.contar_usuarios(db) > 0)


@router.post(
    "/registro",
    response_model=schemas.UsuarioOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar(
    dados: schemas.UsuarioCreate,
    credenciais: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
):
    """O primeiro cadastro é livre. Depois disso, só um usuário logado cadastra outro."""
    if crud.contar_usuarios(db) > 0:
        usuario_atual(credenciais, db)  # levanta 401 se não estiver logado
    if crud.obter_usuario_por_email(db, dados.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com esse e-mail.",
        )
    return crud.criar_usuario(db, dados)


@router.post("/login", response_model=schemas.TokenOut)
def login(dados: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    """Recebe e-mail e senha (JSON) e devolve o token de acesso."""
    usuario = crud.autenticar(db, dados.email, dados.senha)
    if usuario is None:
        # Mesma mensagem para e-mail inexistente e senha errada.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return schemas.TokenOut(
        access_token=security.criar_token(usuario.id),
        usuario=schemas.UsuarioOut.model_validate(usuario),
    )


@router.get("/eu", response_model=schemas.UsuarioOut)
def eu(usuario: models.Usuario = Depends(usuario_atual)):
    """Devolve os dados do usuário logado."""
    return usuario

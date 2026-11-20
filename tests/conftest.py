"""Configuração compartilhada dos testes (fixtures do pytest)."""
import os

# Define uma SECRET_KEY de teste ANTES de importar a aplicação
# (o módulo security lê a chave quando é importado).
os.environ.setdefault("SECRET_KEY", "chave-so-para-testes-com-mais-de-32-caracteres")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

USUARIO_TESTE = {"nome": "Pessoa Teste", "email": "teste@exemplo.com", "senha": "senha-de-teste-123"}


@pytest.fixture()
def db_override():
    """Troca o banco real por um SQLite em memória, só para os testes."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def anon(db_override):
    """Cliente sem login."""
    return TestClient(app)


@pytest.fixture()
def client(db_override):
    """Cliente já logado: cria o primeiro usuário, faz login e guarda o token."""
    c = TestClient(app)
    assert c.post("/auth/registro", json=USUARIO_TESTE).status_code == 201
    resposta = c.post(
        "/auth/login",
        json={"email": USUARIO_TESTE["email"], "senha": USUARIO_TESTE["senha"]},
    )
    assert resposta.status_code == 200
    c.headers["Authorization"] = f"Bearer {resposta.json()['access_token']}"
    return c

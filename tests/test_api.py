"""Testes automáticos da API (rode com: pytest)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # Banco SQLite em memória, só para os testes.
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
    yield TestClient(app)
    app.dependency_overrides.clear()


def novo_produto(client, **extra):
    corpo = {"nome": "Camiseta preta", "categoria": "roupas", "preco": "79.90", "quantidade": 10}
    corpo.update(extra)
    return client.post("/produtos", json=corpo)


def test_criar_e_obter_produto(client):
    resposta = novo_produto(client)
    assert resposta.status_code == 201
    produto = resposta.json()
    assert produto["nome"] == "Camiseta preta"

    resposta = client.get(f"/produtos/{produto['id']}")
    assert resposta.status_code == 200
    assert resposta.json()["quantidade"] == 10


def test_validacao_rejeita_preco_invalido(client):
    resposta = novo_produto(client, preco="-5")
    assert resposta.status_code == 422


def test_produto_inexistente_retorna_404(client):
    assert client.get("/produtos/999").status_code == 404


def test_listar_com_filtros(client):
    novo_produto(client, nome="Camiseta preta", categoria="roupas")
    novo_produto(client, nome="Caneca", categoria="casa", quantidade=2)

    todos = client.get("/produtos").json()
    assert len(todos) == 2

    roupas = client.get("/produtos", params={"categoria": "roupas"}).json()
    assert [p["nome"] for p in roupas] == ["Camiseta preta"]

    busca = client.get("/produtos", params={"busca": "canec"}).json()
    assert [p["nome"] for p in busca] == ["Caneca"]

    baixo = client.get("/produtos", params={"baixo_estoque": True}).json()
    assert [p["nome"] for p in baixo] == ["Caneca"]


def test_atualizar_parcialmente(client):
    produto = novo_produto(client).json()
    resposta = client.patch(f"/produtos/{produto['id']}", json={"preco": "89.90"})
    assert resposta.status_code == 200
    assert resposta.json()["preco"] == "89.90"
    assert resposta.json()["nome"] == "Camiseta preta"


def test_ajuste_de_estoque(client):
    produto = novo_produto(client, quantidade=3).json()
    url = f"/produtos/{produto['id']}/estoque"

    entrada = client.post(url, json={"quantidade": 7})
    assert entrada.json()["quantidade"] == 10

    saida_invalida = client.post(url, json={"quantidade": -50})
    assert saida_invalida.status_code == 400


def test_apagar_produto(client):
    produto = novo_produto(client).json()
    assert client.delete(f"/produtos/{produto['id']}").status_code == 204
    assert client.get(f"/produtos/{produto['id']}").status_code == 404


def test_resumo_do_estoque(client):
    novo_produto(client, preco="10.00", quantidade=4)
    novo_produto(client, nome="Caneca", preco="5.50", quantidade=10)
    resumo = client.get("/relatorios/resumo").json()
    assert resumo["total_produtos"] == 2
    assert resumo["itens_em_estoque"] == 14
    assert resumo["produtos_com_estoque_baixo"] == 1
    assert float(resumo["valor_total_estoque"]) == 95.0

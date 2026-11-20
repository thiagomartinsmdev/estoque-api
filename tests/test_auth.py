"""Testes do login: registro, token JWT e rotas protegidas."""
from app import security
from tests.conftest import USUARIO_TESTE

ROTAS_PROTEGIDAS = [
    ("get", "/produtos"),
    ("post", "/produtos"),
    ("get", "/produtos/1"),
    ("patch", "/produtos/1"),
    ("delete", "/produtos/1"),
    ("post", "/produtos/1/estoque"),
    ("get", "/relatorios/resumo"),
]


def login(cliente, email, senha):
    return cliente.post("/auth/login", json={"email": email, "senha": senha})


def test_raiz_e_status_sao_publicos(anon):
    assert anon.get("/").status_code == 200
    resposta = anon.get("/auth/status")
    assert resposta.status_code == 200
    assert resposta.json() == {"tem_usuarios": False}


def test_rotas_protegidas_sem_token_dao_401(anon):
    for metodo, rota in ROTAS_PROTEGIDAS:
        resposta = getattr(anon, metodo)(rota)
        assert resposta.status_code == 401, rota
        assert resposta.json()["detail"] == "Não autenticado. Faça login."
        assert resposta.headers["www-authenticate"] == "Bearer"


def test_token_falso_da_401(client):
    client.headers["Authorization"] = "Bearer isto-nao-e-um-token"
    assert client.get("/produtos").status_code == 401


def test_token_expirado_da_401(client):
    client.headers["Authorization"] = f"Bearer {security.criar_token(1, minutos=-5)}"
    assert client.get("/produtos").status_code == 401


def test_status_muda_depois_do_primeiro_usuario(anon):
    assert anon.get("/auth/status").json()["tem_usuarios"] is False
    assert anon.post("/auth/registro", json=USUARIO_TESTE).status_code == 201
    assert anon.get("/auth/status").json()["tem_usuarios"] is True


def test_primeiro_registro_livre_segundo_exige_login(anon, client):
    # `client` já criou o primeiro usuário no mesmo banco.
    novo = {"nome": "Segunda Pessoa", "email": "segunda@exemplo.com", "senha": "outra-senha-123"}
    assert anon.post("/auth/registro", json=novo).status_code == 401
    assert client.post("/auth/registro", json=novo).status_code == 201


def test_email_duplicado_da_409(client):
    repetido = dict(USUARIO_TESTE, email=USUARIO_TESTE["email"].upper())
    resposta = client.post("/auth/registro", json=repetido)
    assert resposta.status_code == 409
    assert resposta.json()["detail"] == "Já existe um usuário com esse e-mail."


def test_senha_curta_e_email_invalido_dao_422(anon):
    curta = dict(USUARIO_TESTE, senha="1234567")
    assert anon.post("/auth/registro", json=curta).status_code == 422
    sem_arroba = dict(USUARIO_TESTE, email="email-invalido")
    assert anon.post("/auth/registro", json=sem_arroba).status_code == 422


def test_cadastro_nao_devolve_senha_nem_hash(anon):
    corpo = anon.post("/auth/registro", json=USUARIO_TESTE).json()
    assert set(corpo) == {"id", "nome", "email"}
    texto = str(corpo).lower()
    assert "senha" not in texto and "hash" not in texto
    assert USUARIO_TESTE["senha"] not in texto


def test_login_correto_devolve_token_e_usuario(client):
    resposta = login(client, USUARIO_TESTE["email"], USUARIO_TESTE["senha"])
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    assert security.ler_token(corpo["access_token"]) == corpo["usuario"]["id"]
    assert corpo["usuario"]["email"] == USUARIO_TESTE["email"]


def test_login_aceita_email_em_maiusculas(client):
    resposta = login(client, "  " + USUARIO_TESTE["email"].upper(), USUARIO_TESTE["senha"])
    assert resposta.status_code == 200


def test_senha_errada_e_email_inexistente_dao_a_mesma_resposta(client):
    senha_errada = login(client, USUARIO_TESTE["email"], "senha-errada-123")
    email_inexistente = login(client, "ninguem@exemplo.com", USUARIO_TESTE["senha"])
    assert senha_errada.status_code == email_inexistente.status_code == 401
    assert senha_errada.content == email_inexistente.content
    assert senha_errada.json()["detail"] == "E-mail ou senha incorretos."


def test_auth_eu_devolve_usuario_logado(client):
    resposta = client.get("/auth/eu")
    assert resposta.status_code == 200
    assert resposta.json()["email"] == USUARIO_TESTE["email"]
    assert resposta.json()["nome"] == USUARIO_TESTE["nome"]

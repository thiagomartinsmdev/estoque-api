"""Testes das funções de segurança (hash de senha e token JWT)."""
import jwt

from app import security


def test_hash_nao_contem_a_senha_e_verifica():
    guardado = security.hash_senha("minha-senha-123")
    assert "minha-senha-123" not in guardado
    assert guardado.startswith("scrypt$")
    assert security.verificar_senha("minha-senha-123", guardado) is True
    assert security.verificar_senha("outra-senha-123", guardado) is False


def test_mesma_senha_gera_hashes_diferentes():
    # Cada hash usa um "sal" aleatório diferente.
    assert security.hash_senha("igual-123") != security.hash_senha("igual-123")


def test_hash_malformado_ou_vazio_da_false():
    for ruim in ["", "abc", "scrypt$1$2$3", "bcrypt$a$b$c$d$e", "scrypt$x$8$1$AAAA$BBBB", None]:
        assert security.verificar_senha("qualquer", ruim) is False


def test_token_ida_e_volta():
    token = security.criar_token(42)
    assert security.ler_token(token) == 42
    dados = jwt.decode(token, security.SECRET_KEY, algorithms=["HS256"])
    assert dados["sub"] == "42"
    assert {"iat", "exp"} <= set(dados)


def test_token_expirado_adulterado_ou_lixo_da_none():
    assert security.ler_token(security.criar_token(1, minutos=-5)) is None
    token = security.criar_token(1)
    adulterado = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert security.ler_token(adulterado) is None
    assert security.ler_token("lixo") is None
    assert security.ler_token("") is None


def test_token_de_outra_chave_da_none():
    agora = jwt.decode(security.criar_token(1), security.SECRET_KEY, algorithms=["HS256"])
    falso = jwt.encode(agora, "outra-chave-bem-diferente-com-32-caracteres", algorithm="HS256")
    assert security.ler_token(falso) is None

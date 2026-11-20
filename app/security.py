"""Segurança: hash de senhas (scrypt) e tokens de acesso (JWT).

- As senhas nunca são guardadas: guardamos só um "hash" (impressão digital)
  calculado com scrypt, que é lento de propósito para dificultar ataques.
- O token JWT é um texto assinado com a SECRET_KEY. Quem não tem a chave
  não consegue criar nem alterar um token válido.
"""
import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Sem chave no .env: gera uma temporária. Funciona, mas todos os tokens
    # deixam de valer quando a API reinicia.
    SECRET_KEY = secrets.token_hex(32)
    print(
        "AVISO: SECRET_KEY não definida no .env. Usando uma chave temporária "
        "(os logins expiram quando a API reiniciar)."
    )

ALGORITMO = "HS256"
TOKEN_EXPIRA_MINUTOS = int(os.getenv("TOKEN_EXPIRA_MINUTOS", "60"))

# Parâmetros do scrypt (custo de memória/CPU).
_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode("ascii")


def hash_senha(senha: str) -> str:
    """Gera o hash da senha no formato scrypt$n$r$p$sal_b64$hash_b64."""
    sal = secrets.token_bytes(16)
    resultado = hashlib.scrypt(
        senha.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P, dklen=_DKLEN
    )
    return f"scrypt${_N}${_R}${_P}${_b64(sal)}${_b64(resultado)}"


def verificar_senha(senha: str, guardado: str) -> bool:
    """Confere a senha com o hash guardado. Nunca levanta exceção."""
    try:
        algoritmo, n, r, p, sal_b64, hash_b64 = guardado.split("$")
        if algoritmo != "scrypt":
            return False
        esperado = base64.b64decode(hash_b64)
        calculado = hashlib.scrypt(
            senha.encode("utf-8"),
            salt=base64.b64decode(sal_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(esperado),
        )
        # compare_digest compara em tempo constante (não "vaza" informação).
        return hmac.compare_digest(calculado, esperado)
    except (ValueError, TypeError, AttributeError):
        return False


# Hash usado quando o e-mail não existe: assim o login demora o mesmo tempo
# e ninguém descobre quais e-mails estão cadastrados medindo a resposta.
HASH_FALSO = hash_senha("senha-que-ninguem-usa")


def criar_token(usuario_id: int, minutos: Optional[int] = None) -> str:
    """Cria um JWT com sub (id do usuário, em texto), iat e exp."""
    agora = datetime.now(timezone.utc)
    validade = TOKEN_EXPIRA_MINUTOS if minutos is None else minutos
    dados = {
        "sub": str(usuario_id),
        "iat": agora,
        "exp": agora + timedelta(minutes=validade),
    }
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITMO)


def ler_token(token: str) -> Optional[int]:
    """Devolve o id do usuário, ou None se o token for inválido/expirado."""
    try:
        dados = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
        return int(dados["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None

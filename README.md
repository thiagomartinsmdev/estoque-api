# 📦 API de Estoque

API REST para controle de produtos e estoque, feita com **FastAPI**, **SQLAlchemy** e **PostgreSQL**. Pensada a partir da rotina de uma loja virtual: cadastrar produtos, consultar, ajustar o estoque e acompanhar um resumo.

## Funcionalidades

- **Login com senha e token JWT**: só usuários logados acessam o estoque
- CRUD completo de produtos (criar, listar, consultar, atualizar e apagar)
- Filtros por categoria e busca por nome, com paginação
- Entrada e saída de estoque, com bloqueio de estoque negativo
- Lista de produtos com estoque baixo
- Relatório-resumo: total de produtos, itens, valor em estoque e alertas
- Validação automática dos dados (preço positivo, nome obrigatório, etc.)
- Documentação interativa automática (Swagger)
- Testes automatizados com pytest

## Tecnologias

Python · FastAPI · SQLAlchemy 2 · PostgreSQL · Pydantic · PyJWT · Pytest

## Endpoints

🔒 = exige login (cabeçalho `Authorization: Bearer <token>`).

| Método | Rota | Descrição |
| :-- | :-- | :-- |
| GET | `/` | Status da API (público) |
| GET | `/auth/status` | Diz se já existe algum usuário cadastrado (público) |
| POST | `/auth/registro` | Cadastra um usuário (o primeiro é livre; depois, 🔒) |
| POST | `/auth/login` | Recebe e-mail e senha (JSON) e devolve o token |
| GET | `/auth/eu` | 🔒 Dados do usuário logado |
| POST | `/produtos` | 🔒 Cadastra um produto |
| GET | `/produtos` | 🔒 Lista produtos (filtros: `categoria`, `busca`, `baixo_estoque`, `skip`, `limit`) |
| GET | `/produtos/{id}` | 🔒 Consulta um produto |
| PATCH | `/produtos/{id}` | 🔒 Atualiza campos do produto |
| DELETE | `/produtos/{id}` | 🔒 Apaga um produto |
| POST | `/produtos/{id}/estoque` | 🔒 Entrada (positivo) ou saída (negativo) de estoque |
| GET | `/relatorios/resumo` | 🔒 Resumo geral do estoque |

## Como rodar (Windows)

Requisito: Python 3.9 ou superior.

```bash
# 1. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie a API
uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000/docs** para testar todos os endpoints pelo navegador.

Por padrão a API usa um arquivo SQLite (`estoque.db`), então funciona sem instalar nada.

### Usando PostgreSQL

1. Crie um banco chamado `estoque` no PostgreSQL.
2. Copie `.env.example` para `.env` e preencha a linha `DATABASE_URL` com seus dados:

```
DATABASE_URL=postgresql+psycopg2://postgres:SENHA@localhost:5432/estoque
```

3. Rode `uvicorn app.main:app --reload` de novo. As tabelas são criadas automaticamente (a tabela nova `usuarios` é criada sem mexer na de `produtos`).

## Autenticação

A API usa **login com e-mail e senha** e devolve um **token JWT**. Esse token vai em todas as requisições protegidas, no cabeçalho `Authorization: Bearer <token>`. As senhas nunca são guardadas: o banco guarda só um hash (scrypt com sal aleatório).

### Passo a passo

**1. Gere a sua SECRET_KEY** (a chave que assina os tokens). Com o venv ativado:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o texto que aparecer e cole no seu arquivo `.env`, na linha `SECRET_KEY=` (se ainda não tem `.env`, copie o `.env.example` e renomeie para `.env`). Nunca envie essa chave para o GitHub. Se você não configurar a chave, a API funciona com uma chave temporária e mostra um AVISO; nesse caso todo mundo precisa entrar de novo quando a API reinicia.

**2. Cadastre o primeiro usuário.** Enquanto não existe nenhum usuário, o cadastro é livre. Em `/docs`, abra `POST /auth/registro` → **Try it out** e envie:

```json
{ "nome": "Seu nome", "email": "voce@exemplo.com", "senha": "uma-senha-com-8-ou-mais" }
```

Depois disso, só um usuário logado pode cadastrar outros.

**3. Faça login.** Em `POST /auth/login`, envie `{"email": "...", "senha": "..."}`. A resposta traz o `access_token`.

**4. Use o botão Authorize do /docs.** Clique no cadeado **Authorize** (no topo da página), cole o `access_token` no campo e confirme. Agora as rotas 🔒 funcionam pelo navegador. Quando o token expirar (padrão: 60 minutos, ajustável em `TOKEN_EXPIRA_MINUTOS`), faça login de novo.

Pelo terminal, o mesmo fluxo com `curl`:

```bash
curl -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d "{\"email\": \"voce@exemplo.com\", \"senha\": \"sua-senha\"}"
curl http://127.0.0.1:8000/produtos -H "Authorization: Bearer COLE_O_TOKEN_AQUI"
```

### Variáveis do `.env`

| Variável | Para que serve | Padrão |
| :-- | :-- | :-- |
| `DATABASE_URL` | Endereço do banco | SQLite `estoque.db` |
| `SECRET_KEY` | Chave que assina os tokens | chave temporária (com aviso) |
| `TOKEN_EXPIRA_MINUTOS` | Validade do login | `60` |
| `CORS_ORIGINS` | Sites que podem chamar a API pelo navegador (separados por vírgula) | `*` |

### Cuidados de segurança

- Login errado sempre responde a mesma mensagem ("E-mail ou senha incorretos."), exista o e-mail ou não.
- A API nunca devolve a senha nem o hash.
- `.env`, `estoque.db`, `venv` e `__pycache__` estão no `.gitignore`.

## Exemplo de uso

```bash
curl -X POST http://127.0.0.1:8000/produtos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer COLE_O_TOKEN_AQUI" \
  -d '{"nome": "Camiseta preta", "categoria": "roupas", "preco": "79.90", "quantidade": 10}'
```

## Testes

```bash
pytest
```

São 27 testes: 8 de produtos (`test_api.py`), 13 de login e rotas protegidas (`test_auth.py`) e 6 de hash de senha e token (`test_security.py`). Os testes usam um banco SQLite em memória, então não mexem no seu banco.

## Estrutura

```
app/
  main.py       # rotas da API (produtos e relatórios protegidos)
  auth.py       # rotas /auth e a verificação do token
  security.py   # hash de senha (scrypt) e token JWT
  models.py     # tabelas do banco (produtos e usuarios)
  schemas.py    # validação dos dados
  crud.py       # operações no banco
  database.py   # conexão (SQLite ou PostgreSQL)
tests/
  conftest.py       # banco de teste e clientes (anônimo e logado)
  test_api.py       # testes de produtos
  test_auth.py      # testes de login e rotas protegidas
  test_security.py  # testes de hash e token
```

---

Feito por **Thiago Matosinhos** · [GitHub](https://github.com/thiagomartinsmdev) · [LinkedIn](https://www.linkedin.com/in/thiago-filipe-b08586325/)

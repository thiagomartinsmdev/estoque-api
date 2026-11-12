# 📦 API de Estoque

API REST para controle de produtos e estoque, feita com **FastAPI**, **SQLAlchemy** e **PostgreSQL**. Pensada a partir da rotina de uma loja virtual: cadastrar produtos, consultar, ajustar o estoque e acompanhar um resumo.

## Funcionalidades

- CRUD completo de produtos (criar, listar, consultar, atualizar e apagar)
- Filtros por categoria e busca por nome, com paginação
- Entrada e saída de estoque, com bloqueio de estoque negativo
- Lista de produtos com estoque baixo
- Relatório-resumo: total de produtos, itens, valor em estoque e alertas
- Validação automática dos dados (preço positivo, nome obrigatório, etc.)
- Documentação interativa automática (Swagger)
- Testes automatizados com pytest

## Tecnologias

Python · FastAPI · SQLAlchemy 2 · PostgreSQL · Pydantic · Pytest

## Endpoints

| Método | Rota | Descrição |
| :-- | :-- | :-- |
| GET | `/` | Status da API |
| POST | `/produtos` | Cadastra um produto |
| GET | `/produtos` | Lista produtos (filtros: `categoria`, `busca`, `baixo_estoque`, `skip`, `limit`) |
| GET | `/produtos/{id}` | Consulta um produto |
| PATCH | `/produtos/{id}` | Atualiza campos do produto |
| DELETE | `/produtos/{id}` | Apaga um produto |
| POST | `/produtos/{id}/estoque` | Entrada (positivo) ou saída (negativo) de estoque |
| GET | `/relatorios/resumo` | Resumo geral do estoque |

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

3. Rode `uvicorn app.main:app --reload` de novo. As tabelas são criadas automaticamente.

## Exemplo de uso

```bash
curl -X POST http://127.0.0.1:8000/produtos \
  -H "Content-Type: application/json" \
  -d '{"nome": "Camiseta preta", "categoria": "roupas", "preco": "79.90", "quantidade": 10}'
```

## Testes

```bash
pytest
```

## Estrutura

```
app/
  main.py       # rotas da API
  models.py     # tabelas do banco
  schemas.py    # validação dos dados
  crud.py       # operações no banco
  database.py   # conexão (SQLite ou PostgreSQL)
tests/
  test_api.py   # testes automatizados
```

## Próximos passos

- [ ] Autenticação com JWT
- [ ] Migrações com Alembic
- [ ] Histórico de movimentações do estoque
- [ ] Docker e Docker Compose

---

Feito por **Thiago Matosinhos** · [GitHub](https://github.com/thiagomartinsmdev) · [LinkedIn](https://www.linkedin.com/in/thiago-filipe-b08586325/)

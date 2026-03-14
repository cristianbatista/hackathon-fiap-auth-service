# Auth Service

Microsserviço responsável por cadastro de usuários, autenticação via JWT e proteção de endpoints. É o pré-requisito de toda a plataforma — os demais serviços validam tokens JWT localmente sem chamadas de rede a este serviço.

## Endpoints

| Método | Path | Autenticação | Descrição |
|--------|------|-------------|-----------|
| `POST` | `/auth/register` | Não | Cadastra novo usuário |
| `POST` | `/auth/login` | Não | Autentica e retorna JWT |
| `GET` | `/auth/me` | Bearer JWT | Retorna dados do usuário autenticado |
| `GET` | `/health` | Não | Health check |
| `GET` | `/metrics` | Não | Métricas Prometheus |

### POST /auth/register

```json
// Request
{ "nome": "João Silva", "email": "joao@example.com", "password": "minimo8chars" }

// Response 201
{ "id": "uuid", "email": "joao@example.com", "nome": "João Silva", "created_at": "..." }

// Erros: 409 e-mail duplicado | 422 validação
```

### POST /auth/login

```json
// Request
{ "email": "joao@example.com", "password": "minimo8chars" }

// Response 200
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600 }

// Erros: 401 credenciais inválidas (mesma mensagem para senha errada e e-mail inexistente)
```

### GET /auth/me

```
Authorization: Bearer <access_token>
```

```json
// Response 200
{ "id": "uuid", "email": "joao@example.com", "nome": "João Silva", "created_at": "..." }
```

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição | Exemplo |
|----------|-------------|-----------|---------|
| `DATABASE_URL` | ✅ | URL de conexão PostgreSQL | `postgresql://user:pass@db:5432/authdb` |
| `JWT_SECRET` | ✅ | Chave secreta para assinatura HS256 | `minha-chave-secreta-longa` |
| `JWT_EXPIRY_SECONDS` | — | Expiração do token em segundos (default: `3600`) | `7200` |
| `LOG_LEVEL` | — | Nível de log (default: `INFO`) | `DEBUG` |

Copie `.env.example` e preencha os valores:

```bash
cp services/auth-service/.env.example services/auth-service/.env
```

## Rodando Localmente

### Com Docker

```bash
# Build
docker build services/auth-service -t auth-service

# Run (requer PostgreSQL acessível)
docker run --rm \
  -e DATABASE_URL="postgresql://user:pass@host.docker.internal:5432/authdb" \
  -e JWT_SECRET="dev-secret" \
  -p 8000:8000 \
  auth-service
```

### Direto (sem Docker)

```bash
cd services/auth-service

# Criar e ativar virtualenv
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar ambiente
export DATABASE_URL="postgresql://user:pass@localhost:5432/authdb"
export JWT_SECRET="dev-secret"

# Executar migrações
alembic upgrade head

# Subir servidor
uvicorn src.main:app --reload --port 8000
```

O serviço ficará disponível em `http://localhost:8000`. Documentação interativa em `http://localhost:8000/docs`.

## Rodando os Testes

```bash
cd services/auth-service
source .venv/bin/activate  # ou ative seu virtualenv

# Testes com cobertura (gate: ≥ 90%)
DATABASE_URL="postgresql://user:pass@localhost/db" \
JWT_SECRET="testsecret" \
pytest

# Relatório HTML de cobertura
make coverage
```

Cobertura atual: **98.5%** (gate CI: 90%).

## Migrações de Banco

```bash
# Aplicar todas as migrações
alembic upgrade head

# Criar nova migration após alterar models
alembic revision --autogenerate -m "descricao"

# Reverter última migration
alembic downgrade -1
```

## CI/CD

Pipeline em [.github/workflows/auth-service.yml](../../.github/workflows/auth-service.yml):

- `lint`: ruff + black --check (paralelo com `test`)
- `test`: pytest com cobertura ≥ 90%
- `build`: docker build (após `test` passar)

## Segurança

- Senhas armazenadas com **bcrypt** — nunca em texto plano
- Tokens JWT com algoritmo **HS256** e expiração configurável via `JWT_EXPIRY_SECONDS`
- Segredos apenas via variáveis de ambiente — nunca hard-coded
- Mensagens de erro idênticas para senha errada e e-mail inexistente (anti-enumeração)
- Logs nunca expõem senhas, tokens completos ou dados sensíveis

## Arquitetura

Diagramas Mermaid versionados junto ao serviço:

- [C4 Container Diagram](docs/architecture/c4-container.md) — visão estrutural dos containers e dependências externas
- [Sequence Diagrams](docs/architecture/sequence.md) — cadastro, login, token inválido/expirado

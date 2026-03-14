# C4 Container Diagram — Auth Service

**Nível**: Container (C4 Nível 2)  
**Serviço**: `auth-service`  
**Atualizado**: 2026-03-13

---

```mermaid
C4Container
    title Container Diagram — Auth Service

    Person(user, "Usuário", "Cadastra-se, faz login e acessa recursos protegidos")
    System_Ext(uploadService, "Upload Job Service", "Valida tokens JWT localmente para proteger endpoints")
    System_Ext(workerService, "Worker Service", "Valida tokens JWT localmente para proteger endpoints")

    Container_Boundary(authBoundary, "auth-service") {
        Container(api, "Auth API", "Python 3.11, FastAPI", "Expõe POST /auth/register, POST /auth/login, GET /auth/me, GET /health, GET /metrics")
        Container(jwtService, "JWT Service", "python-jose, HS256", "Assina e valida tokens JWT com expiração configurável via JWT_EXPIRY_SECONDS")
        Container(passwordService, "Password Service", "passlib / bcrypt", "Hash e verificação de senha com bcrypt — nunca armazena texto plano")
        Container(metricsMiddleware, "Metrics Middleware", "prometheus-fastapi-instrumentator", "Coleta latência p50/p95/p99 e taxa de erros por endpoint")
    }

    ContainerDb(postgres, "PostgreSQL", "PostgreSQL 15", "Tabela users: id, email (único), nome, hashed_password, created_at")

    Rel(user, api, "POST /auth/register, POST /auth/login, GET /auth/me", "HTTPS / REST")
    Rel(api, passwordService, "Hash e verifica senha no cadastro/login", "In-process")
    Rel(api, jwtService, "Gera JWT no login; valida JWT em /auth/me", "In-process")
    Rel(api, postgres, "INSERT usuário; SELECT por e-mail", "PostgreSQL protocol")
    Rel(uploadService, jwtService, "Valida assinatura JWT (sem chamada de rede)", "Chave compartilhada JWT_SECRET")
    Rel(workerService, jwtService, "Valida assinatura JWT (sem chamada de rede)", "Chave compartilhada JWT_SECRET")
```

---

## Elementos

| Elemento | Tipo | Tecnologia | Responsabilidade |
|----------|------|-----------|-----------------|
| Auth API | Container | FastAPI | Endpoints de registro, login, /me, health, metrics |
| JWT Service | Container | python-jose | Geração e validação de tokens HS256 |
| Password Service | Container | passlib/bcrypt | Hash bcrypt; rejeita texto plano |
| Metrics Middleware | Container | prometheus-fastapi-instrumentator | `/metrics` com latência e taxa de erros |
| PostgreSQL | ContainerDb | PostgreSQL 15 | Fonte de verdade para identidades de usuário |

## Decisões de design

- Outros serviços validam JWT **localmente** (sem chamada de rede ao auth-service) — escalabilidade horizontal sem ponto único de falha na validação
- Migrations Alembic executadas automaticamente na inicialização do container
- E-mail inválido e senha incorreta retornam o mesmo `401` para evitar enumeração de usuários (RFC 6749)

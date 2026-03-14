# Sequence Diagrams — Auth Service

**Serviço**: `auth-service`  
**Cobertura**: Happy path (US1 + US2) + erros críticos  
**Atualizado**: 2026-03-13

---

## Fluxo 1 — Happy Path: Cadastro de novo usuário (US1)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Cliente HTTP
    participant API as Auth API (FastAPI)
    participant PwdSvc as Password Service
    participant DB as PostgreSQL

    Client->>API: POST /auth/register {nome, email, password}
    API->>DB: SELECT WHERE email = ?
    DB-->>API: (vazio — e-mail disponível)
    API->>PwdSvc: hash_password(password)
    PwdSvc-->>API: hashed_password (bcrypt)
    API->>DB: INSERT INTO users (id, email, nome, hashed_password, created_at)
    DB-->>API: user inserido
    API-->>Client: 201 Created {id, email, nome, created_at}
```

---

## Fluxo 2 — Happy Path: Login e obtenção de JWT (US2)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Cliente HTTP
    participant API as Auth API (FastAPI)
    participant PwdSvc as Password Service
    participant JWTSvc as JWT Service
    participant DB as PostgreSQL

    Client->>API: POST /auth/login {email, password}
    API->>DB: SELECT WHERE email = ?
    DB-->>API: user {id, hashed_password, ...}
    API->>PwdSvc: verify_password(password, hashed_password)
    PwdSvc-->>API: True
    API->>JWTSvc: create_token({sub: user_id, exp: now + JWT_EXPIRY_SECONDS})
    JWTSvc-->>API: signed JWT (HS256)
    API-->>Client: 200 OK {access_token, token_type: "bearer", expires_in}
```

---

## Fluxo 3 — Erro: Credenciais inválidas

```mermaid
sequenceDiagram
    autonumber
    participant Client as Cliente HTTP
    participant API as Auth API (FastAPI)
    participant PwdSvc as Password Service
    participant DB as PostgreSQL

    Client->>API: POST /auth/login {email, password}
    API->>DB: SELECT WHERE email = ?
    alt E-mail não encontrado
        DB-->>API: (vazio)
        API-->>Client: 401 Unauthorized {"detail": "Credenciais inválidas"}
    else Senha incorreta
        DB-->>API: user {hashed_password}
        API->>PwdSvc: verify_password(password, hashed_password)
        PwdSvc-->>API: False
        API-->>Client: 401 Unauthorized {"detail": "Credenciais inválidas"}
    end
    Note over API: Mesma mensagem genérica para ambos os casos<br/>(evita enumeração de e-mails)
```

---

## Fluxo 4 — Erro: Token expirado ou inválido em endpoint protegido (US3)

```mermaid
sequenceDiagram
    autonumber
    participant Client as Cliente HTTP
    participant API as Auth API (FastAPI)
    participant JWTSvc as JWT Service

    Client->>API: GET /auth/me [Authorization: Bearer <token>]
    API->>JWTSvc: decode_token(token)
    alt Token expirado
        JWTSvc-->>API: ExpiredSignatureError
        API-->>Client: 401 Unauthorized {"detail": "Token expirado"}
    else Token inválido / assinatura incorreta
        JWTSvc-->>API: InvalidTokenError
        API-->>Client: 403 Forbidden {"detail": "Token inválido"}
    end
```

---

## Resumo dos fluxos

| Fluxo | Trigger | Resultado final |
|-------|---------|----------------|
| Cadastro | POST /register com dados válidos | 201 + usuário criado |
| Login | POST /login com credenciais corretas | 200 + JWT |
| Credenciais inválidas | E-mail inexistente ou senha errada | 401 (mensagem genérica) |
| Token inválido/expirado | Bearer token ausente, expirado ou adulterado | 401/403 |

# telehubbi: painel de telemetria veicular

Projeto de estudo: uma API que recebe telemetria de veículos (velocidade, RPM, temperatura do motor, combustível e códigos de falha OBD-II), grava em PostgreSQL e repassa as leituras em tempo real para um painel React via WebSocket.

```
dispositivo → POST /telemetria → PostgreSQL → WebSocket → painel React
```

> **Status:** em desenvolvimento (fase 1: configuração, modelos e ingestão).

## Stack

- **API:** Python 3.12, FastAPI, Pydantic v2, pydantic-settings
- **Banco:** PostgreSQL 16, SQLAlchemy 2.0 async + asyncpg
- **Testes:** pytest, pytest-asyncio, httpx
- **Frontend:** React + Vite (JavaScript) e Recharts
- **Infra:** Docker Compose e GitHub Actions

## Como rodar

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Docker.

```bash
cp .env.example .env      # ajuste a senha
docker compose up -d db   # sobe o Postgres
docker compose ps         # aguarde o status "healthy"
uv sync                   # cria o venv e instala as dependências
```

## Endpoints planejados

| Método | Rota             | Descrição                                                |
| ------ | ---------------- | -------------------------------------------------------- |
| POST   | `/telemetria`    | Ingestão de leituras (auth `Bearer <token>` do dispositivo) |
| GET    | `/telemetria`    | Leituras por período, cruas ou agregadas por janela      |
| GET    | `/falhas`        | Códigos de falha por período                             |
| GET    | `/dispositivos`  | Lista de dispositivos                                    |
| WS     | `/ws/telemetria` | Leituras e alertas em tempo real                         |
| GET    | `/health`        | Healthcheck (inclui o banco)                             |

## Decisões e limitações

- **A identidade do dispositivo vem do token, nunca do corpo da requisição.** Isso impede que um dispositivo envie dados em nome de outro. Os tokens são guardados como hash SHA-256.
- **Os GETs e o WebSocket são públicos** para simplificar a demonstração. Em produção, teriam autenticação de usuário.
- **O broadcast do WebSocket é feito em memória**, então só funciona com um worker. Com várias réplicas, o repasse passaria por Redis pub/sub.
- **Não há migrações:** as tabelas são criadas com `create_all` na inicialização. Em produção, eu usaria Alembic.
- **Todas as datas estão em UTC** (`timestamptz`). Uma leitura com `ts` sem fuso é rejeitada.

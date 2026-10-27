# telehubbi: painel de telemetria veicular

Projeto de estudo: uma API que recebe telemetria de veículos (velocidade, RPM, temperatura do motor, combustível e códigos de falha OBD-II), grava em PostgreSQL e repassa as leituras em tempo real para um painel React via WebSocket.

```
dispositivo → POST /telemetria → PostgreSQL → WebSocket → painel React
```

> **Status:** a ingestão está pronta (`POST /telemetria` com autenticação, validação e persistência). Próximos passos: WebSocket, simulador e painel React.

## Stack

- **API:** Python 3.12, FastAPI, Pydantic v2, pydantic-settings
- **Banco:** PostgreSQL 16, SQLAlchemy 2.0 async + asyncpg
- **Testes:** pytest, pytest-asyncio, httpx
- **Frontend:** React + Vite (JavaScript) e Recharts
- **Infra:** Docker Compose e GitHub Actions

## Como rodar

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Docker.

```bash
cp .env.example .env                      # ajuste a senha
docker compose up -d db                   # sobe o Postgres
docker compose ps                         # aguarde o status "healthy"
uv sync                                   # cria o venv e instala as dependências
uv run python scripts/seed.py --quantidade 2   # cadastra dispositivos e imprime os tokens
uv run fastapi dev src/telehubbi/main.py  # sobe a API em http://localhost:8000
```

O seed imprime os tokens **uma única vez**: o banco guarda só o hash. Guarde-os para autenticar os dispositivos.

A documentação interativa fica em http://localhost:8000/docs. Clique em **Authorize** e cole um token para testar o POST.

### Exemplo de ingestão

```bash
curl -X POST http://localhost:8000/telemetria \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "ts": "2026-10-26T22:15:00Z",
        "velocidade_kmh": 62,
        "rpm": 2100,
        "temperatura_motor_c": 89,
        "combustivel_pct": 71.2,
        "codigos_falha": ["P0300"]
      }'
```

| Resposta | Quando |
| -------- | ------ |
| `201`    | Leitura gravada; devolve a leitura com `id`, `dispositivo_id` e `recebido_em` |
| `401`    | Token ausente ou inválido (a mesma mensagem nos dois casos) |
| `422`    | Payload inválido, com um erro por campo no corpo da resposta |

### Regras de validação

| Campo | Regra |
| ----- | ----- |
| `ts` | data com fuso, obrigatória; não pode estar mais de `TOLERANCIA_FUTURO_S` (padrão 5 s) no futuro |
| `velocidade_kmh` | inteiro de 0 a 300 |
| `rpm` | 0 a 10000 |
| `temperatura_motor_c` | inteiro de −40 a 150 |
| `combustivel_pct` | 0 a 100 |
| `codigos_falha` | lista opcional de códigos OBD-II no formato `^[PCBU][0-3][0-9A-F]{3}$`; duplicados são removidos |

## Estrutura

```
src/telehubbi/
├── config.py        # configuração tipada lida do .env (pydantic-settings)
├── db.py            # engine async, sessão por requisição (get_session) e SessaoDep
├── models.py        # tabelas dispositivos, leituras e falhas
├── schemas.py       # LeituraIn e LeituraOut, com as validações
├── auth.py          # Bearer token → SHA-256 → dispositivo, ou 401
├── main.py          # app FastAPI e lifespan (create_all / dispose)
└── routers/
    └── telemetria.py  # POST /telemetria
scripts/seed.py      # cadastra dispositivos e imprime os tokens
```

## Endpoints

| Método | Rota             | Status | Descrição |
| ------ | ---------------- | ------ | --------- |
| POST   | `/telemetria`    | ✅ pronto | Ingestão de leituras (auth `Bearer <token>` do dispositivo) |
| WS     | `/ws/telemetria` | planejado | Leituras e alertas em tempo real |
| GET    | `/telemetria`    | planejado | Leituras por período, cruas ou agregadas por janela |
| GET    | `/falhas`        | planejado | Códigos de falha por período |
| GET    | `/dispositivos`  | planejado | Lista de dispositivos |
| GET    | `/health`        | planejado | Healthcheck (inclui o banco) |

## Decisões e limitações

- **A identidade do dispositivo vem do token, nunca do corpo da requisição.** Um `dispositivo_id` enviado no corpo é ignorado. Isso impede que um dispositivo envie dados em nome de outro.
- **Os tokens são guardados como hash SHA-256**, e não com bcrypt: o token tem 256 bits aleatórios (`secrets.token_urlsafe(32)`), então um hash rápido é seguro, e o hash determinístico permite buscar o dispositivo por um índice único.
- **`ts` × `recebido_em`:** `ts` é a hora da medição no carro; `recebido_em` é preenchido pelo banco na chegada. Separar os dois permite medir latência e lidar com leituras atrasadas ou fora de ordem.
- **Índice composto `(dispositivo_id, ts)`** em `leituras` e `falhas`, na ordem da consulta típica: igualdade no dispositivo e faixa no tempo.
- **`falhas` repete `dispositivo_id` e `ts`** (desnormalização) para filtrar alertas por período sem JOIN. O risco de inconsistência é baixo: tudo é gravado na mesma transação e leituras não são editadas.
- **Async de ponta a ponta** (asyncpg + `AsyncSession`), para não bloquear o event loop. A sessão usa `expire_on_commit=False` para evitar recarregamentos implícitos depois do commit.
- **Os GETs e o WebSocket serão públicos** para simplificar a demonstração. Em produção, teriam autenticação de usuário.
- **O broadcast do WebSocket será feito em memória**, então só funcionará com um worker. Com várias réplicas, o repasse passaria por Redis pub/sub.
- **Não há migrações:** as tabelas são criadas com `create_all` na inicialização. Em produção, eu usaria Alembic.
- **Todas as datas estão em UTC** (`timestamptz`). Uma leitura com `ts` sem fuso é rejeitada.

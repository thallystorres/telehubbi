# telehubbi: painel de telemetria veicular

Projeto de estudo: uma API que recebe telemetria de veículos (velocidade, RPM, temperatura do motor, combustível e códigos de falha OBD-II), grava em PostgreSQL e repassa as leituras em tempo real para um painel React via WebSocket.

```
dispositivo → POST /telemetria → PostgreSQL → WebSocket → painel React
```

> **Status:** a ingestão (`POST /telemetria`) e o tempo real (`/ws/telemetria`) estão prontos: cada leitura gravada é repassada ao vivo para os clientes WebSocket conectados. Em andamento: simulador. Próximos passos: painel React, consultas por período e testes.

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

Toda resposta HTTP traz o header `X-Tempo-Resposta-Ms`, e cada requisição gera uma linha de log com método, caminho, status e tempo.

### Tempo real (WebSocket)

Conecte um cliente e faça o `curl` acima em outro terminal:

```bash
uv run python -m websockets ws://localhost:8000/ws/telemetria
```

Cada POST aceito gera uma mensagem de leitura e, para cada código de falha, uma mensagem de alerta:

```json
{"tipo": "leitura", "id": 42, "dispositivo_id": 1, "ts": "2026-10-26T22:15:00Z", "recebido_em": "...", "velocidade_kmh": 62, "rpm": 2100.0, "temperatura_motor_c": 89, "combustivel_pct": 71.2, "codigos_falha": ["P0300"]}
{"tipo": "alerta", "dispositivo_id": 1, "ts": "2026-10-26T22:15:00Z", "codigo": "P0300"}
```

Requisições recusadas (401/422) não geram mensagem. O que o cliente envia pelo WebSocket é ignorado.

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
├── ws_manager.py    # ConnectionManager: conexões WS ativas e broadcast
├── main.py          # app FastAPI, lifespan (create_all / dispose), CORS e middleware de log
└── routers/
    ├── telemetria.py  # POST /telemetria + broadcast após o commit
    └── ws.py          # WS /ws/telemetria
scripts/seed.py      # cadastra dispositivos e imprime os tokens
simulador/           # simulador de carro (em andamento)
```

## Endpoints

| Método | Rota             | Status | Descrição |
| ------ | ---------------- | ------ | --------- |
| POST   | `/telemetria`    | ✅ pronto | Ingestão de leituras (auth `Bearer <token>` do dispositivo) |
| WS     | `/ws/telemetria` | ✅ pronto | Leituras e alertas em tempo real |
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
- **O broadcast acontece só depois do commit.** Avisar o painel antes seria anunciar uma leitura que ainda pode sofrer rollback.
- **O broadcast roda em `BackgroundTasks`:** o 201 sai antes, e a latência do dispositivo não depende de quantos navegadores estão conectados nem de quão lentos eles são. O custo: não é uma fila (sem retry nem persistência). É aceitável porque a leitura já está no banco; no pior caso, o painel perde um ponto ao vivo.
- **O broadcast envia para todos os clientes em paralelo** (`asyncio.gather`), com timeout por cliente. Um navegador lento ou desconectado é removido sem afetar os outros nem o POST.
- **O broadcast do WebSocket é feito em memória**, então só funciona com um worker. Com várias réplicas, o repasse passaria por Redis pub/sub.
- **O CORS libera só `GET` e só as origens de `CORS_ORIGINS`** (por padrão, o Vite em `http://localhost:5173`). O POST vem do dispositivo, fora do navegador, e não depende de CORS. O CORS não cobre WebSocket.
- **Os GETs e o WebSocket são públicos** para simplificar a demonstração. Em produção, teriam autenticação de usuário (e o WS checaria o header `Origin`).
- **Não há migrações:** as tabelas são criadas com `create_all` na inicialização. Em produção, eu usaria Alembic.
- **Todas as datas estão em UTC** (`timestamptz`). Uma leitura com `ts` sem fuso é rejeitada.

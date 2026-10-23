# Painel de Telemetria Veicular

## Contexto

Projeto de estudo do Thallys, estudante de TI (UFRN/IMD) e estagiário de backend (Python/Django REST Framework, PostgreSQL, Celery, Redis, Docker, GitHub Actions, AWS).

Ele vai fazer entrevista entre **28 e 30/10/2026** para a bolsa de **Desenvolvedor de Integração de Plataforma Júnior** do projeto Hubbi Autopeças 2.0 (IMD/UFRN). O projeto envolve autodiagnóstico veicular, IoT e modelos de IA.

O objetivo é cobrir lacunas da vaga **e conseguir explicar cada decisão na entrevista**. Entender o código importa mais do que entregar muito código.

Lacunas a cobrir:

- React: nunca usou. Já trabalha com JS, HTML, CSS, Bootstrap e Tailwind.
- FastAPI: conhece pouco. O backend é o terreno dele, mas este é o framework que ele quer aprender aqui.
- WebSocket.
- Dados de séries temporais.
- API de ingestão de telemetria.
- MQTT: cortado da implementação; fica só como tema de discussão.

**Mínimo aceitável:** API recebendo dados + tela React mostrando valores ao vivo via WebSocket.

## Como trabalhar comigo

- **Uma fase por vez.** Ao terminar uma fase, pare, mostre como testar e espere minha confirmação antes de seguir.
- **Passos pequenos.** Faça um commit por passo lógico, com mensagem clara em português.
- **Backend (FastAPI):** é a parte em que o aprendizado precisa ser mais profundo. Siga a seção "Backend: como ensinar FastAPI" abaixo. Não basta o código funcionar: eu preciso entender o que o FastAPI faz por baixo.
- **Frontend (React):** vá em camadas e explique antes de escrever. Não pule direto para a versão final.
  1. componentes estáticos com props;
  2. `useState` com dados falsos via `setInterval`;
  3. `useEffect` + `useRef` + cleanup para o WebSocket real.

  Explique por que cada hook está ali e o que causa uma re-renderização.

- **Ao final de cada fase**, escreva um bloco curto "**Como explicar na entrevista**" com 3–5 pontos.
- Não adicione dependências ou funcionalidades fora deste escopo sem perguntar.

## Backend: como ensinar FastAPI

### Ritual para cada arquivo novo

1. **Antes de escrever:** diga qual é a responsabilidade do arquivo, qual seria o equivalente em Django/DRF e onde ele entra no ciclo de uma requisição.
2. **Escreva o arquivo** com comentários curtos só nas linhas não óbvias. Não comente o que é evidente.
3. **Depois de escrever:** explique o que o FastAPI, o Pydantic ou o SQLAlchemy fazem com aquele código em tempo de execução. Exemplos:
   - "quando chega um POST, o FastAPI lê esta assinatura e...";
   - "este `Depends` é resolvido antes da função, uma vez por request...".
4. **Mostre como observar o comportamento na prática**, por exemplo:
   - um `curl` que deveria dar 401;
   - um payload que deveria dar 422, com a leitura do corpo do erro;
   - onde aquilo aparece no `/docs`;
   - um `print`/log temporário para ver a ordem de execução das dependências.

### Ao final de cada fase do backend

- Faça **3 perguntas de checagem** sobre o funcionamento do FastAPI (não sobre o domínio). Espere minhas respostas e corrija o que eu errar.
- Inclua o bloco "Como explicar na entrevista".

### Peças que eu escrevo

Em cada fase do backend, deixe **uma peça pequena para eu implementar**. Dê o enunciado e dicas, não a solução, e revise depois. Se a fase estiver estourando o tempo, avise e escreva você mesmo, explicando.

- Fase 1: o schema `LeituraOut` e o validador do código OBD-II.
- Fase 2: o `GET /falhas` (espelhando o `GET /telemetria`) e dois testes de validação.
- Fase 3: o teste do WebSocket com o `TestClient`.

### Conceitos por fase

Todos devem ser explicados quando aparecerem no código, sempre com o paralelo Django/DRF quando existir.

**Fase 1: a anatomia de uma requisição**

- **ASGI e as camadas:** Uvicorn (servidor) → Starlette (roteamento, request/response, WebSocket, middleware) → FastAPI (injeção de dependências, validação, OpenAPI) → Pydantic (validação/serialização). Comparar com WSGI/Gunicorn/Django.
- **Caminho completo de um POST:** roteamento → resolução das dependências → parsing e validação do corpo → execução da função → filtragem pelo `response_model` → serialização para JSON.
- **`async def` vs `def`:**
  - uma `def` comum roda num threadpool;
  - uma chamada bloqueante dentro de `async def` trava o event loop de todo mundo;
  - por isso usamos asyncpg e sessão async.
- **Pydantic v2:**
  - `BaseModel`, `Field` com restrições, `field_validator`, `model_config = ConfigDict(from_attributes=True)`;
  - por que separar `In` e `Out` (o serializer do DRF faz os dois papéis);
  - o formato do corpo de erro 422.
- **`pydantic-settings`:** tipagem e validação de variáveis de ambiente vs `settings.py`.
- **SQLAlchemy 2.0 async:**
  - `DeclarativeBase`, `Mapped`/`mapped_column`;
  - `create_async_engine`, `async_sessionmaker`;
  - por que `expire_on_commit=False` em contexto async;
  - comparação com o ORM do Django (sessão explícita vs conexão implícita por request).
- **`Depends`:**
  - o grafo de dependências;
  - o cache por request (a mesma dependência é resolvida uma vez);
  - dependência com `yield` como setup/teardown (abre e fecha a sessão);
  - `Annotated[AsyncSession, Depends(get_session)]` como alias reutilizável;
  - comparação com `authentication_classes`/`permission_classes` e middleware.
- **Segurança:** `HTTPBearer`, `HTTPException(401)` com o header `WWW-Authenticate`, por que guardar o hash do token, `secrets.token_urlsafe`.
- **`APIRouter`:** `prefix`, `tags`, `status_code=201`, `response_model`; `include_router` vs `urls.py`.
- **Lifespan:** o que roda no startup e no shutdown (`create_all`, `engine.dispose()`); por que substituiu `@app.on_event`.
- **OpenAPI:** como o `/docs` é gerado a partir dos type hints, sem configuração.

**Fase 2: leitura, consultas e testes**

- **Query params tipados:** `Annotated[datetime, Query()]`, valores padrão, `Literal` para o intervalo, validação automática e o 422 que resulta dela.
- **SQLAlchemy:**
  - `select()` no estilo 2.0, `where`, `order_by`, `limit`;
  - `func.date_bin`, `func.avg`, `func.max`, `group_by`;
  - por que expressões parametrizadas evitam SQL injection;
  - por que o intervalo vem de um mapa fechado (`{"1m": timedelta(minutes=1), ...}`) e nunca de string livre.
- **Validações entre campos:** `inicio < fim` e intervalo máximo da consulta, via dependência ou `model_validator`.
- **Testes:**
  - fixtures do pytest e escopo;
  - `httpx.AsyncClient` com `ASGITransport` (a app é chamada sem servidor HTTP real);
  - `app.dependency_overrides` para trocar a sessão;
  - banco de teste com isolamento por teste (transação + rollback);
  - modo do pytest-asyncio.
- **Erros:** como o FastAPI monta respostas de erro; quando valeria um `exception_handler` próprio.

**Fase 3: tempo real**

- **WebSocket no Starlette/FastAPI:**
  - `accept`, `send_json`, `receive_text`, `WebSocketDisconnect`;
  - o ciclo de vida de uma conexão;
  - por que o endpoint fica num loop.
- **`ConnectionManager`:**
  - broadcast com `asyncio.gather`;
  - remoção de clientes mortos sem derrubar os outros;
  - estado global em memória e a limitação a um worker (solução com Redis pub/sub).
- **Ordem no POST:** gravar → `commit` → só então fazer o broadcast. Explicar por que fazer o broadcast antes do commit é um bug (avisar algo que pode sofrer rollback).
- **`BackgroundTasks` vs `await` direto no broadcast:** escolher e justificar.
- **Middleware:**
  - `CORSMiddleware` (necessário para o front no Vite) e o que é CORS;
  - um middleware simples de log com o tempo de resposta, para entender a cadeia de middlewares.

## Stack e decisões

- **API:** Python 3.12 + FastAPI.
- **Banco e ORM:** SQLAlchemy 2.0 async + asyncpg + PostgreSQL 16.
- **Configuração:** `pydantic-settings` lendo o `.env`.
- **Migrações:** sem Alembic. Use `create_all` no lifespan para não gastar tempo com migrações; mencionar que em produção usaria Alembic.
- **Testes:** pytest + pytest-asyncio + httpx (`AsyncClient`).
  - WebSocket testado com o `TestClient` do FastAPI.
  - Os testes usam um banco **Postgres** de teste, não SQLite, porque usamos `date_bin` e tipos do Postgres.
- **Frontend:** React + Vite, em **JavaScript puro, sem TypeScript** (decisão consciente: aprender React sem ruído de tipos). Gráficos com **Recharts**, que é declarativo e ajuda a fixar o modelo de componentes.
- **Infra:** Docker Compose com `db`, `api` e `front`; GitHub Actions rodando o pytest.
- **Simulador:** script Python com `httpx`.

## Modelagem

**`dispositivos`**: `id`, `nome`, `token_hash`, `criado_em`

- O token é guardado como hash SHA-256, nunca em texto puro.
- Os dispositivos são criados por `scripts/seed.py`, que imprime os tokens gerados. Não existe endpoint de cadastro.

**`leituras`**: `id` (bigserial), `dispositivo_id` (FK), `ts` (timestamptz, hora da medição no carro), `recebido_em` (timestamptz, hora em que a API recebeu), `velocidade_kmh`, `rpm`, `temperatura_motor_c`, `combustivel_pct`

- Índice composto em `(dispositivo_id, ts)`.

**`falhas`**: `id`, `dispositivo_id` (FK), `leitura_id` (FK), `ts`, `codigo`

- É uma tabela separada porque uma leitura pode trazer vários códigos e o histórico de alertas vira uma consulta simples.

## Endpoints

| Método | Rota             | Descrição                                                                                                                                                                                                      |
| ------ | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| POST   | `/telemetria`    | Ingestão. Auth `Authorization: Bearer <token>`. Retorna 201.                                                                                                                                                   |
| GET    | `/telemetria`    | `dispositivo_id`, `inicio`, `fim`, `intervalo` opcional (ex.: `1m`, `5m`). Sem `intervalo`: leituras cruas, com limite. Com `intervalo`: agregação por janela via `date_bin` (média e máximo de cada métrica). |
| GET    | `/falhas`        | `dispositivo_id`, `inicio`, `fim`, para a carga inicial da lista de alertas.                                                                                                                                   |
| GET    | `/dispositivos`  | Lista os dispositivos (id e nome) para o front.                                                                                                                                                                |
| WS     | `/ws/telemetria` | Repassa em tempo real cada leitura e alerta novos.                                                                                                                                                             |
| GET    | `/health`        | Healthcheck.                                                                                                                                                                                                   |

Os GETs e o WS são públicos para simplificar a demo. Em produção teriam autenticação de usuário; registrar isso no README.

### Payload do POST

```json
{
  "ts": "2026-10-20T22:15:00Z",
  "velocidade_kmh": 62.5,
  "rpm": 2100,
  "temperatura_motor_c": 89.4,
  "combustivel_pct": 71.2,
  "codigos_falha": ["P0300"]
}
```

- **O `dispositivo_id` vem do token, nunca do corpo.** Isso impede que um dispositivo se passe por outro.
- Validações no Pydantic:
  - velocidade de 0 a 300;
  - RPM de 0 a 10000;
  - temperatura de −40 a 150;
  - combustível de 0 a 100;
  - cada código no formato `^[PCBU][0-3][0-9A-F]{3}$`;
  - `ts` não pode estar no futuro (tolerância de ~5 s para relógio dessincronizado).

### Mensagens do WebSocket (tipadas)

```json
{"tipo": "leitura", "dispositivo_id": 1, "ts": "...", "velocidade_kmh": 62.5, ...}
{"tipo": "alerta", "dispositivo_id": 1, "ts": "...", "codigo": "P0300"}
```

O broadcast usa um `ConnectionManager` em memória. **Limitação a explicar:** ele só funciona com um worker. Com várias réplicas, o broadcast passaria por Redis pub/sub. Isso não será implementado, mas deve ser documentado no README.

## Backend: especificação detalhada

**Configuração (`.env`, lida via `pydantic-settings`):**

- `DATABASE_URL` (`postgresql+asyncpg://...`);
- `DATABASE_URL_TESTE`;
- `CORS_ORIGINS` (lista; por padrão `http://localhost:5173`);
- `TOLERANCIA_FUTURO_S` (padrão 5);
- `LIMITE_LEITURAS_CRUAS` (padrão 1000);
- `JANELA_MAXIMA_CONSULTA_H` (padrão 72).

**Datas:**

- tudo em UTC, com `datetime` _timezone-aware_ e colunas `timestamptz`;
- um `ts` sem fuso no payload é rejeitado com 422.

**`POST /telemetria`:**

- Fluxo: autentica → valida → insere a leitura e as falhas **numa única transação** → `commit` → broadcast no WS.
- Respostas:
  - **201** com `LeituraOut`;
  - **401** com token ausente ou inválido (mesma mensagem nos dois casos, para não revelar qual falhou);
  - **422** com payload inválido.
- Códigos de falha duplicados no mesmo payload são deduplicados.

**`GET /telemetria`:**

- Sem `intervalo`: leituras cruas, ordenadas por `ts` ascendente, limitadas a `LIMITE_LEITURAS_CRUAS`.
  - Se o resultado for truncado, indicar isso na resposta, por exemplo com um campo `truncado: true` num envelope `{dados, truncado}`.
- Com `intervalo` (`1m`, `5m`, `15m` ou `1h`): agregação via `date_bin`, devolvendo para cada janela `inicio_janela`, média e máximo de cada métrica e a quantidade de leituras.
- Validações:
  - `inicio < fim`, senão 422;
  - janela maior que `JANELA_MAXIMA_CONSULTA_H`, 422;
  - `dispositivo_id` inexistente, 404.

**`GET /falhas`:** mesmos filtros de período, ordenado por `ts` descendente, com limite.

**`GET /health`:** executa `SELECT 1` no banco e retorna 200, ou 503 se o banco estiver fora. O Compose usa isso no `healthcheck`.

**Testes mínimos (pytest):**

Autenticação:

- POST sem token → 401;
- POST com token inválido → 401;
- POST com token válido → 201 e linha gravada com o `dispositivo_id` do token, mesmo que o corpo tente outro.

Validação:

- velocidade fora da faixa → 422;
- código OBD-II malformado → 422;
- `ts` no futuro → 422;
- `ts` sem fuso → 422.

Falhas:

- POST com dois códigos → duas linhas em `falhas`.

Consultas:

- GET cru respeita o período e a ordem;
- GET agregado com leituras conhecidas → médias e contagens corretas por janela;
- `inicio >= fim` → 422.

WebSocket:

- cliente conectado recebe `{"tipo": "leitura"}` após um POST;
- cliente conectado recebe `{"tipo": "alerta"}` quando há código de falha.

## Simulador

- Usa random walk em vez de valores uniformes:
  - RPM acompanha a velocidade;
  - temperatura sobe até ~90 °C e estabiliza;
  - combustível só desce.
- Envia uma leitura a cada 1 s (`--intervalo`).
- `--devices N`: simula N carros, cada um com seu token (lidos do `.env` ou de argumento).
- `--prob-falha`: probabilidade de anexar um código OBD-II, sorteado de uma lista realista (P0300, P0171, P0420, P0128, P0507...).
- `--backfill-horas H`: gera H horas de histórico antes de entrar no modo ao vivo, para que o `GET` por período tenha o que mostrar.

## Frontend

- **Cards** com velocidade, RPM, temperatura e combustível ao vivo.
- **Seletor de dispositivo.**
- **Gráfico de linha** com janela deslizante dos últimos ~120 pontos, guardados em estado.
- **Lista de alertas**: carga inicial via `GET /falhas` e novos alertas via WS.
- **Reconexão simples** do WebSocket se a conexão cair.
- Explicar o comportamento do `StrictMode` em desenvolvimento: ele monta o efeito duas vezes, o que abriria duas conexões. Por isso o cleanup do `useEffect` é obrigatório.

## Estrutura

```
telemetria/
├── api/
│   ├── app/
│   │   ├── main.py          # app, lifespan, include_router
│   │   ├── config.py        # pydantic-settings
│   │   ├── db.py            # engine async, get_session (Depends com yield)
│   │   ├── models.py
│   │   ├── schemas.py       # LeituraIn, LeituraOut, AgregadoOut...
│   │   ├── auth.py          # dependency autenticar_dispositivo
│   │   ├── ws_manager.py
│   │   └── routers/ (telemetria.py, falhas.py, dispositivos.py, ws.py)
│   ├── scripts/seed.py
│   ├── tests/
│   └── Dockerfile
├── simulador/
├── front/
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

Os nomes de domínio ficam em português (`leituras`, `falhas`, `dispositivos`), com consistência em todo o projeto.

## Fases

Replanejado em 23/10: a fase 1 atrasou, então o ritmo passa a ser concentrado no fim de semana. Thallys continua escrevendo as peças dele em todas as fases; o ritmo não muda isso.

| Fase | Quando           | Conteúdo                                                                                            | Marco                                 |
| ---- | ---------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------- |
| 1    | Sex 23 (noite)   | Compose só com o `db`, venv, `config`/`db`/`models`/`schemas`, `auth`, seed, `POST /telemetria`     | POST funcionando pelo `/docs`         |
| 2    | Sáb 24 (manhã)   | `GET /telemetria` (cru + agregado), `/falhas`, `/dispositivos`, pytest (auth, validação, agregação) | Testes verdes                         |
| 3    | Sáb 24 (tarde)   | `ConnectionManager` + `/ws/telemetria` + simulador completo                                         | `websocat` recebendo leituras ao vivo |
| 4    | Dom 25 (manhã)   | React camadas 1–2: componentes, props, `useState` com dados falsos                                  | Cards atualizando com dados fake      |
| 5    | Dom 25 (tarde)   | React camada 3: WS real, gráfico, alertas                                                           | **Mínimo aceitável**                  |
| 6    | Seg 26           | Compose completo (api, db, front), CI, README com diagrama e decisões                               | Projeto apresentável                  |
| —    | Ter 27 em diante | Buffer e ensaio da explicação (se a entrevista não for no dia 28, o buffer se estende até ela)      | —                                     |

**MQTT e TimescaleDB foram cortados** (decisão de 23/10). Não implementar. Na entrevista, aparecem só como discussão e próximos passos.

**Ordem de corte se faltar tempo:** gráfico → CI.

## Pontos para a entrevista (manter atualizado)

- Fluxo: dispositivo → ingestão → persistência → tempo real → visualização.
- A identidade do dispositivo vem do token, não do payload.
- `ts` vs `recebido_em`: latência e leituras fora de ordem.
- Índice `(dispositivo_id, ts)` e agregação por janela com `date_bin`; quando partir para TimescaleDB.
- Limite do WS em memória e a solução com Redis pub/sub.
- MQTT vs HTTP para IoT: conexão persistente, payload leve, QoS, broker desacoplando produtor e consumidor.
- React: estado, re-render, `useEffect` com cleanup, `useRef` para guardar o socket, `StrictMode`.

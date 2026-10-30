import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from telehubbi.config import settings
from telehubbi.db import Base, engine
from telehubbi.routers import telemetria, ws

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Telehubbi: telemetria veicular", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=[],
)


@app.middleware("http")
async def log_middleware(request: Request, call_next) -> Response:
    tempo_inicio = time.perf_counter()
    metodo = request.method
    caminho = request.url.path

    resposta = await call_next(request)
    tempo_processamento = (time.perf_counter() - tempo_inicio) * 1000
    status = resposta.status_code
    resposta.headers["X-Tempo-Resposta-Ms"] = f"{tempo_processamento:.2f}"

    logger.info(
        "Método: %s | Rota: %s | Status: %s | Tempo: %.2fms",
        metodo,
        caminho,
        status,
        tempo_processamento,
    )

    return resposta


app.include_router(ws.router)
app.include_router(telemetria.router)

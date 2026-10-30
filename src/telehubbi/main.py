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
    method = request.method
    url = request.url.path

    response = await call_next(request)
    tempo_processamento = (time.perf_counter() - tempo_inicio) * 1000
    status_code = response.status_code
    response.headers["X-Tempo-Resposta-Ms"] = f"{tempo_processamento:.2f}"

    logger.info(
        "Método: %s | Rota: %s | Status: %s | Tempo: %.2f",
        method,
        url,
        status_code,
        tempo_processamento,
    )

    return response


app.include_router(ws.router)
app.include_router(telemetria.router)

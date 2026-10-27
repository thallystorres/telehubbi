from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from telehubbi.db import Base, engine
from telehubbi.routers import telemetria


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Telehubbi: telemetria veicular", lifespan=lifespan)
app.include_router(telemetria.router)

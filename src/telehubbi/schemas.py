from datetime import UTC, datetime, timedelta
from typing import Annotated

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from telehubbi.config import settings

VelocidadeKmh = Annotated[int, Field(ge=0, le=300)]
Rpm = Annotated[float, Field(ge=0, le=10000)]
TemperaturaMotorC = Annotated[int, Field(ge=-40, le=150)]
CombustivelPct = Annotated[float, Field(ge=0, le=100)]
CodigoDtc = Annotated[str, StringConstraints(pattern=r"^[PCBU][0-3][0-9A-F]{3}$")]


class LeituraIn(BaseModel):
    ts: AwareDatetime
    velocidade_kmh: VelocidadeKmh
    rpm: Rpm
    temperatura_motor_c: TemperaturaMotorC
    combustivel_pct: CombustivelPct
    codigos_falha: list[CodigoDtc] = []

    @field_validator("ts")
    @classmethod
    def ts_nao_futuro(cls, ts: datetime) -> datetime:
        agora = datetime.now(tz=UTC)
        tolerancia_futuro = timedelta(seconds=settings.TOLERANCIA_FUTURO_S)
        if ts > (agora + tolerancia_futuro):
            raise ValueError(
                f"TS está no futuro em um delta maior que {tolerancia_futuro}."
            )
        return ts

    @field_validator("codigos_falha")
    @classmethod
    def deduplicar_codigos_falha(cls, codigos: list[str]) -> list[str]:
        return list(dict.fromkeys(codigos))


class LeituraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dispositivo_id: int
    ts: AwareDatetime
    recebido_em: AwareDatetime
    velocidade_kmh: VelocidadeKmh
    rpm: Rpm
    temperatura_motor_c: TemperaturaMotorC
    combustivel_pct: CombustivelPct
    codigos_falha: list[CodigoDtc] = []

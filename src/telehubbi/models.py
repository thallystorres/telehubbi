from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from telehubbi.db import Base


class Dispositivo(Base):
    __tablename__ = "dispositivos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    leituras: Mapped[list["Leitura"]] = relationship(back_populates="dispositivo")
    falhas: Mapped[list["Falha"]] = relationship(back_populates="dispositivo")


class Leitura(Base):
    __tablename__ = "leituras"
    __table_args__ = (Index("ix_leituras_dispositivo_ts", "dispositivo_id", "ts"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dispositivo_id: Mapped[int] = mapped_column(ForeignKey("dispositivos.id"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recebido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    velocidade_kmh: Mapped[int]
    rpm: Mapped[float]
    temperatura_motor_c: Mapped[int]
    combustivel_pct: Mapped[float]
    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="leituras")
    falhas: Mapped[list["Falha"]] = relationship(back_populates="leitura")

    @property
    def codigos_falha(self) -> list[str]:
        return [falha.codigo for falha in self.falhas]


class Falha(Base):
    __tablename__ = "falhas"
    __table_args__ = (Index("ix_falhas_dispositivo_ts", "dispositivo_id", "ts"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    codigo: Mapped[str] = mapped_column(String(5))
    dispositivo_id: Mapped[int] = mapped_column(ForeignKey("dispositivos.id"))
    leitura_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("leituras.id"))

    dispositivo: Mapped["Dispositivo"] = relationship(back_populates="falhas")
    leitura: Mapped["Leitura"] = relationship(back_populates="falhas")

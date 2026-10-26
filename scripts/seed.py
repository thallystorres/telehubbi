import argparse
import asyncio
import secrets

from telehubbi.auth import calcular_hash_token
from telehubbi.db import Base, SessionLocal, engine
from telehubbi.models import Dispositivo


def ler_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Script para popular o banco de dados de dispositivos"
    )

    parser.add_argument(
        "--quantidade",
        type=int,
        default=3,
        help="Quantidade de dispositivos a se adicionar",
    )

    return parser.parse_args()


async def criar_tabelas() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def token_e_hash() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = calcular_hash_token(token)
    return (
        token,
        token_hash,
    )


def gerar_dispositivos(quantidade: int) -> dict[str, Dispositivo]:
    dispositivos = {}
    for i in range(1, quantidade + 1):
        token, token_hash = token_e_hash()
        dispositivos[token] = Dispositivo(nome=f"carro-{i}", token_hash=token_hash)
    return dispositivos


async def main() -> None:

    args = ler_argumentos()
    try:
        await criar_tabelas()
        dispositivos = gerar_dispositivos(args.quantidade)

        async with SessionLocal() as sessao:
            sessao.add_all(dispositivos.values())
            await sessao.commit()

    finally:
        await engine.dispose()

    for token, dispositivo in dispositivos.items():
        print(f"{dispositivo.id}) {dispositivo.nome}: {token}")


if __name__ == "__main__":
    asyncio.run(main())

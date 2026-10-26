import argparse
import asyncio

from telehubbi.auth import gerar_token
from telehubbi.db import Base, SessionLocal, engine
from telehubbi.models import Dispositivo


def ler_quantidade() -> int:
    parser = argparse.ArgumentParser(
        description="Script para popular o banco de dados de dispositivos"
    )

    parser.add_argument(
        "--quantidade",
        type=int,
        default=3,
        help="Quantidade de dispositivos a se adicionar",
    )
    args = parser.parse_args()
    if args.quantidade < 1:
        parser.error("Deve haver ao menos um dispositivo criado")

    return args.quantidade


async def criar_tabelas() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def gerar_dispositivos(quantidade: int) -> dict[str, Dispositivo]:
    dispositivos = {}
    for i in range(1, quantidade + 1):
        token, token_hash = gerar_token()
        dispositivos[token] = Dispositivo(nome=f"carro-{i}", token_hash=token_hash)
    return dispositivos


def mostrar_dispositivos(dispositivos: dict[str, Dispositivo]) -> None:
    print("Guarde os tokens: eles não serão exibidos de novo.")
    for token, dispositivo in dispositivos.items():
        print(f"{dispositivo.id}) {dispositivo.nome}: {token}")


async def main() -> None:
    quantidade = ler_quantidade()

    try:
        await criar_tabelas()
        dispositivos = gerar_dispositivos(quantidade)

        async with SessionLocal() as sessao:
            sessao.add_all(dispositivos.values())
            await sessao.commit()

    finally:
        await engine.dispose()

    mostrar_dispositivos(dispositivos)


if __name__ == "__main__":
    asyncio.run(main())

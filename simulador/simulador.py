import argparse


def ler_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulador de veículo para testes da API"
    )

    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="Token de autenticação do veículo",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="URL para a requisição",
    )
    parser.add_argument(
        "--intervalo",
        type=float,
        default=1.0,
        help="Intervalo de envio de requisição em segundos",
    )
    parser.add_argument(
        "--prob-falha",
        type=float,
        default=0.5,
        help="Probabilidade de ocorrer alguma falha pseudo-aleatória",
    )

    return parser.parse_args()

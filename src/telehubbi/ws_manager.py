import asyncio
import json

from fastapi import WebSocket

TIMEOUT_ENVIO_S = 2


class ConnectionManager:
    def __init__(self) -> None:
        self.conexoes: set[WebSocket] = set()

    async def conectar(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.conexoes.add(websocket)

    def desconectar(self, websocket: WebSocket) -> None:
        self.conexoes.discard(websocket)

    async def broadcast(self, mensagem: dict) -> None:
        mensagem_json = json.dumps(mensagem)
        conexoes = list(self.conexoes)
        respostas = await asyncio.gather(
            *(
                asyncio.wait_for(
                    conexao.send_text(mensagem_json), timeout=TIMEOUT_ENVIO_S
                )
                for conexao in conexoes
            ),
            return_exceptions=True,
        )

        for conexao, resposta in zip(conexoes, respostas):
            if isinstance(resposta, Exception):
                self.desconectar(conexao)


gerenciador = ConnectionManager()

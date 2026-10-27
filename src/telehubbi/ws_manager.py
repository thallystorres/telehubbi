import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.conexoes: set[WebSocket] = set()

    async def conectar(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.conexoes.add(websocket)

    def desconectar(self, websocket: WebSocket) -> None:
        self.conexoes.discard(websocket)

    async def broadcast(self, mensagem: dict) -> None:
        conexoes = list(self.conexoes)
        respostas = await asyncio.gather(
            *(conexao.send_json(mensagem) for conexao in conexoes),
            return_exceptions=True,
        )

        for conexao, resposta in zip(conexoes, respostas):
            if isinstance(resposta, Exception):
                self.desconectar(conexao)


gerenciador = ConnectionManager()

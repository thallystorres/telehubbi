from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from telehubbi.ws_manager import gerenciador

router = APIRouter(tags=["ws"])


@router.websocket("/ws/telemetria")
async def receber_websocket(websocket: WebSocket) -> None:
    await gerenciador.conectar(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        gerenciador.desconectar(websocket)

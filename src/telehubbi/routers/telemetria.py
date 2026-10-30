from fastapi import APIRouter, BackgroundTasks, status

from telehubbi.auth import DispositivoAutenticado
from telehubbi.db import SessaoDep
from telehubbi.models import Falha, Leitura
from telehubbi.schemas import LeituraIn, LeituraOut
from telehubbi.ws_manager import gerenciador


def montar_mensagem_alerta(falha: Falha, ts: str) -> dict:
    return {
        "tipo": "alerta",
        "ts": ts,
        "dispositivo_id": falha.dispositivo_id,
        "codigo": falha.codigo,
    }


async def enviar_mensagens(leitura: dict, alertas: list[dict]) -> None:
    await gerenciador.broadcast({**leitura, "tipo": "leitura"})
    for falha in alertas:
        await gerenciador.broadcast(falha)


router = APIRouter(prefix="/telemetria", tags=["telemetria"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LeituraOut)
async def criar_leitura(
    dados: LeituraIn,
    dispositivo: DispositivoAutenticado,
    sessao: SessaoDep,
    background_tasks: BackgroundTasks,
) -> Leitura:
    falhas = [
        Falha(codigo=codigo_falha, ts=dados.ts, dispositivo_id=dispositivo.id)
        for codigo_falha in dados.codigos_falha
    ]
    leitura = Leitura(
        **dados.model_dump(exclude={"codigos_falha"}),
        dispositivo_id=dispositivo.id,
        falhas=falhas,
    )
    sessao.add(leitura)
    await sessao.commit()
    mensagem_leitura = LeituraOut.model_validate(leitura).model_dump(mode="json")
    mensagens_alerta = [
        montar_mensagem_alerta(falha, mensagem_leitura["ts"]) for falha in falhas
    ]
    # Usando BackgroundTasks, o carro não deveria esperar os navegadores receberem as mensagens
    background_tasks.add_task(enviar_mensagens, mensagem_leitura, mensagens_alerta)
    return leitura

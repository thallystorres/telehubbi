from fastapi import APIRouter, status

from telehubbi.auth import DispositivoAutenticado
from telehubbi.db import SessaoDep
from telehubbi.models import Falha, Leitura
from telehubbi.schemas import LeituraIn, LeituraOut

router = APIRouter(prefix="/telemetria", tags=["telemetria"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LeituraOut)
async def criar_leitura(
    dados: LeituraIn, dispositivo: DispositivoAutenticado, sessao: SessaoDep
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
    LeituraOut.model_validate(leitura).model_dump(mode="json")
    return leitura

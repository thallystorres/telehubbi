import hashlib
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from telehubbi.db import SessaoDep
from telehubbi.models import Dispositivo

ERRO_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token ausente ou inválido",
    headers={"WWW-Authenticate": "Bearer"},
)
esquema_bearer = HTTPBearer(auto_error=False)


async def autenticar_dispositivo(
    credenciais: Annotated[
        HTTPAuthorizationCredentials | None, Depends(esquema_bearer)
    ],
    sessao: SessaoDep,
) -> Dispositivo:
    if credenciais is None:
        raise ERRO_401
    token_hash = hashlib.sha256(credenciais.credentials.encode()).hexdigest()
    consulta = select(Dispositivo).where(Dispositivo.token_hash == token_hash)
    dispositivo = await sessao.scalar(consulta)
    if dispositivo is None:
        raise ERRO_401
    return dispositivo


DispositivoAutenticado = Annotated[Dispositivo, Depends(autenticar_dispositivo)]

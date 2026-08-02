from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jwt import encode
from pwdlib import PasswordHash

from fast_zero.settings import Settings

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

pwd_context = PasswordHash.recommended()

settings = Settings()

BOT_KEY_HEADER = APIKeyHeader(name='X-Bot-Api-Key')


async def verify_bot_token(api_key: str = Security(BOT_KEY_HEADER)):
    if api_key != settings.BOT_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Acesso não autorizado: Apenas o Bot tem permissão de chamar esta API.',
        )



def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({'exp': expire})
    encoded_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pwdlib import PasswordHash

from fast_zero.settings import Settings

pwd_context = PasswordHash.recommended()

settings = Settings()

BOT_KEY_HEADER = APIKeyHeader(name='X-Bot-Api-Key')


async def verify_bot_token(api_key: str = Security(BOT_KEY_HEADER)):
    if not secrets.compare_digest(api_key, settings.BOT_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                'Acesso não autorizado: '
                'Apenas o Bot tem permissão de chamar esta API.'
            ),
        )


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


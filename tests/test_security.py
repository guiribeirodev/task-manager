from http import HTTPStatus

from fastapi import HTTPException
import pytest

from fast_zero.security import settings, verify_bot_token


@pytest.mark.asyncio
async def test_verify_bot_token_valid():
    await verify_bot_token(api_key=settings.BOT_KEY)


@pytest.mark.asyncio
async def test_verify_bot_token_invalid():
    with pytest.raises(HTTPException) as exc_info:
        await verify_bot_token(api_key='invalid-key')
    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED

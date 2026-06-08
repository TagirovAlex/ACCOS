from collections.abc import Callable
from typing import Any

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import decode_token


def _rate_limit_key(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            payload = decode_token(token)
            uid = payload.get("sub")
            if uid:
                return f"user:{uid}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)


def rate_limit(limit_str: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    if not settings.rate_limits_enabled:
        return lambda func: func
    return limiter.limit(limit_str)

"""JWT authentication utilities (FastAPI dependency + token helpers)."""
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, HTTPException, Request, status
from fastapi.responses import RedirectResponse


_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
_ALGO = os.getenv("JWT_ALGORITHM", "HS256")
_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "6"))


def create_token(user_id: str, username: str) -> str:
    """Create a signed JWT for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(hours=_EXPIRE_HOURS)
    payload = {"sub": user_id, "username": username, "exp": expire}
    return jwt.encode(payload, _SECRET, algorithm=_ALGO)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT, raises HTTPException on failure."""
    try:
        return jwt.decode(token, _SECRET, algorithms=[_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def get_current_user(request: Request) -> dict:
    """FastAPI dependency: extract and verify the JWT from the cookie."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"},
        )
    return decode_token(token)


def redirect_to_login() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=302)

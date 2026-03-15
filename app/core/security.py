"""
Security helpers: password hashing + JWT encode/decode.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

import bcrypt
from jose import JWTError, ExpiredSignatureError, jwt

from app.core.exceptions.auth import TokenExpiredException, TokenInvalidException

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_REFRESH_EXPIRE_MINUTES", "43200"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def _create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "jti": str(uuid.uuid4()),
    })
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    return _create_token(
        data,
        expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
        "refresh",
    )


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError as exc:
        raise TokenExpiredException() from exc
    except JWTError as exc:
        raise TokenInvalidException() from exc


# Backward-compatible alias

def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token)

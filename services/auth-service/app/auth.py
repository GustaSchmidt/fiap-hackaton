import json
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    # Cache the token in Redis
    user_id = data.get("sub")
    if user_id:
        redis_client.setex(
            f"token:{user_id}",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            encoded_jwt,
        )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def invalidate_token(user_id: str) -> None:
    redis_client.delete(f"token:{user_id}")

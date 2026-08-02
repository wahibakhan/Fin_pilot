import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from src.core.config import get_settings

settings = get_settings()
_password_hasher = PasswordHasher()


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    return _password_hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(*, user_id: uuid.UUID, role: str) -> str:
    return _encode_token(
        subject=str(user_id),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"role": role},
    )


def create_refresh_token(*, user_id: uuid.UUID) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token = _encode_token(
        subject=str(user_id),
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
    return token, expires_at


def _encode_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        # iat/exp only have second-level precision, so without a random
        # component two tokens issued for the same user within the same
        # second (e.g. rapid refresh calls in a test suite) would encode to
        # the identical JWT string — colliding on refresh_tokens.token_hash's
        # unique constraint.
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


class TokenError(Exception):
    """Raised for any invalid/expired/mistyped JWT. Caller maps this to AuthenticationError."""


def decode_token(token: str, *, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if payload.get("type") != expected_type.value:
        raise TokenError(f"Expected a {expected_type.value} token")

    return payload

import uuid
from datetime import timedelta

import jwt
import pytest

from src.core.config import get_settings
from src.core.security import (
    TokenError,
    TokenType,
    _encode_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_roundtrip():
    password = "correct horse battery staple"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")

    assert verify_password("wrong password", hashed) is False


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id, role="accountant")

    payload = decode_token(token, expected_type=TokenType.ACCESS)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "accountant"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    user_id = uuid.uuid4()
    token, expires_at = create_refresh_token(user_id=user_id)

    payload = decode_token(token, expected_type=TokenType.REFRESH)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert expires_at.timestamp() == pytest.approx(payload["exp"], abs=2)


def test_decode_token_rejects_wrong_type():
    user_id = uuid.uuid4()
    access_token = create_access_token(user_id=user_id, role="accountant")

    with pytest.raises(TokenError):
        decode_token(access_token, expected_type=TokenType.REFRESH)


def test_decode_token_rejects_garbage():
    with pytest.raises(TokenError):
        decode_token("not-a-real-token", expected_type=TokenType.ACCESS)


def test_decode_token_rejects_expired_token():
    expired_token = _encode_token(
        subject=str(uuid.uuid4()),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(TokenError):
        decode_token(expired_token, expected_type=TokenType.ACCESS)


def test_decode_token_rejects_wrong_secret():
    user_id = uuid.uuid4()
    settings = get_settings()
    forged = jwt.encode(
        {"sub": str(user_id), "type": "access"},
        "a-different-secret",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(TokenError):
        decode_token(forged, expected_type=TokenType.ACCESS)

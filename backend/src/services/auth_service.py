from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AuthenticationError, ConflictError
from src.core.security import (
    TokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.models.user import User, UserRole
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.user_repository import UserRepository
from src.schemas.auth import TokenPair


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._refresh_tokens = RefreshTokenRepository(db)

    async def register(
        self, *, full_name: str, email: str, password: str, role: UserRole
    ) -> TokenPair:
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        user = await self._users.create(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        return await self._issue_token_pair(user)

    async def login(self, *, email: str, password: str) -> TokenPair:
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        return await self._issue_token_pair(user)

    async def refresh(self, *, refresh_token: str) -> TokenPair:
        try:
            decode_token(refresh_token, expected_type=TokenType.REFRESH)
        except TokenError as exc:
            raise AuthenticationError(str(exc)) from exc

        record = await self._refresh_tokens.get_active_by_token(refresh_token)
        if record is None:
            raise AuthenticationError("Refresh token is invalid, expired, or revoked")

        if record.expires_at < datetime.now(UTC):
            raise AuthenticationError("Refresh token is invalid, expired, or revoked")

        user = await self._users.get_by_id(record.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        # Rotate: revoke the presented token, issue a brand new pair.
        await self._refresh_tokens.revoke(record)
        return await self._issue_token_pair(user)

    async def logout(self, *, refresh_token: str) -> None:
        record = await self._refresh_tokens.get_active_by_token(refresh_token)
        if record is not None:
            await self._refresh_tokens.revoke(record)
        await self._db.commit()

    async def _issue_token_pair(self, user: User) -> TokenPair:
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token, expires_at = create_refresh_token(user_id=user.id)
        await self._refresh_tokens.create(
            user_id=user.id, token=refresh_token, expires_at=expires_at
        )
        await self._db.commit()
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

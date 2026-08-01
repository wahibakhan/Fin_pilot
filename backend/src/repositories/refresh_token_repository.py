import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_token import RefreshToken


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, *, user_id: uuid.UUID, token: str, expires_at: datetime) -> RefreshToken:
        record = RefreshToken(user_id=user_id, token_hash=hash_token(token), expires_at=expires_at)
        self._db.add(record)
        await self._db.flush()
        return record

    async def get_active_by_token(self, token: str) -> RefreshToken | None:
        result = await self._db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(token))
        )
        record = result.scalar_one_or_none()
        if record is None or record.revoked_at is not None:
            return None
        return record

    async def revoke(self, record: RefreshToken) -> None:
        record.revoked_at = datetime.now(UTC)
        await self._db.flush()

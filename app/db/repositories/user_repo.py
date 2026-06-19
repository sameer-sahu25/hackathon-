from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sa_update, func
from typing import Optional, List
import uuid
from datetime import datetime, UTC, timedelta
from app.db.repositories.base_repo import BaseRepository
from app.db.models.user import User
import secrets


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    async def get_by_session_token(self, token: str) -> Optional[User]:
        stmt = select(User).where(User.session_token == token, User.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_anonymous(self) -> User:
        session_token = secrets.token_urlsafe(32)
        user = User(
            session_token=session_token,
            is_anonymous=True
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def upgrade_to_registered(self, user_id: uuid.UUID, email: str, hashed_password: str) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        user.email = email
        user.hashed_password = hashed_password
        user.is_anonymous = False
        user.updated_at = datetime.now(UTC)
        
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_last_active(self, user_id: uuid.UUID) -> None:
        stmt = (
            sa_update(User)
            .where(User.id == user_id, User.is_deleted == False)
            .values(last_active_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def get_users_for_deletion(self) -> List[User]:
        cutoff_date = datetime.now(UTC) - timedelta(days=90)
        stmt = select(User).where(
            User.last_active_at < cutoff_date,
            User.data_deletion_requested_at.isnot(None),
            User.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_state(self, state: str) -> int:
        stmt = select(func.count(User.id)).where(
            User.state == state, User.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def count_anonymous(self) -> int:
        stmt = select(func.count(User.id)).where(
            User.is_anonymous == True, User.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar()

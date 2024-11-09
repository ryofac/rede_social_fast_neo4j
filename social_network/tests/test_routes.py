import pytest
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from social_network.users.models import Base, User

CREATE_LIST_USERS_URL = "/users/"


@pytest.fixture
@pytest.mark.asyncio
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as async_session:
        yield async_session

    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_get_users(session: AsyncSession):
    created_user = User(
        username="roberto_carlos",
        email="roberto@carlos.com",
        full_name="Roberto Carlos",
        password="123321",
    )
    await session.add(created_user)
    await session.commit()
    session.refresh(created_user)

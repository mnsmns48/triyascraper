from asyncio import current_task
from contextlib import asynccontextmanager
from typing import Type

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, async_scoped_session

from config import local_config, DBConfig, oc_config
from v_2_db.model import Base


class Settings():
    def __init__(self, config: DBConfig):
        self.db_url: str = (f"mysql+aiomysql://{config.db_username}:{config.db_password}"
                            f"@{config.db_host}:{config.db_local_port}/{config.db_name}")
        self.db_echo: bool = False


class DataBase:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            poolclass=NullPool
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def scoped_session(self) -> AsyncSession:
        session = async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )
        try:
            async with session() as s:
                yield s
        finally:
            await session.remove()


async def db_start_sync(engine: DataBase, base: Type[Base]):
    async with engine.engine.begin() as async_connect:
        # await async_connect.run_sync(base.metadata.drop_all)
        await async_connect.run_sync(base.metadata.create_all)


db_local_settings = Settings(config=local_config)
db_oc_settings = Settings(config=oc_config)
local_engine = DataBase(db_local_settings.db_url, db_local_settings.db_echo)
oc_engine = DataBase(db_oc_settings.db_url, db_oc_settings.db_echo)

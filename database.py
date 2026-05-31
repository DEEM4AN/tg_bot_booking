from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


# 1. Настройка URL для SQLite (асинхронный драйвер aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///cities.db"

# 2. Создание движка (Engine)
engine = create_async_engine(DATABASE_URL)

# 3. Фабрика сессий (Session Factory)
new_session = async_sessionmaker(engine, expire_on_commit=False)

# 4. Базовый класс моделей
class Model(MappedAsDataclass, DeclarativeBase):
    pass


# Наша зависимость (Ассистент)
async def get_db():
    async with new_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
        
# Создаем аннотацию для типа
# Аннотация говорит: "Это переменная типа AsyncSession, 
# и чтобы её получить, нужно выполнить функцию get_db"

SessionDep = Annotated[AsyncSession, Depends(get_db)]
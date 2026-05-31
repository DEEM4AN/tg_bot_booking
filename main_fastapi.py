import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, KeyboardButton
from aiogram.filters import CommandStart

from fastapi import FastAPI
import uvicorn

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import UsersModel

from contextlib import asynccontextmanager
from database import engine, Model, SessionDep
from routers.routes import router_routes
from handlers.user import user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- КОД ПРИ СТАРТЕ ---
    # Мы обращаемся к движку и просим создать все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    
    print("База данных готова к работе")
    yield  # Разделяет старт и выключение
    # --- КОД ПРИ ВЫКЛЮЧЕНИИ ---
    print("Выключение сервера")


app = FastAPI(lifespan=lifespan)
app.include_router(router_routes)

bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()
dp.include_router(user)

    
async def run_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def run_fastapi():
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    
    await asyncio.gather(
        run_bot(),
        run_fastapi(),
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
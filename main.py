import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
import logging

from aiogram import Bot, Dispatcher

from database import engine, Model
from handlers.user import user
from handlers.admin import admin
from monitor import run_monitor
from database import get_db
from tasks.background_tasks import cleanup_expired_requests

async def main():
    # Создаём таблицы при старте
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    print("База данных готова к работе")
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher()
    dp.include_routers(user, admin)

    await bot.delete_webhook(drop_pending_updates=True)

    await asyncio.gather(
        asyncio.create_task(run_monitor(bot, get_db)),
        dp.start_polling(bot),
        asyncio.create_task(cleanup_expired_requests()),
    )


if __name__ == "__main__":
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s - %(name)s"
    )
    asyncio.run(main())
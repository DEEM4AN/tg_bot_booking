import asyncio
from datetime import datetime
from repositories.user_requests import UserRequestsRepository
from database import get_db


async def cleanup_expired_requests():
    """Проверяет и удаляет истекшие заявки каждый час"""
    while True:
        try:
            async for session in get_db():
                await UserRequestsRepository.deactivate_expired(session)
                print(f"[{datetime.now()}] Проверка истекших заявок выполнена")
        except Exception as e:
            print(f"Error in cleanup_expired_requests: {e}")
        
        # Ждём 1 час перед следующей проверкой (3600 секунд)
        await asyncio.sleep(3600)
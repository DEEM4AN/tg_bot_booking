from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date, time
import os
from dotenv import load_dotenv
load_dotenv()
from repositories.user_requests import UserRequestsRepository
from repositories.users import UsersRepository
from repositories.routes import RoutesRepository
from database import get_db
from sqlalchemy import select, and_
from models.user_requests import UserRequestsModel

admin = Router()

admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── FSM состояния ────────────────────────────────────────────────────────────

class AdminFSM(StatesGroup):
    waiting_for_request_id = State()


# ── Главное меню админа ──────────────────────────────────────────────────────

@admin.message(Command("admint"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return

    from keyboards import userkb as kb
    await message.answer(
        "👨‍💼 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=kb.admin_menu_kb()
    )


# ── Показать все активные заявки ─────────────────────────────────────────────

@admin.callback_query(F.data == "show_all_requests")
async def show_all_requests(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    async for session in get_db():
        try:
            # Очищаем истекшие заявки
            await UserRequestsRepository.deactivate_expired(session)
            
            # Получаем все активные заявки
            result = await session.execute(
                select(UserRequestsModel).where(UserRequestsModel.is_active == True)
            )
            requests = result.scalars().all()

            if not requests:
                await callback.message.edit_text(
                    "📭 Активных заявок нет.",
                    reply_markup=None
                )
                await callback.answer()
                return

            # Формируем список с пагинацией
            from keyboards import userkb as kb
            text = f"📋 Всего активных заявок: {len(requests)}\n\n"
            
            # Показываем первые 10
            for req in requests[:10]:  # ← Убрали enumerate
                user = await UsersRepository.get_by_id(req.user_id, session)
                route = await RoutesRepository.get_by_id(req.route_id, session)
                
                if route and route.from_city and route.to_city:
                    route_name = f"{route.from_city.city_name} → {route.to_city.city_name}"
                else:
                    route_name = f"маршрут #{req.route_id}"

                username = f"@{user.username}" if user.username else f"ID: {user.telegram_id}"
                
                # ✅ Используем req.id вместо счётчика
                text += (
                    f"ID: {req.id}\n"
                    f"   Пользователь: {username}\n"
                    f"   🗺 {route_name}\n"
                    f"   📅 {req.request_date.strftime('%d.%m.%Y')}\n"
                    f"   🕐 {req.time_from.strftime('%H:%M')} — {req.time_to.strftime('%H:%M')}\n"
                    f"   💺 Мест: {req.seats_count}\n\n"
                )

            await callback.message.edit_text(
                text,
                reply_markup=kb.admin_back_kb()
            )
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")
            print(f"Error show_all_requests: {e}")

    await callback.answer()


# ── Деактивировать заявку по ID ──────────────────────────────────────────────

@admin.callback_query(F.data == "deactivate_request")
async def deactivate_request_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "Введите ID заявки для деактивации:\n\n"
        "💡 Подсказка: ID вы видите в списке заявок"
    )
    await state.set_state(AdminFSM.waiting_for_request_id)
    await callback.answer()


# ── Обработка введённого ID ─────────────────────────────────────────────────

@admin.message(AdminFSM.waiting_for_request_id, F.text.isdigit())
async def deactivate_request_by_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен.")
        return

    request_id = int(message.text)

    async for session in get_db():
        try:
            req = await UserRequestsRepository.get_by_id(request_id, session)
            
            if not req:
                await message.answer(f"❌ Заявка с ID {request_id} не найдена.")
                await state.clear()
                return

            if not req.is_active:
                await message.answer(f"⚠️ Заявка с ID {request_id} уже неактивна.")
                await state.clear()
                return

            # Деактивируем
            await UserRequestsRepository.deactivate_by_id(request_id, session)

            user = await UsersRepository.get_by_id(req.user_id, session)
            username = f"@{user.username}" if user.username else f"ID: {user.telegram_id}"

            await message.answer(
                f"✅ Заявка {request_id} деактивирована.\n"
                f"Пользователь: {username}"
            )
            
            # Отправляем уведомление пользователю
            try:
                await message.bot.send_message(
                    chat_id=user.telegram_id,
                    text="ℹ️ Ваша заявка была деактивирована администратором."
                )
            except Exception as e:
                print(f"Could not notify user: {e}")

            await state.clear()

        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
            print(f"Error deactivate_request: {e}")
            await state.clear()


# ── Статистика ──────────────────────────────────────────────────────────────

@admin.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    async for session in get_db():
        try:
            # Активные заявки
            result = await session.execute(
                select(UserRequestsModel).where(UserRequestsModel.is_active == True)
            )
            active_count = len(result.scalars().all())

            # Всего заявок
            result = await session.execute(select(UserRequestsModel))
            total_count = len(result.scalars().all())

            # Всего пользователей
            from models.users import UsersModel
            result = await session.execute(select(UsersModel))
            users_count = len(result.scalars().all())

            stats_text = (
                f"📊 Статистика\n\n"
                f"👥 Всего пользователей: {users_count}\n"
                f"📋 Всего заявок: {total_count}\n"
                f"🟢 Активных заявок: {active_count}\n"
                f"🔴 Деактивных заявок: {total_count - active_count}\n"
            )

            from keyboards import userkb as kb
            await callback.message.edit_text(
                stats_text,
                reply_markup=kb.admin_back_kb()
            )
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка: {e}")
            print(f"Error admin_stats: {e}")

    await callback.answer()


# ── Назад в меню ────────────────────────────────────────────────────────────

@admin.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен", show_alert=True)
        return

    await state.clear()
    from keyboards import userkb as kb
    await callback.message.edit_text(
        "👨‍💼 Админ-панель\n\n"
        "Выберите действие:",
        reply_markup=kb.admin_menu_kb()
    )
    await callback.answer()
from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
 
from schemas.users import SUserAdd
from repositories.users import UsersRepository
from repositories.routes import RoutesRepository
import keyboards.userkb as kb
from keyboards.userkb import RouteCD, DateCD, TimeRangeCD, SeatsCD, make_route_kb
from database import get_db
 
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
 
user = Router()
 
 
class BookingFSM(StatesGroup):
    choosing_route    = State()
    choosing_date     = State()
    choosing_time_from = State()
    choosing_time_to   = State()
    choosing_seats    = State()
 
@user.message(CommandStart())
async def send_welcome(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username

    async for session in get_db():
        user_data = {"telegram_id": user_id, "username": username}
        user_add_instance = SUserAdd(**user_data)

        try:
            new_user, is_new = await UsersRepository.add_one(user_add_instance, session)
            response_text = (
                "Добро пожаловать! Вы успешно зарегистрированы."
                if is_new else
                "Вы уже зарегистрированы ранее. Добро пожаловать обратно!"
            )
            # ✅ Сохраняем user_id В НАЧАЛЕ в состояние FSM
            await state.update_data(user_id=new_user.id)
            await message.answer(response_text, reply_markup=kb.start)
        except Exception as e:
            await message.answer("Произошла ошибка при регистрации.")
            print(f"Error: {e}")
 
 
# ── Шаг 1: показать список маршрутов ──────────────────────────────────────────
 
@user.callback_query(F.data == "select_route")
async def select_route(callback: CallbackQuery, bot: Bot, state: FSMContext):
    async for session in get_db():
        try:
            route_kb = await make_route_kb(session)
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="Выберите направление поездки:",
                reply_markup=route_kb,
            )
            await state.set_state(BookingFSM.choosing_route)
        except Exception as e:
            await callback.answer("Ошибка загрузки маршрутов.")
            print(f"Error: {e}")
    await callback.answer()
 
 
# ── Шаг 2: маршрут выбран → показать календарь ────────────────────────────────
 
@user.callback_query(RouteCD.filter())
async def on_route(callback: CallbackQuery, callback_data: RouteCD, state: FSMContext):
    await state.update_data(route_id=callback_data.route_id)
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=kb.make_date_kb(),
    )
    await state.set_state(BookingFSM.choosing_date)
    await callback.answer()
 
 
# ── Шаг 3: дата выбрана → выбор начала диапазона ─────────────────────────────
 
@user.callback_query(DateCD.filter())
async def on_date(callback: CallbackQuery, callback_data: DateCD, state: FSMContext):
    await state.update_data(date=callback_data.value)
    await callback.message.edit_text(
        "Выберите диапазон времени:\n"
        "Установите начальное время:",
        reply_markup=kb.make_time_kb(is_from=True),
    )
    await state.set_state(BookingFSM.choosing_time_from)
    await callback.answer()
    
 # ── Назад: со времени ОТ → к дате ────────────────────────────────────────────

@user.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=kb.make_date_kb(),
    )
    await state.set_state(BookingFSM.choosing_date)
    await callback.answer()
 
# ── Шаг 4а: начало диапазона выбрано → выбор конца ───────────────────────────
 
@user.callback_query(TimeRangeCD.filter(F.is_from == True))
async def on_time_from(callback: CallbackQuery, callback_data: TimeRangeCD, state: FSMContext):
    await state.update_data(time_from=callback_data.value)
    await callback.message.edit_text(
        f"Начало: {callback_data.value.replace('-', ':')}\nУстановите конечное время:",
        reply_markup=kb.make_time_kb(is_from=False),
    )
    await state.set_state(BookingFSM.choosing_time_to)
    await callback.answer()
# ── Назад: со времени ДО → ко времени ОТ ─────────────────────────────────────

@user.callback_query(F.data == "back_to_time_from")
async def back_to_time_from(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Выберите диапазон времени:\n"
        "Установите начальное время:",
        reply_markup=kb.make_time_kb(is_from=True),
    )
    await state.set_state(BookingFSM.choosing_time_from)
    await callback.answer()
 
# ── Шаг 4б: конец диапазона выбран → выбор мест ──────────────────────────────
 
@user.callback_query(TimeRangeCD.filter(F.is_from == False))
async def on_time_to(callback: CallbackQuery, callback_data: TimeRangeCD, state: FSMContext):
    data = await state.get_data()
    time_from = data["time_from"].replace("-", ":")
    time_to   = callback_data.value.replace("-", ":")
 
    # Проверка: конец должен быть позже начала
    if callback_data.value < data["time_from"]:
        await callback.answer("⚠️ Конечное должно быть позже времени «от»!", show_alert=True)
        return
 
    await state.update_data(time_to=callback_data.value)
    await callback.message.edit_text(
        f"🕐 Диапазон: {time_from} — {time_to}\nСколько мест?",
        reply_markup=kb.make_seats_kb(),
    )
    await state.set_state(BookingFSM.choosing_seats)
    await callback.answer()

# ── Назад: с мест → ко времени ДО ────────────────────────────────────────────

@user.callback_query(F.data == "back_to_time")
async def back_to_time(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    time_from = data.get("time_from", "??-??").replace("-", ":")
    await callback.message.edit_text(
        f"Начало: {time_from}\nУстановите конечное время:",
        reply_markup=kb.make_time_kb(is_from=False),
    )
    await state.set_state(BookingFSM.choosing_time_to)
    await callback.answer()
 
# ── Шаг 5: места выбраны → итог ──────────────────────────────────────────────
 
@user.callback_query(SeatsCD.filter())
async def on_seats(callback: CallbackQuery, callback_data: SeatsCD, state: FSMContext):
    await state.update_data(seats=callback_data.n)
    data = await state.get_data()
    
    async for session in get_db():
        try:
            route = await RoutesRepository.get_by_id(data['route_id'], session)
            if route and route.from_city and route.to_city:
                route_name = f"{route.from_city.city_name} → {route.to_city.city_name}"
            else:
                route_name = f"маршрут #{data['route_id']}"
            
            text = (
                f"✅ Маршрут: {route_name}\n"
                f"📅 Дата: {data['date']}\n"
                f"🕐 Время: {data['time_from'].replace('-', ':')} — {data['time_to'].replace('-', ':')}\n"
                f"💺 Мест: {callback_data.n}"
            )
            await callback.message.edit_text(text, reply_markup=kb.confirm_kb)
        except Exception as e:
            await callback.message.edit_text("Ошибка при загрузке маршрута.")
            print(f"Error: {e}")
    
    await callback.answer()
    
# ── Подтверждение → сохранить в БД ───────────────────────────────────────────
 
@user.callback_query(F.data == "confirm_booking")
async def on_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    async for session in get_db():
        try:
            from repositories.user_requests import UserRequestsRepository
            from schemas.user_requests import SUserRequestAdd
            from datetime import date, time

            request = SUserRequestAdd(
                user_id=data["user_id"],
                route_id=data["route_id"],
                request_date=date.fromisoformat(data["date"]),
                time_from=time(*map(int, data["time_from"].split("-"))),
                time_to=time(*map(int, data["time_to"].split("-"))),
                seats_count=data["seats"],
            )
            await UserRequestsRepository.add_one(request, session)
            await callback.message.edit_text(
                "🎉 Готово! Слежу за местами и пришлю уведомление как только что-то появится.\n\n"
                "📋 /status — посмотреть текущую заявку\n"
                "🔕 /stop — остановить уведомления\n"
                "🔄 /start — изменить заявку"
            )
            await state.clear()
        except Exception as e:
            await callback.message.edit_text("Ошибка при сохранении. Попробуйте ещё раз.")
            print(f"Error: {e}")
    await callback.answer()
 
 
 
@user.callback_query(F.data == "cancel_booking")
async def on_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Бронирование отменено.",
        reply_markup=kb.start,
    )
    await callback.answer()
 
 
@user.callback_query(F.data == "back_to_seats")
async def back_to_seats(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Сколько мест?",
        reply_markup=kb.make_seats_kb(),
    )
    await state.set_state(BookingFSM.choosing_seats)
    await callback.answer()

#  ── /stop — остановка заявки ────────────────────────────────────────

    
@user.message(Command("stop"))
async def cmd_stop(message: Message):
    async for session in get_db():
        try:
            from repositories.user_requests import UserRequestsRepository
            # получите user_id из БД по telegram_id
            await UserRequestsRepository.deactivate(message.from_user.id, session)
            await message.answer("🔕 Уведомления отключены. Все ваши заявки деактивированы.")
        except Exception as e:
            await message.answer("Ошибка при отключении уведомлений.")
            print(f"Error: {e}")
 
# ── /status — текущая активная заявка ────────────────────────────────────────

@user.message(Command("status"))
async def cmd_status(message: Message, state: FSMContext):
    async for session in get_db():
        try:
            fsm_data = await state.get_data()
            user_id = fsm_data.get("user_id")

            if not user_id:
                from repositories.users import UsersRepository
                db_user = await UsersRepository.get_by_telegram_id(message.from_user.id, session)
                if db_user:
                    user_id = db_user.id

            if not user_id:
                await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
                return

            from repositories.user_requests import UserRequestsRepository
            req = await UserRequestsRepository.get_active_by_user(user_id, session)
            if not req:
                await message.answer(
                    "У вас нет активных заявок.\n"
                    "Нажмите /start чтобы создать новую."
                )
                return

            route = await RoutesRepository.get_by_id(req.route_id, session)
            if route and route.from_city and route.to_city:
                route_name = f"{route.from_city.city_name} → {route.to_city.city_name}"
            else:
                # Крайний случай — берём из get_all_city_with_names
                all_routes = await RoutesRepository.get_all_city_with_names(session)
                match = next((r for r in all_routes if r[2] == req.route_id), None)
                route_name = f"{match[0]} → {match[1]}" if match else f"маршрут #{req.route_id}"

            await message.answer(
                f"📋 Ваша активная заявка:\n\n"
                f"🗺 Маршрут: {route_name}\n"
                f"📅 Дата: {req.request_date.strftime('%d.%m.%Y')}\n"
                f"🕐 Время: {req.time_from.strftime('%H:%M')} — {req.time_to.strftime('%H:%M')}\n"
                f"💺 Мест: {req.seats_count}\n\n"
                f"🔕 /stop — остановить уведомления\n"
                f"🔄 /start — изменить заявку"
            )
        except Exception as e:
            await message.answer("Ошибка при получении заявки.")
            print(f"Error cmd_status: {e}")
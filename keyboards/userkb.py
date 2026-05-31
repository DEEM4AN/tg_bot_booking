from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from datetime import date, timedelta
from aiogram.filters.callback_data import CallbackData
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.routes import RoutesRepository

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Выбрать машрут")], 
], resize_keyboard=True)

start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Выбрать маршрут', callback_data="select_route")]
])

routes = InlineKeyboardMarkup(inline_keyboard=[   # ЗАГЛУШКА. ДОРАБОТАТЬ
    [InlineKeyboardButton(text='Минск-Мозырь', callback_data="from_minsk")],
    [InlineKeyboardButton(text='Мозырь-Минск', callback_data="from_mozyr")]
])




# --- CallbackData factories (рекомендуется вместо сырых строк) ---
class RouteCD(CallbackData, prefix="route"):
    route_id: int

class DateCD(CallbackData, prefix="date"):
    value: str  # YYYY-MM-DD

class TimeCD(CallbackData, prefix="time"):
    value: str  # HH-MM

class SeatsCD(CallbackData, prefix="seats"):
    n: int

class TimeRangeCD(CallbackData, prefix="tr"):
    value: str      # "HH-MM"
    is_from: bool   # True = выбираем начало, False = выбираем конец


async def make_route_kb(session: AsyncSession) -> InlineKeyboardMarkup:
    """Кнопки всех маршрутов из БД, по 2 в строке."""
    routes = await RoutesRepository.get_all_city_with_names(session)

    buttons = []
    row = []

    for from_city, to_city, route_id in routes:
        label = f"{from_city} → {to_city}"
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=RouteCD(route_id=route_id).pack()
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def make_date_kb() -> InlineKeyboardMarkup:
    """30 дней начиная с сегодня, по 3 кнопки в строке."""
    today = date.today()
    buttons = []
    row = []
    for i in range(0, 31):
        d = today + timedelta(days=i)
        label = d.strftime("%d.%m")  # «01.06»
        row.append(InlineKeyboardButton(
            text=label,
            callback_data=DateCD(value=d.isoformat()).pack()
        ))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="select_route")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def make_time_kb(is_from: bool = True) -> InlineKeyboardMarkup:
    """00:00–23:30 с шагом 30 минут, по 4 кнопки в строке."""
    buttons = []
    row = []
    for h in range(24):
        for m in (0, 30):
            label = f"{h:02d}:{m:02d}"
            row.append(InlineKeyboardButton(
                text=label,
                callback_data=TimeRangeCD(value=f"{h:02d}-{m:02d}", is_from=is_from).pack()
            ))
            if len(row) == 4:
                buttons.append(row)
                row = []
    if row:
        buttons.append(row)

    back_cb = "back_to_date" if is_from else "back_to_time_from"
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def make_seats_kb() -> InlineKeyboardMarkup:
    """1–4 места."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(n), callback_data=SeatsCD(n=n).pack()) for n in range(1, 5)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_time")]
        
    ])

confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
        InlineKeyboardButton(text="❌ Отменить",    callback_data="cancel_booking"),
    ],
    [
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_seats"),
    ]
])



def admin_menu_kb():
    """Главное меню админа"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все заявки", callback_data="show_all_requests")],
        [InlineKeyboardButton(text="❌ Деактивировать", callback_data="deactivate_request")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
    ])
    return kb


def admin_back_kb():
    """Кнопка назад"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")],
    ])
    return kb
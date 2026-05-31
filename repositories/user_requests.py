from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.user_requests import UserRequestsModel
from schemas.user_requests import SUserRequestAdd
from datetime import date, time, datetime


class UserRequestsRepository:
    @classmethod
    async def add_one(cls, data: SUserRequestAdd, session: AsyncSession) -> UserRequestsModel:
        # Деактивируем предыдущую заявку пользователя (1 заявка на пользователя)
        await session.execute(
            update(UserRequestsModel)
            .where(UserRequestsModel.user_id == data.user_id)
            .values(is_active=False)
        )

        obj = UserRequestsModel(**data.model_dump())
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    @classmethod
    async def get_active(cls, session: AsyncSession) -> list[UserRequestsModel]:
        """Все активные заявки (is_active=True, notified=False)."""
        query = select(UserRequestsModel).where(
            UserRequestsModel.is_active == True,
            UserRequestsModel.notified == False,
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_monitor_params(cls, session: AsyncSession) -> list[dict]:
        """
        Возвращает параметры для мониторинга по каждой активной заявке:
        {
            "user_id":    <telegram_id пользователя>,
            "base_url":   "https://smilebus.by/api/v2/route/schedule-detail?id_city_from=X&id_city_to=Y&date=",
            "dates":      ["2025-06-01", ...],   # одна дата из заявки
            "time_slots": ["12:00", "12:30", ...]  # шаг 30 мин в диапазоне time_from..time_to
            "seats_count": req.seats_count
        }
        """
        from models.routes import RoutesModel
        from models.cities import CitiesModel
        from models.users import UsersModel
        from sqlalchemy.orm import aliased
        from datetime import datetime, timedelta

        FromCity = aliased(CitiesModel)
        ToCity = aliased(CitiesModel)

        query = (
            select(
                UserRequestsModel,
                RoutesModel.from_city_id,
                RoutesModel.to_city_id,
                UsersModel.telegram_id,
            )
            .join(RoutesModel, UserRequestsModel.route_id == RoutesModel.id)
            .join(UsersModel, UserRequestsModel.user_id == UsersModel.id)
            .where(
                UserRequestsModel.is_active == True,
                UserRequestsModel.notified == False,
            )
        )
        result = await session.execute(query)
        rows = result.all()

        params = []
        for req, from_city_id, to_city_id, telegram_id in rows:
            # Генерируем временные слоты с шагом 30 минут в диапазоне [time_from, time_to)
            slots = []
            cursor = datetime.combine(req.request_date, req.time_from)
            end    = datetime.combine(req.request_date, req.time_to)
            while cursor <= end:
                slots.append(cursor.strftime("%H:%M"))
                cursor += timedelta(minutes=30)

            params.append({
                "telegram_id": telegram_id,
                "base_url": (
                    f"https://smilebus.by/api/v2/route/schedule-detail"
                    f"?id_city_from={from_city_id}&id_city_to={to_city_id}&date="
                ),
                "dates":      [req.request_date.isoformat()],
                "time_slots": slots,
                "seats_count": req.seats_count,
            })

        return params

    @classmethod
    async def deactivate(cls, telegram_id: int, session: AsyncSession) -> None:
        """Отключить все заявки пользователя (/stop) по telegram_id."""
        from models.users import UsersModel

        subq = select(UsersModel.id).where(UsersModel.telegram_id == telegram_id).scalar_subquery()
        await session.execute(
            update(UserRequestsModel)
            .where(UserRequestsModel.user_id == subq)
            .values(is_active=False)
        )
        await session.commit()
        
    @classmethod
    async def get_active_by_user(cls, user_id: int, session: AsyncSession) -> UserRequestsModel | None:
        result = await session.execute(
            select(UserRequestsModel).where(
                UserRequestsModel.user_id == user_id,
                UserRequestsModel.is_active == True,
            )
        )
        return result.scalar_one_or_none()
    

    @staticmethod
    async def deactivate_expired(session):
        from datetime import datetime
        from sqlalchemy import and_, func
        """Деактивирует все истекшие заявки"""
        # Получаем все активные заявки
        result = await session.execute(
            select(UserRequestsModel).where(UserRequestsModel.is_active == True)
        )
        requests = result.scalars().all()
        
        for req in requests:
            # Объединяем дату и время_to
            req_datetime = datetime.combine(req.request_date, req.time_to)
            
            if req_datetime < datetime.now():
                req.is_active = False
        
        await session.commit()

    @staticmethod
    async def get_by_id(request_id: int, session):
        """Получить заявку по ID"""
        result = await session.execute(
            select(UserRequestsModel).where(UserRequestsModel.id == request_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def deactivate_by_id(request_id: int, session):
        """Деактивировать заявку по ID"""
        req = await UserRequestsRepository.get_by_id(request_id, session)
        if req:
            req.is_active = False
            await session.commit()
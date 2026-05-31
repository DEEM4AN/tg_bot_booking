from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
from models.routes import RoutesModel
from schemas.routes import SRouteAdd, SRouteUpdate
from sqlalchemy.orm import selectinload


class RoutesRepository:
    @classmethod
    async def add_one(cls, data: SRouteAdd, session: AsyncSession) -> RoutesModel:
        route_dict = data.model_dump()
        route = RoutesModel(**route_dict)

        session.add(route)
        try:
            await session.commit()
            await session.refresh(route)
        except IntegrityError as e:
            await session.rollback()  # Откатить транзакцию в случае ошибки
            raise Exception("Integrity error: possible violation of foreign key constraints.") from e

        return route

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(RoutesModel)
        result = await session.execute(query)
        route_models = result.scalars().all()
        return route_models

    @classmethod
    async def get_one(cls, id: int, session: AsyncSession) -> RoutesModel:
        query = select(RoutesModel).where(RoutesModel.id == id)
        result = await session.execute(query)
        route = result.scalar_one_or_none()
        
        if route is None:
            raise NoResultFound(f"Route with id {id} not found.")
        
        return route

    @classmethod
    async def update_one(cls, id: int, data: SRouteUpdate, session: AsyncSession) -> RoutesModel:
        route = await cls.get_one(id, session)  # Проверить, существует ли маршрут
        
        # Применяем обновления из Pydantic
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(route, key, value)

        try:
            await session.commit()
            await session.refresh(route)
        except IntegrityError as e:
            await session.rollback()  # Откатить транзакцию в случае ошибки
            raise Exception("Integrity error: possible violation of foreign key constraints.") from e
        
        return route

    @classmethod
    async def delete_one(cls, id: int, session: AsyncSession) -> None:
        route = await cls.get_one(id, session)  # Проверить, существует ли маршрут
        
        await session.delete(route)

        try:
            await session.commit()
        except IntegrityError as e:
            await session.rollback()  # Откатить транзакцию в случае ошибки
            raise Exception("Integrity error: possible violation of foreign key constraints.") from e

    @classmethod
    async def get_all_city_with_names(cls, session: AsyncSession) -> list[tuple[str, str, int]]:
        query = (
            select(RoutesModel)
            .options(
                selectinload(RoutesModel.from_city),
                selectinload(RoutesModel.to_city)
            )
        )
        result = await session.execute(query)
        routes = result.scalars().all()

        city_pairs = [
            (route.from_city.city_name, route.to_city.city_name, route.id)
            for route in routes
        ]

        return city_pairs
    
    @classmethod
    async def get_by_id(cls, route_id: int, session: AsyncSession):
        from sqlalchemy.orm import selectinload
        from models.routes import RoutesModel
        result = await session.execute(
            select(RoutesModel)
            .options(selectinload(RoutesModel.from_city), selectinload(RoutesModel.to_city))
            .where(RoutesModel.id == route_id)
        )
        return result.scalar_one_or_none()
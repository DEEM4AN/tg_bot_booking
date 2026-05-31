from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
from models.cities import CitiesModel
from schemas.cities import SCity, SCityAdd, SCityUpdate

class CitiesRepository:
    @classmethod
    async def add_one(cls, data: SCityAdd, session: AsyncSession) -> CitiesModel:
        city_dict = data.model_dump()  # Преобразуем данные из Pydantic в словарь
        city = CitiesModel(**city_dict)  # Создаем объект модели

        session.add(city)
        try:
            await session.commit()  # Сохраняем изменения в базе данных
            await session.refresh(city)  # Обновляем объект на основе данных из БД
        except IntegrityError as e:
            await session.rollback()  # Откат транзакции в случае ошибки
            raise Exception("Integrity error: possible violation of foreign key constraints.") from e

        return city

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(CitiesModel)
        result = await session.execute(query)
        city_models = result.scalars().all()  # Извлекаем все города
        return city_models

    @classmethod
    async def get_one(cls, id: int, session: AsyncSession) -> CitiesModel:
        query = select(CitiesModel).where(CitiesModel.id_city == id)
        result = await session.execute(query)
        city = result.scalar_one_or_none()

        if city is None:
            raise NoResultFound(f"City with id {id} not found.")
        
        return city

    @classmethod
    async def update_one(cls, id: int, data: SCityUpdate, session: AsyncSession) -> CitiesModel:
        city = await cls.get_one(id, session)  # Проверка существования города

        for key, value in data.model_dump(exclude_unset=True).items():  # Применяем обновление
            setattr(city, key, value)

        try:
            await session.commit()
            await session.refresh(city)  # Обновляем объект
        except IntegrityError as e:
            await session.rollback()  # Откат транзакции в случае ошибки
            raise Exception("Integrity error: possible violation of foreign key constraints.") from e
        
        return city

    @classmethod
    async def delete_one(cls, id: int, session: AsyncSession) -> None:
        city = await cls.get_one(id, session)  # Проверка существования города

        await session.delete(city)  # Удаляем объект

        try:
            await session.commit()  # Сохраняем изменения
        except IntegrityError as e:
            await session.rollback()  # Откат транзакции в случае ошибки
            raise Exception("Integrity error: possible violation of foreign key constraints.") from e

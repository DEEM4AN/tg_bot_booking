from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
from models.users import UsersModel
from schemas.users import SUser, SUserAdd, SUserUpdate  # Импортируем необходимые схемы

class UsersRepository:
    @classmethod
    async def add_one(cls, data: SUserAdd, session: AsyncSession) -> UsersModel:
        user_dict = data.model_dump()  # Преобразуем данные из Pydantic в словарь
        user = UsersModel(**user_dict)  # Создаем объект модели
         # Проверяем, существует ли пользователь с таким telegram_id
        existing_user = await session.execute(
            select(UsersModel).where(UsersModel.telegram_id == user_dict["telegram_id"])
        )
        existing_user = existing_user.scalar_one_or_none()

        if existing_user:
            print(f"Пользователь с telegram_id={user_dict['telegram_id']} уже существует")
            return existing_user, False  # False — пользователь не новый

        user = UsersModel(**user_dict)
        session.add(user)

        try:
            await session.commit()
            await session.refresh(user)
            return user, True  # True — пользователь новый
        except Exception as e:
            await session.rollback()
            raise Exception(f"Unexpected error while saving user: {e}") from e

        return user

    @classmethod
    async def get_all(cls, session: AsyncSession):
        query = select(UsersModel)
        result = await session.execute(query)
        user_models = result.scalars().all()  # Извлекаем всех пользователей
        return user_models

    @classmethod
    async def get_one(cls, telegram_id: int, session: AsyncSession) -> UsersModel:
        query = select(UsersModel).where(UsersModel.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            raise NoResultFound(f"User with telegram_id {telegram_id} not found.")
        
        return user

    @classmethod
    async def update_one(cls, telegram_id: int, data: SUserUpdate, session: AsyncSession) -> UsersModel:
        user = await cls.get_one(telegram_id, session)  # Проверка существования пользователя

        for key, value in data.model_dump(exclude_unset=True).items():  # Применяем обновление
            setattr(user, key, value)

        try:
            await session.commit()
            await session.refresh(user)  # Обновляем объект
        except IntegrityError as e:
            await session.rollback()  # Откат транзакции в случае ошибки
            raise Exception("Integrity error: possible violation of unique constraints.") from e
        
        return user

    @classmethod
    async def delete_one(cls, telegram_id: int, session: AsyncSession) -> None:
        user = await cls.get_one(telegram_id, session)  # Проверка существования пользователя

        await session.delete(user)  # Удаляем объект

        try:
            await session.commit()  # Сохраняем изменения
        except IntegrityError as e:
            await session.rollback()  # Откат транзакции в случае ошибки
            raise Exception("Integrity error: possible violation of constraints.") from e

    @classmethod
    async def get_by_telegram_id(cls, telegram_id: int, session: AsyncSession):
        from models.users import UsersModel
        result = await session.execute(
            select(UsersModel).where(UsersModel.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_id(cls, user_id: int, session: AsyncSession):
        result = await session.execute(
            select(UsersModel).where(UsersModel.id == user_id)
        )
        return result.scalar_one_or_none()
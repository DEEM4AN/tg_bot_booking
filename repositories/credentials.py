from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user_credentials import UserCredentialsModel
from services.crypto import encrypt, decrypt


class CredentialsRepository:

    @classmethod
    async def save(cls, user_id: int, login: str, password: str, session: AsyncSession) -> None:
        """Сохранить (или обновить) зашифрованные логин/пароль пользователя."""
        existing = await cls._get_model(user_id, session)
        if existing:
            existing.login = encrypt(login)
            existing.password = encrypt(password)
        else:
            obj = UserCredentialsModel(
                user_id=user_id,
                login=encrypt(login),
                password=encrypt(password),
            )
            session.add(obj)
        await session.commit()

    @classmethod
    async def get(cls, user_id: int, session: AsyncSession) -> tuple[str, str] | None:
        """Вернуть (login, password) в открытом виде или None если нет записи."""
        row = await cls._get_model(user_id, session)
        if row is None:
            return None
        return decrypt(row.login), decrypt(row.password)

    @classmethod
    async def exists(cls, user_id: int, session: AsyncSession) -> bool:
        """Есть ли сохранённые данные у пользователя."""
        return await cls._get_model(user_id, session) is not None

    @classmethod
    async def _get_model(cls, user_id: int, session: AsyncSession) -> UserCredentialsModel | None:
        result = await session.execute(
            select(UserCredentialsModel).where(UserCredentialsModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

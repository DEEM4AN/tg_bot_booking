from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Model
from sqlalchemy import Column, BigInteger, Integer, String


class UsersModel(Model):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
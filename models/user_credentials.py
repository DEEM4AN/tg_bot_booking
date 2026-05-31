from sqlalchemy import Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Model


class UserCredentialsModel(Model):
    __tablename__ = "user_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    login: Mapped[str] = mapped_column(String, nullable=False)       # зашифровано Fernet
    password: Mapped[str] = mapped_column(String, nullable=False)    # зашифровано Fernet

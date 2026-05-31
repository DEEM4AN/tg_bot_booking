from sqlalchemy import ForeignKey, Date, Time, Integer, Boolean, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Model
from datetime import date, time, datetime


class UserRequestsModel(Model):
    __tablename__ = "user_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(Integer, ForeignKey("routes.id"), nullable=False)
    request_date: Mapped[date] = mapped_column(Date, nullable=False)
    time_from: Mapped[time] = mapped_column(Time, nullable=False)   # начало диапазона
    time_to: Mapped[time] = mapped_column(Time, nullable=False)     # конец диапазона
    seats_count: Mapped[int] = mapped_column(Integer, nullable=False)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # False после /stop

    __table_args__ = (
        CheckConstraint("seats_count > 0 AND seats_count <= 4", name="ck_seats_count"),
        CheckConstraint("time_to >= time_from", name="ck_time_range"),
    )
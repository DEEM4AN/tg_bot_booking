from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Model


class CitiesModel(Model):
    __tablename__ = "cities"

    id_city: Mapped[int] = mapped_column(primary_key=True, init = False)
    city_name: Mapped[str]
        
    routes_from: Mapped[list["RoutesModel"]] = relationship(
        "RoutesModel",
        back_populates="from_city",
        foreign_keys="[RoutesModel.from_city_id]"
    )
    routes_to: Mapped[list["RoutesModel"]] = relationship(
        "RoutesModel",
        back_populates="to_city",
        foreign_keys="[RoutesModel.to_city_id]"
    )
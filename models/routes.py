from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Model
from sqlalchemy import Integer, ForeignKey
from .cities import CitiesModel


class RoutesModel(Model):
    __tablename__ = "routes"
        
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, init=False)
    
    from_city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.id_city'), nullable=False)
    to_city_id: Mapped[int] = mapped_column(Integer, ForeignKey('cities.id_city'), nullable=False)
    
    # Устанавливаем отношения между таблицами
    from_city = relationship("CitiesModel", foreign_keys=[from_city_id])
    to_city = relationship("CitiesModel", foreign_keys=[to_city_id])
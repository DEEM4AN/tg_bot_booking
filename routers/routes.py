from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from models.routes import RoutesModel
from models.routes import CitiesModel
from schemas.routes import SRouteAdd, SRouteUpdate, SRoute
from schemas.cities import SCityAdd, SCityUpdate
from repositories.routes import RoutesRepository
from repositories.cities import CitiesRepository
from repositories.users import UsersRepository
from database import SessionDep  

router_routes = APIRouter()

@router_routes.post("/routes", response_model=RoutesModel, status_code=status.HTTP_201_CREATED, description="Добавление маршрута")
async def add_route(route: SRouteAdd, session: SessionDep):
    route_model = await RoutesRepository.add_one(route, session)
    return route_model

@router_routes.get("/routes", response_model=list[SRoute], description="Получение всех маршрутов")
async def get_routes(session: SessionDep):
    return await RoutesRepository.get_all(session)

@router_routes.get("/routes/{id}", response_model=RoutesModel, description="Получение маршрута по ID")
async def get_route(id: int, session: SessionDep):
    try:
        route = await RoutesRepository.get_one(id, session)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return route

@router_routes.put("/routes/{id}", response_model=RoutesModel, description="Обновление маршрута по ID")
async def update_route(id: int, route: SRouteUpdate, session: SessionDep):
    try:
        updated_route = await RoutesRepository.update_one(id, route, session)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return updated_route

@router_routes.delete("/routes/{id}", response_model=None, status_code=status.HTTP_204_NO_CONTENT, description="Удаление маршрута по ID")
async def delete_route(id: int, session: SessionDep):
    try:
        await RoutesRepository.delete_one(id, session)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return None

@router_routes.get("/cities/{city_id}", response_model=SCityAdd, description="Получени названия города по ID")
async def get_city_name(city_id : int, session : SessionDep):
    try:
        result = await CitiesRepository.get_one(city_id, session)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    return result
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class SRouteAdd(BaseModel):
    from_city_id: int
    to_city_id: int

class SRoute(SRouteAdd):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SRouteUpdate(SRouteAdd):
    from_city_id: Optional[int] = None
    to_city_id: Optional[int] = None
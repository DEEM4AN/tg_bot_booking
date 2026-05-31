from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class SCityAdd(BaseModel):
    city_name: str

class SCity(SCityAdd):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SCityUpdate(SCityAdd):
    city_name: Optional[str] = None
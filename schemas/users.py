from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class SUserAdd(BaseModel):
    telegram_id : int
    username : str


class SUser(SUserAdd):
    id : int
    
    
class SUserUpdate(SUserAdd):
    telegram_id : Optional[int] = None
    username : Optional[str] = None
from pydantic import BaseModel
from datetime import date, time


class SUserRequestAdd(BaseModel):
    user_id: int
    route_id: int
    request_date: date
    time_from: time
    time_to: time
    seats_count: int
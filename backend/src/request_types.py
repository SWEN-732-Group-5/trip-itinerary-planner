from pydantic import BaseModel
from datetime import datetime

class CreateTripRequest(BaseModel):
    trip_name: str
    start_time: datetime 
    end_time: datetime

class AddUserRequest(BaseModel):
    trip_id: str
    users: dict[str, bool]

from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class CreateTripRequest(BaseModel):
    trip_name: str
    start_time: datetime 
    end_time: datetime

class UpdateTripRequest(BaseModel):
    trip_id: str
    trip_name: str
    start_time: datetime 
    end_time: datetime

class UpdateOrganizersRequest(BaseModel):
    trip_id: str
    users: dict[str, bool]

class CreateEventRequest(BaseModel):
    trip_id: str
    event_name: str
    event_type: str
    event_description: Optional[str]
    location_name: str
    location_type: str
    location_coords: list[float]
    start_time: datetime
    end_time: datetime

class UpdateEventRequest(BaseModel):
    trip_id: str
    event_id: str
    event_name: str
    event_type: str
    event_description: Optional[str]
    start_time: datetime
    end_time: datetime

class UpdateEventLocationRequest(BaseModel):
    trip_id: str
    event_id: str
    location_name: str
    location_type: str
    location_coords: list[float]
    is_end_location: bool

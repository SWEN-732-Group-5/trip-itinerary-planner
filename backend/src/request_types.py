from typing import Optional

from pydantic import BaseModel
from datetime import datetime

from src.db_types import EventType

class CreateTripRequest(BaseModel):
    trip_name: str
    start_time: datetime 
    end_time: datetime

class UpdateTripRequest(BaseModel):
    trip_name: str
    start_time: datetime 
    end_time: datetime

class UpdateOrganizersRequest(BaseModel):
    users: dict[str, bool]

class CreateEventRequest(BaseModel):
    event_name: str
    event_type: EventType
    event_description: Optional[str]
    location_name: str
    location_type: EventType
    location_coords: list[float]
    start_time: datetime
    end_time: datetime

class UpdateEventRequest(BaseModel):
    event_name: str
    event_type: str
    event_description: Optional[str]
    start_time: datetime
    end_time: datetime

class UpdateEventLocationRequest(BaseModel):
    location_name: str
    location_type: str
    location_coords: list[float]
    is_end_location: bool

class CreateTripInvitationRequest(BaseModel):
    limit_uses: int
    is_organizer: bool
    expiry_time: datetime

class CreateUserRequest(BaseModel):
    user_id: str
    display_name: str
    phone_number: str
    password: str

class AuthenticateUserRequest(BaseModel):
    user_id: str
    password: str

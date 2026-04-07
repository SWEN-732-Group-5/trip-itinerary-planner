from pydantic import BaseModel
from datetime import datetime

class BookingSummaryItem(BaseModel):
    booking_id: str
    trip_id: str
    user_id: str
    reference_number: str
    customer_service_number: str
    provider_name: str

class User(BaseModel):
    user_id: str
    display_name: str
    phone_number: str

class TripEvent(BaseModel):
    event_id: str
    event_name: str
    event_description: str
    location: str
    start_time: datetime 
    end_time: datetime

class Trip(BaseModel):
    trip_id: str
    trip_name: str
    start_time: datetime 
    end_time: datetime
    organizers: list[User]
    guests: list[User]
    events: list[TripEvent]
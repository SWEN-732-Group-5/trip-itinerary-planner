from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class EventType(StrEnum):
    """named 'EventType' but recycled for other types of things, like locations and expenses"""

    attraction = "attraction"
    food = "food"
    lodging = "lodging"
    transportation = "transportation"
    other = "other"


class BookingSummaryItem(BaseModel):
    booking_id: str
    trip_id: str
    user_id: str
    reference_number: str
    customer_service_number: str
    provider_name: str


class AttachmentType(StrEnum):
    image = "image"
    pdf = "pdf"


class EventAttachment(BaseModel):
    attachment_id: str
    event_id: str
    title: str
    description: Optional[str]
    uri: str


class User(BaseModel):
    user_id: str
    display_name: str
    phone_number: str
    password_hash: str


class UserSession(BaseModel):
    user_id: str
    session_token: str
    expiry_time: datetime


class EventLocation(BaseModel):
    name: str
    location_type: EventType
    gps_position: Optional[tuple[float, float]] = None  # GPS location


class TripEvent(BaseModel):
    event_id: str
    event_name: str
    event_type: EventType
    event_description: Optional[str]
    location: EventLocation
    end_location: Optional[EventLocation]
    start_time: datetime
    end_time: datetime
    attachments: list[EventAttachment]


class Trip(BaseModel):
    trip_id: str
    trip_name: str
    start_time: datetime
    end_time: datetime
    organizers: list[str]
    guests: list[str]
    events: list[TripEvent]


class TripInvitation(BaseModel):
    invitation_id: str
    trip_id: str
    inviter_id: str
    is_organizer: bool
    limit_uses: int
    expiry_time: datetime


class ExpenseType(StrEnum):
    attraction = "attraction"
    food = "food"
    lodging = "lodging"
    shopping = "shopping"
    transportation = "transporation"
    other = "other"


class Expense(BaseModel):
    trip_id: str
    user_id: str
    amount: float  # in USD, floating point for currency conversion
    description: Optional[str]
    category: ExpenseType
    time_added: datetime
    split_among: dict[str, float]  # maps user IDs to amount of expense owed


class Comment(BaseModel):
    comment_id: str
    event_id: str
    user_id: str
    text: str
    timestamp: datetime

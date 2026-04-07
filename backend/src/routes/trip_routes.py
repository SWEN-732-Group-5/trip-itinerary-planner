from fastapi import APIRouter
from pydantic import BaseModel

from src.db import get_db_client

trip_router = APIRouter(
    prefix="/trips", 
    tags=["trips"]
)

class BookingSummaryItem(BaseModel):
    booking_id: str
    trip_id: str
    user_id: str
    reference_number: str
    customer_service_number: str
    provider_name: str

@trip_router.get("/{trip_id}/booking-summary/{user_id}", response_model=list[BookingSummaryItem])
async def get_booking_summary(trip_id: str, user_id: str):
    db = get_db_client().trip_itinerary_planner
    bookings = await db.bookings.find({"trip_id": trip_id, "user_id": user_id}).to_list(
        length=100
    )
    return [
        BookingSummaryItem(
            booking_id=str(booking["_id"]),
            trip_id=booking["trip_id"],
            user_id=booking["user_id"],
            reference_number=booking["reference_number"],
            customer_service_number=booking["customer_service_number"],
            provider_name=booking["provider_name"],
        )
        for booking in bookings
    ]

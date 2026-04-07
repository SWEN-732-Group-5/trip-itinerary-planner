from fastapi import APIRouter

from src.db import get_db_client
from src.db_types import Trip, BookingSummaryItem
from src.request_types import CreateTripRequest

trip_router = APIRouter(
    prefix="/trips", 
    tags=["trips"]
)

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



@trip_router.post("", response_model=Trip)
async def create_trip(creation_request: CreateTripRequest):
    db = get_db_client().trip_itinerary_planner
    trips = await db.trips.find().to_list()
    next_id = len(trips)+1
    new_trip = Trip(
        trip_id=f"trip{next_id}", 
        trip_name=creation_request.trip_name, 
        start_time=creation_request.start_time, 
        end_time=creation_request.end_time, 
        organizers=[], 
        guests=[],
        events=[]
    )
    await db.trips.insert_one(new_trip)
    return new_trip

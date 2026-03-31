import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import AsyncMongoClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = AsyncMongoClient(os.environ["MONGODB_URL"])
    app.state.db = app.state.client.trip_itinerary_planner
    app.state.bookings_collection = app.state.db.bookings
    await app.state.bookings_collection.delete_many({})
    await app.state.bookings_collection.insert_many(
        [
            {
                "user_id": "user1",
                "reference_number": "REF123",
                "customer_service_number": "CSN123",
                "provider_name": "Provider A",
            },
            {
                "user_id": "user1",
                "reference_number": "REF456",
                "customer_service_number": "CSN456",
                "provider_name": "Provider B",
            },
            {
                "user_id": "user2",
                "reference_number": "REF789",
                "customer_service_number": "CSN789",
                "provider_name": "Provider C",
            },
        ]
    )
    yield
    # Cleanup code can be added here if needed


app = FastAPI(lifespan=lifespan)


class BookingSummaryItem(BaseModel):
    booking_id: str
    user_id: str
    reference_number: str
    customer_service_number: str
    provider_name: str


@app.get("/booking-summary/{user_id}", response_model=list[BookingSummaryItem])
async def get_booking_summary(user_id: str):
    bookings = await app.state.bookings_collection.find({"user_id": user_id}).to_list(
        length=100
    )
    return [
        BookingSummaryItem(
            booking_id=str(booking["_id"]),
            user_id=booking["user_id"],
            reference_number=booking["reference_number"],
            customer_service_number=booking["customer_service_number"],
            provider_name=booking["provider_name"],
        )
        for booking in bookings
    ]


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()

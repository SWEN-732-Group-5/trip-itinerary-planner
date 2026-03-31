import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import AsyncMongoClient


def config_logger(name) -> logging.Logger:
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger = logging.getLogger(name)
    return logger


def gen_mongodb_url():
    username = os.getenv("MONGO_USERNAME", "admin")
    password = os.getenv("MONGO_PASSWORD", "password")
    host = os.getenv("MONGO_HOST", "localhost")
    port = os.getenv("MONGO_PORT", "27017")
    return f"mongodb://{username}:{password}@{host}:{port}"


def get_env():
    load_dotenv()
    if "MONGODB_URL" in os.environ:
        return os.environ["MONGODB_URL"]
    return gen_mongodb_url()


@asynccontextmanager
async def lifespan(app: FastAPI):
    url = get_env()
    app.state.logger = config_logger("main")
    app.state.logger.info(f"Connecting to MongoDB at {url}")
    app.state.client = AsyncMongoClient(url)
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
    # Cleanup: close MongoDB connection
    app.state.db.close()
    app.state.client.close()


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


def main(reload: bool = False):
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=reload)


def dev():
    main(reload=True)


if __name__ == "__main__":
    main()

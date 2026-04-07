import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import get_mongodb_url, get_db_client
from src.routes.trip_routes import trip_router

def config_logger(name) -> logging.Logger:
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    logger = logging.getLogger(name)
    return logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    url = get_mongodb_url()
    app.state.logger = config_logger("main")
    app.state.logger.info(f"Connecting to MongoDB at {url}")
    app.state.client = get_db_client()
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
    app.include_router(trip_router)
    yield
    # Cleanup: close MongoDB connection
    app.state.db.close()


app = FastAPI(lifespan=lifespan)


def main(reload: bool = False):
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=reload)


def dev():
    main(reload=True)


if __name__ == "__main__":
    main()

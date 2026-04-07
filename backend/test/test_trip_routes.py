from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# --- Fake data ---
FAKE_BOOKINGS = [
    {
        "_id": "aaa",
        "trip_id": "trip1", 
        "user_id": "user1",
        "reference_number": "REF123",
        "customer_service_number": "CSN123",
        "provider_name": "Provider A",
    },
    {
        "_id": "aab",
        "trip_id": "trip1", 
        "user_id": "user1",
        "reference_number": "REF321",
        "customer_service_number": "CSN321",
        "provider_name": "Provider B",
    },
    {
        "_id": "bbb",
        "trip_id": "trip2", 
        "user_id": "user1",
        "reference_number": "REF456",
        "customer_service_number": "CSN456",
        "provider_name": "Provider B",
    },
    {
        "_id": "ccc",
        "trip_id": "trip1", 
        "user_id": "user2",
        "reference_number": "REF789",
        "customer_service_number": "CSN789",
        "provider_name": "Provider C",
    },
]


def make_mock_collection(fake_data: list[dict]):
    """Return a mock collection whose .find(...).to_list() yields filtered fake data."""

    def fake_find(query):
        user_id = query.get("user_id")
        trip_id = query.get("trip_id")
        results = [d for d in fake_data if d["trip_id"] == trip_id and d["user_id"] == user_id]
        cursor = MagicMock()
        cursor.to_list = AsyncMock(return_value=results)
        return cursor

    collection = MagicMock()
    collection.find.side_effect = fake_find
    collection.delete_many = AsyncMock()
    collection.insert_many = AsyncMock()
    return collection


def test_booking_summary_success():
    mock_collection = make_mock_collection(FAKE_BOOKINGS)

    # Patch AsyncMongoClient before the app's lifespan runs
    with patch("src.db.get_db_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.trip_itinerary_planner.bookings = mock_collection

        from src.main import app

        with TestClient(app) as client:
            # user1 has two bookings
            response = client.get("/trips/trip1/booking-summary/user1")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            references = sorted([entry["reference_number"] for entry in data])
            assert references == ["REF123", "REF321"]
            cs_numbers = sorted([entry["customer_service_number"] for entry in data])
            assert cs_numbers == ["CSN123", "CSN321"]
            provider_names = sorted([entry["provider_name"] for entry in data])
            assert provider_names == ["Provider A", "Provider B"]

            # user2 has one booking
            response = client.get("/trips/trip1/booking-summary/user2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["reference_number"] == "REF789"
            assert data[0]["provider_name"] == "Provider C"

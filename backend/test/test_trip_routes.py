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


def make_trip_dict(trip_id: str = "trip1"):
    return {
        "trip_id": trip_id,
        "trip_name": "Test Trip",
        "start_time": "2025-01-01T09:00:00",
        "end_time": "2025-01-02T17:00:00",
        "organizers": [],
        "guests": [],
        "events": [],
        "locations": [],
    }


def make_update_result(raw_result, modified_count: int = 1):
    result = MagicMock()
    result.modified_count = modified_count
    result.raw_result = raw_result
    return result


def make_delete_result(deleted_count: int = 1):
    result = MagicMock()
    result.deleted_count = deleted_count
    return result


def make_mock_db_client(trips_collection):
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_db.bookings = MagicMock()
    mock_db.bookings.delete_many = AsyncMock()
    mock_db.bookings.insert_many = AsyncMock()
    mock_db.trips = trips_collection
    mock_client.trip_itinerary_planner = mock_db
    return mock_client


def test_booking_summary_success():
    mock_collection = make_mock_collection(FAKE_BOOKINGS)

    # Patch AsyncMongoClient before the app's lifespan runs
    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = MagicMock()
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_client.trip_itinerary_planner.bookings = mock_collection

        from src.main import app

        with TestClient(app) as client:
            # user1 has two bookings
            response = client.get("/api/trips/trip1/booking-summary/user1")
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
            response = client.get("/api/trips/trip1/booking-summary/user2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["reference_number"] == "REF789"
            assert data[0]["provider_name"] == "Provider C"


def test_get_trip_success():
    expected_trip = make_trip_dict("trip1")
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=expected_trip)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/trip1")
            assert response.status_code == 200
            assert response.json() == expected_trip


def test_get_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/trip999")
            assert response.status_code == 404
            assert response.json()["detail"] == "Trip trip999 not found"


def test_create_trip_success():
    trips_collection = MagicMock()
    trips_collection.find.return_value = MagicMock(to_list=AsyncMock(return_value=[]))
    trips_collection.insert_one = AsyncMock()

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            payload = {
                "trip_name": "Spring Break",
                "start_time": "2025-03-01T08:00:00",
                "end_time": "2025-03-07T20:00:00",
            }
            response = client.post("/api/trips", json=payload)
            assert response.status_code == 201
            data = response.json()
            assert data["trip_id"] == "trip1"
            assert data["trip_name"] == "Spring Break"
            assert data["organizers"] == []
            trips_collection.insert_one.assert_awaited_once()


def test_update_trip_success():
    updated_trip = make_trip_dict("trip1")
    updated_trip["trip_name"] = "Updated Name"
    trips_collection = MagicMock()
    trips_collection.update_one = AsyncMock(return_value=make_update_result(updated_trip))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            payload = {
                "trip_name": "Updated Name",
                "start_time": "2025-01-01T09:00:00",
                "end_time": "2025-01-02T17:00:00",
            }
            response = client.put("/api/trips/trip1", json=payload)
            assert response.status_code == 200
            assert response.json()["trip_name"] == "Updated Name"
            trips_collection.update_one.assert_awaited_once()


def test_delete_trip_success():
    trips_collection = MagicMock()
    trips_collection.delete_one = AsyncMock(return_value=make_delete_result(1))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.delete("/api/trips/trip1")
            assert response.status_code == 204
            trips_collection.delete_one.assert_awaited_once_with({"trip_id": "trip1"})


def test_create_event_success():
    trip = make_trip_dict("trip1")
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    new_event = {
        "event_id": "event1",
        "event_name": "Dinner",
        "event_description": "Group dinner",
        "event_type": "food",
        "location": {
            "name": "Pasta Place",
            "location_type": "food",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    trips_collection.find_one = AsyncMock(side_effect=[trip, {**trip, "events": [new_event]}])

    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/trips/trip1/event",
                json={
                    "event_name": "Dinner",
                    "event_type": "food",
                    "event_description": "Group dinner",
                    "location_name": "Pasta Place",
                    "location_type": "food",
                    "location_coords": [40.0, -74.0],
                    "start_time": "2025-03-02T19:00:00",
                    "end_time": "2025-03-02T21:00:00",
                },
            )
            # print(response.json())
            assert response.status_code == 201
            data = response.json()
            assert data["events"][0]["event_name"] == "Dinner"
            trips_collection.update_one.assert_awaited_once()


def test_update_event_success():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Dinner",
        "event_description": "Group dinner",
        "event_type": "food",
        "location": {
            "name": "Pasta Place",
            "location_type": "food",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    updated_event = {
        "event_id": "event1",
        "event_name": "Lunch",
        "event_description": "Group lunch",
        "event_type": "food",
        "location": {
            "name": "Pasta Place",
            "location_type": "food",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T12:00:00",
        "end_time": "2025-03-02T13:00:00",
        "attachments": [],
    }
    
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": [updated_event]}))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event1",
                json={
                    "event_name": "Lunch",
                    "event_type": "food",
                    "event_description": "Group lunch",
                    "start_time": "2025-03-02T12:00:00",
                    "end_time": "2025-03-02T13:00:00",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["events"][0]["event_name"] == "Lunch"
            assert data["events"][0]["event_description"] == "Group lunch"
            assert data["events"][0]["start_time"] == "2025-03-02T12:00:00"
            trips_collection.update_one.assert_awaited_once()


def test_update_event_location_success():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Dinner",
        "event_description": "Group dinner",
        "event_type": "food",
        "location": {
            "name": "Pasta Place",
            "location_type": "food",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    updated_event = {
        "event_id": "event1",
        "event_name": "Dinner",
        "event_description": "Group dinner",
        "event_type": "food",
        "location": {
            "name": "Pizza Place",
            "location_type": "food",
            "gps_position": [41.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": [updated_event]}))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event1/location",
                json={
                    "location_name": "Pizza Place", 
                    "location_type": "food",
                    "location_coords": [41.0, -74.0],
                    "is_end_location": False,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["events"][0]["location"]["name"] == "Pizza Place"
            assert data["events"][0]["location"]["gps_position"] == [41.0, -74.0]
            trips_collection.update_one.assert_awaited_once()


def test_update_event_end_location_success():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Hike",
        "event_description": "Group hike",
        "event_type": "attraction",
        "location": {
            "name": "Trailhead",
            "location_type": "attraction",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T09:00:00",
        "end_time": "2025-03-02T15:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    updated_event = {
        "event_id": "event1",
        "event_name": "Hike",
        "event_description": "Group hike",
        "event_type": "attraction",
        "location": {
            "name": "Trailhead",
            "location_type": "attraction",
            "gps_position": [40.0, -74.0],
        },
        "end_location": {
            "name": "Trail end",
            "location_type": "attraction",
            "gps_position": [42.0, -74.0],
        },
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": [updated_event]}))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event1/location",
                json={
                    "location_name": "Trail end", 
                    "location_type": "attraction",
                    "location_coords": [42.0, -74.0],
                    "is_end_location": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["events"][0]["location"]["name"] == "Trailhead"
            assert data["events"][0]["location"]["gps_position"] == [40.0, -74.0]
            assert data["events"][0]["end_location"]["name"] == "Trail end"
            assert data["events"][0]["end_location"]["gps_position"] == [42.0, -74.0]
            trips_collection.update_one.assert_awaited_once()


def test_delete_event_success():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Hike",
        "event_description": "Group hike",
        "event_type": "attraction",
        "location": {
            "name": "Trailhead",
            "location_type": "attraction",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T09:00:00",
        "end_time": "2025-03-02T15:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": []}))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.delete("/api/trips/trip1/event/event1")
            assert response.status_code == 200
            data = response.json()
            assert data["events"] == []
            trips_collection.update_one.assert_awaited_once()


def test_update_organizers_success():
    trip = MagicMock()
    trip.organizers = ["user1"]
    trip.guests = ["user2"]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(
        return_value=make_update_result(
            {
                **make_trip_dict(),
                "organizers": [{"user_id": "user2", "display_name": "User Two", "phone_number": ""}],
                "guests": [{"user_id": "user1", "display_name": "User One", "phone_number": ""}],
            }
        )
    )

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/organizers",
                json={"users": {"user2": True, "user1": False}},
            )
            assert response.status_code == 200
            assert response.json()["organizers"][0]["user_id"] == "user2"
            assert response.json()["guests"][0]["user_id"] == "user1"
            trips_collection.update_one.assert_awaited_once()


# --- Error case tests ---

def test_update_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip999",
                json={
                    "trip_name": "Updated Name",
                    "start_time": "2025-01-01T09:00:00",
                    "end_time": "2025-01-02T17:00:00",
                },
            )
            assert response.status_code == 404
            assert "Could not find trip trip999 to update" in response.json()["detail"]


def test_delete_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.delete_one = AsyncMock(return_value=make_delete_result(deleted_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.delete("/api/trips/trip999")
            assert response.status_code == 404
            assert "Could not find trip trip999 to delete" in response.json()["detail"]


def test_update_organizers_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip999/organizers",
                json={"users": {"user2": True, "user1": False}},
            )
            assert response.status_code == 404
            assert "Could not find trip trip999 to update" in response.json()["detail"]


def test_create_event_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/trips/trip999/event",
                json={
                    "event_name": "Dinner",
                    "event_type": "food",
                    "event_description": "Group dinner",
                    "location_name": "Pasta Place",
                    "location_type": "food",
                    "location_coords": [40.0, -74.0],
                    "start_time": "2025-03-02T19:00:00",
                    "end_time": "2025-03-02T21:00:00",
                },
            )
            assert response.status_code == 404
            assert "Could not find trip trip999 to add an event to" in response.json()["detail"]


def test_update_event_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip999/event/event1",
                json={
                    "event_name": "Lunch",
                    "event_type": "food",
                    "event_description": "Group lunch",
                    "start_time": "2025-03-02T12:00:00",
                    "end_time": "2025-03-02T13:00:00",
                },
            )
            assert response.status_code == 404
            assert "Could not find trip trip999 to update" in response.json()["detail"]


def test_update_event_event_not_found():
    trip = MagicMock()
    trip.id = "trip1"
    trip.events = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event999",
                json={
                    "event_name": "Lunch",
                    "event_type": "food",
                    "event_description": "Group lunch",
                    "start_time": "2025-03-02T12:00:00",
                    "end_time": "2025-03-02T13:00:00",
                },
            )
            assert response.status_code == 404
            assert "Could not find event event999 in trip trip1" in response.json()["detail"]


def test_update_event_location_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip999/event/event1/location",
                json={
                    "location_name": "Pizza Place",
                    "location_type": "food",
                    "location_coords": [41.0, -74.0],
                    "is_end_location": False,
                },
            )
            assert response.status_code == 404
            assert "Could not find trip trip999 to update" in response.json()["detail"]


def test_update_event_location_event_not_found():
    trip = MagicMock()
    trip.id = "trip1"
    trip.events = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event999/location",
                json={
                    "location_name": "Pizza Place",
                    "location_type": "food",
                    "location_coords": [41.0, -74.0],
                    "is_end_location": False,
                },
            )
            assert response.status_code == 404
            assert "Could not find event event999 in trip trip1" in response.json()["detail"]


def test_delete_event_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.delete("/api/trips/trip999/event/event1")
            assert response.status_code == 404
            assert "Could not find trip trip999 to update" in response.json()["detail"]


def test_delete_event_event_not_found():
    trip = MagicMock()
    trip.id = "trip1"
    trip["events"] = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.delete("/api/trips/trip1/event/event999")
            assert response.status_code == 404
            assert "Could not find event event999 in trip trip1" in response.json()["detail"]


# --- Update failure tests ---

def test_create_event_update_fails():
    trip = MagicMock()
    trip.events = []
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": []}, modified_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/trips/trip1/event",
                json={
                    "event_name": "Dinner",
                    "event_type": "food",
                    "event_description": "Group dinner",
                    "location_name": "Pasta Place",
                    "location_type": "food",
                    "location_coords": [40.0, -74.0],
                    "start_time": "2025-03-02T19:00:00",
                    "end_time": "2025-03-02T21:00:00",
                },
            )
            assert response.status_code == 500
            assert "Found trip trip1 but failed to parse it" in response.json()["detail"]


def test_update_event_update_fails():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Dinner",
        "event_description": "Group dinner",
        "event_type": "food",
        "location": {
            "name": "Pasta Place",
            "location_type": "food",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": [existing_event]}, modified_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event1",
                json={
                    "event_name": "Lunch",
                    "event_type": "food",
                    "event_description": "Group lunch",
                    "start_time": "2025-03-02T12:00:00",
                    "end_time": "2025-03-02T13:00:00",
                },
            )
            assert response.status_code == 500
            assert "Found trip trip1 but failed to update it" in response.json()["detail"]


def test_update_event_location_update_fails():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Dinner",
        "event_description": "Group dinner",
        "event_type": "food",
        "location": {
            "name": "Pasta Place",
            "location_type": "food",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T19:00:00",
        "end_time": "2025-03-02T21:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": [existing_event]}, modified_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/event/event1/location",
                json={
                    "location_name": "Pizza Place",
                    "location_type": "food",
                    "location_coords": [41.0, -74.0],
                    "is_end_location": False,
                },
            )
            assert response.status_code == 500
            assert "Found trip trip1 but failed to update it" in response.json()["detail"]


def test_update_organizers_update_fails():
    trip = MagicMock()
    trip.organizers = ["user1"]
    trip.guests = ["user2"]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "guests": ["user2"]}, modified_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/trips/trip1/organizers",
                json={"users": {"user2": True, "user1": False}},
            )
            assert response.status_code == 500
            assert "Found trip trip1 but failed to update it" in response.json()["detail"]


def test_delete_event_update_fails():
    trip = MagicMock()
    existing_event = {
        "event_id": "event1",
        "event_name": "Hike",
        "event_description": "Group hike",
        "event_type": "attraction",
        "location": {
            "name": "Trailhead",
            "location_type": "attraction",
            "gps_position": [40.0, -74.0],
        },
        "end_location": None,
        "start_time": "2025-03-02T09:00:00",
        "end_time": "2025-03-02T15:00:00",
        "attachments": [],
    }
    trip.events = [existing_event]
    trip.id = "trip1"
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "events": [existing_event]}, modified_count=0))

    with patch("src.db.get_db_client") as mock_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.delete("/api/trips/trip1/event/event1")
            assert response.status_code == 500
            assert "Found trip trip1 but failed to update it" in response.json()["detail"]

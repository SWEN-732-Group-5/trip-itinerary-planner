from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from src.routes.auth import authenticated_user


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

def make_user_dict(user_id: str = "user1"):
    """Create a mock user dictionary"""
    return {
        "_id": user_id,
        "user_id": user_id,
        "display_name": "Test User",
        "phone_number": "555-1234",
        "password_hash": "hashed_password_123",
    }

def make_trip_dict(trip_id: str = "trip1"):
    return {
        "trip_id": trip_id,
        "trip_name": "Test Trip",
        "start_time": "2025-01-01T09:00:00",
        "end_time": "2025-01-02T17:00:00",
        "organizers": [],
        "guests": [],
        "events": [],
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
    mock_db.bookings.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))
    mock_db.bookings.insert_many = AsyncMock()
    mock_db.trips = trips_collection
    mock_db.trip_invitations = MagicMock()
    mock_db.trip_invitations.delete_many = AsyncMock()
    mock_client.trip_itinerary_planner = mock_db
    mock_client.close = AsyncMock()
    return mock_client


def make_invitation_dict(invitation_id: str = "invitation1", trip_id: str = "trip1", is_organizer: bool = False):
    return {
        "_id": invitation_id,
        "invitation_id": invitation_id,
        "trip_id": trip_id,
        "inviter_id": "user1",
        "is_organizer": is_organizer,
        "limit_uses": 5,
        "expiry_time": datetime.now() + timedelta(days=30),
    }


async def async_iter_mock(items):
    """Helper to create an async iterator for mocking async for loops"""
    for item in items:
        yield item


def test_booking_summary_success():
    mock_collection = make_mock_collection(FAKE_BOOKINGS)

    # Patch before importing the app
    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = MagicMock()
        mock_client.trip_itinerary_planner = MagicMock()
        mock_client.trip_itinerary_planner.bookings = mock_collection
        mock_client.trip_itinerary_planner.trips = MagicMock()
        mock_client.trip_itinerary_planner.trip_invitations = MagicMock()
        mock_client.close = AsyncMock()
        
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

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
    expected_trip["organizers"] = ["user1"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=expected_trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.get("/api/trips/trip1", headers={"session_token": "fake_token"})
                assert response.status_code == 200
                assert response.json() == expected_trip
        finally:
            app.dependency_overrides.clear()


def test_get_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.get("/api/trips/trip999", headers={"session_token": "fake_token"})
                assert response.status_code == 404
                assert response.json()["detail"] == "Trip trip999 not found"
        finally:
            app.dependency_overrides.clear()


# --- Trip summary route tests ---

def test_get_trip_summary_success():
    """Test successful retrieval of trip summary"""
    trip_summary = {
        "trip_id": "trip1",
        "trip_name": "Spring Break",
        "start_time": "2025-03-01T08:00:00",
        "end_time": "2025-03-07T20:00:00",
        "organizers": ["user1"],
        "guests": ["user2"],
        "events": [],
    }
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip_summary)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/trip1/summary")
            assert response.status_code == 200
            data = response.json()
            assert data["trip_name"] == "Spring Break"
            assert data["start_time"] == "2025-03-01T08:00:00"
            assert data["end_time"] == "2025-03-07T20:00:00"


def test_get_trip_summary_not_found():
    """Test trip summary request when trip is not found"""
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/nonexistent/summary")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


def test_create_trip_success():
    trips_collection = MagicMock()
    trips_collection.find.return_value = MagicMock(to_list=AsyncMock(return_value=[]))
    trips_collection.insert_one = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                payload = {
                    "trip_name": "Spring Break",
                    "start_time": "2025-03-01T08:00:00",
                    "end_time": "2025-03-07T20:00:00",
                }
                response = client.post("/api/trips", json=payload, headers={"session_token": "fake_token"})
                assert response.status_code == 201
                data = response.json()
                assert data["trip_id"] == "trip1"
                assert data["trip_name"] == "Spring Break"
                assert data["organizers"] == ["user1"]
                trips_collection.insert_one.assert_awaited_once()
        finally:
            app.dependency_overrides.clear()


def test_update_trip_success():
    updated_trip = make_trip_dict("trip1")
    updated_trip["trip_name"] = "Updated Name"
    updated_trip["organizers"] = ["user1"]
    trips_collection = MagicMock()
    trip_to_find = make_trip_dict("trip1")
    trip_to_find["organizers"] = ["user1"]
    trips_collection.find_one = AsyncMock(return_value=trip_to_find)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(updated_trip))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                payload = {
                    "trip_name": "Updated Name",
                    "start_time": "2025-01-01T09:00:00",
                    "end_time": "2025-01-02T17:00:00",
                }
                response = client.put("/api/trips/trip1", json=payload, headers={"session_token": "fake_token"})
                assert response.status_code == 200
                assert response.json()["trip_name"] == "Updated Name"
                trips_collection.update_one.assert_awaited_once()
        finally:
            app.dependency_overrides.clear()


def test_delete_trip_success():
    trips_collection = MagicMock()
    trip_to_find = make_trip_dict("trip1")
    trip_to_find["organizers"] = ["user1"]
    trips_collection.find_one = AsyncMock(return_value=trip_to_find)
    trips_collection.delete_one = AsyncMock(return_value=make_delete_result(1))
    trips_collection.delete_many = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete("/api/trips/trip1", headers={"session_token": "fake_token"})
                assert response.status_code == 204
                trips_collection.delete_one.assert_awaited_once_with({"trip_id": "trip1"})
        finally:
            app.dependency_overrides.clear()


def test_create_event_success():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(side_effect=[trip, {**trip, "events": []}])

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
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 201
                trips_collection.update_one.assert_awaited_once()
        finally:
            app.dependency_overrides.clear()

def test_update_event_success():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
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

    result_trip = make_trip_dict()
    result_trip["organizers"] = ["user1"]
    result_trip["events"] = [updated_event]
    trips_collection.update_one = AsyncMock(return_value=make_update_result(result_trip))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["events"][0]["event_name"] == "Lunch"
                assert data["events"][0]["event_description"] == "Group lunch"
                assert data["events"][0]["start_time"] == "2025-03-02T12:00:00"
                trips_collection.update_one.assert_awaited_once()
        finally:
            app.dependency_overrides.clear()

def test_update_event_location_success():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
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

    result_trip = make_trip_dict()
    result_trip["organizers"] = ["user1"]
    result_trip["events"] = [updated_event]
    trips_collection.update_one = AsyncMock(return_value=make_update_result(result_trip))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/event/event1/location",
                    json={
                        "location_name": "Pizza Place",
                        "location_type": "food",
                        "location_coords": [41.0, -74.0],
                        "is_end_location": False,
                    },
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["events"][0]["location"]["name"] == "Pizza Place"
                assert data["events"][0]["location"]["gps_position"] == [41.0, -74.0]
                trips_collection.update_one.assert_awaited_once()


        finally:
            app.dependency_overrides.clear()

def test_update_event_end_location_success():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
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
    
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "events": [updated_event]}))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/event/event1/location",
                    json={
                        "location_name": "Trail end", 
                        "location_type": "attraction",
                        "location_coords": [42.0, -74.0],
                        "is_end_location": True,
                    },
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["events"][0]["location"]["name"] == "Trailhead"
                assert data["events"][0]["location"]["gps_position"] == [40.0, -74.0]
                assert data["events"][0]["end_location"]["name"] == "Trail end"
                assert data["events"][0]["end_location"]["gps_position"] == [42.0, -74.0]
                trips_collection.update_one.assert_awaited_once()


        finally:
            app.dependency_overrides.clear()

def test_delete_event_success():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "events": []}))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete("/api/trips/trip1/event/event1", headers={"session_token": "fake_token"})
                assert response.status_code == 200
                data = response.json()
                assert data["events"] == []
                trips_collection.update_one.assert_awaited_once()


        finally:
            app.dependency_overrides.clear()

def test_update_organizers_success():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(
        return_value=make_update_result(
            {
                **make_trip_dict(),
                "organizers": ["user2"],
                "guests": ["user1"],
            }
        )
    )

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/organizers",
                    json={"is_organizer": {"user2": True, "user1": False}},
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                assert response.json()["organizers"] == ["user2"]
                assert response.json()["guests"] == ["user1"]
                trips_collection.update_one.assert_awaited_once()


        finally:
            app.dependency_overrides.clear()

# --- Error case tests ---

def test_update_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip999",
                    json={
                        "trip_name": "Updated Name",
                        "start_time": "2025-01-01T09:00:00",
                        "end_time": "2025-01-02T17:00:00",
                    },
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip999 to update" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)
    trips_collection.delete_one = AsyncMock(return_value=make_delete_result(deleted_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete("/api/trips/trip999", headers={"session_token": "fake_token"})
                assert response.status_code == 404
                assert "Could not find trip trip999 to delete" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_organizers_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip999/organizers",
                    json={"is_organizer": {"user2": True, "user1": False}},
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip999 to update" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_create_event_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip999 to add an event to" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_event_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip999 to update" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_event_event_not_found():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find event event999 in trip trip1" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_event_location_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip999/event/event1/location",
                    json={
                        "location_name": "Pizza Place",
                        "location_type": "food",
                        "location_coords": [41.0, -74.0],
                        "is_end_location": False,
                    },
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip999 to update" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_event_location_event_not_found():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/event/event999/location",
                    json={
                        "location_name": "Pizza Place",
                        "location_type": "food",
                        "location_coords": [41.0, -74.0],
                        "is_end_location": False,
                    },
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find event event999 in trip trip1" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_event_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete("/api/trips/trip999/event/event1", headers={"session_token": "fake_token"})
                assert response.status_code == 404
                assert "Could not find trip trip999 to update" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_event_event_not_found():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete("/api/trips/trip1/event/event999", headers={"session_token": "fake_token"})
                assert response.status_code == 404
                assert "Could not find event event999 in trip trip1" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

# --- Update failure tests ---

def test_create_event_update_fails():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = []
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "events": []}, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_event_update_fails():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "events": [existing_event]}, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
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
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_event_location_update_fails():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "events": [existing_event]}, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/event/event1/location",
                    json={
                        "location_name": "Pizza Place",
                        "location_type": "food",
                        "location_coords": [41.0, -74.0],
                        "is_end_location": False,
                    },
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_update_organizers_update_fails():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "guests": ["user2"]}, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/organizers",
                    json={"is_organizer": {"user2": True, "user1": False}},
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_event_update_fails():
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
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["events"] = [existing_event]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result({**make_trip_dict(), "organizers": ["user1"], "events": [existing_event]}, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete("/api/trips/trip1/event/event1", headers={"session_token": "fake_token"})
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

# --- Invitation-related tests ---

def test_create_trip_invitation_success():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    invitations_collection = MagicMock()
    invitations_collection.find = MagicMock(return_value=MagicMock(to_list=AsyncMock(return_value=[])))
    invitations_collection.insert_one = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/trips/trip1/invite",
                    json={"is_organizer": True, "limit_uses": 5, "expiry_time": (datetime.now() + timedelta(days=30)).isoformat()},
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 201
                data = response.json()
                assert data["trip_id"] == "trip1"
                assert data["is_organizer"] == True
                assert data["inviter_id"] == "user1"


        finally:
            app.dependency_overrides.clear()

def test_create_trip_invitation_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/trips/trip1/invite",
                    json={"is_organizer": False, "limit_uses": 5, "expiry_time": (datetime.now() + timedelta(days=30)).isoformat()},
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip1 to invite users to" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_create_trip_invitation_not_organizer():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user2"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/trips/trip1/invite",
                    json={"is_organizer": False, "limit_uses": 5, "expiry_time": (datetime.now() + timedelta(days=30)).isoformat()},
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 403
                assert "Only organizers can create invitations for a trip" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_get_trip_invitations_success():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    invitations = [
        make_invitation_dict("invitation1", "trip1", False),
        make_invitation_dict("invitation2", "trip1", True),
    ]

    invitations_collection = MagicMock()
    invitations_collection.find = MagicMock(return_value=async_iter_mock(invitations))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.get(
                    "/api/trips/trip1/invitations",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["invitation_id"] == "invitation1"
                assert data[1]["is_organizer"] == True


        finally:
            app.dependency_overrides.clear()

def test_get_trip_invitations_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.get(
                    "/api/trips/trip1/invitations",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip1 to get invitations for" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_get_trip_invitations_not_organizer():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user2"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.get(
                    "/api/trips/trip1/invitations",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 403
                assert "Only organizers can view invitations for a trip" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_get_trip_invitation_success():
    invitation = make_invitation_dict("invitation1", "trip1")
    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    user = make_user_dict("user1")
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user)

    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_client.trip_itinerary_planner.trips = trips_collection
        mock_client.trip_itinerary_planner.users = users_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/invitation/invitation1")
            assert response.status_code == 200
            data = response.json()
            assert data["trip_name"] == "Test Trip"
            assert data["inviter_name"] == "Test User"


def test_get_trip_invitation_not_found():
    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=None)

    trips_collection = MagicMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/invitation/invalid_invitation")
            assert response.status_code == 404
            assert "Could not find invitation invalid_invitation" in response.json()["detail"]


def test_get_invitation_trip_not_found():
    invitation = make_invitation_dict("invitation1", "trip1")
    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/invitation/invalid_invitation")
            assert response.status_code == 404
            assert "Invitation invalid_invitation not valid" in response.json()["detail"]


def test_get_inviter_not_found():
    invitation = make_invitation_dict("invitation1", "trip1")
    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    trip = make_trip_dict("trip1")
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_client.trip_itinerary_planner.trips = trips_collection
        mock_client.trip_itinerary_planner.users = users_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.get("/api/trips/invitation/invalid_invitation")
            assert response.status_code == 404
            assert "Invitation invalid_invitation not valid" in response.json()["detail"]


def test_accept_trip_invitation_success_as_guest():
    invitation = make_invitation_dict("invitation1", "trip1", False)
    invitation["limit_uses"] = 5
    invitation["expiry_time"] = datetime.now() + timedelta(days=30)

    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = []

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(side_effect=[trip, trip])
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)
    invitations_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user2"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invitation1/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["trip"]["trip_id"] == "trip1"


        finally:
            app.dependency_overrides.clear()

def test_accept_trip_invitation_success_as_organizer():
    invitation = make_invitation_dict("invitation1", "trip1", True)
    invitation["limit_uses"] = 3
    invitation["expiry_time"] = datetime.now() + timedelta(days=30)

    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = []

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(side_effect=[trip, trip])
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)
    invitations_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user3"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invitation1/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200


        finally:
            app.dependency_overrides.clear()

def test_accept_trip_invitation_not_found():
    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(MagicMock())
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invalid_invitation/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find invitation invalid_invitation" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_accept_trip_invitation_expired():
    invitation = make_invitation_dict("invitation1", "trip1", False)
    invitation["expiry_time"] = datetime.now() - timedelta(days=1)

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(MagicMock())
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invitation1/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 400
                assert "has expired and can no longer be accepted" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_accept_trip_invitation_no_uses_left():
    invitation = make_invitation_dict("invitation1", "trip1", False)
    invitation["limit_uses"] = 0
    invitation["expiry_time"] = datetime.now() + timedelta(days=30)

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(MagicMock())
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invitation1/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 400
                assert "has already been used the maximum number of times" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_accept_trip_invitation_trip_not_found():
    invitation = make_invitation_dict("invitation1", "trip1", False)
    invitation["expiry_time"] = datetime.now() + timedelta(days=30)

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invitation1/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip1 to accept invitation for" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_accept_trip_invitation_already_member():
    invitation = make_invitation_dict("invitation1", "trip1", False)
    invitation["expiry_time"] = datetime.now() + timedelta(days=30)

    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.delete_many = AsyncMock()

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/invitation/invitation1/accept",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 400
                assert "is already a member of trip" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_trip_invitation_success():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    invitation = make_invitation_dict("invitation1", "trip1")

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)
    invitations_collection.delete_one = AsyncMock(return_value=make_delete_result(1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/api/trips/trip1/invite/invitation1",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 204


        finally:
            app.dependency_overrides.clear()

def test_delete_trip_invitation_not_found():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/api/trips/trip1/invite/invalid_invitation",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find invitation invalid_invitation for trip trip1" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_trip_invitation_trip_not_found():
    invitations_collection = MagicMock()
    invitation = make_invitation_dict("invitation1", "trip1")
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/api/trips/trip1/invite/invitation1",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip1 to delete invitation from" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_delete_trip_invitation_not_organizer():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user2"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    invitation = make_invitation_dict("invitation1", "trip1")

    invitations_collection = MagicMock()
    invitations_collection.find_one = AsyncMock(return_value=invitation)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_client.trip_itinerary_planner.trip_invitations = invitations_collection
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.delete(
                    "/api/trips/trip1/invite/invitation1",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 403
                assert "Only organizers can delete invitations for a trip" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

# --- Leave trip and remove user routes ---

def test_leave_trip_success_as_organizer():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1", "user2"]
    trip["guests"] = ["user3"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/leave-trip",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert "trip" in data


        finally:
            app.dependency_overrides.clear()

def test_leave_trip_success_as_guest():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2", "user3"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user2"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/leave-trip",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200


        finally:
            app.dependency_overrides.clear()

def test_leave_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/leave-trip",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip1" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_leave_trip_not_member():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user2"]
    trip["guests"] = ["user3"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/leave-trip",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 403
                assert "Not a member of this trip" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_leave_trip_update_fails():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = []

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/leave-trip",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_remove_user_from_trip_success():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2", "user3"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/remove-user/user2",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200
                data = response.json()
                assert "trip" in data


        finally:
            app.dependency_overrides.clear()

def test_remove_user_from_trip_organizer():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1", "user2"]
    trip["guests"] = ["user3"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=1))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/remove-user/user2",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 200


        finally:
            app.dependency_overrides.clear()

def test_remove_user_from_trip_not_found():
    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/remove-user/user2",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 404
                assert "Could not find trip trip1" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_remove_user_from_trip_not_organizer():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2", "user3"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user2"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/remove-user/user3",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 403
                assert "Only organizers can remove users from a trip" in response.json()["detail"]


        finally:
            app.dependency_overrides.clear()

def test_remove_user_from_trip_update_fails():
    trip = make_trip_dict("trip1")
    trip["organizers"] = ["user1"]
    trip["guests"] = ["user2"]

    trips_collection = MagicMock()
    trips_collection.find_one = AsyncMock(return_value=trip)
    trips_collection.update_one = AsyncMock(return_value=make_update_result(None, modified_count=0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, patch("src.routes.trip_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        from src.main import app


        app.dependency_overrides[authenticated_user] = lambda: {"user_id": "user1"}
        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/trips/trip1/remove-user/user2",
                    headers={"session_token": "fake_token"},
                )
                assert response.status_code == 500
                assert "Found trip trip1 but failed to update it" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

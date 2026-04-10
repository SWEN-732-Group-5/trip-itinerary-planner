from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import bcrypt
import os


# --- Helper functions ---

def make_user_dict(user_id: str = "user1"):
    """Create a mock user dictionary"""
    return {
        "_id": user_id,
        "user_id": user_id,
        "display_name": "Test User",
        "phone_number": "555-1234",
        "password_hash": "hashed_password_123",
    }


def make_trip_dict(trip_id: str = "trip1", organizers=None, guests=None):
    """Create a mock trip dictionary"""
    if organizers is None:
        organizers = []
    if guests is None:
        guests = []
    return {
        "trip_id": trip_id,
        "trip_name": "Test Trip",
        "start_time": "2025-01-01T09:00:00",
        "end_time": "2025-01-02T17:00:00",
        "organizers": organizers,
        "guests": guests,
        "events": [],
    }


def make_delete_result(deleted_count: int = 1):
    """Create a mock delete result"""
    result = MagicMock()
    result.deleted_count = deleted_count
    return result


def make_update_result(modified_count: int = 1):
    """Create a mock update result"""
    result = MagicMock()
    result.modified_count = modified_count
    return result


def make_mock_db_client(users_collection, trips_collection=None, sessions_collection=None):
    """Create a mock database client"""
    if trips_collection is None:
        trips_collection = MagicMock()
        trips_collection.update_many = AsyncMock(return_value=make_update_result(1))
    if sessions_collection is None:
        sessions_collection = MagicMock()
        sessions_collection.delete_many = AsyncMock()
    else:
        # Ensure the provided sessions_collection has delete_many as AsyncMock if not already set
        if not hasattr(sessions_collection.delete_many, '_is_coroutine'):
            sessions_collection.delete_many = AsyncMock()
    
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_db.users = users_collection
    mock_db.trips = trips_collection
    mock_db.user_sessions = sessions_collection
    
    # Set up bookings collection with proper async mocks
    bookings_collection = MagicMock()
    bookings_collection.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))
    bookings_collection.insert_many = AsyncMock()
    mock_db.bookings = bookings_collection
    
    trip_invitations_collection = MagicMock()
    trip_invitations_collection.delete_many = AsyncMock()
    mock_db.trip_invitations = trip_invitations_collection
    
    mock_client.trip_itinerary_planner = mock_db
    mock_client.close = AsyncMock()
    return mock_client


async def async_iter_mock(items):
    """Helper to create an async iterator for mocking async for loops"""
    for item in items:
        yield item


# --- Tests for create_user ---

def test_create_user_success():
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=None)
    users_collection.insert_one = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.bcrypt") as mock_bcrypt:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        
        # Mock bcrypt.hashpw to return a hashed password
        mock_bcrypt.hashpw.return_value = b"hashed_password_123"

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/user",
                json={
                    "user_id": "newuser",
                    "display_name": "New User",
                    "phone_number": "555-9999",
                    "password": "secure_password123"
                }
            )
            assert response.status_code == 201
            data = response.json()
            assert "created successfully" in data["message"]
            assert "newuser" in data["message"]


def test_create_user_already_exists():
    existing_user = make_user_dict("user1")
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=existing_user)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/user",
                json={
                    "user_id": "user1",
                    "display_name": "Duplicate User",
                    "phone_number": "555-5555",
                    "password": "password123"
                }
            )
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]


# --- Tests for get_user ---

def test_get_user_success():
    user_data = make_user_dict("user1")
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.get(
                "/api/user/user1",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Test User"
            assert data["phone_number"] == "555-1234"


def test_get_user_not_found():
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.get(
                "/api/user/nonexistent",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


# --- Tests for get_user_trips ---

def test_get_user_trips_success():
    trips = [
        make_trip_dict("trip1", organizers=["user1"], guests=[]),
        make_trip_dict("trip2", organizers=[], guests=["user1"]),
    ]
    
    users_collection = MagicMock()
    trips_collection = MagicMock()
    trips_collection.find = MagicMock(return_value=async_iter_mock(trips))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection, trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.get(
                "/api/user/user1/trips",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["trips"]) == 2
            assert data["trips"][0]["trip_id"] == "trip1"
            assert data["trips"][1]["trip_id"] == "trip2"


def test_get_user_trips_empty():
    users_collection = MagicMock()
    trips_collection = MagicMock()
    trips_collection.find = MagicMock(return_value=async_iter_mock([]))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection, trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.get(
                "/api/user/user1/trips",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["trips"]) == 0
            assert data["trips"] == []


def test_get_user_trips_unauthorized():
    users_collection = MagicMock()
    trips_collection = MagicMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection, trips_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        # Current user is user1, but trying to access user2's trips
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.get(
                "/api/user/user2/trips",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 403
            assert "only access your own" in response.json()["detail"]


# --- Tests for delete_user ---

def test_delete_user_success():
    users_collection = MagicMock()
    users_collection.delete_one = AsyncMock(return_value=make_delete_result(1))
    
    trips_collection = MagicMock()
    trips_collection.update_many = AsyncMock(return_value=make_update_result(1))
    
    sessions_collection = MagicMock()
    sessions_collection.delete_many = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection, trips_collection, sessions_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.delete(
                "/api/user",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 204


def test_delete_user_not_found():
    users_collection = MagicMock()
    users_collection.delete_one = AsyncMock(return_value=make_delete_result(0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.delete(
                "/api/user",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


def test_delete_user_success_with_trips():
    """Test that deleting a user also removes them from trip organizers and guests"""
    users_collection = MagicMock()
    users_collection.delete_one = AsyncMock(return_value=make_delete_result(1))
    
    trips_collection = MagicMock()
    # First call for organizers removal, second call for guests removal
    trips_collection.update_many = AsyncMock(return_value=make_update_result(2))
    
    sessions_collection = MagicMock()
    sessions_collection.delete_many = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection, trips_collection, sessions_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {"user_id": "user1"}

        from src.main import app

        with TestClient(app) as client:
            response = client.delete(
                "/api/user",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 204
            # Verify update_many was called twice (for organizers and guests)
            assert trips_collection.update_many.call_count == 2


# --- Tests for update_user ---

def test_update_user_success():
    """Test successful user update"""
    user_data = make_user_dict("user1")
    user_data["display_name"] = "Updated Name"
    user_data["phone_number"] = "555-9999"
    
    users_collection = MagicMock()
    users_collection.update_one = AsyncMock(return_value=make_update_result(1))
    users_collection.find_one = AsyncMock(return_value=user_data)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {
            "user_id": "user1",
            "display_name": "Updated Name",
            "phone_number": "555-9999"
        }

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/user",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["user_id"] == "user1"
            assert data["display_name"] == "Updated Name"
            assert data["phone_number"] == "555-9999"


def test_update_user_not_found():
    """Test update fails when user is not found (modified_count == 0)"""
    users_collection = MagicMock()
    users_collection.update_one = AsyncMock(return_value=make_update_result(0))

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {
            "user_id": "user1",
            "display_name": "Test User",
            "phone_number": "555-1234"
        }

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/user",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 404
            assert "Failed to update user" in response.json()["detail"]


def test_update_user_validates_returned_object():
    """Test that update_user properly validates and returns User model"""
    user_data = make_user_dict("user1")
    user_data["display_name"] = "New Display Name"
    user_data["phone_number"] = "555-8888"
    
    users_collection = MagicMock()
    users_collection.update_one = AsyncMock(return_value=make_update_result(1))
    users_collection.find_one = AsyncMock(return_value=user_data)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.user_routes.get_db_client") as mock_route_client_fn, \
         patch("src.routes.user_routes.get_user_from_session_token") as mock_get_user:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        mock_get_user.return_value = {
            "user_id": "user1",
            "display_name": "New Display Name",
            "phone_number": "555-8888"
        }

        from src.main import app

        with TestClient(app) as client:
            response = client.put(
                "/api/user",
                headers={"session_token": "fake_token"}
            )
            assert response.status_code == 200
            # Verify all User model fields are present
            data = response.json()
            assert "user_id" in data
            assert "display_name" in data
            assert "phone_number" in data
            assert "password_hash" in data

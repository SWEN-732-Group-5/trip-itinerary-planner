from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
import bcrypt
import pytest


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


def make_session_dict(user_id: str = "user1", session_token: str = "test_token_123"):
    """Create a mock session dictionary"""
    return {
        "_id": "session_id_123",
        "user_id": user_id,
        "session_token": session_token,
        "expiry_time": datetime.now(timezone.utc) + timedelta(minutes=30),
    }


def make_expired_session_dict(user_id: str = "user1", session_token: str = "expired_token"):
    """Create an expired session dictionary"""
    return {
        "_id": "expired_session_id",
        "user_id": user_id,
        "session_token": session_token,
        "expiry_time": datetime.now(timezone.utc) - timedelta(minutes=5),
    }


def make_mock_db_client(users_collection, sessions_collection=None):
    """Create a mock database client"""
    if sessions_collection is None:
        sessions_collection = MagicMock()
        sessions_collection.insert_one = AsyncMock()
    else:
        # Ensure the provided sessions_collection has insert_one as AsyncMock if not already set
        if not hasattr(sessions_collection.insert_one, '_is_coroutine'):
            sessions_collection.insert_one = AsyncMock()
    
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_db.users = users_collection
    mock_db.user_sessions = sessions_collection
    
    # Set up bookings collection with proper async mocks
    bookings_collection = MagicMock()
    bookings_collection.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))
    bookings_collection.insert_many = AsyncMock()
    mock_db.bookings = bookings_collection
    
    trip_invitations_collection = MagicMock()
    trip_invitations_collection.delete_many = AsyncMock()
    mock_db.trip_invitations = trip_invitations_collection
    
    trips_collection = MagicMock()
    mock_db.trips = trips_collection
    
    mock_client.trip_itinerary_planner = mock_db
    mock_client.close = AsyncMock()
    return mock_client


# --- Tests for authenticate_user ---

def test_authenticate_user_success():
    """Test successful user authentication"""
    user_data = make_user_dict("user1")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)
    
    sessions_collection = MagicMock()
    sessions_collection.insert_one = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.auth.get_db_client") as mock_route_client_fn, \
         patch("src.routes.auth.bcrypt") as mock_bcrypt:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        
        # Mock bcrypt functions
        mock_bcrypt.checkpw.return_value = True
        mock_bcrypt.gensalt.return_value = b"generated_salt_123"

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/auth",
                json={
                    "user_id": "user1",
                    "password": "correct_password"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "session_token" in data
            # Verify session was inserted
            sessions_collection.insert_one.assert_called_once()


def test_authenticate_user_not_found():
    """Test authentication when user doesn't exist"""
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=None)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.auth.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/auth",
                json={
                    "user_id": "nonexistent",
                    "password": "some_password"
                }
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


def test_authenticate_user_invalid_password():
    """Test authentication with incorrect password"""
    user_data = make_user_dict("user1")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.auth.get_db_client") as mock_route_client_fn, \
         patch("src.routes.auth.bcrypt") as mock_bcrypt:
        mock_client = make_mock_db_client(users_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        
        # Mock bcrypt to return False (password mismatch)
        mock_bcrypt.checkpw.return_value = False

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/auth",
                json={
                    "user_id": "user1",
                    "password": "wrong_password"
                }
            )
            assert response.status_code == 401
            assert "Invalid password" in response.json()["detail"]


def test_authenticate_user_session_creation():
    """Test that session token is properly created and stored"""
    user_data = make_user_dict("user1")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)
    
    sessions_collection = MagicMock()
    sessions_collection.insert_one = AsyncMock()

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.auth.get_db_client") as mock_route_client_fn, \
         patch("src.routes.auth.bcrypt") as mock_bcrypt:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        
        # Mock bcrypt functions
        mock_bcrypt.checkpw.return_value = True
        mock_bcrypt.gensalt.return_value = b"new_session_token"

        from src.main import app

        with TestClient(app) as client:
            response = client.post(
                "/api/auth",
                json={
                    "user_id": "user1",
                    "password": "correct_password"
                }
            )
            assert response.status_code == 200
            
            # Verify that insert_one was called with session data
            call_args = sessions_collection.insert_one.call_args
            assert call_args is not None
            inserted_data = call_args[0][0]
            assert inserted_data["user_id"] == "user1"
            assert "session_token" in inserted_data
            assert "expiry_time" in inserted_data


# --- Tests for authenticated_user ---

def test_authenticated_user_success():
    """Test successful retrieval of user from valid session token"""
    user_data = make_user_dict("user1")
    session_data = make_session_dict("user1", "valid_token_123")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)
    
    sessions_collection = MagicMock()
    sessions_collection.find_one = AsyncMock(return_value=session_data)

    with patch("src.routes.auth.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_route_client_fn.return_value = mock_client

        from src.routes.auth import authenticated_user

        # This is an async function, so we need to run it in an event loop
        import asyncio
        result = asyncio.run(authenticated_user("valid_token_123"))
        
        assert result["user_id"] == "user1"
        assert result["display_name"] == "Test User"


def test_authenticated_user_none():
    """Test that missing session token raises error"""
    with patch("src.routes.auth.get_db_client"):
        from src.routes.auth import authenticated_user

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(authenticated_user(None))
        assert "Session token is required" in str(exc_info.value.detail)


def test_authenticated_user_not_found():
    """Test that invalid session token raises error"""
    users_collection = MagicMock()
    
    sessions_collection = MagicMock()
    sessions_collection.find_one = AsyncMock(return_value=None)

    with patch("src.routes.auth.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_route_client_fn.return_value = mock_client

        from src.routes.auth import authenticated_user

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(authenticated_user("invalid_token"))
        assert "Invalid or expired session token" in str(exc_info.value.detail)


def test_authenticated_user_expired():
    """Test that expired session token raises error"""
    session_data = make_expired_session_dict("user1", "expired_token")
    
    users_collection = MagicMock()
    
    sessions_collection = MagicMock()
    sessions_collection.find_one = AsyncMock(return_value=session_data)

    with patch("src.routes.auth.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_route_client_fn.return_value = mock_client

        from src.routes.auth import authenticated_user

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(authenticated_user("expired_token"))
        assert "Invalid or expired session token" in str(exc_info.value.detail)


def test_authenticated_user_user_not_found():
    """Test that session references deleted user"""
    session_data = make_session_dict("deleted_user", "valid_token")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=None)
    
    sessions_collection = MagicMock()
    sessions_collection.find_one = AsyncMock(return_value=session_data)

    with patch("src.routes.auth.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_route_client_fn.return_value = mock_client

        from src.routes.auth import authenticated_user

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(authenticated_user("valid_token"))
        assert "not found" in str(exc_info.value.detail)


def test_authenticated_user_queries_database():
    """Test that function properly queries session and user collections"""
    user_data = make_user_dict("user1")
    session_data = make_session_dict("user1", "test_token")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)
    
    sessions_collection = MagicMock()
    sessions_collection.find_one = AsyncMock(return_value=session_data)

    with patch("src.routes.auth.get_db_client") as mock_route_client_fn:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_route_client_fn.return_value = mock_client

        from src.routes.auth import authenticated_user

        import asyncio
        asyncio.run(authenticated_user("test_token"))
        
        # Verify that session lookup was performed with correct token
        sessions_collection.find_one.assert_called_once_with({"session_token": "test_token"})
        
        # Verify that user lookup was performed with correct user_id
        users_collection.find_one.assert_called_once_with({"user_id": "user1"})


# --- Integration tests ---

def test_authenticate_then_use_session():
    """Test full flow: authenticate user, then use returned session token"""
    user_data = make_user_dict("user1")
    session_data = make_session_dict("user1", "generated_token_from_auth")
    
    users_collection = MagicMock()
    users_collection.find_one = AsyncMock(return_value=user_data)
    
    sessions_collection = MagicMock()
    sessions_collection.insert_one = AsyncMock()
    sessions_collection.find_one = AsyncMock(return_value=session_data)

    with patch("src.main.get_db_client") as mock_main_db_client_fn, \
         patch("src.routes.auth.get_db_client") as mock_route_client_fn, \
         patch("src.routes.auth.bcrypt") as mock_bcrypt:
        mock_client = make_mock_db_client(users_collection, sessions_collection)
        mock_main_db_client_fn.return_value = mock_client
        mock_route_client_fn.return_value = mock_client
        
        # Mock bcrypt functions
        mock_bcrypt.checkpw.return_value = True
        mock_bcrypt.gensalt.return_value = b"generated_token_from_auth"

        from src.main import app
        from src.routes.auth import authenticated_user

        # First, authenticate the user
        with TestClient(app) as client:
            auth_response = client.post(
                "/api/auth",
                json={
                    "user_id": "user1",
                    "password": "correct_password"
                }
            )
            assert auth_response.status_code == 200
            session_token = auth_response.json()["session_token"]
        
        # Then, use that token to get the user
        import asyncio
        user = asyncio.run(authenticated_user(session_token))
        assert user["user_id"] == "user1"

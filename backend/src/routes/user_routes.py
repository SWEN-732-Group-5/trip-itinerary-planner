import os
from typing_extensions import Optional
import bcrypt
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Header

from src.routes.auth import get_user_from_session_token
from src.db import get_db_client
from src.db_types import (
    Trip,
    User,
)
from src.request_types import (
    CreateUserRequest
)

load_dotenv()
salt = os.getenv("HASH_SALT", "placeholder_salt").encode()

user_router = APIRouter(prefix="/api/user", tags=["users"])

@user_router.post("", status_code=201)
async def create_user(request: CreateUserRequest):
    db = get_db_client().trip_itinerary_planner
    existing_user = await db.users.find_one({"user_id": request.user_id})
    if existing_user is not None:
        raise HTTPException(status_code=400, detail=f"User with id {request.user_id} already exists")
    hashed_password = bcrypt.hashpw(request.password.encode(), salt).decode()
    user = User(
        user_id=request.user_id,
        display_name=request.display_name,
        phone_number=request.phone_number, 
        password_hash=hashed_password
    )
    await db.users.insert_one(user.model_dump())
    return {"message": f"User {request.user_id} created successfully"}


@user_router.get("/{user_id}", status_code=200)
async def get_user(user_id: str, session_token: Optional[str] = Header(None)):
    await get_user_from_session_token(session_token)
    db = get_db_client().trip_itinerary_planner
    user_data = await db.users.find_one({"user_id": user_id})
    if user_data is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return {"display_name": user_data["display_name"], "phone_number": user_data["phone_number"]}


@user_router.get("/{user_id}/trips", status_code=200)
async def get_user_trips(user_id: str, session_token: Optional[str] = Header(None)):
    user = await get_user_from_session_token(session_token)
    if user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only access your own trips")
    db = get_db_client().trip_itinerary_planner
    trips_cursor = db.trips.find({"$or": [{"organizers": user_id}, {"guests": user_id}]})
    trips = []
    async for trip_data in trips_cursor:
        trip = Trip.model_validate(trip_data)
        trips.append(trip)
    return {"trips": trips}


@user_router.delete("", status_code=204)
async def delete_user(session_token: Optional[str] = Header(None)):
    user = await get_user_from_session_token(session_token)
    db = get_db_client().trip_itinerary_planner
    result = await db.users.delete_one({"user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"User with id {user['user_id']} not found")
    result = await db.user_sessions.delete_many({"user_id": user["user_id"]})
    result = await db.trips.update_many(
        {"organizers": user["user_id"]},
        {"$pull": {"organizers": user["user_id"]}}
    )
    result = await db.trips.update_many(
        {"guests": user["user_id"]},
        {"$pull": {"guests": user["user_id"]}}
    )
    return None

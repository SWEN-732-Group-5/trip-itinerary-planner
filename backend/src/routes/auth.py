import os
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from src.db import get_db_client
from src.request_types import AuthenticateUserRequest

load_dotenv()
salt = os.getenv("HASH_SALT", "placeholder_hash").encode()

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

@auth_router.post("", status_code=200)
async def authenticate_user(request: AuthenticateUserRequest):
    db = get_db_client().trip_itinerary_planner
    user = await db.users.find_one({"user_id": request.user_id})
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {request.user_id} not found")
    hashed_password = bcrypt.hashpw(request.password.encode(), salt)
    if not bcrypt.checkpw(request.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")
    session_token = bcrypt.gensalt().decode() 
    expiry_time = datetime.now() + timedelta(minutes=30)
    await db.user_sessions.insert_one({
        "user_id": request.user_id,
        "session_token": session_token,
        "expiry_time": expiry_time
    })
    return {"session_token": session_token}

async def get_user_from_session_token(session_token: str | None):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Session token is required")
    db = get_db_client().trip_itinerary_planner
    session = await db.user_sessions.find_one({"session_token": session_token})
    if session is None or session["expiry_time"] < datetime.now():
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    user = await db.users.find_one({"user_id": session["user_id"]})
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {session['user_id']} not found")
    return user

import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException
from src.db import get_db_client
from src.request_types import AuthenticateUserRequest

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
SESSION_DURATION = timedelta(minutes=30)


@auth_router.post("", status_code=200)
async def authenticate_user(request: AuthenticateUserRequest):
    db = get_db_client().trip_itinerary_planner
    user = await db.users.find_one({"user_id": request.user_id})
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {request.user_id} not found"
        )
    if not bcrypt.checkpw(request.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")
    session_token = secrets.token_urlsafe(32)
    expiry_time = datetime.now() + SESSION_DURATION
    await db.user_sessions.insert_one(
        {
            "user_id": request.user_id,
            "session_token": session_token,
            "expiry_time": expiry_time,
        }
    )
    return {"session_token": session_token, "expiry_time": expiry_time}


async def authenticated_user(session_token: str | None = Header(None)):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Session token is required")
    db = get_db_client().trip_itinerary_planner
    session = await db.user_sessions.find_one({"session_token": session_token})
    if session is None or session["expiry_time"] < datetime.now():
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    user = await db.users.find_one({"user_id": session["user_id"]})
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {session['user_id']} not found"
        )
    return user


@auth_router.post("/renew", status_code=200)
async def refresh_session(user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    new_session_token = secrets.token_urlsafe(32)
    new_expiry_time = datetime.now() + SESSION_DURATION
    await db.user_sessions.insert_one(
        {
            "user_id": user["user_id"],
            "session_token": new_session_token,
            "expiry_time": new_expiry_time,
        }
    )
    return {"session_token": new_session_token, "expiry_time": new_expiry_time}

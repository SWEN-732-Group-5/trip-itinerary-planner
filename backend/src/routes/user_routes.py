import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from src.db import get_db_client
from src.db_types import (
    Trip,
    User,
)
from src.request_types import (
    CreateUserRequest,
    UpdatePasswordRequest,
    UpdateUserRequest,
)
from src.routes.auth import authenticated_user
from typing_extensions import Optional

user_router = APIRouter(prefix="/api/user", tags=["users"])


@user_router.post("", status_code=201)
async def create_user(request: CreateUserRequest):
    db = get_db_client().trip_itinerary_planner
    existing_user = await db.users.find_one({"user_id": request.user_id})
    if existing_user is not None:
        raise HTTPException(
            status_code=400, detail=f"User with id {request.user_id} already exists"
        )
    hashed_password = bcrypt.hashpw(
        request.password.encode(), bcrypt.gensalt()
    ).decode()
    user = User(
        user_id=request.user_id,
        display_name=request.display_name,
        phone_number=request.phone_number,
        password_hash=hashed_password,
    )
    await db.users.insert_one(user.model_dump())
    return {"message": f"User {request.user_id} created successfully"}


@user_router.get("/self", status_code=200)
async def get_self(user: dict = Depends(authenticated_user)):
    return {"display_name": user["display_name"], "phone_number": user["phone_number"]}


@user_router.get("/trips", status_code=200)
async def get_user_trips(
    user: dict = Depends(authenticated_user), user_id: Optional[str] = None
):
    if user_id is not None and user["user_id"] != user_id:
        raise HTTPException(
            status_code=403, detail="You can only access your own trips"
        )
    db = get_db_client().trip_itinerary_planner
    trips_cursor = db.trips.find(
        {"$or": [{"organizers": user["user_id"]}, {"guests": user["user_id"]}]}
    )
    trips = []
    async for trip_data in trips_cursor:
        trip = Trip.model_validate(trip_data)
        trips.append(trip)
    return {"trips": trips}


@user_router.get("/{user_id}", status_code=200)
async def get_user(user_id: str, _user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    user_data = await db.users.find_one({"user_id": user_id})
    if user_data is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return {
        "display_name": user_data["display_name"],
        "phone_number": user_data["phone_number"],
    }


@user_router.put("", response_model=User, status_code=200)
async def update_user(
    update_request: UpdateUserRequest, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    result = await db.users.update_one(
        {"user_id": user["user_id"]},
        {
            "$set": {
                "display_name": update_request.display_name,
                "phone_number": update_request.phone_number,
            }
        },
    )
    if result.modified_count == 0:
        raise HTTPException(
            status_code=404, detail=f"Failed to update user with id {user['user_id']}"
        )
    updated_user = await db.users.find_one({"user_id": user["user_id"]})
    return User.model_validate(updated_user)


@user_router.put("/password", status_code=200)
async def update_password(
    update_request: UpdatePasswordRequest, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    if not bcrypt.checkpw(
        update_request.current_password.encode(), user["password_hash"].encode()
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    hashed_password = bcrypt.hashpw(
        update_request.new_password.encode(), bcrypt.gensalt()
    ).decode()
    result = await db.users.update_one(
        {"user_id": user["user_id"]}, {"$set": {"password_hash": hashed_password}}
    )
    if result.modified_count == 0:
        raise HTTPException(
            status_code=404, detail=f"Failed to update user with id {user['user_id']}"
        )
    return {"message": "Password updated successfully"}


@user_router.delete("", status_code=204)
async def delete_user(user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    result = await db.users.delete_one({"user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404, detail=f"User with id {user['user_id']} not found"
        )
    result = await db.user_sessions.delete_many({"user_id": user["user_id"]})
    result = await db.trips.update_many(
        {"organizers": user["user_id"]}, {"$pull": {"organizers": user["user_id"]}}
    )
    result = await db.trips.update_many(
        {"guests": user["user_id"]}, {"$pull": {"guests": user["user_id"]}}
    )
    return None

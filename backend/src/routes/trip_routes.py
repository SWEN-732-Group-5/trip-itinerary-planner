from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from src.db import get_db_client
from src.db_types import (
    BookingSummaryItem,
    EventLocation,
    EventType,
    Trip,
    TripEvent,
    TripInvitation,
    User,
)
from src.request_types import (
    CreateEventRequest,
    CreateTripInvitationRequest,
    CreateTripRequest,
    UpdateEventLocationRequest,
    UpdateEventRequest,
    UpdateOrganizersRequest,
    UpdateTripRequest,
)
from src.routes.auth import authenticated_user

trip_router = APIRouter(prefix="/api/trips", tags=["trips"])


@trip_router.get(
    "/{trip_id}/booking-summary/{user_id}", response_model=list[BookingSummaryItem]
)
async def get_booking_summary(trip_id: str, user_id: str):
    db = get_db_client().trip_itinerary_planner
    bookings = await db.bookings.find({"trip_id": trip_id, "user_id": user_id}).to_list(
        length=100
    )
    return [
        BookingSummaryItem(
            booking_id=str(booking["_id"]),
            trip_id=booking["trip_id"],
            user_id=booking["user_id"],
            reference_number=booking["reference_number"],
            customer_service_number=booking["customer_service_number"],
            provider_name=booking["provider_name"],
        )
        for booking in bookings
    ]


@trip_router.get("/{trip_id}", response_model=Trip, status_code=200)
async def get_trip(trip_id: str, user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    if (
        user["user_id"] not in trip["organizers"]
        and user["user_id"] not in trip["guests"]
    ):
        raise HTTPException(
            status_code=403, detail="Only trip members can view trip details"
        )
    return trip


@trip_router.get("/{trip_id}/summary", status_code=200)
async def get_trip_summary(trip_id: str):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(status_code=404, detail=f"Trip {trip_id} not found")
    return {
        "trip_name": trip["trip_name"],
        "start_time": trip["start_time"],
        "end_time": trip["end_time"],
    }


@trip_router.post("", response_model=Trip, status_code=201)
async def create_trip(
    creation_request: CreateTripRequest, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    trips = await db.trips.find().to_list()
    next_id = len(trips) + 1
    new_trip = Trip(
        trip_id=f"trip{next_id}",
        trip_name=creation_request.trip_name,
        start_time=creation_request.start_time,
        end_time=creation_request.end_time,
        organizers=[user["user_id"]],
        guests=[],
        events=[],
    )
    new_trip_data = new_trip.model_dump()
    await db.trips.insert_one(new_trip_data)
    return new_trip


@trip_router.put("/{trip_id}", response_model=Trip)
async def update_trip(
    trip_id: str,
    update_request: UpdateTripRequest,
    user: dict = Depends(authenticated_user),
):
    db = get_db_client().trip_itinerary_planner
    trip: Trip | None = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(status_code=403, detail="Only organizers can update a trip")
    result = await db.trips.update_one(
        {"trip_id": trip_id},
        {
            "$set": {
                "trip_name": update_request.trip_name,
                "start_time": update_request.start_time,
                "end_time": update_request.end_time,
            }
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    return result.raw_result


@trip_router.put("/{trip_id}/organizers", response_model=Trip)
async def update_organizers(
    trip_id: str,
    update_request: UpdateOrganizersRequest,
    user: dict = Depends(authenticated_user),
):
    db = get_db_client().trip_itinerary_planner
    trip: Trip | None = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can modify trip organizers"
        )
    adding_organizers = set(
        [
            user_id
            for user_id in update_request.is_organizer.keys()
            if update_request.is_organizer[user_id]
        ]
    )
    removing_organizers = update_request.is_organizer.keys() - adding_organizers
    new_organizers = (set(trip["organizers"]) - removing_organizers) | adding_organizers
    new_guests = (set(trip["guests"]) - adding_organizers) | removing_organizers
    result = await db.trips.update_one(
        {"trip_id": trip["trip_id"]},
        {"$set": {"organizers": [*new_organizers], "guests": [*new_guests]}},
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it",
        )
    return result.raw_result


@trip_router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: str, user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to delete"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(status_code=403, detail="Only organizers can delete a trip")
    result = await db.trips.delete_one({"trip_id": trip_id})
    if result.deleted_count < 1:
        raise HTTPException(status_code=404, detail=f"Failed to delete trip {trip_id}")
    result = await db.trip_invitations.delete_many({"trip_id": trip_id})
    return None


@trip_router.post("/{trip_id}/event", response_model=Trip, status_code=201)
async def create_event(
    trip_id: str,
    creation_request: CreateEventRequest,
    user: dict = Depends(authenticated_user),
):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to add an event to"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can add events to a trip"
        )
    try:
        trip = Trip.model_validate(trip)
    except ValidationError as e:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip_id} but failed to parse it: {e}"
        )
    next_id = len(trip.events) + 1
    location = EventLocation(
        name=creation_request.location_name,
        location_type=EventType[creation_request.location_type],
        gps_position=(
            creation_request.location_coords[0],
            creation_request.location_coords[1],
        ),
    )
    new_event = TripEvent(
        event_id=f"event{next_id}",
        event_name=creation_request.event_name,
        event_description=creation_request.event_description,
        event_type=creation_request.event_type,
        location=location,
        end_location=None,
        start_time=creation_request.start_time,
        end_time=creation_request.end_time,
        attachments=[],
    )

    result = await db.trips.update_one(
        {"trip_id": trip_id}, {"$push": {"events": new_event.model_dump()}}
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip.trip_id} but failed to update it"
        )

    updated_trip = await db.trips.find_one({"trip_id": trip_id})
    if updated_trip is None:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip_id} but failed to retrieve it after update",
        )
    return Trip.model_validate(updated_trip)


@trip_router.put("/{trip_id}/event/{event_id}", response_model=Trip)
async def update_event(
    trip_id: str,
    event_id: str,
    update_request: UpdateEventRequest,
    user: dict = Depends(authenticated_user),
):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can edit events in a trip"
        )
    matching_events = [
        e for e in filter(lambda event: event["event_id"] == event_id, trip["events"])
    ]
    if len(matching_events) < 1:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find event {event_id} in trip {trip['trip_id']}",
        )
    if update_request.event_type not in EventType:
        raise HTTPException(
            status_code=400,
            detail=f'"{update_request.event_type}" is not a valid event type!',
        )
    updated_event = matching_events[0]
    updated_event["event_name"] = update_request.event_name
    updated_event["event_type"] = update_request.event_type
    updated_event["event_description"] = update_request.event_description
    updated_event["start_time"] = update_request.start_time
    updated_event["end_time"] = update_request.end_time

    result = await db.trips.update_one(
        {"trip_id": trip["trip_id"]},
        {
            "$set": {
                "events": [
                    updated_event if event["event_id"] == event_id else event
                    for event in trip["events"]
                ]
            }
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it",
        )
    return result.raw_result


@trip_router.put("/{trip_id}/event/{event_id}/location", response_model=Trip)
async def update_event_location(
    trip_id: str,
    event_id: str,
    update_request: UpdateEventLocationRequest,
    user: dict = Depends(authenticated_user),
):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can edit events in a trip"
        )
    matching_events = [
        e for e in filter(lambda event: event["event_id"] == event_id, trip["events"])
    ]
    if len(matching_events) < 1:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find event {event_id} in trip {trip['trip_id']}",
        )
    if update_request.location_type not in EventType:
        raise HTTPException(
            status_code=400,
            detail=f'"{update_request.location_type}" is not a valid location type!',
        )
    location = EventLocation(
        name=update_request.location_name,
        location_type=EventType[update_request.location_type],
        gps_position=(
            update_request.location_coords[0],
            update_request.location_coords[1],
        ),
    )
    updated_event = matching_events[0]
    if update_request.is_end_location:
        updated_event["end_location"] = location
    else:
        updated_event["location"] = location
    result = await db.trips.update_one(
        {"trip_id": trip["trip_id"]},
        {
            "$set": {
                "events": [
                    updated_event if event["event_id"] == event_id else event
                    for event in trip["events"]
                ]
            }
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it",
        )
    return result.raw_result


@trip_router.delete("/{trip_id}/event/{event_id}")
async def delete_event(
    trip_id: str, event_id: str, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can delete events from a trip"
        )
    if event_id not in [e["event_id"] for e in trip["events"]]:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find event {event_id} in trip {trip['trip_id']}",
        )
    result = await db.trips.update_one(
        {"trip_id": trip_id},
        {
            "$set": {
                "events": [
                    event for event in trip["events"] if event["event_id"] != event_id
                ]
            }
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it",
        )
    return result.raw_result


@trip_router.post("/{trip_id}/invite", response_model=TripInvitation, status_code=201)
async def create_trip_invitation(
    trip_id: str,
    creation_request: CreateTripInvitationRequest,
    user: dict = Depends(authenticated_user),
):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to invite users to"
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can create invitations for a trip"
        )
    all_invitations = await db.trip_invitations.find().to_list()
    next_id = len(all_invitations) + 1
    invitation = TripInvitation(
        invitation_id=f"invitation{next_id}",
        trip_id=trip_id,
        inviter_id=user["user_id"],
        is_organizer=creation_request.is_organizer,
        limit_uses=creation_request.limit_uses,
        expiry_time=creation_request.expiry_time,
    )
    await db.trip_invitations.insert_one(invitation.model_dump())
    return invitation


@trip_router.get(
    "/{trip_id}/invitations", response_model=list[TripInvitation], status_code=200
)
async def get_trip_invitations(trip_id: str, user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find trip {trip_id} to get invitations for",
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can view invitations for a trip"
        )
    invitations_cursor = db.trip_invitations.find({"trip_id": trip_id})
    invitations = []
    async for invitation in invitations_cursor:
        invitations.append(TripInvitation.model_validate(invitation))
    return invitations


@trip_router.get(
    "/invitation/{invitation_id}", status_code=200
)
async def get_trip_invitation(invitation_id: str):
    db = get_db_client().trip_itinerary_planner
    invitation = await db.trip_invitations.find_one({"invitation_id": invitation_id})
    if invitation is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find invitation {invitation_id}"
        )
    invitation = TripInvitation.model_validate(invitation)
    trip = await db.trips.find_one({"trip_id": invitation.trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Invitation {invitation_id} not valid"
        )
    trip = Trip.model_validate(trip)
    inviter = await db.users.find_one({"user_id": invitation.inviter_id})
    if inviter is None:
        raise HTTPException(
            status_code=404, detail=f"Invitation {invitation_id} not valid"
        )
    inviter = User.model_validate(inviter)
    if invitation.inviter_id not in trip.organizers:
        raise HTTPException(
            status_code=404, detail=f"Invitation {invitation_id} not valid"
        )
    return {
        "trip_name": trip.trip_name, 
        "trip_start": trip.start_time, 
        "trip_end": trip.end_time, 
        "inviter": invitation.inviter_id, 
        "inviter_name": inviter.display_name, 
        "is_organizer": invitation.is_organizer, 
        "expiry_time": invitation.expiry_time
    }


@trip_router.put("/invitation/{invitation_id}/accept", status_code=200)
async def accept_trip_invitation(
    invitation_id: str, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    invitation = await db.trip_invitations.find_one({"invitation_id": invitation_id})
    if invitation is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find invitation {invitation_id}"
        )
    if invitation["expiry_time"] < datetime.now():
        raise HTTPException(
            status_code=400,
            detail=f"Invitation {invitation_id} has expired and can no longer be accepted",
        )
    if invitation["limit_uses"] <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Invitation {invitation_id} has already been used the maximum number of times",
        )
    trip = await db.trips.find_one({"trip_id": invitation["trip_id"]})
    if trip is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find trip {invitation['trip_id']} to accept invitation for",
        )
    if user["user_id"] in trip["guests"] or user["user_id"] in trip["organizers"]:
        raise HTTPException(
            status_code=400,
            detail=f"User {user['user_id']} is already a member of trip {trip['trip_id']}",
        )
    if invitation["is_organizer"]:
        new_organizers = trip["organizers"] + [user["user_id"]]
        new_guests = trip["guests"]
    else:
        new_organizers = trip["organizers"]
        new_guests = trip["guests"] + [user["user_id"]]
    result = await db.trips.update_one(
        {"trip_id": trip["trip_id"]},
        {
            "$set": {
                "organizers": new_organizers,
                "guests": new_guests,
            }
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it with new guest",
        )
    result = await db.trip_invitations.update_one(
        {"invitation_id": invitation_id, "trip_id": trip["trip_id"]},
        {"$inc": {"limit_uses": -1}},
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found invitation {invitation_id} but failed to update its remaining uses",
        )
    result = await db.trips.find_one({"trip_id": trip["trip_id"]})
    if result is None:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to retrieve it after update",
        )
    return {"trip": Trip.model_validate(result)}


@trip_router.delete("/{trip_id}/invite/{invitation_id}", status_code=204)
async def delete_trip_invitation(
    trip_id: str, invitation_id: str, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    invitation = await db.trip_invitations.find_one(
        {"_id": invitation_id, "trip_id": trip_id}
    )
    if invitation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find invitation {invitation_id} for trip {trip_id}",
        )
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find trip {trip_id} to delete invitation from",
        )
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can delete invitations for a trip"
        )
    result = await db.trip_invitations.delete_one({"_id": invitation["_id"]})
    if result.deleted_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found invitation {invitation_id} but failed to delete it",
        )
    return None


@trip_router.put("/{trip_id}/leave-trip", status_code=200)
async def leave_trip(trip_id: str, user: dict = Depends(authenticated_user)):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(status_code=404, detail=f"Could not find trip {trip_id}")
    if (
        user["user_id"] not in trip["organizers"]
        and user["user_id"] not in trip["guests"]
    ):
        raise HTTPException(status_code=403, detail="Not a member of this trip")
    new_organizers = [
        organizer for organizer in trip["organizers"] if organizer != user["user_id"]
    ]
    new_guests = [guest for guest in trip["guests"] if guest != user["user_id"]]
    result = await db.trips.update_one(
        {"trip_id": trip_id},
        {
            "organizers": new_organizers,
            "guests": new_guests,
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it",
        )
    return {"trip": Trip.model_validate(trip)}


@trip_router.put("/{trip_id}/remove-user/{user_id}", status_code=200)
async def remove_user_from_trip(
    trip_id: str, user_id: str, user: dict = Depends(authenticated_user)
):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(status_code=404, detail=f"Could not find trip {trip_id}")
    if user["user_id"] not in trip["organizers"]:
        raise HTTPException(
            status_code=403, detail="Only organizers can remove users from a trip"
        )
    new_organizers = [
        organizer for organizer in trip["organizers"] if organizer != user_id
    ]
    new_guests = [guest for guest in trip["guests"] if guest != user_id]
    result = await db.trips.update_one(
        {"trip_id": trip_id},
        {
            "organizers": new_organizers,
            "guests": new_guests,
        },
    )
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500,
            detail=f"Found trip {trip['trip_id']} but failed to update it",
        )
    return {"trip": Trip.model_validate(trip)}

from fastapi import APIRouter, HTTPException

from src.db import get_db_client
from src.db_types import EventLocation, EventType, Trip, BookingSummaryItem, TripEvent, User
from src.request_types import CreateEventRequest, CreateTripRequest, UpdateEventLocationRequest, UpdateEventRequest, UpdateOrganizersRequest, UpdateTripRequest

trip_router = APIRouter(
    prefix="/trips", 
    tags=["trips"]
)

@trip_router.get("/{trip_id}/booking-summary/{user_id}", response_model=list[BookingSummaryItem])
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
async def get_trip(trip_id: str):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Trip {trip_id} not found"
        )
    return trip

@trip_router.post("", response_model=Trip, status_code=201)
async def create_trip(creation_request: CreateTripRequest):
    db = get_db_client().trip_itinerary_planner
    trips = await db.trips.find().to_list()
    next_id = len(trips)+1
    new_trip = Trip(
        trip_id=f"trip{next_id}", 
        trip_name=creation_request.trip_name, 
        start_time=creation_request.start_time, 
        end_time=creation_request.end_time, 
        organizers=[], 
        guests=[],
        events=[], 
        locations=[]
    )
    await db.trips.insert_one(new_trip)
    return new_trip

@trip_router.put("/{trip_id}", response_model=Trip)
async def update_trip(trip_id: str, update_request: UpdateTripRequest):
    db = get_db_client().trip_itinerary_planner
    result = await db.trips.update_one({"trip_id": trip_id}, {
        "trip_name": update_request.trip_name, 
        "start_time": update_request.start_time, 
        "end_time": update_request.end_time
    })
    if result.modified_count < 1:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    return result.raw_result

@trip_router.put("/{trip_id}/organizers", response_model=Trip)
async def update_organizers(trip_id: str, update_request: UpdateOrganizersRequest):
    db = get_db_client().trip_itinerary_planner
    trip: Trip | None = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    adding_organizers = set([user_id for user_id in update_request.users.keys() if update_request.users[user_id] == True])
    removing_organizers = update_request.users.keys() - adding_organizers
    new_organizers = (set(trip.organizers) - removing_organizers) | adding_organizers
    new_guests = (set(trip.guests) - adding_organizers) | removing_organizers
    result = await db.trips.update_one({"trip_id": trip.id}, {
        "organizers": [*new_organizers], 
        "guests": [*new_guests]
    })
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip.id} but failed to update it"
        )
    return result.raw_result

@trip_router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: str):
    db = get_db_client().trip_itinerary_planner
    result = await db.trips.delete_one({"trip_id": trip_id})
    if result.deleted_count < 1:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to delete"
        )
    return None
    
@trip_router.post("/{trip_id}/event", response_model=Trip, status_code=201)
async def create_event(trip_id: str, creation_request: CreateEventRequest):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to add an event to"
        )
    next_id = len(trip.events) + 1
    if creation_request.event_type not in EventType:
        raise HTTPException(
            status_code=400, detail=f'"{creation_request.event_type}" is not a valid event type!'
        )
    if creation_request.location_type not in EventType:
        raise HTTPException(
            status_code=400, detail=f'"{creation_request.location_type}" is not a valid location type!'
        )
    if len(creation_request.location_coords) != 2:
        raise HTTPException(
            status_code=400, detail=f'Must provide both a latitude and longitude coordinate!'
        )
    location = EventLocation(
        name=creation_request.location_name, 
        location_type=EventType[creation_request.location_type], 
        gps_position=(creation_request.location_coords[0], creation_request.location_coords[1])
    )
    new_event = TripEvent(
        event_id=f"event{next_id}", 
        event_name=creation_request.event_name, 
        event_description=creation_request.event_description, 
        event_type=EventType[creation_request.event_type], 
        location=location, 
        end_location=None, 
        start_time=creation_request.start_time, 
        end_time=creation_request.end_time, 
        attachments=[]
    )
    result = await db.trips.update_one({"trip_id": trip.id}, {
        "events": [*trip.events, new_event]
    })
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip.id} but failed to update it"
        )
    return result.raw_result

@trip_router.put("/{trip_id}/event/{event_id}", response_model=Trip)
async def update_event(trip_id: str, event_id: str, update_request: UpdateEventRequest):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    matching_events = [e for e in filter(lambda event: event['event_id'] == event_id, trip.events)]
    if len(matching_events) < 1:
        raise HTTPException(
            status_code=404, detail=f"Could not find event {event_id} in trip {trip.id}"
        )
    if update_request.event_type not in EventType:
        raise HTTPException(
            status_code=400, detail=f'"{update_request.event_type}" is not a valid event type!'
        )
    updated_event = matching_events[0]
    updated_event["event_name"] = update_request.event_name
    updated_event["event_type"] = update_request.event_type
    updated_event["event_description"] = update_request.event_description
    updated_event["start_time"] = update_request.start_time
    updated_event["end_time"] = update_request.end_time

    result = await db.trips.update_one({"trip_id": trip.id}, {
        "events": [updated_event if event["event_id"] == event_id else event for event in trip["events"]]
    })
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip.id} but failed to update it"
        )
    return result.raw_result
    

@trip_router.put("/{trip_id}/event/{event_id}/location", response_model=Trip)
async def update_event_location(trip_id: str, event_id: str, update_request: UpdateEventLocationRequest):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    matching_events = [e for e in filter(lambda event: event['event_id'] == event_id, trip.events)]
    if len(matching_events) < 1:
        raise HTTPException(
            status_code=404, detail=f"Could not find event {event_id} in trip {trip.id}"
        )
    if update_request.location_type not in EventType:
        raise HTTPException(
            status_code=400, detail=f'"{update_request.location_type}" is not a valid location type!'
        )
    location = EventLocation(
        name=update_request.location_name, 
        location_type=EventType[update_request.location_type], 
        gps_position=(update_request.location_coords[0], update_request.location_coords[1])
    )
    updated_event = matching_events[0]
    if update_request.is_end_location:
        updated_event["end_location"] = location
    else:
        updated_event["location"] = location
    result = await db.trips.update_one({"trip_id": trip.id}, {
        "events": [updated_event if event["event_id"] == event_id else event for event in trip["events"]]
    })
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip.id} but failed to update it"
        )
    return result.raw_result

@trip_router.delete("/{trip_id}/event/{event_id}")
async def delete_event(trip_id: str, event_id: str):
    db = get_db_client().trip_itinerary_planner
    trip = await db.trips.find_one({"trip_id": trip_id})
    if trip is None:
        raise HTTPException(
            status_code=404, detail=f"Could not find trip {trip_id} to update"
        )
    if not event_id in [e["event_id"] for e in trip.events]:
        raise HTTPException(
            status_code=404, detail=f"Could not find event {event_id} in trip {trip.id}"
        )
    result = await db.trips.update_one({"trip_id": trip_id}, {
        "events": [event for event in trip["events"] if event["event_id"] != event_id]
    })
    if result.modified_count < 1:
        raise HTTPException(
            status_code=500, detail=f"Found trip {trip.id} but failed to update it"
        )
    return result.raw_result

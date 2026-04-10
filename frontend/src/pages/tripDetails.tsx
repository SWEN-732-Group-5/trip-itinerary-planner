import { useState } from 'react';
import { useParams } from 'react-router';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowRight, MapPin } from 'lucide-react';

import {
	createEventInput,
	useCreateTripEvent,
	useTrip,
	type CreateTripEventInput,
} from '@/api/trip';
import { Button } from '@/components/ui/button';
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const DEFAULT_FORM_STATE: Partial<CreateTripEventInput> = {
	event_name: '',
	event_description: '',
	event_type: 'other',
	location_name: '',
	location_type: 'other',
};
const DEFAULT_COORDS: [string, string] = ['', ''];
const DEFAULT_DATE = () => new Date().toISOString().slice(0, 16); // current date and time in YYYY-MM-DDTHH:mm format

function TripDetails() {
	const { id } = useParams();
	const { data: tripData, isLoading } = useTrip(id);
	const { mutateAsync: updateTripEvent } = useCreateTripEvent({ trip_id: id });
	const [open, setOpen] = useState(false);

	if (isLoading) return <div className="p-6">Loading...</div>;
	if (!tripData) return <div className="p-6">Trip not found</div>;

	const { trip_name, start_time, end_time, organizers, guests, events } =
		tripData;

	const handleCreateEvent = async (form: FormData) => {
		const newEventPayload = createEventInput.safeParse(form);
		if (!newEventPayload.success) {
			alert('Invalid event data');
			return;
		}
		try {
			await updateTripEvent(newEventPayload.data);
			setOpen(false);
		} catch (err) {
			console.error(err);
		}
	};

	return (
		<div className="p-6 space-y-6">
			<div>
				<h1 className="text-3xl font-bold mb-2">{trip_name}</h1>
				<p className="text-muted-foreground">
					{new Date(start_time).toLocaleString()}{' '}
					<ArrowRight className="inline mx-1" />
					{new Date(end_time).toLocaleString()}
				</p>
			</div>

			<Separator />

			<Card>
				<CardHeader>
					<CardTitle>People</CardTitle>
				</CardHeader>
				<CardContent className="space-y-3">
					<div>
						<h3 className="font-semibold mb-1">Organizers</h3>
						{organizers.length === 0 ?
							<p className="text-sm text-muted-foreground">None</p>
						:	organizers.map((user) => (
								<Badge key={user.user_id} className="mr-2">
									{user.display_name}
								</Badge>
							))
						}
					</div>

					<div>
						<h3 className="font-semibold mb-1">Guests</h3>
						{guests.length === 0 ?
							<p className="text-sm text-muted-foreground">None</p>
						:	guests.map((user) => (
								<Badge key={user.user_id} variant="secondary" className="mr-2">
									{user.display_name}
								</Badge>
							))
						}
					</div>
				</CardContent>
			</Card>

			{/* Events */}
			<Card>
				<CardHeader>
					<CardTitle>Events</CardTitle>
					<Dialog open={open} onOpenChange={setOpen}>
						<DialogTrigger asChild>
							<Button>Add Event</Button>
						</DialogTrigger>
						<DialogContent>
							<DialogHeader>
								<DialogTitle>Create Event</DialogTitle>
							</DialogHeader>
							<form action={handleCreateEvent}>
								<div className="space-y-3">
									<div>
										<Label>Name</Label>
										<Input
											name="event_name"
											defaultValue={DEFAULT_FORM_STATE.event_name}
										/>
									</div>

									<div>
										<Label>Description</Label>
										<Input
											name="event_description"
											defaultValue={DEFAULT_FORM_STATE.event_description}
										/>
									</div>

									<div>
										<Label>Location</Label>
										<Input
											name="location_name"
											defaultValue={DEFAULT_FORM_STATE.location_name}
										/>
									</div>

									<div className="flex gap-2">
										<Input
											placeholder="Lat"
											type="number"
											name="location_lat"
											defaultValue={DEFAULT_COORDS[0]}
										/>
										<Input
											placeholder="Lng"
											type="number"
											name="location_lng"
											defaultValue={DEFAULT_COORDS[1]}
										/>
									</div>

									<div>
										<Label>Start</Label>
										<Input
											type="datetime-local"
											name="start_time"
											defaultValue={DEFAULT_DATE()}
										/>
									</div>

									<div>
										<Label>End</Label>
										<Input
											type="datetime-local"
											name="end_time"
											defaultValue={''}
										/>
									</div>

									<Button type="submit" className="w-full">
										Create
									</Button>
								</div>
							</form>
						</DialogContent>
					</Dialog>
				</CardHeader>
				<CardContent className="space-y-4">
					{events.length === 0 ?
						<p className="text-muted-foreground">No events yet</p>
					:	events.map((event) => (
							<div key={event.event_id} className="border p-3 rounded-xl">
								<div className="flex justify-between items-center">
									<h3 className="font-semibold">{event.event_name}</h3>
									<Badge>{event.event_type}</Badge>
								</div>

								<p className="text-sm text-muted-foreground">
									{new Date(event.start_time).toLocaleString()}{' '}
									<ArrowRight className="inline mx-1" />
									{new Date(event.end_time).toLocaleString()}
								</p>

								<p className="text-sm mt-1">
									{event.event_description || 'No description'}
								</p>

								{event.location && (
									<p className="text-sm mt-1 text-muted-foreground">
										<MapPin className="inline" /> {event.location.name}
									</p>
								)}
							</div>
						))
					}
				</CardContent>
			</Card>
		</div>
	);
}

export default TripDetails;

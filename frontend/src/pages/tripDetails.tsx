import { useState } from 'react';
import { useParams } from 'react-router';
import { Controller, useForm } from 'react-hook-form';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowRight, MapPin } from 'lucide-react';
import { zodResolver } from '@hookform/resolvers/zod';

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
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type z from 'zod';
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field';

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

	const form = useForm<CreateTripEventInput>({
		resolver: zodResolver(createEventInput),
		defaultValues: {
			...DEFAULT_FORM_STATE,
			location_coords: DEFAULT_COORDS,
			start_time: new Date(),
			end_time: new Date(),
		},
	});

	if (isLoading) return <div className="p-6">Loading...</div>;
	if (!tripData) return <div className="p-6">Trip not found</div>;

	const { trip_name, start_time, end_time, organizers, guests, events } =
		tripData;

	const onSubmit = async (values: z.infer<typeof createEventInput>) => {
		try {
			await updateTripEvent(values);
			setOpen(false);
			form.reset();
		} catch (err: any) {
			form.setError("root", { message: err?.message ?? "Failed to create event" });
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
							: organizers.map((user) => (
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
							: guests.map((user) => (
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
							<form id="event-create-form" onSubmit={form.handleSubmit(onSubmit)}>
								<FieldGroup>
									<Controller name="event_name" control={form.control} render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="event_create_form_name">Event Name</FieldLabel>
											<Input {...field} id="event_create_form_name" aria-invalid={fieldState.invalid} placeholder="Plane" autoComplete="off" />
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)} />
								</FieldGroup>
								<FieldGroup>
									<Controller name="event_description" control={form.control} render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="event_create_form_description">Description</FieldLabel>
											<Input {...field} id="event_create_form_description" aria-invalid={fieldState.invalid} placeholder="Flight to Paris" autoComplete="off" />
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)} />
								</FieldGroup>
								<FieldGroup>
									<Controller name="location_name" control={form.control} render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="event_create_form_location_name">Location Name</FieldLabel>
											<Input {...field} id="event_create_form_location_name" aria-invalid={fieldState.invalid} placeholder="CDG Airport" autoComplete="off" />
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)} />
								</FieldGroup>
								<FieldGroup>
									<Controller name="location_coords" control={form.control} render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel>Location Coordinates</FieldLabel>
											<div className="flex gap-2">
												<Input {...field} id="event_create_form_location_lat" aria-invalid={fieldState.invalid} placeholder="Lat" autoComplete="off" onChange={e => {
													const lat = Number(e.target.value);
													const lng = field.value[1] || 0;
													field.onChange([lat, lng]);
												}} value={
													field.value[0].toString() || ''
												} />
												<Input {...field} id="event_create_form_location_lng" aria-invalid={fieldState.invalid} placeholder="Lng" autoComplete="off" onChange={e => {
													const lng = Number(e.target.value);
													const lat = field.value[0] || 0;
													field.onChange([lat, lng]);
												}} value={
													field.value[1].toString() || ''
												} />
											</div>
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)} />
								</FieldGroup>
								<FieldGroup>
									<Controller name="start_time" control={form.control} render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="event_create_form_start_time">Start Time</FieldLabel>
											<Input {...field} id="event_create_form_start_time" aria-invalid={fieldState.invalid} type="datetime-local" onChange={e => {
												const orig = e.target.value; // e.g. "2025-05-05T14:30"
												// Only transform when the value is "YYYY-MM-DDTHH:MM"
												let val = orig;
												if (orig && orig.length === 16) {
													val = orig + ":00Z"; // → "2025-05-05T14:30:00Z"
												}
												field.onChange(val);
											}}
												value={
													// To keep the display correct in the input,
													// parse from the ISO (with Z) back to "YYYY-MM-DDTHH:MM"
													typeof field.value === "string"
														? field.value.replace(":00Z", "")
														: ""
												} />
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)} />
								</FieldGroup>
								<FieldGroup>
									<Controller name="end_time" control={form.control} render={({ field, fieldState }) => (
										<Field data-invalid={fieldState.invalid}>
											<FieldLabel htmlFor="event_create_form_end_time">End Time</FieldLabel>
											<Input {...field} id="event_create_form_end_time" aria-invalid={fieldState.invalid} type="datetime-local" onChange={e => {
												const orig = e.target.value; // e.g. "2025-05-05T14:30"
												// Only transform when the value is "YYYY-MM-DDTHH:MM"
												let val = orig;
												if (orig && orig.length === 16) {
													val = orig + ":00Z"; // → "2025-05-05T14:30:00Z"
												}
												field.onChange(val);
											}}
												value={
													// To keep the display correct in the input,
													// parse from the ISO (with Z) back to "YYYY-MM-DDTHH:MM"
													typeof field.value === "string"
														? field.value.replace(":00Z", "")
														: ""
												} />
											{fieldState.invalid && (
												<FieldError errors={[fieldState.error]} />
											)}
										</Field>
									)} />
								</FieldGroup>
							</form>
							<DialogFooter>
								<Button type="submit" form="event-create-form">Create</Button>
							</DialogFooter>
						</DialogContent>
					</Dialog>
				</CardHeader>
				<CardContent className="space-y-4">
					{events.length === 0 ?
						<p className="text-muted-foreground">No events yet</p>
						: events.map((event) => (
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

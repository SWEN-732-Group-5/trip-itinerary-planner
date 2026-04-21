import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router';
import { Controller, useForm } from 'react-hook-form';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowRight, Copy, CopyIcon, MapPin, Trash } from 'lucide-react';
import { zodResolver } from '@hookform/resolvers/zod';

import {
	createEventInput,
	useCreateTripEvent,
	useTrip,
	type CreateTripEventInput,
} from '@/api/trip';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
	Dialog,
	DialogContent,
	DialogFooter,
	DialogHeader,
	DialogTitle,
	DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Field, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type z from 'zod';
import { createInvitationInput, useCreateInvitation, useDeleteInvitation, useTripInvitations, type CreateInvitationInput } from '@/api/invitation';
import { useSelf } from '@/lib/auth/auth';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const DEFAULT_EVENT_FORM_STATE: Partial<CreateTripEventInput> = {
	event_name: '',
	event_description: '',
	event_type: 'other',
	location_name: '',
	location_type: 'other',
};
const DEFAULT_COORDS: [number, number] = [0, 0];
const DEFAULT_DATE = () => new Date().toISOString().slice(0, 16); // current date and time in YYYY-MM-DDTHH:mm format

const DEFAULT_INVITATION_FORM_STATE: Partial<CreateInvitationInput> = {
	limit_uses: 1, 
	is_organizer: false,
}

function TripDetails() {
	const location = useLocation();
	const { hash, pathname, search } = location;
	const { id } = useParams();
	const { data: userData } = useSelf();
	const { data: tripData, isLoading: tripLoading } = useTrip(id);
	const { data: invitations } = useTripInvitations(id);
	const { mutateAsync: updateTripEvent } = useCreateTripEvent({ trip_id: id });
	const { mutateAsync: createInvitation, isPending: invitationPending } = useCreateInvitation({ tripId: id });
	const { mutateAsync: deleteInvitation } = useDeleteInvitation({ tripId: id });
	const [eventOpen, setEventOpen] = useState(false);
	const [inviteOpen, setInviteOpen] = useState(false);
	const [displayInviteLink, setDisplayInviteLink] = useState<string | null>(null);

	useEffect(() => {console.log(`Logged in as ` + userData?.display_name)})
	useEffect(() => {console.log(`Trip has ` + invitations + " invitations")})

	useEffect(() => {setDisplayInviteLink(null)}, [inviteOpen]);

	const eventForm = useForm<CreateTripEventInput>({
		resolver: zodResolver(createEventInput),
		defaultValues: {
			...DEFAULT_EVENT_FORM_STATE,
			location_coords: DEFAULT_COORDS,
			start_time: new Date(),
			end_time: new Date(),
		},
	});

	const invitationForm = useForm<CreateInvitationInput>({
		resolver: zodResolver(createInvitationInput),
		defaultValues: {
			...DEFAULT_INVITATION_FORM_STATE,
			limit_uses: 1, 
			is_organizer: false,
			expiry_time: new Date(),
		},
	});

	const invitationLink = (invitationId: string) => window.location.origin + "/accept-invitation/" + invitationId;

	if (tripLoading) return <div className="p-6">Loading...</div>;
	if (!tripData) return <div className="p-6">Trip not found</div>;

	const { trip_name, start_time, end_time, organizers, guests, events } =
		tripData;

	const onSubmitEvent = async (values: z.infer<typeof createEventInput>) => {
		try {
			await updateTripEvent(values);
			setEventOpen(false);
			eventForm.reset();
		} catch (err: any) {
			eventForm.setError("root", { message: err?.message ?? "Failed to create event" });
		}
	};

	const onSubmitInvitation = async (values: z.infer<typeof createInvitationInput>) => {
		try {
			const invitation = await createInvitation(values);
			setDisplayInviteLink(invitationLink(invitation.invitation_id));
			eventForm.reset();
		} catch (err: any) {
			eventForm.setError("root", { message: err?.message ?? "Failed to create invitation" });
		}
	};

	return (
		<div className="p-6 space-y-6">
			<TooltipProvider>
				<div>
					<h1 className="text-3xl font-bold mb-2">{trip_name}</h1>
					<p className="text-muted-foreground">
						{new Date(start_time).toLocaleString()}{' '}
						<ArrowRight className="inline mx-1" />
						{new Date(end_time).toLocaleString()}
					</p>
				</div>

				<Separator />

				<Tabs defaultValue='events' onValueChange={() => {setEventOpen(false); setInviteOpen(false);}}>
					<TabsList>
						<TabsTrigger value='events'>Events</TabsTrigger>
						<TabsTrigger value='people'>People</TabsTrigger>
						{userData && tripData.organizers.includes(userData.user_id) && <TabsTrigger value='invitations'>Invitations</TabsTrigger>}
					</TabsList>
					<TabsContent value='events'>
						<Card>
							<CardHeader>
								<CardTitle>Events</CardTitle>
								<Dialog open={eventOpen} onOpenChange={setEventOpen}>
									<DialogTrigger asChild>
										<Button>Add Event</Button>
									</DialogTrigger>
									<DialogContent>
										<DialogHeader>
											<DialogTitle>Create Event</DialogTitle>
										</DialogHeader>
										<form id="event-create-form" onSubmit={eventForm.handleSubmit(onSubmitEvent)}>
											<FieldGroup>
												<Controller name="event_name" control={eventForm.control} render={({ field, fieldState }) => (
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
												<Controller name="event_description" control={eventForm.control} render={({ field, fieldState }) => (
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
												<Controller name="location_name" control={eventForm.control} render={({ field, fieldState }) => (
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
												<Controller name="location_coords" control={eventForm.control} render={({ field, fieldState }) => (
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
												<Controller name="start_time" control={eventForm.control} render={({ field, fieldState }) => (
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
												<Controller name="end_time" control={eventForm.control} render={({ field, fieldState }) => (
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
					</TabsContent>
					<TabsContent value='people'>
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
					</TabsContent>
					{userData && tripData.organizers.includes(userData.user_id) && 
						<TabsContent value='invitations'>
							<Card>
								<CardHeader>
									<CardTitle>Invitations</CardTitle>
									<Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
										<DialogTrigger asChild>
											<Button>Create Invitation</Button>
										</DialogTrigger>
										<DialogContent>
											<DialogHeader>
												<DialogTitle>Create Invitation</DialogTitle>
											</DialogHeader>
											<form className='space-y-2' id="invitation-create-form" onSubmit={invitationForm.handleSubmit(onSubmitInvitation)}>
												<FieldGroup>
													<Controller name="limit_uses" control={invitationForm.control} render={({ field, fieldState }) => (
														<Field data-invalid={fieldState.invalid}>
															<FieldLabel htmlFor="invitation_create_form_limit">Number of Uses</FieldLabel>
															<Input {...field} id="invitation_create_form_limit" aria-invalid={fieldState.invalid} type="number" autoComplete="off" />
															{fieldState.invalid && (
																<FieldError errors={[fieldState.error]} />
															)}
														</Field>
													)} />
												</FieldGroup>
												<FieldGroup>
													<Controller name="is_organizer" control={invitationForm.control} render={({ field, fieldState }) => (
														<Field data-invalid={fieldState.invalid} orientation="horizontal">
															<Checkbox {...field} id="invitation_create_form_organizer" name={field.name} checked={field.value} onCheckedChange={field.onChange} />
															<FieldLabel htmlFor="invitation_create_form_organizer">Invite as Organizer?</FieldLabel>
														</Field>
													)} />
												</FieldGroup>
												<FieldGroup>
													<Controller name="expiry_time" control={invitationForm.control} render={({ field, fieldState }) => (
														<Field data-invalid={fieldState.invalid}>
															<FieldLabel htmlFor="invitation_create_form_expiry_time">Expires</FieldLabel>
															<Input {...field} id="invitation_create_form_expiry_time" aria-invalid={fieldState.invalid} type="datetime-local" onChange={e => {
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
											<DialogFooter className={displayInviteLink ? 'sm:justify-start' : ''}>
												{displayInviteLink ? 
													<div className='flex flex-row items-center justify-between border-2 rounded-sm bg-gray-800 p-2'>
														<p className=''>{displayInviteLink}</p>
														<Tooltip>
															<TooltipTrigger asChild>
																<Button variant="ghost" onClick={() => {navigator.clipboard.writeText(displayInviteLink)}}>
																	<CopyIcon />
																</Button>
															</TooltipTrigger>
															<TooltipContent>Copy invite link</TooltipContent>
														</Tooltip>
													</div>
												:
													<Button 
														type="submit" form="invitation-create-form"
														disabled={invitationPending}
													>
														{invitationPending ? "Creating..." : "Create"}
													</Button>
												}
												
											</DialogFooter>
										</DialogContent>
									</Dialog>
								</CardHeader>
								<CardContent className="space-y-4">
									{!invitations || invitations.length === 0 ?
										<p className="text-muted-foreground">No invitations yet</p>
										: invitations.map((invitation) => {
											const isExpired = new Date(invitation.expiry_time) < new Date();
											return (
												<div key={invitation.invitation_id} className="border p-3 rounded-xl">
													<div className="flex justify-between items-center">
														<div className='flex flex-row justify-start items-center space-x-4'>
															<h3 className="text-sm text-muted-foreground">{invitation.invitation_id}</h3>
															<Badge>{invitation.is_organizer ? "Organizer" : "Guest"}</Badge>
														</div>
														<div>
															{!isExpired && invitation.limit_uses > 0 && 
																<Tooltip>
																	<TooltipTrigger asChild>
																		<Button variant="ghost" onClick={() => {navigator.clipboard.writeText(invitationLink(invitation.invitation_id))}}>
																			<CopyIcon />
																		</Button>
																	</TooltipTrigger>
																	<TooltipContent>Copy invite link</TooltipContent>
																</Tooltip>
															}
															<Button variant="ghost" onClick={() => deleteInvitation({invitationId: invitation.invitation_id})}>
																<Trash className='text-destructive' />
															</Button>
														</div>
													</div>

													<div className="flex justify-between items-center">
														<p className="font-semibold">
															{invitation.limit_uses} uses remaining
														</p>
														<p className="font-semibold">
															Expire{isExpired ? "d" : "s"} {new Date(invitation.expiry_time).toLocaleString()}
														</p>
													</div>
													
												</div>
											)
										})
									}
								</CardContent>
							</Card>
						</TabsContent>
					}
				</Tabs>
			</TooltipProvider>
		</div>
	);
}

export default TripDetails;

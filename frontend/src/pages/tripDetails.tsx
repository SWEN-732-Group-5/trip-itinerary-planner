import { useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router';
import { Controller, useForm } from 'react-hook-form';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { ArrowRight, MapPin, Edit2, Trash2, CopyIcon, Trash } from 'lucide-react';
import { zodResolver } from '@hookform/resolvers/zod';

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

import {
    eventInput,
    useCreateTripEvent,
    useMutateTripEvent,
    useDeleteTripEvent,
    useTrip,
    type CreateTripEventInput,
    useUploadFile,
} from '@/api/trip';
import { useUserNames } from '@/api/user';

const DEFAULT_FORM_STATE: Partial<CreateTripEventInput> = {
    event_name: '',
    event_description: '',
    event_type: 'other',
    location_name: '',
    location_type: 'other',
    image_urls: [],
};

const toLocalISO = (dateStr: string | Date) => {
    const d = new Date(dateStr);
    const offset = d.getTimezoneOffset() * 60000;
    return new Date(d.getTime() - offset).toISOString().slice(0, 16);
};


const DEFAULT_EVENT_FORM_STATE: Partial<CreateTripEventInput> = {
    event_name: '',
    event_description: '',
    event_type: 'other',
    location_name: '',
    location_type: 'other',
    image_urls: [],
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
    const { data: userNames } = useUserNames([...(tripData?.organizers || []), ...(tripData?.guests || [])], !!tripData);
    const { mutateAsync: createTripEvent } = useCreateTripEvent({ trip_id: id });
    const { mutateAsync: updateTripEvent } = useMutateTripEvent({ trip_id: id });
    const { mutateAsync: deleteTripEvent } = useDeleteTripEvent({ trip_id: id });
    const { uploadFile } = useUploadFile();
    const { mutateAsync: createInvitation, isPending: invitationPending } = useCreateInvitation({ tripId: id });
    const { mutateAsync: deleteInvitation } = useDeleteInvitation({ tripId: id });
    const [eventOpen, setEventOpen] = useState(false);
    const [inviteOpen, setInviteOpen] = useState(false);
    const [displayInviteLink, setDisplayInviteLink] = useState<string | null>(null);
    const [editingEventId, setEditingEventId] = useState<string | null>(null);

    useEffect(() => { console.log(`Logged in as ` + userData?.display_name) })
    useEffect(() => { console.log(`Trip has ` + invitations + " invitations") })

    useEffect(() => { setDisplayInviteLink(null) }, [inviteOpen]);

    const eventForm = useForm<CreateTripEventInput>({
        resolver: zodResolver(eventInput),
        defaultValues: {
            ...DEFAULT_EVENT_FORM_STATE,
            location_coords: DEFAULT_COORDS,
            start_time: new Date().toISOString(),
            end_time: new Date().toISOString(),
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
    const handleDelete = async (event_id: string, event_name: string) => {
        if (window.confirm(`Are you sure you want to delete "${event_name}"?`)) {
            try {
                await deleteTripEvent(event_id);
            } catch (err: any) {
                alert(err?.message ?? "Failed to delete event");
            }
        }
    };

    const form = useForm<CreateTripEventInput>({
        resolver: zodResolver(eventInput),
        defaultValues: {
            ...DEFAULT_FORM_STATE,
            location_coords: [0, 0],
            start_time: new Date().toISOString(),
            end_time: new Date().toISOString(),
        },
    });


    if (tripLoading) return <div className="p-6">Loading...</div>;
    if (!tripData) return <div className="p-6">Trip not found</div>;

    const { trip_name, start_time, end_time, organizers, guests, events } = tripData;

    const onOpenDialog = (eventToEdit?: any) => {
        if (eventToEdit) {
            setEditingEventId(eventToEdit.event_id);
            form.reset({
                event_name: eventToEdit.event_name,
                event_description: eventToEdit.event_description || '',
                event_type: eventToEdit.event_type,
                location_name: eventToEdit.location?.name || '',
                location_type: eventToEdit.location?.location_type || 'other',
                location_coords: eventToEdit.location?.gps_position || [0, 0],
                start_time: eventToEdit.start_time,
                end_time: eventToEdit.end_time,
                image_urls: eventToEdit.image_urls || [],
            });
        } else {
            setEditingEventId(null);
            form.reset({
                ...DEFAULT_FORM_STATE,
                location_coords: [0, 0],
                start_time: new Date().toISOString(),
                end_time: new Date().toISOString(),
            });
        }
        setEventOpen(true);
    };

    const onSubmitEvent = async (values: CreateTripEventInput) => {
        try {
            if (editingEventId) {
                // Use the update mutation (passing the ID if your API expects it in the body)
                console.log('Updating event with ID:', editingEventId, 'Values:', values);
                await updateTripEvent({ ...values, event_id: editingEventId } as any);
            } else {
                await createTripEvent(values);
            }
            setEventOpen(false);
            form.reset();
        } catch (err: any) {
            form.setError("root", { message: err?.message ?? "Failed to save event" });
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

                <Tabs defaultValue='events' onValueChange={() => { setEventOpen(false); setInviteOpen(false); }}>
                    <TabsList>
                        <TabsTrigger value='events'>Events</TabsTrigger>
                        <TabsTrigger value='people'>People</TabsTrigger>
                        {userData && tripData.organizers.includes(userData.user_id) && <TabsTrigger value='invitations'>Invitations</TabsTrigger>}
                    </TabsList>
                    <TabsContent value='events'>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle>Events</CardTitle>
                                <Dialog open={eventOpen} onOpenChange={setEventOpen}>
                                    <Button onClick={() => onOpenDialog()}>Add Event</Button>
                                    <DialogContent className="max-w-md overflow-y-auto max-h-[90vh]">
                                        <DialogHeader>
                                            <DialogTitle>{editingEventId ? 'Edit Event' : 'Create Event'}</DialogTitle>
                                        </DialogHeader>
                                        <form id="event-form" onSubmit={form.handleSubmit(onSubmitEvent)} className="space-y-4">
                                            <FieldGroup>
                                                <Controller name="event_name" control={form.control} render={({ field, fieldState }) => (
                                                    <Field data-invalid={fieldState.invalid}>
                                                        <FieldLabel>Event Name</FieldLabel>
                                                        <Input {...field} placeholder="Plane" />
                                                        {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
                                                    </Field>
                                                )} />
                                                <Controller name="event_description" control={form.control} render={({ field, fieldState }) => (
                                                    <Field data-invalid={fieldState.invalid}>
                                                        <FieldLabel>Description</FieldLabel>
                                                        <Input {...field} placeholder="Flight to Paris" />
                                                    </Field>
                                                )} />
                                                <Controller name="location_name" control={form.control} render={({ field, fieldState }) => (
                                                    <Field data-invalid={fieldState.invalid}>
                                                        <FieldLabel>Location Name</FieldLabel>
                                                        <Input {...field} placeholder="CDG Airport" />
                                                    </Field>
                                                )} />
                                                <Controller name="location_coords" control={form.control} render={({ field, fieldState }) => (
                                                    <Field data-invalid={fieldState.invalid}>
                                                        <FieldLabel>Coordinates (Lat, Lng)</FieldLabel>
                                                        <div className="flex gap-2">
                                                            <Input type="number" step="any" placeholder="Lat" value={field.value[0]}
                                                                onChange={e => field.onChange([Number(e.target.value), field.value[1]])} />
                                                            <Input type="number" step="any" placeholder="Lng" value={field.value[1]}
                                                                onChange={e => field.onChange([field.value[0], Number(e.target.value)])} />
                                                        </div>
                                                    </Field>
                                                )} />
                                                <Controller name="start_time" control={form.control} render={({ field, fieldState }) => (
                                                    <Field data-invalid={fieldState.invalid}>
                                                        <FieldLabel>Start Time</FieldLabel>
                                                        <Input type="datetime-local"
                                                            value={toLocalISO(field.value)}
                                                            onChange={e => field.onChange(new Date(e.target.value).toISOString())} />
                                                    </Field>
                                                )} />
                                                <Controller name="end_time" control={form.control} render={({ field, fieldState }) => (
                                                    <Field data-invalid={fieldState.invalid}>
                                                        <FieldLabel>End Time</FieldLabel>
                                                        <Input type="datetime-local"
                                                            value={toLocalISO(field.value)}
                                                            onChange={e => field.onChange(new Date(e.target.value).toISOString())} />
                                                    </Field>
                                                )} />

                                                <Field>
                                                    <FieldLabel>Attachments (Tickets/Photos)</FieldLabel>
                                                    <div className="space-y-2">
                                                        {/* Hidden actual file input */}
                                                        <Input
                                                            type="file"
                                                            accept="image/*"
                                                            className="cursor-pointer"
                                                            onChange={async (e) => {
                                                                const file = e.target.files?.[0];
                                                                if (!file) return;

                                                                try {
                                                                    const url = await uploadFile(file);
                                                                    // Add the new URL to the existing list
                                                                    const currentUrls = form.getValues('image_urls') || [];
                                                                    form.setValue('image_urls', [...currentUrls, url]);
                                                                } catch (err) {
                                                                    alert("Upload failed");
                                                                }
                                                            }}
                                                        />

                                                        {/* Preview Gallery */}
                                                        <div className="flex flex-wrap gap-2 mt-2">
                                                            {form.watch('image_urls')?.map((url, index) => (
                                                                <div key={index} className="relative w-20 h-20 border rounded-md overflow-hidden group">
                                                                    <img src={url} className="object-cover w-full h-full" alt="attachment" />
                                                                    <button
                                                                        type="button"
                                                                        className="absolute top-0 right-0 bg-destructive text-white p-0.5 opacity-0 group-hover:opacity-100"
                                                                        onClick={() => {
                                                                            const current = form.getValues('image_urls');
                                                                            form.setValue('image_urls', current.filter((_, i) => i !== index));
                                                                        }}
                                                                    >
                                                                        <Trash2 className="h-3 w-3" />
                                                                    </button>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </Field>
                                            </FieldGroup>
                                        </form>
                                        <DialogFooter>
                                            <Button type="submit" form="event-form">
                                                {editingEventId ? 'Update Event' : 'Create Event'}
                                            </Button>
                                        </DialogFooter>
                                    </DialogContent>
                                </Dialog>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {events.length === 0 ? <p className="text-muted-foreground">No events yet</p> :
                                    events.map((event) => (
                                        <div key={event.event_id} className="border p-3 rounded-xl flex justify-between items-start">
                                            <div className="space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <h3 className="font-semibold">{event.event_name}</h3>
                                                    <Badge variant="outline">{event.event_type}</Badge>
                                                </div>
                                                <p className="text-sm text-muted-foreground">
                                                    {new Date(event.start_time).toLocaleString()} <ArrowRight className="inline mx-1 h-3 w-3" /> {new Date(event.end_time).toLocaleString()}
                                                </p>
                                                {event.location && (
                                                    <p className="text-sm text-muted-foreground"><MapPin className="inline h-3 w-3" /> {event.location.name}</p>
                                                )}
                                                {/* Inside the event card loop */}
                                                {event.image_urls && event.image_urls.length > 0 && (
                                                    <div className="mt-4 flex gap-2 overflow-x-auto pb-2">
                                                        {event.image_urls.map((url, i) => (
                                                            <a
                                                                href={url}
                                                                target="_blank"
                                                                rel="noreferrer"
                                                                key={i}
                                                                className="block flex-shrink-0"
                                                            >
                                                                <img
                                                                    src={url}
                                                                    className="h-24 w-32 object-cover rounded-lg border hover:opacity-80 transition"
                                                                    alt="Ticket/Attachment"
                                                                />
                                                            </a>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex gap-1">
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => onOpenDialog(event)}
                                                >
                                                    <Edit2 className="h-4 w-4" />
                                                </Button>

                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                                    onClick={() => handleDelete(event.event_id, event.event_name)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
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
                                        : organizers.map((user) => <Badge key={user} variant="secondary" className="mr-2">{userNames?.user_names[user] || user}</Badge>)}
                                </div>

                                <div>
                                    <h3 className="font-semibold mb-1">Guests</h3>
                                    {guests.length === 0 ?
                                        <p className="text-sm text-muted-foreground">None</p>
                                        : guests.map((user) => <Badge key={user} variant="outline" className="mr-2">{userNames?.user_names[user] || user}</Badge>)}
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
                                                                <Button variant="ghost" onClick={() => { navigator.clipboard.writeText(displayInviteLink) }}>
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
                                                                        <Button variant="ghost" onClick={() => { navigator.clipboard.writeText(invitationLink(invitation.invitation_id)) }}>
                                                                            <CopyIcon />
                                                                        </Button>
                                                                    </TooltipTrigger>
                                                                    <TooltipContent>Copy invite link</TooltipContent>
                                                                </Tooltip>
                                                            }
                                                            <Button variant="ghost" onClick={() => deleteInvitation({ invitationId: invitation.invitation_id })}>
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

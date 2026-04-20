import * as z from 'zod';

export const datetime = z.string().datetime();

export const userSchema = z.object({
	user_id: z.string(),
	display_name: z.string(),
	phone_number: z.string(),
});

export const attachmentEnum = z.enum(['pdf', 'image', 'other']);
export const eventTypeEnum = z.enum([
	'attraction',
	'food',
	'lodging',
	'transportation',
	'other',
]);
export const expenseEnum = z.enum([
	'attraction',
	'food',
	'lodging',
	'shopping',
	'transportation',
	'other',
]);

export const bookingSummaryItemSchema = z.object({
	booking_id: z.string(),
	trip_id: z.string(),
	user_id: z.string(),
	reference_number: z.string(),
	customer_service_number: z.string(),
	provider_name: z.string(),
});

export const eventAttachmentSchema = z.object({
	attachment_id: z.string(),
	event_id: z.string(),
	title: z.string(),
	description: z.string().optional().nullable(),
	uri: z.string(),
});

export const eventLocationSchema = z.object({
	name: z.string(),
	location_type: eventTypeEnum,
	gps_position: z.tuple([z.number(), z.number()]), // [latitude, longitude]
});

export const tripEventSchema = z.object({
	event_id: z.string(),
	event_name: z.string(),
	event_type: eventTypeEnum,
	event_description: z.string().optional().nullable(),
	location: eventLocationSchema,
	end_location: eventLocationSchema.optional().nullable(),
	start_time: datetime,
	end_time: datetime,
	attachments: z.array(eventAttachmentSchema),
});

export const tripSchema = z.object({
	trip_id: z.string(),
	trip_name: z.string(),
	start_time: z.string(),
	end_time: z.string(),
	organizers: z.array(z.string()),
	guests: z.array(z.string()),
	events: z.array(tripEventSchema),
});

export const tripSummarySchema = z.object({
	trip_name: z.string(), 
	start_time: z.string(), // ISO date string
	end_time: z.string(), // ISO date string
})

export const expenseSchema = z.object({
	trip_id: z.string(),
	user_id: z.string(),
	amount: z.number(),
	description: z.string().optional(),
	category: expenseEnum,
	time_added: datetime,
	split_among: z.record(z.string(), z.number()), // user_id to amount mapping
});

export const commentSchema = z.object({
	comment_id: z.string(),
	trip_id: z.string(),
	user_id: z.string(),
	content: z.string(),
	timestamp: datetime,
});

export const invitationSchema = z.object({
	invitation_id: z.string(), 
	trip_id: z.string(), 
	inviter_id: z.string(), 
	is_organizer: z.boolean(), 
	limit_uses: z.number(), 
	expiry_time: z.string() // ISO date string
})

export const invitationSummarySchema = z.object({
	trip_id: z.string(), 
	trip_name: z.string(), 
	trip_start: z.string(), 
	trip_end: z.string(), 
	inviter: z.string(), 
	inviter_name: z.string(), 
	is_organizer: z.boolean(), 
	expiry_time: z.string()
})

export type EventType = z.infer<typeof eventTypeEnum>;
export type ExpenseType = z.infer<typeof expenseEnum>;
export type AttachmentType = z.infer<typeof attachmentEnum>;

export type User = z.infer<typeof userSchema>;
export type BookingSummaryItem = z.infer<typeof bookingSummaryItemSchema>;
export type EventAttachment = z.infer<typeof eventAttachmentSchema>;
export type EventLocation = z.infer<typeof eventLocationSchema>;
export type TripEvent = z.infer<typeof tripEventSchema>;
export type Trip = z.infer<typeof tripSchema>;
export type TripSummary = z.infer<typeof tripSchema>;
export type Expense = z.infer<typeof expenseSchema>;
export type Comment = z.infer<typeof commentSchema>;
export type Invitation = z.infer<typeof invitationSchema>;

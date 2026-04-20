import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import z from 'zod';
import { useAuthFetch, get } from './fetch';
import { eventTypeEnum, tripSchema, tripSummarySchema, type Trip } from './model';


export function useTrips() {
	const { get } = useAuthFetch();
	return useQuery({
		queryKey: ["trips"],
		queryFn: async () => {
			const response = await get("/api/user/trips");
			if (!response.ok) {
				throw new Error(`Error fetching trips: ${response.statusText}`);
			}
			const data = await response.json();
			console.log("Fetched trips data:", data);
			return z.array(tripSchema).parse(data.trips);
		},
	});
}


export function useTrip(tripId?: string) {
	const { get } = useAuthFetch();

	return useQuery({
		queryKey: ['trip', tripId],
		queryFn: async () => {
			const response = await get(
				!tripId ? '/api/user/trips' : `/api/trips/${tripId}`,
			);
			if (!response.ok) {
				throw new Error(`Error fetching trip details: ${response.statusText}`);
			}
			return tripSchema.parse(await response.json());
		},
	});
}

export function useTripSummary(tripId?: string) {
	return useQuery({
		queryKey: ['trip', tripId],
		queryFn: async () => {
			if (!tripId) throw new Error(`No trip to retrieve!`);
			const response = await get(
				`/api/trips/${tripId}/summary`,
			);
			if (!response.ok) {
				throw new Error(`Error fetching trip details: ${response.statusText}`);
			}
			return tripSummarySchema.parse(await response.json());
		},
	});
}

export function useMutateTrip() {
	const { post } = useAuthFetch();
	const client = useQueryClient();
	return useMutation({
		mutationFn: async (updatedTrip: Partial<Trip>) => {
			const response = await post(`/api/trips`, {
				body: JSON.stringify(updatedTrip),
			});
			if (!response.ok) {
				throw new Error(`Error updating trip: ${response.statusText}`);
			}
			const [trip] = await Promise.allSettled([
				response.json(),
				client.invalidateQueries({ queryKey: ['trips'] }),
			]);
			if (trip.status === 'rejected') {
				throw new Error(
					`Error parsing trip response: ${trip.reason instanceof Error ? trip.reason.message : 'Unknown error'}`,
				);
			}
			return tripSchema.parse(trip.value);
		},
	});
}

export const createEventInput = z.object({
	event_name: z.string(),
	event_type: eventTypeEnum,
	event_description: z.string().optional(),
	location_name: z.string(),
	location_type: eventTypeEnum,
	location_coords: z.tuple([
		z.number().min(-90).max(90), // latitude
		z.number().min(-180).max(180), // longitude
	]), // [latitude, longitude]
	start_time: z.string().datetime(),
	end_time: z.string().datetime(),
});


export type CreateTripEventInput = z.infer<typeof createEventInput>;
export function useCreateTripEvent({ trip_id }: { trip_id?: string }) {
	const { post } = useAuthFetch();
	const client = useQueryClient();
	return useMutation({
		mutationFn: async (data: CreateTripEventInput) => {
			if (!trip_id) {
				throw new Error('Trip ID is required to create an event');
			}
			const response = await post(`/api/trips/${trip_id}/event`, {
				body: JSON.stringify(data),
			});
			if (!response.ok) {
				throw new Error(`Error creating trip event: ${response.statusText}`);
			}
			const [trip] = await Promise.allSettled([
				response.json(),
				client.invalidateQueries({ queryKey: ['trip'] }),
			]);
			if (trip.status === 'rejected') {
				throw new Error(
					`Error parsing trip response: ${trip.reason instanceof Error ? trip.reason.message : 'Unknown error'}`,
				);
			}
			return tripSchema.parse(trip.value);
		},
	});
}

export const updateEventInput = z.object({
	event_name: z.string(),
	event_type: eventTypeEnum,
	event_description: z.string().optional(),
	start_time: z.date(),
	end_time: z.date(),
});

export type UpdateEventInput = z.infer<typeof updateEventInput>;

export function useMutateTripEvent({ trip_id }: { trip_id?: string }) {
	const { put } = useAuthFetch();
	const client = useQueryClient();
	return useMutation({
		mutationFn: async (data: UpdateEventInput) => {
			if (!trip_id) {
				throw new Error('Trip ID is required to update an event');
			}
			const response = await put(`/api/trips/${trip_id}/event`, {
				body: JSON.stringify(data),
			});
			if (!response.ok) {
				throw new Error(`Error updating trip event: ${response.statusText}`);
			}
			const [trip] = await Promise.allSettled([
				response.json(),
				client.invalidateQueries({ queryKey: ['trip'] }),
			]);
			if (trip.status === 'rejected') {
				throw new Error(
					`Error parsing trip response: ${trip.reason instanceof Error ? trip.reason.message : 'Unknown error'}`,
				);
			}
			return tripSchema.parse(trip.value);
		},
	});
}

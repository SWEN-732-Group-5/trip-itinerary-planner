import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import z from 'zod';
import { useAuthFetch } from './fetch';
import { eventTypeEnum, tripSchema, type Trip } from './model';

export function useTrip(tripId?: string) {
	const { get } = useAuthFetch();
	return useQuery({
		queryKey: ['trip', tripId],
		queryFn: async () => {
			const response = await get(
				!tripId ? `/api/trips` : `/api/trips/${tripId}`,
			);
			if (!response.ok) {
				throw new Error(`Error fetching trip details: ${response.statusText}`);
			}
			return tripSchema.parse(await response.json());
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
			if (updatedTrip.trip_id) {
				await client.invalidateQueries({
					queryKey: ['trip', updatedTrip.trip_id],
				});
				await client.invalidateQueries({
					queryKey: ['trip', updatedTrip.trip_id],
				});
			}
			return tripSchema.parse(await response.json());
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
		z.string().transform(z.coerce.number),
		z.string().transform(z.coerce.number),
	]), // [latitude, longitude]
	start_time: z.date(),
	end_time: z.date(),
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
			await client.invalidateQueries({
				queryKey: ['trip', trip_id],
			});
			return tripSchema.parse(await response.json());
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
			await client.invalidateQueries({
				queryKey: ['trip', trip_id],
			});
			return tripSchema.parse(await response.json());
		},
	});
}

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

export const eventInput = z.object({
	event_name: z.string(),
	event_type: eventTypeEnum,
	event_description: z.string().optional(),
	location_name: z.string(),
	location_type: eventTypeEnum,
	location_coords: z.preprocess(
		(value) => {
			if (!Array.isArray(value) || value.length < 2) {
				return undefined;
			}

			const latRaw = String(value[0] ?? '').trim();
			const lngRaw = String(value[1] ?? '').trim();

			if (!latRaw && !lngRaw) {
				return undefined;
			}

			return [Number(latRaw), Number(lngRaw)];
		},
		z
			.tuple([
				z.number().min(-90).max(90), // latitude
				z.number().min(-180).max(180), // longitude
			])
			.optional(),
	), // [latitude, longitude]
	start_time: z.string().datetime(),
	end_time: z.string().datetime(),
	image_urls: z.array(z.string()).default([]),
});


export type CreateTripEventInput = z.infer<typeof eventInput>;
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

export type UpdateEventInput = z.infer<typeof eventInput>;

export function useMutateTripEvent({ trip_id }: { trip_id?: string }) {
	const { put } = useAuthFetch();
	const client = useQueryClient();
	return useMutation({
		mutationFn: async (data: UpdateEventInput & { event_id?: string }) => {
			if (!trip_id || !data.event_id) {
				throw new Error('Trip ID is required to update an event');
			}
			const response = await put(`/api/trips/${trip_id}/event/${data.event_id}`, {
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

export function useDeleteTripEvent({ trip_id }: { trip_id?: string }) {
	const { del } = useAuthFetch();
	const client = useQueryClient();

	return useMutation({
		mutationFn: async (event_id: string) => {
			if (!trip_id) throw new Error('Trip ID required');

			const response = await del(`/api/trips/${trip_id}/event/${event_id}`);

			if (!response.ok) {
				throw new Error(`Error deleting event: ${response.statusText}`);
			}

			// Invalidate the trip query to refresh the list
			await client.invalidateQueries({ queryKey: ['trip', trip_id] });
			return response.json();
		},
	});
}

export function useUploadFile() {
	const { postFormData } = useAuthFetch();

	const uploadFile = async (file: File): Promise<string> => {
		const formData = new FormData();
		formData.append('file', file);

		// Note: When sending FormData, most fetch wrappers (like useAuthFetch) 
		// should NOT have a 'Content-Type' header set manually, 
		// as the browser needs to set the boundary.
		const response = await postFormData('/api/file/upload', formData);

		if (!response.ok) {
			throw new Error("Failed to upload image to MinIO");
		}

		const data = await response.json();
		// Return the URL from your backend response
		return data.url;
	};

	return { uploadFile };
}

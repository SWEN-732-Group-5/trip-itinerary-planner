import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { useAuthFetch } from './fetch';
import { userNamesSchema } from "./model";

const selfSchema = z.object({
	display_name: z.string(),
	phone_number: z.string(),
});

export type SelfProfile = z.infer<typeof selfSchema>;
export const updateSelfInput = z.object({
	display_name: z.string().min(1, 'Display name is required'),
	phone_number: z.string().min(1, 'Phone number is required'),
});

export type UpdateSelfInput = z.infer<typeof updateSelfInput>;

export function useSelf(enabled = true) {
	const { get } = useAuthFetch();
	return useQuery({
		queryKey: ['self-profile'],
		enabled,
		queryFn: async () => {
			const response = await get('/api/user/self');
			if (!response.ok) {
				throw new Error(`Error fetching account profile: ${response.statusText}`);
			}
			return selfSchema.parse(await response.json());
		},
	});
}

export function useUpdateSelf() {
	const { put } = useAuthFetch();
	const client = useQueryClient();
	return useMutation({
		mutationFn: async (payload: UpdateSelfInput) => {
			const response = await put('/api/user', {
				body: JSON.stringify(payload),
			});
			if (!response.ok) {
				throw new Error(`Error updating profile: ${response.statusText}`);
			}
			const data = await response.json();
			return selfSchema.parse(data);
		},
		onSuccess: async () => {
			await client.invalidateQueries({ queryKey: ['self-profile'] });
		},

	});
}

export function useUserNames(users: string[], enabled: boolean = true) {
	const { get } = useAuthFetch();

	return useQuery({
		queryKey: ['user', users],
		queryFn: async () => {
			const response = await get(
				`/api/user/names?ids=${users.join(',')}`,
			);
			if (!response.ok) {
				throw new Error(`Error fetching user names: ${response.statusText}`);
			}
			return userNamesSchema.parse(await response.json());
		},
		enabled: enabled && users.length > 0,
	});
}

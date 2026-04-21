import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import z from 'zod';
import { get, useAuthFetch } from './fetch';
import { invitationSchema, invitationSummarySchema } from './model';

export function useInvitationSummary(invitationId?: string) {
    return useQuery({
		queryKey: ['invitation', invitationId],
		queryFn: async () => {
            if (!invitationId) throw new Error("No invitation to retrieve");
			const response = await get(`/api/trips/invitation/${invitationId}`,
			);
			if (!response.ok) {
				throw new Error(`Error fetching invitation: ${response.statusText}`);
			}
			return invitationSummarySchema.parse(await response.json());
		},
	});
}

export function useTripInvitations(tripId?: string) {
    const { get } = useAuthFetch();
    return useQuery({
		queryKey: ['tripInvitations', tripId],
		queryFn: async () => {
            if (!tripId) throw new Error("No trip to retrieve invitations for");
			const response = await get(`/api/trips/${tripId}/invitations`,
			);
			if (!response.ok) {
				throw new Error(`Error fetching invitation: ${response.statusText}`);
			}
            const data = await response.json();
            console.log("Fetched invitations: " + data)
			return z.array(invitationSchema).parse(data);
		},
	});
}

export const createInvitationInput = z.object({
    limit_uses: z.coerce.number().min(1), 
    is_organizer: z.boolean(), 
    expiry_time: z.string().datetime(),
});

export type CreateInvitationInput = z.infer<typeof createInvitationInput>;
export function useCreateInvitation({ tripId }: { tripId?: string }) {
    const { post } = useAuthFetch();
    const client = useQueryClient();
    return useMutation({
        mutationFn: async (inviteData: CreateInvitationInput) => {
            const response = await post(`/api/trips/${tripId}/invite`, {
                body: JSON.stringify({
                    limit_uses: inviteData.limit_uses, 
                    is_organizer: inviteData.is_organizer, 
                    expiry_time: inviteData.expiry_time
                }),
            });
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Invitation creation error response:', errorText);
                throw new Error(`Failed to create invitation: ${response.statusText}`);
            }
            const jsonData = await response.json();
            await client.invalidateQueries({ queryKey: ['tripInvitations', tripId] });
            console.log('Invitation created successfully:', jsonData);
            return invitationSchema.parse(jsonData);
        },
    });
}

export function useDeleteInvitation({ tripId }: { tripId?: string }) {
    const { del } = useAuthFetch();
    const client = useQueryClient();
    return useMutation({
        mutationFn: async ({ invitationId }: { invitationId?: string }) => {
            const response = await del(`/api/trips/${tripId}/invite/${invitationId}`);
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Invitation deletion error response:', errorText);
                throw new Error(`Failed to delete invitation: ${response.statusText}`);
            }
            await client.invalidateQueries({ queryKey: ['tripInvitations', tripId] });
            return
        },
    });
}

export function useAcceptInvitation() {
	const { put } = useAuthFetch();
    return useMutation({
        mutationFn: async (invitation_id: string | undefined ) => {
            const response = await put(`/api/trips/invitation/${invitation_id}/accept`, {});
            const accepted = await response.json();
            console.log(accepted)
            if (!response.ok) {
                throw new Error(`Error: ${accepted.detail}`);
            }
            if (accepted.status === 'rejected') {
                throw new Error(
                    `Error: ${accepted.reason instanceof Error ? accepted.detail : 'Unknown error'}`,
                );
            }
            return accepted;
        },
    });
}

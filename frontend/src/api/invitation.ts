import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
// import z from 'zod';
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

export function useCreateInvitation() {
    const { post } = useAuthFetch();
    const client = useQueryClient();
    return useMutation({
        mutationFn: async (inviteData: {
            trip_id: string
            limit_uses: number;
            is_organizer: boolean;
            expiry_time: Date;
        }) => {
            const response = await post(`/api/trips/${inviteData.trip_id}/invite`, {
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
            await client.invalidateQueries({ queryKey: ['invitations'] });
            console.log('Invitation created successfully:', jsonData);
            return invitationSchema.parse(jsonData);
        },
    });
}

export function useAcceptInvitation() {
	const { put } = useAuthFetch();
    return useMutation({
        mutationFn: async (invitation_id: string | undefined ) => {
            const response = await put(`/api/trips/invitation/${invitation_id}/accept`, {});
            if (!response.ok) {
                throw new Error(`Error accepting invitation: ${response.statusText}`);
            }
            const accepted = await response.json();
            if (accepted.status === 'rejected') {
                throw new Error(
                    `Error parsing trip response: ${accepted.reason instanceof Error ? accepted.reason.message : 'Unknown error'}`,
                );
            }
            return accepted;
        },
    });
}

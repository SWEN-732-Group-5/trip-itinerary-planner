import { useQuery } from "@tanstack/react-query";
import { userNamesSchema } from "./model";
import { useAuthFetch } from "./fetch";

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

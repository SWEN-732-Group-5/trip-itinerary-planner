import { post } from '@/api/fetch';
import { useMutation } from '@tanstack/react-query';
import { createContext, useContext } from 'react';
import z from 'zod';

export interface SessionContextType {
	session_token?: string;
	setSession: (session?: string) => void;
}

export const SessionContext = createContext<SessionContextType | undefined>(
	undefined,
);

const userAuthResponse = z.object({
	session_token: z.string(),
});

export const useLogin = () => {
	return useMutation({
		mutationFn: async (cred: { user_id: string; password: string }) => {
			const response = await post('/api/auth', {
				body: JSON.stringify(cred),
			});
			if (!response.ok) {
				throw new Error(`Login failed: ${response.statusText}`);
			}
			return userAuthResponse.parse(await response.json());
		},
	});
};

export const createUserInput = z.object({
	user_id: z.string(),
	password: z.string(),
	display_name: z.string(),
	phone_number: z.string(),
});
export type CreateUserInput = z.infer<typeof createUserInput>;
export const useSignup = () => {
	return useMutation({
		mutationFn: async (cred: CreateUserInput) => {
			const response = await post('/api/user', {
				body: JSON.stringify(cred),
			});
			if (!response.ok) {
				throw new Error(`Signup failed: ${response.statusText}`);
			}
			return response.json();
		},
	});
};
export type SessionActions = {
	login: (cred: { user_id: string; password: string }) => void;
	logout: () => void;
	signup: (cred: CreateUserInput) => void;
};
export type SessionContext = {
	session_token?: string;
	isLoggedIn: boolean;
	action: SessionActions;
};

export const useSession = (): SessionContext => {
	const context = useContext(SessionContext);
	const { mutateAsync: login } = useLogin();
	const { mutateAsync: signup } = useSignup();
	if (!context) {
		throw new Error('useSession must be used within SessionProvider');
	}
	const { session_token, setSession } = context;
	const isLoggedIn = session_token != null;

	return {
		session_token,
		isLoggedIn,
		action: {
			logout: () => setSession(),
			login: async (cred: { user_id: string; password: string }) =>
				setSession((await login(cred)).session_token),
			signup: async (cred: CreateUserInput) => {
				console.log(cred);

				await signup(cred);
				setSession((await login(cred)).session_token);
			},
		},
	};
};

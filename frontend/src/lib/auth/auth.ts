import { authPost, post, useAuthFetch } from '@/api/fetch';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createContext, useContext, useMemo, useRef } from 'react';
import z from 'zod';
import { useAtTime } from '../utils';

export type SessionObject = {
	session_token: string;
	expiry_time: Date;
};

export interface SessionContextType {
	session_token?: string;
	expiry_time?: Date;
	setSession: (session?: SessionObject | undefined) => void;
}

export const SessionContext = createContext<SessionContextType | undefined>(
	undefined,
);

const userAuthResponse = z.object({
	session_token: z.string(),
	expiry_time: z.string().pipe(z.coerce.date()),
});
type UserAuthResponse = z.output<typeof userAuthResponse>;

export const LOGIN_ERROR_MSG = {
	404: 'User not found',
	401: 'Invalid user ID or password',
	400: 'Bad request. Please check your input.',
	500: 'Unknown Error. Please try again later.',
	DEFAULT: 'Unknown Error. Please try again later.',
};

export const useLogin = () => {
	return useMutation({
		mutationFn: async (cred: {
			user_id: string;
			password: string;
		}): Promise<UserAuthResponse> => {
			const response = await post('/api/auth', {
				body: JSON.stringify(cred),
			});
			if (!response.ok) {
				const message =
					LOGIN_ERROR_MSG[response.status as keyof typeof LOGIN_ERROR_MSG] ||
					LOGIN_ERROR_MSG.DEFAULT;
				throw new Error(`Login failed: ${message}`);
			}
			return userAuthResponse.parse(await response.json());
		},
	});
};

export const SIGNUP_ERROR_MSG = {
	409: 'User ID already exists',
	400: 'Bad request. Please check your input.',
	500: 'Unknown Error. Please try again later.',
	DEFAULT: 'Unknown Error. Please try again later.',
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
				if (response.status === 400) {
					const text = await response.json();
					if (text.detail) {
						throw new Error(`Signup failed: ${text.detail}`);
					}
				}
				const message =
					SIGNUP_ERROR_MSG[response.status as keyof typeof SIGNUP_ERROR_MSG] ||
					SIGNUP_ERROR_MSG.DEFAULT;
				throw new Error(`Signup failed: ${message}`);
			}
			return response.json();
		},
	});
};
export const useRenewSession = (session: SessionContextType | undefined) => {
	const { setSession, expiry_time, session_token } = session ?? {};
	const lastRenewedExpiryRef = useRef<number | null>(null);
	const expiryTimeMs = expiry_time?.getTime();
	const renewAt = useMemo(
		() => (expiryTimeMs ? new Date(expiryTimeMs - 60 * 1000) : null),
		[expiryTimeMs],
	);
	const { mutateAsync } = useMutation({
		mutationFn: async () => {
			if (!session_token)
				throw new Error('No session token available for renewal');
			const response = await authPost('/api/auth/renew', session_token);
			if (!response.ok) throw new Error('Session renewal failed');
			return userAuthResponse.parse(await response.json());
		},
	});
	useAtTime(() => {
		const expiryMs = expiryTimeMs ?? null;
		if (expiryMs == null) return;
		if (lastRenewedExpiryRef.current === expiryMs) return;
		lastRenewedExpiryRef.current = expiryMs;

		mutateAsync()
			.then((newSession) => {
				setSession?.(newSession);
			})
			.catch((error) => {
				console.error('Failed to renew session:', error);
				lastRenewedExpiryRef.current = null;
				setSession?.();
			});
	}, renewAt);
};

export type SessionActions = {
	login: (cred: { user_id: string; password: string }) => void;
	logout: () => void;
	signup: (cred: CreateUserInput) => void;
};
export type SessionContextObject = {
	session_token?: string;
	isLoggedIn: boolean;
	action: SessionActions;
};

export const useSession = (): SessionContextObject => {
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
			login: async (cred: { user_id: string; password: string }) => {
				const session = await login(cred);
				setSession(session);
			},
			signup: async (cred: CreateUserInput) => {
				await signup(cred);
				setSession(await login(cred));
			},
		},
	};
};

export const userData = z.object({
	user_id: z.string(),
	display_name: z.string(),
	phone_number: z.string(),
});
export const useSelf = () => {
	const { get } = useAuthFetch();
	return useQuery({
		queryKey: ["self"],
		queryFn: async () => {
			const response = await get("/api/user/self");
			if (!response.ok) {
				throw new Error(`Error fetching own account: ${response.statusText}`);
			}
			const data = await response.json();
			console.log(data)
			return userData.parse(data);
		},
	});
}

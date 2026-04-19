import { useSession } from '@/lib/auth/auth';

type FetchPayload = Omit<NonNullable<Parameters<typeof fetch>[1]>, 'method'>;

export async function post(endpoint: string, payload: FetchPayload) {
	return fetch(endpoint, {
		method: 'POST',
		...payload,
		headers: { 'Content-Type': 'application/json', ...payload?.headers },
	});
}

export async function get(endpoint: string, payload?: FetchPayload) {
	return fetch(endpoint, {
		method: 'GET',
		...payload,
		headers: { 'Content-Type': 'application/json', ...payload?.headers },
	});
}

export async function put(endpoint: string, payload: FetchPayload) {
	return fetch(endpoint, {
		method: 'PUT',
		...payload,
		headers: { 'Content-Type': 'application/json', ...payload?.headers },
	});
}

export async function del(endpoint: string, payload?: FetchPayload) {
	return fetch(endpoint, {
		method: 'DELETE',
		...payload,
		headers: { 'Content-Type': 'application/json', ...payload?.headers },
	});
}

type SessionKey = string | undefined;

export async function authPost(
	endpoint: string,
	session: SessionKey,
	payload?: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return post(endpoint, {
		...payload,
		headers: {
			'session-token': session,
			...payload?.headers,
		},
	});
}

export async function authGet(
	endpoint: string,
	session: SessionKey,
	payload?: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return get(endpoint, {
		...payload,
		headers: {
			'session-token': session,
			...payload?.headers,
		},
	});
}

export async function authPut(
	endpoint: string,
	session: SessionKey,
	payload?: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return put(endpoint, {
		...payload,
		headers: {
			'session-token': session,
			...payload?.headers,
		},
	});
}

export async function authDel(
	endpoint: string,
	session: SessionKey,
	payload?: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return del(endpoint, {
		...payload,
		headers: {
			'session-token': session,
			...payload?.headers,
		},
	});
}

export function useAuthFetch() {
	const { session_token } = useSession();
	return {
		post: (endpoint: string, payload: FetchPayload) =>
			authPost(endpoint, session_token, payload),
		get: (endpoint: string, payload?: FetchPayload) =>
			authGet(endpoint, session_token, payload),
		put: (endpoint: string, payload: FetchPayload) =>
			authPut(endpoint, session_token, payload),
		del: (endpoint: string, payload?: FetchPayload) =>
			authDel(endpoint, session_token, payload),
	};
}

import { useSession } from '@/lib/auth/auth';

type FetchPayload = Omit<Parameters<typeof fetch>[1], 'method' | 'headers'>;

export async function post(endpoint: string, payload: FetchPayload) {
	return fetch(endpoint, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		...payload,
	});
}

export async function patch(endpoint: string, payload: FetchPayload) {
	return fetch(endpoint, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		...payload,
	});
}

export async function get(endpoint: string, payload?: FetchPayload) {
	return fetch(endpoint, {
		method: 'GET',
		headers: { 'Content-Type': 'application/json' },
		...payload,
	});
}

export async function put(endpoint: string, payload: FetchPayload) {
	return fetch(endpoint, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		...payload,
	});
}

export async function del(endpoint: string, payload?: FetchPayload) {
	return fetch(endpoint, {
		method: 'DELETE',
		headers: { 'Content-Type': 'application/json' },
		...payload,
	});
}

type SessionKey = string | undefined;

export async function authPost(
	endpoint: string,
	session: SessionKey,
	payload: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return fetch(endpoint, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${session}`,
		},
		...payload,
	});
}

export async function authPatch(
	endpoint: string,
	session: SessionKey,
	payload: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return fetch(endpoint, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${session}`,
		},
		...payload,
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
	return fetch(endpoint, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${session}`,
		},
		...payload,
	});
}

export async function authPut(
	endpoint: string,
	session: SessionKey,
	payload: FetchPayload,
) {
	if (!session) {
		throw new Error('No session available for authenticated request');
	}
	return fetch(endpoint, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${session}`,
		},
		...payload,
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
	return fetch(endpoint, {
		method: 'DELETE',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${session}`,
		},
		...payload,
	});
}

export function useAuthFetch() {
	const { session_token } = useSession();
	return {
		post: (endpoint: string, payload: FetchPayload) =>
			authPost(endpoint, session_token, payload),
		patch: (endpoint: string, payload: FetchPayload) =>
			authPatch(endpoint, session_token, payload),
		get: (endpoint: string, payload?: FetchPayload) =>
			authGet(endpoint, session_token, payload),
		put: (endpoint: string, payload: FetchPayload) =>
			authPut(endpoint, session_token, payload),
		del: (endpoint: string, payload?: FetchPayload) =>
			authDel(endpoint, session_token, payload),
	};
}

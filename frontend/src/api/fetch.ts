type FetchPayload = Omit<Parameters<typeof fetch>[1], 'method' | 'headers'>;

export async function post(endpoint: string, payload: FetchPayload) {
	return fetch(endpoint, {
		method: 'POST',
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

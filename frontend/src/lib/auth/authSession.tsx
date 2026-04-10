import { SessionContext, useSession } from '@/lib/auth/auth';
import { useLocalStorage } from 'usehooks-ts';

function SessionProvider({ children }: { children: React.ReactNode }) {
	const [session_token, setSession] = useLocalStorage<string | undefined>(
		'user_session',
		undefined,
	);

	return (
		<SessionContext.Provider value={{ session_token, setSession }}>
			{children}
		</SessionContext.Provider>
	);
}

export function LoggedIn({ children }: { children: React.ReactNode }) {
	const { isLoggedIn } = useSession();
	if (!isLoggedIn) {
		return null;
	}
	return <>{children}</>;
}

export function LoggedOut({ children }: { children: React.ReactNode }) {
	const { isLoggedIn } = useSession();
	if (isLoggedIn) {
		return null;
	}
	return <>{children}</>;
}

export function LogoutButton() {
	const {
		isLoggedIn,
		action: { logout },
	} = useSession();
	if (!isLoggedIn) {
		return null;
	}
	return (
		<button
			onClick={() => logout()}
			className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
		>
			Logout
		</button>
	);
}

export default SessionProvider;

import { Button } from '@/components/ui/button';
import {
	SessionContext,
	useSession,
	type SessionObject,
} from '@/lib/auth/auth';
import { useLocalStorage } from 'usehooks-ts';

function SessionProvider({ children }: { children: React.ReactNode }) {
	const [session, setSession] = useLocalStorage<SessionObject | undefined>(
		'user_session',
		undefined,
	);
	const session_token = session?.session_token;
	const expiry_time =
		session?.expiry_time && typeof session.expiry_time == 'string' ?
			new Date(session?.expiry_time)
		:	undefined;

	return (
		<SessionContext.Provider value={{ session_token, expiry_time, setSession }}>
			{children}
		</SessionContext.Provider>
	);
}

export function LoggedIn({ children }: { children: React.ReactNode }) {
	const { isLoggedIn } = useSession();
	if (!isLoggedIn) return null;
	return <>{children}</>;
}

export function LoggedOut({ children }: { children: React.ReactNode }) {
	const { isLoggedIn } = useSession();
	if (isLoggedIn) return null;
	return <>{children}</>;
}

export function LogoutButton() {
	const {
		isLoggedIn,
		action: { logout },
	} = useSession();
	if (!isLoggedIn) return null;
	return (
		<Button onClick={() => logout()} variant="destructive" size="lg">
			Logout
		</Button>
	);
}

export default SessionProvider;

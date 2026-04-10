import { Button } from '@/components/ui/button';
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

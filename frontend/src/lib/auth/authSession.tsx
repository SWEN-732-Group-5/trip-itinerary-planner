import { SessionContext } from '@/lib/auth/auth';
import { type ReactNode } from 'react';
import { useLocalStorage } from 'usehooks-ts';

export const SessionProvider: React.FC<{ children: ReactNode }> = ({
	children,
}) => {
	const [session_token, setSession] = useLocalStorage<string | undefined>(
		'user_session',
		undefined,
	);

	return (
		<SessionContext.Provider value={{ session_token, setSession }}>
			{children}
		</SessionContext.Provider>
	);
};

export default SessionProvider;

import { Button } from '@/components/ui/button';
import { UserTrips } from '@/components/user-trips';
import { LoggedIn, LoggedOut } from '@/lib/auth/authSession';
import { Link } from 'react-router';

export default function Home() {
	return (
		<div className="p-6">
			<h1 className="text-2xl font-bold">Welcome to Trip Itinerary Planner</h1>
			<p className="mt-4 text-muted-foreground">
				Plan your trips with ease and keep all your travel details in one place.
			</p>
			<LoggedOut>
				<div className="mt-6">
					<Button asChild size="lg">
						<Link to="/login">login</Link>
					</Button>
				</div>
			</LoggedOut>
			<LoggedIn>
				<UserTrips />
				<div className="mt-4 flex items-center gap-2"></div>
			</LoggedIn>
		</div>
	);
}

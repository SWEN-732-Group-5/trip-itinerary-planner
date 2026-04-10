import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LoggedIn, LoggedOut, LogoutButton } from '@/lib/auth/authSession';
import { Link, useNavigate } from 'react-router';

export default function Home() {
	const navigate = useNavigate();
	const navigateToTrip = (formData: FormData) => {
		const tripId = formData.get('id');
		if (!tripId) return;
		navigate(`/trips/${tripId}`);
	};
	return (
		<div className="p-6">
			<h1 className="text-2xl font-bold">Welcome to Trip Itinerary Planner</h1>
			<p className="mt-4 text-muted-foreground">
				Plan your trips with ease and keep all your travel details in one place.
			</p>
			<LoggedOut>
				<div className="mt-6">
					<Link to="/login">login</Link>
				</div>
			</LoggedOut>
			<LoggedIn>
				<div className="p-4 w-fit">
					<form action={navigateToTrip} className="flex flex-row gap-2">
						<Input placeholder="Trip ID" name="id" type="text" />
						<Button
							type="submit"
							className="peer-placeholder-shown:opacity-50 p-2 bg-blue-500 text-white rounded-md  peer-[:not(:placeholder-shown)]:hover:bg-blue-400 peer-[:not(:placeholder-shown)]:active:bg-blue-600"
						>
							Go to trip
						</Button>
					</form>
				</div>
				<LogoutButton />
			</LoggedIn>
		</div>
	);
}

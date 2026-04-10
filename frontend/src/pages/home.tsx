import { LoggedIn, LoggedOut, LogoutButton } from '@/lib/auth/authSession';
import { Link, useNavigate } from 'react-router';

export default function Home() {
	const navigate = useNavigate();
	const navigateToTrip = (formData: FormData) => {
		const tripId = formData.get('id');
		if (!tripId) {
			alert('Please enter a trip ID');
			return;
		}
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
					<form action={navigateToTrip}>
						<input
							name="id"
							type="text"
							className="text-lg border-2 rounded-md mr-4"
						/>
						<button type="submit">Go to trip</button>
					</form>
				</div>
				<LogoutButton />
			</LoggedIn>
		</div>
	);
}

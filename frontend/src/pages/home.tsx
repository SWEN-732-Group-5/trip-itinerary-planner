import { useSession } from '@/lib/auth/auth';
import { Link, useNavigate } from 'react-router';

export default function Home() {
	const { isLoggedIn } = useSession();
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
		<div className="p-6 bg-slate-800">
			<h1 className="text-2xl font-bold">Welcome to Trip Itinerary Planner</h1>
			<p className="mt-4 text-muted-foreground">
				Plan your trips with ease and keep all your travel details in one place.
			</p>
			{!isLoggedIn ?
				<div className="mt-6">
					<Link to="/login">login</Link>
				</div>
			:	<div className="bg-slate-600 p-4 w-fit">
					<form action={navigateToTrip}>
						<input
							name="id"
							type="text"
							className="text-lg border-2 border-white bg-blue-300 rounded-md mr-4"
						/>
						<button type="submit">Go to trip</button>
					</form>
				</div>
			}
		</div>
	);
}

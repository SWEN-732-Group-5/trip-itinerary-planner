import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogFooter,
	DialogTitle,
	DialogTrigger,
} from '@/components/ui/dialog';
import { LoggedIn, LoggedOut, LogoutButton } from '@/lib/auth/authSession';
import { Link, useNavigate } from 'react-router';
import { toast } from 'sonner';
import { useCreateTrip } from '@/api/trip';

export default function Home() {
	const navigate = useNavigate();
	const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
	const [tripName, setTripName] = useState('');
	const [startDate, setStartDate] = useState('');
	const [endDate, setEndDate] = useState('');
	const [isSubmitting, setIsSubmitting] = useState(false);

	const { mutateAsync: createTrip } = useCreateTrip();

	const navigateToTrip = (formData: FormData) => {
		const tripId = formData.get('id');
		if (!tripId) return;
		navigate(`/trips/${tripId}`);
	};

	const handleCreateTrip = async (e: React.FormEvent) => {
		e.preventDefault();

		if (!tripName.trim()) {
			toast.error('Please enter a trip name');
			return;
		}

		if (!startDate || !endDate) {
			toast.error('Please select both start and end dates');
			return;
		}

		const start = new Date(startDate);
		const end = new Date(endDate);

		if (start >= end) {
			toast.error('End date must be after start date');
			return;
		}

		setIsSubmitting(true);
		try {
			const tripData = {
				trip_name: tripName,
				start_time: start,
				end_time: end,
			};
			console.log('Creating trip with data:', tripData);
			const newTrip = await createTrip(tripData);

			toast.success('Trip created successfully!');
			setTripName('');
			setStartDate('');
			setEndDate('');
			setIsCreateDialogOpen(false);
			navigate(`/trips/${newTrip.trip_id}`);
		} catch (error) {
			console.error('Create trip error:', error);
			toast.error(
				error instanceof Error ? error.message : 'Failed to create trip'
			);
		} finally {
			setIsSubmitting(false);
		}
	};

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
				<div className="mt-6 space-y-4">
					<Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
						<DialogTrigger asChild>
							<Button size="lg">Create New Trip</Button>
						</DialogTrigger>
						<DialogContent>
							<DialogHeader>
								<DialogTitle>Create a New Trip</DialogTitle>
							</DialogHeader>
							<form onSubmit={handleCreateTrip} className="space-y-4">
								<div className="space-y-2">
									<Label htmlFor="trip-name">Trip Name</Label>
									<Input
										id="trip-name"
										placeholder="e.g., Summer Vacation 2026"
										value={tripName}
										onChange={(e) => setTripName(e.target.value)}
										disabled={isSubmitting}
									/>
								</div>
								<div className="space-y-2">
									<Label htmlFor="start-date">Start Date</Label>
									<Input
										id="start-date"
										type="datetime-local"
										value={startDate}
										onChange={(e) => setStartDate(e.target.value)}
										disabled={isSubmitting}
									/>
								</div>
								<div className="space-y-2">
									<Label htmlFor="end-date">End Date</Label>
									<Input
										id="end-date"
										type="datetime-local"
										value={endDate}
										onChange={(e) => setEndDate(e.target.value)}
										disabled={isSubmitting}
									/>
								</div>
								<DialogFooter>
									<Button
										type="button"
										variant="outline"
										onClick={() => setIsCreateDialogOpen(false)}
										disabled={isSubmitting}
									>
										Cancel
									</Button>
									<Button type="submit" disabled={isSubmitting}>
										{isSubmitting ? 'Creating...' : 'Create Trip'}
									</Button>
								</DialogFooter>
							</form>
						</DialogContent>
					</Dialog>

					<div className="p-4 w-fit border rounded-lg">
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
				</div>
				<LogoutButton />
			</LoggedIn>
		</div>
	);
}

import { useSelf, useUpdateSelf } from '@/api/user';
import { Button } from '@/components/ui/button';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { useSession } from '@/lib/auth/auth';
import { LogoutButton } from '@/lib/auth/authSession';
import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { toast } from 'sonner';

export default function Account() {
	const { isLoggedIn } = useSession();
	const { data, isLoading, isError, error } = useSelf(isLoggedIn);
	const { mutateAsync: updateSelf, isPending: isSaving } = useUpdateSelf();
	const [displayName, setDisplayName] = useState('');
	const [phoneNumber, setPhoneNumber] = useState('');

	useEffect(() => {
		if (!data) return;
		setDisplayName(data.display_name);
		setPhoneNumber(data.phone_number);
	}, [data]);

	const hasChanges =
		data != null &&
		(displayName.trim() !== data.display_name ||
			phoneNumber.trim() !== data.phone_number);

	const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
		event.preventDefault();
		if (!hasChanges || isSaving) return;
		if (!displayName.trim() || !phoneNumber.trim()) {
			toast.error('Display name and phone number are required.');
			return;
		}

		try {
			await updateSelf({
				display_name: displayName.trim(),
				phone_number: phoneNumber.trim(),
			});
			toast.success('Account updated.');
		} catch (updateError) {
			toast.error(
				updateError instanceof Error
					? updateError.message
					: 'Unable to update account.'
			);
		}
	};

	if (!isLoggedIn) {
		return (
			<div className="p-6">
				<Card>
					<CardHeader>
						<CardTitle>Account</CardTitle>
						<CardDescription>
							Log in to view your account details.
						</CardDescription>
					</CardHeader>
					<CardContent>
						<Button asChild>
							<Link to="/login">Go to Login</Link>
						</Button>
					</CardContent>
				</Card>
			</div>
		);
	}

	if (isLoading) {
		return (
			<div className="p-6 space-y-4">
				<Skeleton className="h-8 w-48" />
				<Skeleton className="h-20 w-full" />
			</div>
		);
	}

	if (isError) {
		return (
			<div className="p-6">
				<Card>
					<CardHeader>
						<CardTitle>Account</CardTitle>
						<CardDescription>
							{error instanceof Error
								? error.message
								: 'Unable to load account details.'}
						</CardDescription>
					</CardHeader>
				</Card>
			</div>
		);
	}

	return (
		<div className="p-6 flex justify-center">
            <div className="inline-block">
            <Card className="w-[400px]">
				<CardHeader>
					<CardTitle>Account</CardTitle>
					<CardDescription>View and update your profile details</CardDescription>
				</CardHeader>
				<CardContent>
					<form className="space-y-4" onSubmit={onSubmit}>
						<div>
							<p className="mb-1 text- text-muted-foreground">Display Name</p>
							<Input
								value={displayName}
								onChange={(e) => setDisplayName(e.target.value)}
								placeholder="Display Name"
								autoComplete="name"
								required
							/>
						</div>
						<div>
							<p className="mb-1 text-sm text-muted-foreground">Phone Number</p>
							<Input
								value={phoneNumber}
								onChange={(e) => setPhoneNumber(e.target.value)}
								placeholder="Phone Number"
								autoComplete="tel"
								required
							/>
						</div>
						<Button type="submit" disabled={!hasChanges || isSaving}>
							{isSaving ? 'Saving...' : 'Save Changes'}
						</Button>
					</form>
				</CardContent>
			</Card>
            <div className="flex justify-center pt-6">
            <LogoutButton/>
            </div>
            </div>
		</div>
	);
}

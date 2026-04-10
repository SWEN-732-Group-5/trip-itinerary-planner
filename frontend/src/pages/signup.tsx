import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { SIGNUP_ERROR_MSG, useSession } from '@/lib/auth/auth';
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router';
import { toast } from 'sonner';

export default function Signup() {
	const {
		isLoggedIn,
		action: { signup },
	} = useSession();
	const navigate = useNavigate();

	const handleSubmit = async (form: FormData) => {
		const user_id = form.get('user_id');
		const password = form.get('password');
		const display_name = form.get('display_name');
		const phone_number = form.get('phone_number');
		if (
			typeof user_id !== 'string' ||
			typeof password !== 'string' ||
			typeof display_name !== 'string' ||
			typeof phone_number !== 'string'
		) {
			return;
		}
		toast.promise(
			async () => signup({ user_id, password, display_name, phone_number }),
			{
				loading: 'Creating account...',
				success: () => {
					navigate('/');
					return 'Success!';
				},
				error: (err) =>
					`${err instanceof Error ? err.message : SIGNUP_ERROR_MSG.DEFAULT}`,
			},
		);
	};
	useEffect(() => {
		if (isLoggedIn) {
			navigate('/');
		}
	}, [isLoggedIn, navigate]);

	return (
		<div className="w-full grow flex justify-center items-center">
			<div className="p-6 pb-3 w-100 border-2 rounded-2xl">
				<h1 className="text-2xl font-bold mb-4">Create a new account</h1>
				<form
					onSubmit={(e) => {
						e.preventDefault();
						const formData = new FormData(e.currentTarget);
						handleSubmit(formData);
					}}
					className="space-y-4"
				>
					<label
						htmlFor="user_id"
						className="block text-sm font-medium opacity-80 mb-0"
					>
						Username
					</label>
					<Input
						type="text"
						name="user_id"
						id="user_id"
						placeholder="Username"
						required
						className="block w-full p-5 text-xl peer/uid"
					/>
					<label
						htmlFor="display_name"
						className="block text-sm font-medium opacity-80 mb-0"
					>
						Name
					</label>
					<Input
						type="text"
						name="display_name"
						id="display_name"
						placeholder="Name"
						required
						className="block w-full p-5 text-xl peer/nam"
					/>
					<label
						htmlFor="phone_number"
						className="block text-sm font-medium opacity-80 mb-0"
					>
						Phone Number
					</label>
					<Input
						type="text"
						autoComplete="tel"
						name="phone_number"
						placeholder="Phone Number"
						id="phone_number"
						required
						className="mt-1 block w-full p-5 text-xl peer/phn"
					/>
					<label
						htmlFor="password"
						className="block text-sm font-medium opacity-80 mb-0"
					>
						Password
					</label>
					<Input
						type="password"
						name="password"
						placeholder="Password"
						id="password"
						required
						className="mt-1 block w-full p-5 text-xl peer/pwd mb-0"
					/>
					<Button
						type="submit"
						size="lg"
						className="w-full mt-5 text-lg py-5 peer-placeholder-shown/uid:opacity-50 peer-placeholder-shown/nam:opacity-50 peer-placeholder-shown/phn:opacity-50 peer-placeholder-shown/pwd:opacity-50"
					>
						Create Account
					</Button>
				</form>
				<Button variant="link" size="sm" className="py-5" asChild>
					<Link to="/login">Already have an account? Log in</Link>
				</Button>
			</div>
		</div>
	);
}

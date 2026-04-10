import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LOGIN_ERROR_MSG, useSession } from '@/lib/auth/auth';
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router';
import { toast } from 'sonner';

export default function Login() {
	const {
		isLoggedIn,
		action: { login },
	} = useSession();
	const navigate = useNavigate();

	const handleSubmit = async (form: FormData) => {
		const user_id = form.get('user_id');
		const password = form.get('password');
		if (typeof user_id !== 'string' || typeof password !== 'string') {
			alert('Please enter both username and password');
			return;
		}
		toast.promise(async () => await login({ user_id, password }), {
			loading: 'Logging in...',
			success: () => {
				navigate('/');
				return 'Login successful!';
			},
			error: (err) =>
				`${err instanceof Error ? err.message : LOGIN_ERROR_MSG.DEFAULT}`,
		});
	};
	useEffect(() => {
		if (isLoggedIn) {
			navigate('/');
		}
	}, [isLoggedIn, navigate]);

	return (
		<div className="w-full grow flex justify-center items-center">
			<div className="p-6 pb-3 w-100 border-2 rounded-2xl">
				<h1 className="text-2xl font-bold mb-4">Login</h1>
				<form
					onSubmit={(e) => {
						e.preventDefault();
						const formData = new FormData(e.currentTarget);
						handleSubmit(formData);
					}}
					className="space-y-4"
				>
					<label htmlFor="user_id" className="block mb-0">
						Username
					</label>
					<Input
						type="text"
						name="user_id"
						id="user_id"
						placeholder="Username"
						required
						className="mt-1 block w-full p-5 text-xl peer/uid"
					/>
					<label htmlFor="password" className="block mb-0">
						Password
					</label>
					<Input
						type="password"
						name="password"
						id="password"
						placeholder="Password"
						required
						className="mt-1 block w-full p-5 text-xl peer/pwd mb-0"
					/>
					<Button
						type="submit"
						size="lg"
						className="w-full mt-5 text-lg py-5 peer-placeholder-shown/uid:opacity-50 peer-placeholder-shown/pwd:opacity-50"
					>
						Login
					</Button>
				</form>
				<Button variant="link" size="sm" className="py-5" asChild>
					<Link to="/signup">Don't have an account? Sign up</Link>
				</Button>
			</div>
		</div>
	);
}

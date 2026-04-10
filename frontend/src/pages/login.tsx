import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useSession } from '@/lib/auth/auth';
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router';

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
			alert('Please enter both user ID and password');
			return;
		}
		try {
			await login({ user_id, password });
			alert('Login successful!');
		} catch (error) {
			alert(
				`Login failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
			);
		}
	};
	useEffect(() => {
		if (isLoggedIn) {
			console.log('user already logged in navigating...');
			navigate('/');
		}
	}, [isLoggedIn, navigate]);

	return (
		<div className="w-full h-svh flex justify-center items-center">
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

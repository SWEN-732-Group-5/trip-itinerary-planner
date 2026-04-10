import { useSession } from '@/lib/auth/auth';
import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router';

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
			alert('Please fill in all fields');
			return;
		}
		try {
			await signup({ user_id, password, display_name, phone_number });
			alert('Signup successful!');
		} catch (error) {
			alert(
				`Sign up failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
			);
		}
	};
	useEffect(() => {
		if (isLoggedIn) {
			navigate('/');
		}
	}, [isLoggedIn, navigate]);

	return (
		<div className="p-6 bg-slate-700 w-100">
			<h1 className="text-2xl font-bold mb-4">Create a new account</h1>
			<form
				onSubmit={(e) => {
					e.preventDefault();
					const formData = new FormData(e.currentTarget);
					handleSubmit(formData);
				}}
				className="space-y-4"
			>
				<div>
					<label
						htmlFor="user_id"
						className="block text-sm font-medium text-gray-300"
					>
						User ID
					</label>
					<input
						type="text"
						name="user_id"
						id="user_id"
						required
						className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
					/>
				</div>
				<div>
					<label
						htmlFor="display_name"
						className="block text-sm font-medium text-gray-300"
					>
						Name
					</label>
					<input
						type="text"
						name="display_name"
						id="display_name"
						required
						className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
					/>
				</div>
				<div>
					<label
						htmlFor="phone_number"
						className="block text-sm font-medium text-gray-300"
					>
						Phone Number
					</label>
					<input
						type="text"
						autoComplete="tel"
						name="phone_number"
						id="phone_number"
						required
						className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
					/>
				</div>
				<div>
					<label
						htmlFor="password"
						className="block text-sm font-medium text-gray-300"
					>
						Password
					</label>
					<input
						type="password"
						name="password"
						id="password"
						required
						className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
					/>
				</div>
				<button
					type="submit"
					className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
				>
					Create Account
				</button>
			</form>
			<Link
				to="/login"
				className="block mt-4 text-sm text-blue-400 hover:underline"
			>
				Already have an account? Log in
			</Link>
		</div>
	);
}

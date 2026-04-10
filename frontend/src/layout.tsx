import { Toaster } from 'sonner';

function Layout({ children }: { children: React.ReactNode }) {
	return (
		<div className="min-h-screen flex flex-col">
			<Toaster />
			<header className="bg-gray-800 text-white p-4">
				<h1 className="text-xl font-bold">My App</h1>
			</header>
			<main className="grow p-4 flex flex-col">{children}</main>
			<footer className="bg-gray-800 text-white p-4 text-center">
				&copy; 2024 My App. All rights reserved.
			</footer>
		</div>
	);
}

export default Layout;

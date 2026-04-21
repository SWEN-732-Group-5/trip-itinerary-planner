import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Route, Routes } from 'react-router';
import './App.css';
import Layout from './layout';
import SessionProvider from './lib/auth/authSession';
import Home from './pages/home';
import Login from './pages/login';
import Signup from './pages/signup';
import TripDetails from './pages/tripDetails';
import ViewInvitation from './pages/viewInvitation';

// Create a react query client
const queryClient = new QueryClient();

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<SessionProvider>
				<Layout>
					<Routes>
						<Route path="/" element={<Home />} />
						<Route path="/trips/:id" element={<TripDetails />} />
						<Route path="/login/:redirect?" element={<Login />} />
						<Route path="/signup" element={<Signup />} />
						<Route path="/accept-invitation/:id" element={<ViewInvitation />} />
					</Routes>
				</Layout>
			</SessionProvider>
		</QueryClientProvider>
	);
}

export default App;

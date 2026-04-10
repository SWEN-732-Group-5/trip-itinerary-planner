import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Route, Routes } from 'react-router';
import './App.css';
import Layout from './layout';
import TripDetails from './pages/trip-details';

// Create a react query client
const queryClient = new QueryClient();

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<Layout>
				<Routes>
					<Route path="/" element={<h1>Home</h1>} />
					<Route path="/trips/:id" element={<TripDetails />} />
				</Routes>
			</Layout>
		</QueryClientProvider>
	);
}

export default App;

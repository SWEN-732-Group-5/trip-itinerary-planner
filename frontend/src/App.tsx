import { Route, Routes } from 'react-router'
import './App.css'
import Layout from './layout'
import TripDetails from './pages/trip-details'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<h1>Home</h1>} />
        <Route path="/trips/:id" element={<TripDetails />} />

      </Routes>
    </Layout>
  )
}

export default App

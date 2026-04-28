import { Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'

// Auth is bypassed for demo — login/register will be wired back in for production
export default function App() {
  return (
    <Routes>
      <Route path="/*" element={<Dashboard />} />
    </Routes>
  )
}

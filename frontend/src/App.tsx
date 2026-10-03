import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'

function Home() {
  const [status, setStatus] = useState('Checking backend...')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((d) => setStatus(d.status === 'ok' ? 'Backend connected' : 'Backend unreachable'))
      .catch(() => setStatus('Backend unreachable'))
  }, [])

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold">CareBridge</h1>
      <p>{status}</p>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
    </Routes>
  )
}

import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Console from './pages/Console'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('frank_token'))

  useEffect(() => {
    const handler = () => setToken(localStorage.getItem('frank_token'))
    window.addEventListener('storage', handler)
    return () => window.removeEventListener('storage', handler)
  }, [])

  if (!token) {
    return <Login onLogin={(t) => { localStorage.setItem('frank_token', t); setToken(t) }} />
  }

  return <Console onLogout={() => { localStorage.removeItem('frank_token'); setToken(null) }} />
}

'use client'

import { useState } from 'react'

export function Login({ setToken }: { setToken: (t: string) => void }) {
  const [username, setUsername] = useState('test_admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const res = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString()
      })
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Invalid credentials')
        } else if (res.status === 422) {
          throw new Error('Validation error: Please check your input format')
        } else {
          throw new Error(`Server error: ${res.status}`)
        }
      }
      const data = await res.json()
      setToken(data.access_token)
    } catch (err: any) {
      if (err.name === 'TypeError' || err.message === 'Failed to fetch') {
        setError('Network error: Unable to connect to backend')
      } else {
        setError(err.message || 'Login failed')
      }
    } finally {
      setLoading(false)
    }
  }
  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: '#09090b', color: 'white' }}>
      <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '2rem', border: '1px solid #27272a', borderRadius: '8px' }}>
        <h2>MoneyTrail Login</h2>
        <input style={{ padding: '0.5rem', background: '#18181b', color: 'white', border: '1px solid #3f3f46', borderRadius: '4px' }} value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
        <input style={{ padding: '0.5rem', background: '#18181b', color: 'white', border: '1px solid #3f3f46', borderRadius: '4px' }} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <button style={{ padding: '0.5rem', background: 'white', color: 'black', borderRadius: '4px', cursor: 'pointer' }} type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  )
}

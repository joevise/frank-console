import React, { useState } from 'react'
import { authApi } from '../api/client'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(username, password)
      onLogin(res.data.access_token)
    } catch (err) {
      setError(err?.response?.data?.detail || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center font-sans">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-9 h-9 rounded-lg bg-ink text-accent font-mono font-semibold flex items-center justify-center text-sm">
            F
          </div>
          <div>
            <div className="text-lg font-semibold">Frank Console</div>
            <div className="text-[10px] font-mono text-ink-soft tracking-widest uppercase">
              Private Fund Manager · AI Copilot
            </div>
          </div>
        </div>

        <form onSubmit={submit} className="bg-panel border border-border rounded-xl p-8 space-y-4">
          <div>
            <label className="block text-xs font-mono text-ink-soft mb-1.5 uppercase tracking-wide">
              账号
            </label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-code border border-border rounded-lg px-3.5 py-2.5 text-sm outline-none focus:border-ink transition"
              placeholder="username"
            />
          </div>
          <div>
            <label className="block text-xs font-mono text-ink-soft mb-1.5 uppercase tracking-wide">
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-code border border-border rounded-lg px-3.5 py-2.5 text-sm outline-none focus:border-ink transition"
              placeholder="••••••••"
            />
          </div>
          {error && <div className="text-xs text-bull font-mono">{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-ink text-white rounded-lg py-2.5 text-sm font-mono flex items-center justify-center gap-2 hover:bg-black transition disabled:opacity-50"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-accent pulse-dot" />
            {loading ? '登录中...' : '登录'}
          </button>
        </form>
      </div>
    </div>
  )
}

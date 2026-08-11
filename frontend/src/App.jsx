import { useState, useEffect } from "react";
import { authApi } from "./api";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("frank_token"));

  useEffect(() => {
    const handler = () => setToken(localStorage.getItem("frank_token"));
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  return token ? (
    <Console
      onLogout={() => {
        localStorage.removeItem("frank_token");
        setToken(null);
      }}
    />
  ) : (
    <Login
      onLogin={(t) => {
        localStorage.setItem("frank_token", t);
        setToken(t);
      }}
    />
  );
}

/* ------------------------------------------------------------------ */
/*  Login Page (recovered from L2 in bundle)                          */
/* ------------------------------------------------------------------ */

function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await authApi.login(username, password);
      onLogin(res.data.access_token);
    } catch (err) {
      setError(err.response?.data?.detail || "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center font-sans"
      style={{
        backgroundColor: "#0a0a0a",
        backgroundImage:
          "radial-gradient(circle, rgba(255,215,0,0.02) 1px, transparent 1px)",
        backgroundSize: "24px 24px",
      }}
    >
      <div className="w-full max-w-[400px] mx-auto px-4">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-base font-mono font-bold"
            style={{ backgroundColor: "#FFD700", color: "#0a0a0a" }}
          >
            F
          </div>
          <div>
            <div className="text-lg font-semibold text-ink">Frank Console</div>
            <div className="text-[10px] font-mono text-ink-soft tracking-widest uppercase">
              Private Fund Manager · AI Copilot
            </div>
          </div>
        </div>
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl p-8 space-y-4 backdrop-blur-sm"
          style={{
            backgroundColor: "#161616",
            border: "1px solid rgba(255,215,0,0.15)",
          }}
        >
          <div>
            <label className="block text-xs font-mono text-ink-soft mb-1.5 uppercase tracking-wide">
              账号
            </label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-[#121212] border border-border rounded-lg px-3.5 py-2.5 text-sm text-ink outline-none focus:border-gold/50 transition"
              placeholder="username"
              autoFocus
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
              className="w-full bg-[#121212] border border-border rounded-lg px-3.5 py-2.5 text-sm text-ink outline-none focus:border-gold/50 transition"
              placeholder="••••••••"
            />
          </div>
          {error && (
            <div className="text-xs text-up font-mono">{error}</div>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg py-2.5 text-sm font-mono font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50"
            style={{ backgroundColor: "#FFD700", color: "#0a0a0a" }}
          >
            {loading ? "登录中…" : "登录"}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Console placeholder (imported from pages/Console.jsx)               */
/* ------------------------------------------------------------------ */

// Forward declaration — actual Console is in pages/Console.jsx
import Console from "./pages/Console";

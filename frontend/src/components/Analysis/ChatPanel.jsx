import React, { useEffect, useRef, useState, useCallback } from "react"
import { chatApi } from "../../api/client"

// ============================================================
// ChatPanel v3.1 — 原始版 + 多会话管理（不动样式/颜色）
// ============================================================

const API_BASE = "/api"
const DSA_PROXY_URL = `${API_BASE}/chat/dsa/chat`
const DSA_DIRECT_URL = "http://67.209.190.54:8120/chat"
const MAX_RETRY = 3

function getToken() {
  return localStorage.getItem("frank_token")
}

async function consumeSSE(resp, onData) {
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop() || ""
    for (const line of lines) {
      const t = line.trim()
      if (!t.startsWith("data:")) continue
      try { onData(JSON.parse(t.slice(5).trim())) } catch {}
    }
  }
}

function friendlyFrankError(msg) {
  if (!msg) return "Frank 大脑连接异常，请稍后重试"
  if (/401|unauthorized|认证/i.test(msg)) return "Frank 大脑连接异常（OpenMind 认证失败）"
  if (/超时|timeout/i.test(msg)) return "Frank 响应超时，请稍后重试"
  return `Frank 大脑连接异常：${msg}`
}

async function streamFrankOnce(message, conversationId, onChunk) {
  const resp = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify({ message, conversation_id: conversationId || undefined }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: `HTTP ${resp.status}` }))
    return { text: "", error: err.detail || `HTTP ${resp.status}` }
  }
  let text = ""
  let error = null
  await consumeSSE(resp, (data) => {
    if (data.type === "answer" && data.chunk) { text += data.chunk; onChunk?.(text) }
    else if (data.type === "frank_chunk") { text += data.text || ""; onChunk?.(text) }
    else if (data.type === "frank_final") { text += data.text || ""; onChunk?.(text) }
    else if (data.type === "done") { text = data.full_text || text }
    else if (data.type === "error") { error = data.message || "连接失败" }
  })
  return { text, error }
}

async function streamDSAOnce(url, message, onChunk, withAuth) {
  const headers = { "Content-Type": "application/json" }
  if (withAuth) headers.Authorization = `Bearer ${getToken()}`
  const resp = await fetch(url, { method: "POST", headers, body: JSON.stringify({ message }) })
  if (!resp.ok) return { text: "", error: `HTTP ${resp.status}` }
  let text = ""
  let error = null
  await consumeSSE(resp, (data) => {
    if (data.type === "chunk" && data.text) { text += data.text; onChunk?.(text) }
    else if (data.type === "done") { if (!text && data.full_text) text = data.full_text }
    else if (data.type === "error") { error = data.message || "连接失败" }
  })
  return { text, error }
}

const STAGE_LABEL = {
  thinking: { text: "Frank 思考中…", dot: "bg-warn" },
  consulting_dsa: { text: "咨询 DSA 分析师…", dot: "bg-accent" },
  replying: { text: "Frank 回复中…", dot: "bg-accent" },
  retrying: { text: "连接异常，重试中…", dot: "bg-warn" },
}

export default function ChatPanel({ open, onToggle, initialMessage }) {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "你好，我是 Frank。今天市场怎么看？" },
  ])
  const [input, setInput] = useState("")
  const [conversationId, setConversationId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState("")
  const [stage, setStage] = useState(null)

  const [sessions, setSessions] = useState([])
  const [sessionListOpen, setSessionListOpen] = useState(false)

  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  const loadSessions = useCallback(async () => {
    try {
      const res = await chatApi.sessions()
      setSessions(res.data || [])
    } catch {}
  }, [])

  useEffect(() => { loadSessions() }, [loadSessions])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streaming])

  useEffect(() => {
    if (initialMessage) { setInput(initialMessage); onToggle?.(true) }
  }, [initialMessage])

  const pushAssistant = (content) =>
    setMessages((m) => [...m, { role: "assistant", content }])

  const newConversation = () => {
    setConversationId(null)
    setMessages([{ role: "assistant", content: "新对话已开启。有什么想聊的？" }])
    setStreaming("")
    setStage(null)
    setSessionListOpen(false)
    inputRef.current?.focus()
  }

  const switchSession = async (sid) => {
    setSessionListOpen(false)
    if (sid === conversationId) return
    setConversationId(sid)
    setStreaming("")
    setStage(null)
    try {
      const res = await chatApi.sessionMessages(sid)
      const msgs = (res.data || []).map((m) => ({ role: m.role, content: m.content }))
      setMessages(msgs.length > 0 ? msgs : [{ role: "assistant", content: "（空对话）" }])
    } catch {
      setMessages([{ role: "assistant", content: "加载历史消息失败" }])
    }
  }

  const deleteSession = async (sid) => {
    try {
      await chatApi.deleteSession(sid)
      if (sid === conversationId) newConversation()
      loadSessions()
    } catch {}
  }

  const sendDSA = async (dsaMsg) => {
    setStage("consulting_dsa")
    let result = await streamDSAOnce(DSA_PROXY_URL, dsaMsg, setStreaming, true)
    if (result.error || !result.text) {
      setStreaming("")
      try { result = await streamDSAOnce(DSA_DIRECT_URL, dsaMsg, setStreaming, false) }
      catch { result = { text: "", error: "unreachable" } }
    }
    setStreaming("")
    if (result.error || !result.text) {
      pushAssistant("⚠️ DSA 分析师连接失败")
    } else {
      pushAssistant(result.text)
    }
  }

  const sendFrank = async (msg) => {
    let lastError = null
    for (let attempt = 1; attempt <= MAX_RETRY; attempt++) {
      if (attempt > 1) {
        setStage("retrying"); setStreaming("")
        await new Promise((r) => setTimeout(r, 800))
      } else { setStage("thinking") }
      try {
        const { text, error } = await streamFrankOnce(msg, conversationId, (t) => {
          setStage("replying"); setStreaming(t)
        })
        if (!error && text) {
          setStreaming(""); pushAssistant(text)
          loadSessions()
          return
        }
        lastError = error || "empty reply"
      } catch { lastError = "network error" }
    }
    setStage("retrying"); setStreaming("")
    try {
      const res = await chatApi.send(msg, conversationId || undefined)
      if (res.data?.conversation_id) setConversationId(res.data.conversation_id)
      if (res.data?.reply && !res.data?.error) {
        pushAssistant(res.data.reply)
        loadSessions()
        return
      }
      lastError = res.data?.error || lastError
    } catch {}
    pushAssistant(`⚠️ ${friendlyFrankError(lastError)}`)
  }

  const send = async () => {
    if (!input.trim() || loading) return
    const msg = input
    setMessages((m) => [...m, { role: "user", content: msg }])
    setInput("")
    setLoading(true)
    setStreaming("")
    setStage("thinking")
    try {
      if (msg.trim().startsWith("@DSA")) {
        await sendDSA(msg.replace(/^@DSA\s*/, ""))
      } else {
        await sendFrank(msg)
      }
    } finally {
      setStreaming(""); setStage(null); setLoading(false)
    }
  }

  const stageInfo = stage ? STAGE_LABEL[stage] : null

  return (
    <>
      {/* 会话列表抽屉 */}
      {sessionListOpen && (
        <div className="fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/40" onClick={() => setSessionListOpen(false)} />
          <div className="relative ml-auto w-72 h-full bg-panel border-l border-border shadow-2xl flex flex-col">
            <div className="h-12 px-3 flex items-center justify-between border-b border-border shrink-0">
              <span className="text-sm font-semibold">对话列表</span>
              <button onClick={newConversation}
                className="bg-ink text-accent rounded-md px-2.5 py-1 text-[11px] font-mono font-semibold hover:bg-ink/90">
                + 新对话
              </button>
            </div>
            <div className="flex-1 overflow-y-auto py-2 px-1.5 space-y-0.5">
              {sessions.length === 0 && (
                <div className="text-[11px] text-ink-soft text-center py-6">还没有对话</div>
              )}
              {sessions.map((s) => (
                <div key={s.id}
                  onClick={() => switchSession(s.id)}
                  className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-[12px] ${
                    s.id === conversationId ? "bg-accent/10 text-accent" : "text-ink-soft hover:bg-code hover:text-ink"
                  }`}>
                  <span className="flex-1 truncate">{s.title || "新对话"}</span>
                  <button onClick={(e) => { e.stopPropagation(); deleteSession(s.id) }}
                    className="shrink-0 text-[10px] text-ink-soft opacity-0 group-hover:opacity-60 hover:!text-down">
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 原始 ChatPanel（只加了 ☰ 和 + 按钮） */}
      <div className={`fixed bottom-0 left-16 right-0 z-40 transition-all ${open ? "h-[420px]" : "h-12"}`}>
        <div className="h-full bg-panel border-t border-border shadow-[0_-4px_20px_rgba(0,0,0,0.06)] flex flex-col">
          <div onClick={() => onToggle?.(!open)}
            className="h-12 px-3 md:px-5 flex items-center gap-2 cursor-pointer hover:bg-code/50 border-b border-border">
            <div className="w-6 h-6 rounded bg-ink text-accent font-mono text-[11px] font-semibold flex items-center justify-center">F</div>
            <span className="font-semibold text-sm">Frank</span>
            <span className="font-mono text-[10px] text-ink-soft hidden md:inline">AI Copilot</span>
            <div className="ml-auto flex items-center gap-2">
              {stageInfo && (
                <span className="flex items-center gap-1.5 font-mono text-[10px] text-ink-soft">
                  <span className={`w-1.5 h-1.5 rounded-full ${stageInfo.dot} pulse-dot`} />
                  {stageInfo.text}
                </span>
              )}
              <button onClick={(e) => { e.stopPropagation(); setSessionListOpen(true) }}
                className="flex items-center gap-1 text-[11px] font-mono text-ink-soft hover:text-ink bg-code px-2 py-1 rounded-md">
                ☰ <span className="hidden md:inline">会话</span>
              </button>
              <button onClick={(e) => { e.stopPropagation(); newConversation() }}
                className="flex items-center gap-1 text-[11px] font-mono text-accent bg-accent/10 px-2 py-1 rounded-md hover:bg-accent/20">
                + <span className="hidden md:inline">新对话</span>
              </button>
              <span className="text-ink-soft text-xs hidden md:inline">{open ? "▾" : "▴"}</span>
            </div>
          </div>

          {open && (
            <>
              <div className="flex-1 overflow-y-auto px-4 md:px-5 py-3 space-y-2.5">
                {messages.map((m, i) => (
                  <div key={i}
                    className={`text-[13px] leading-relaxed rounded-xl px-3 py-2 max-w-[80%] whitespace-pre-wrap ${
                      m.role === "user" ? "bg-ink text-white ml-auto" : "bg-code"
                    }`}>
                    {m.content}
                  </div>
                ))}
                {streaming && (
                  <div className="text-[13px] leading-relaxed rounded-xl px-3 py-2 max-w-[80%] bg-code whitespace-pre-wrap">
                    {streaming}
                    <span className="inline-block w-1.5 h-3 bg-ink ml-0.5 animate-pulse" />
                  </div>
                )}
                {stageInfo && !streaming && (
                  <div className="flex items-center gap-1.5 font-mono text-[11px] text-ink-soft px-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${stageInfo.dot} pulse-dot`} />
                    {stageInfo.text}
                  </div>
                )}
                <div ref={bottomRef} />
              </div>
              <div className="px-4 md:px-5 py-3 mb-2 md:mb-0 border-t border-border flex gap-2">
                <input ref={inputRef} value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
                  placeholder="问 Frank…（Enter 发送）"
                  className="flex-1 bg-code border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-ink" />
                <button onClick={send} disabled={loading}
                  className="bg-ink text-accent rounded-lg px-4 text-sm disabled:opacity-50 min-w-[44px] min-h-[44px] md:min-h-0">➤</button>
                <button onClick={() => { setInput("@DSA "); inputRef.current?.focus() }}
                  disabled={loading}
                  className="bg-accent/10 text-accent border border-accent/30 rounded-lg px-3 text-sm disabled:opacity-50 font-mono min-h-[44px] md:min-h-0">@DSA</button>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  )
}

import { useState, useEffect, useRef, useCallback } from "react";
import {
  MessageCircle,
  Plus,
  ChevronLeft,
  X,
  Trash2,
} from "lucide-react";
import { chatApi } from "../../api";
import { MarkdownContent } from "../../utils/md.jsx";

/* ------------------------------------------------------------------ */
/*  Sub-components (originally Tl, uP, tY, nY, rY, eY)                */
/* ------------------------------------------------------------------ */

async function parseStream(reader, onChunk) {
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data:")) {
        try {
          onChunk(JSON.parse(trimmed.slice(5).trim()));
        } catch {}
      }
    }
  }
}

function FrankMessage({ text }) {
  return (
    <div className="bg-[#1c1c1c] rounded-xl px-3 py-2 text-[13px] text-ink leading-relaxed">
      <MarkdownContent content={text} />
    </div>
  );
}

function DSACard({ query, steps, result }) {
  return (
    <div className="border border-gold/30 rounded-xl overflow-hidden">
      <div className="bg-gold/10 px-3 py-1.5 flex items-center gap-1.5">
        <span className="font-mono text-[10px] text-gold uppercase tracking-wider">
          📊 DSA 分析师
        </span>
      </div>
      {query && (
        <div className="px-3 py-1.5 text-[11px] text-ink-soft border-b border-border">
          🔍 {query}
        </div>
      )}
      {steps.length > 0 && (
        <div className="px-3 py-2 space-y-0.5 bg-[#161616]">
          {steps.map((s, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 font-mono text-[10px]"
            >
              <span className="text-gold">✓</span>
              <span className="text-ink-soft">{s}</span>
            </div>
          ))}
        </div>
      )}
      {result && (
        <div className="px-3 py-2 text-[12px] text-ink border-t border-border">
          <MarkdownContent content={result} />
        </div>
      )}
    </div>
  );
}

function UserMessage({ text }) {
  return (
    <div className="bg-[#0a0a0a] border border-gold/20 rounded-xl px-3 py-2 text-[13px] text-ink ml-auto max-w-[85%] whitespace-pre-wrap">
      {text}
    </div>
  );
}

function StreamingState({ streaming, steps, dsaQuery, dsaResult, stage }) {
  const labels = {
    thinking: "思考中…",
    consulting_dsa: "DSA 分析中…",
    replying: "回复中…",
  };
  return (
    <div className="space-y-2">
      {dsaQuery && <DSACard query={dsaQuery} steps={steps} result={dsaResult} />}
      {streaming && (
        <FrankMessage text={streaming + (stage ? " ▋" : "")} />
      )}
      {stage && !streaming && (
        <div className="flex items-center gap-1.5 font-mono text-[10px] text-gold px-1">
          <span className="w-1 h-1 rounded-full bg-gold pulse-dot" />
          {labels[stage] || stage}
        </div>
      )}
    </div>
  );
}

function SessionList({
  sessions,
  currentId,
  onSelect,
  onDelete,
  onNew,
  onClose,
}) {
  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 p-3 border-b border-border shrink-0">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest flex-1">
          对话列表
        </span>
        <button
          onClick={onNew}
          className="w-7 h-7 rounded-lg bg-gold/10 flex items-center justify-center text-gold hover:bg-gold/20 transition"
        >
          <Plus size={14} strokeWidth={1.5} />
        </button>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-ink-soft hover:text-ink transition"
        >
          <X size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="text-[12px] text-ink-dim text-center py-8">
            暂无对话
          </div>
        ) : (
          sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => onSelect(s.id)}
              className={`px-3 py-2.5 cursor-pointer border-b border-border/50 transition group ${
                currentId === s.id ? "bg-gold/10" : "hover:bg-[#1c1c1c]"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`text-[12px] font-medium flex-1 truncate ${
                    currentId === s.id ? "text-gold" : "text-ink"
                  }`}
                >
                  {s.title || "新对话"}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(s.id);
                  }}
                  className="text-ink-dim hover:text-[#ff3860] transition opacity-0 group-hover:opacity-100 shrink-0"
                >
                  <Trash2 size={11} strokeWidth={1.5} />
                </button>
              </div>
              {s.last_message && (
                <div className="font-mono text-[9px] text-ink-dim truncate mt-0.5">
                  {s.last_message}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  ChatPanel                                                         */
/* ------------------------------------------------------------------ */

export default function ChatPanel({ open, onToggle, initialMessage }) {
  const [messages, setMessages] = useState([]);
  const [streamingText, setStreamingText] = useState("");
  const [dsaSteps, setDsaSteps] = useState([]);
  const [dsaQuery, setDsaQuery] = useState("");
  const [dsaResult, setDsaResult] = useState("");
  const [stage, setStage] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState([]);

  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [streamingText, messages, dsaSteps]);

  const loadSessions = useCallback(async () => {
    try {
      const res = await chatApi.conversations();
      setSessions(res.data || []);
    } catch {
      setSessions([]);
    }
  }, []);

  const loadMessages = useCallback(async (id) => {
    try {
      const res = await chatApi.messages(id);
      setMessages(res.data || []);
    } catch {
      setMessages([]);
    }
  }, []);

  useEffect(() => {
    if (open && conversationId === null && messages.length === 0) {
      loadSessions();
    }
  }, [open]);

  useEffect(() => {
    if (initialMessage) {
      setInput(initialMessage);
      onToggle?.(true);
    }
  }, [initialMessage]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    setStreamingText("");
    setDsaSteps([]);
    setDsaQuery("");
    setDsaResult("");
    setStage("thinking");

    try {
      const token = localStorage.getItem("frank_token");
      const res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId || undefined,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      let frankText = "";
      let steps = [];
      let query = "";
      let result = "";

      await parseStream(res, (chunk) => {
        const type = chunk.type;
        if (type === "frank_chunk") {
          setStage("replying");
          frankText += chunk.text;
          setStreamingText(frankText);
        } else if (type === "dsa_start") {
          setStage("consulting_dsa");
          query = chunk.query;
          setDsaQuery(query);
          setStreamingText("");
        } else if (type === "dsa_step") {
          steps.push(chunk.text);
          setDsaSteps([...steps]);
        } else if (type === "dsa_result") {
          result = chunk.text;
          setDsaResult(result);
          setStage("replying");
        } else if (type === "frank_final") {
          frankText += chunk.text;
          setStreamingText(frankText);
        } else if (type === "done") {
          if (chunk.conversation_id) setConversationId(chunk.conversation_id);
          setMessages((prev) => [
            ...prev,
            result
              ? {
                  role: "assistant",
                  content: "",
                  dsa: { query, steps, result },
                  frank_final: frankText,
                }
              : { role: "assistant", content: frankText },
          ]);
          setStreamingText("");
          setDsaSteps([]);
          setDsaQuery("");
          setDsaResult("");
        } else if (type === "error") {
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content: `⚠️ ${chunk.message || "连接失败"}`,
            },
          ]);
        }
      });
    } catch {
      try {
        const res = await chatApi.send(text, conversationId || undefined);
        if (res.data?.conversation_id) setConversationId(res.data.conversation_id);
        if (res.data?.reply) {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: res.data.reply },
          ]);
        }
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "⚠️ 连接失败，请稍后重试" },
        ]);
      }
    } finally {
      setStreamingText("");
      setStage(null);
      setLoading(false);
    }
  };

  const handleNewChat = async () => {
    setConversationId(null);
    setMessages([]);
    setShowHistory(false);
  };

  const handleSelectSession = async (id) => {
    setConversationId(id);
    await loadMessages(id);
    setShowHistory(false);
  };

  const handleDeleteSession = async (id) => {
    if (!confirm("确定删除？")) return;
    try {
      await chatApi.deleteConversation(id);
      setSessions(sessions.filter((s) => s.id !== id));
      if (conversationId === id) {
        setConversationId(null);
        setMessages([]);
      }
    } catch {}
  };

  if (!open) return null;

  return (
    <>
      <div
        className="fixed inset-0 bg-black z-40 md:hidden"
        onClick={() => onToggle?.(false)}
      />
      <div className="fixed inset-0 z-50 md:z-20 md:inset-auto md:top-14 md:bottom-0 md:right-0 md:w-[480px] md:border-l md:border-[#262626] bg-[#0a0a0a] md:bg-[#121212] md:flex">
        {showHistory && (
          <div className="w-full md:w-[240px] md:border-r md:border-border bg-[#0a0a0a] absolute md:relative inset-0 md:inset-auto z-10">
            <SessionList
              sessions={sessions}
              currentId={conversationId}
              onSelect={handleSelectSession}
              onDelete={handleDeleteSession}
              onNew={handleNewChat}
              onClose={() => setShowHistory(false)}
            />
          </div>
        )}
        <div className="flex-1 flex flex-col h-full">
          {/* Header */}
          <div className="h-12 px-3 flex items-center gap-2 border-b border-border shrink-0">
            <button
              onClick={() => {
                setShowHistory(!showHistory);
                if (!showHistory) loadSessions();
              }}
              className="md:hidden w-7 h-7 flex items-center justify-center text-ink-soft hover:text-gold"
            >
              <ChevronLeft size={16} />
            </button>
            <div className="w-6 h-6 rounded bg-[#FFD700] text-[#0a0a0a] font-mono text-[11px] font-semibold flex items-center justify-center">
              F
            </div>
            <span className="font-semibold text-sm text-ink">Frank</span>
            <span className="font-mono text-[10px] text-ink-soft hidden sm:block">
              AI Copilot
            </span>
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="hidden md:flex ml-2 items-center gap-1 font-mono text-[10px] text-ink-soft hover:text-gold px-2 py-1 rounded hover:bg-[#1c1c1c]"
            >
              <MessageCircle size={12} strokeWidth={1.5} /> 历史
            </button>
            <button
              onClick={() => {
                handleNewChat();
                loadSessions();
              }}
              className="hidden md:flex items-center gap-1 font-mono text-[10px] text-gold border border-gold/30 rounded px-2 py-1 hover:bg-gold/10"
            >
              <Plus size={11} strokeWidth={1.5} /> 新对话
            </button>
            <div className="ml-auto flex items-center gap-2">
              {stage && (
                <span className="flex items-center gap-1.5 font-mono text-[10px] text-gold">
                  <span className="w-1 h-1 rounded-full bg-gold pulse-dot" />
                  {stage === "thinking"
                    ? "思考中"
                    : stage === "consulting_dsa"
                    ? "DSA分析中"
                    : "回复中"}
                </span>
              )}
              <button
                onClick={() => onToggle?.(false)}
                className="text-ink-soft hover:text-ink text-sm w-7 h-7 flex items-center justify-center"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.length === 0 && !streamingText && (
              <div className="text-center py-10">
                <div className="text-3xl mb-2 opacity-50">🤝</div>
                <div className="text-sm text-ink-soft">跟 Frank 聊聊？</div>
                <div className="font-mono text-[10px] text-ink-dim mt-1">
                  问市场、问个股、问操作策略
                </div>
              </div>
            )}
            {messages.map((msg, idx) =>
              msg.role === "user" ? (
                <div key={idx} className="flex">
                  <UserMessage text={msg.content} />
                </div>
              ) : msg.dsa ? (
                <div key={idx} className="space-y-2">
                  <DSACard
                    query={msg.dsa.query}
                    steps={msg.dsa.steps}
                    result={msg.dsa.result}
                  />
                  {msg.frank_final && <FrankMessage text={msg.frank_final} />}
                  {msg.content && !msg.frank_final && (
                    <FrankMessage text={msg.content} />
                  )}
                </div>
              ) : (
                <FrankMessage key={idx} text={msg.content} />
              )
            )}
            {(streamingText || dsaQuery || dsaSteps.length > 0) && (
              <StreamingState
                streaming={streamingText}
                steps={dsaSteps}
                dsaQuery={dsaQuery}
                dsaResult={dsaResult}
                stage={stage}
              />
            )}
            <div ref={scrollRef} />
          </div>

          {/* Input */}
          <div className="px-3 py-3 border-t border-border flex gap-2">
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="问 Frank…（Enter 发送）"
              className="flex-1 bg-[#1c1c1c] border border-border rounded-lg px-3 py-2 text-sm text-ink outline-none focus:border-[#FFD700] transition"
            />
            <button
              onClick={handleSend}
              disabled={loading}
              className="bg-[#FFD700] text-[#0a0a0a] rounded-lg px-4 min-w-[44px] min-h-[44px] md:min-h-0 text-sm font-mono font-semibold disabled:opacity-50"
            >
              ➤
            </button>
            <button
              onClick={() => {
                setInput("@DSA ");
                inputRef.current?.focus();
              }}
              disabled={loading}
              className="bg-gold/10 text-[#FFD700] border border-gold/30 rounded-lg px-3 min-h-[44px] md:min-h-0 text-sm font-mono disabled:opacity-50"
            >
              @DSA
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

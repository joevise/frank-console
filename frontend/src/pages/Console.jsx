import { useState, useEffect, useCallback } from "react";
import {
  Home,
  BarChart3,
  Swords,
  Newspaper,
  FileText,
  Settings,
  MessageCircle,
  RotateCcw,
  Calendar,
  TrendingUp,
  Download,
  Plus,
  Trash2,
  Search,
} from "lucide-react";
import client, { marketApi, watchlistApi, briefApi, chatApi } from "../api";
import { MarkdownContent } from "../utils/md.jsx";
import ChatPanel from "../components/Analysis/ChatPanel";
import StockDrawer from "../components/Analysis/StockDrawer";
import MorningBrief from "../components/Analysis/MorningBrief";

/* ------------------------------------------------------------------ */
/*  Dashboard / Market components (referenced but not recovered)        */
/* ------------------------------------------------------------------ */
import MarketDashboard from "../components/Market/MarketDashboard";
import BattleRoom from "../components/Market/BattleRoom";

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

const RATING_MAP = {
  attack: { label: "进攻", color: "#00d1b2", icon: "🟢" },
  caution: { label: "震荡", color: "#ffdd57", icon: "🟡" },
  defend: { label: "防守", color: "#ff3860", icon: "🔴" },
};

const DESKTOP_NAV = [
  { key: "home", icon: Home, label: "首页" },
  { key: "dashboard", icon: BarChart3, label: "仪表盘" },
  { key: "battle", icon: Swords, label: "作战室" },
  { key: "brief", icon: Newspaper, label: "晨报" },
  { key: "reports", icon: FileText, label: "报告" },
  { key: "settings", icon: Settings, label: "设置" },
];

const MOBILE_NAV = [
  { key: "home", icon: Home, label: "首页" },
  { key: "brief", icon: Newspaper, label: "晨报" },
  { key: "reports", icon: FileText, label: "报告" },
  { key: "settings", icon: Settings, label: "设置" },
];

/* ------------------------------------------------------------------ */
/*  HomePage sub-component                                            */
/* ------------------------------------------------------------------ */

function Greeting() {
  const hour = new Date().getHours();
  let greeting = "早安";
  if (hour >= 12 && hour < 18) greeting = "午安";
  else if (hour >= 18) greeting = "晚上好";
  const date = new Date().toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <div className="text-xl md:text-2xl font-semibold text-ink">
          {greeting}，Frank
        </div>
        <div className="font-mono text-[11px] text-ink-soft mt-0.5">{date}</div>
      </div>
    </div>
  );
}

function WatchlistCard({ item }) {
  const quote = item.quote;
  const changePct = quote?.change_pct;
  const color =
    changePct > 0 ? "#ff3860" : changePct < 0 ? "#00d1b2" : "#888";
  const score = item.health_score;
  const scoreColor =
    score >= 70 ? "#ff3860" : score >= 45 ? "#ffdd57" : "#00d1b2";
  const highlight = score >= 70;
  return (
    <div
      className={`bg-panel border border-border rounded-xl p-3 ${highlight ? "border-l-2" : ""}`}
      style={
        highlight ? { borderLeftColor: "#FFD700", borderLeftWidth: "2px" } : {}
      }
    >
      <div className="text-[12px] font-medium text-ink truncate">
        {item.stock_name || item.stock_code}
      </div>
      <div className="font-mono text-base font-semibold text-ink mt-1 leading-tight">
        {quote?.price?.toFixed(2) || "—"}
      </div>
      <div className="flex items-center justify-between mt-1 gap-1">
        <span className="font-mono text-[11px] shrink-0" style={{ color }}>
          {changePct > 0 ? "+" : ""}
          {changePct || 0}%
        </span>
        <span className="flex items-center gap-1 shrink-0">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: scoreColor }}
          />
          <span className="font-mono text-[10px]" style={{ color: scoreColor }}>
            {score ?? "—"}
          </span>
        </span>
      </div>
    </div>
  );
}

function QuickEntry({ icon: Icon, label, sublabel, onClick }) {
  return (
    <button
      onClick={onClick}
      className="flex-1 bg-panel border border-border rounded-xl p-2.5 md:p-4 hover:border-gold/40 transition group text-left flex items-center gap-2 md:gap-3 min-w-0"
    >
      <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg bg-gold/10 flex items-center justify-center shrink-0">
        <Icon size={16} strokeWidth={1.5} className="text-gold" />
      </div>
      <div className="min-w-0">
        <div className="text-[11px] md:text-[13px] font-medium text-ink group-hover:text-gold transition truncate">
          {label}
        </div>
        <div className="font-mono text-[9px] md:text-[10px] text-ink-soft truncate hidden sm:block">
          {sublabel}
        </div>
      </div>
    </button>
  );
}

function HomePage({ brief, holdings, onNavigate, onSelectStock }) {
  const rating = brief?.rating;
  const ratingInfo = rating ? RATING_MAP[rating] : null;
  return (
    <div className="max-w-[1200px] mx-auto animate-fade-in-up">
      <Greeting />

      {/* Rating Card */}
      <div className="bg-panel border border-border rounded-2xl p-4 md:p-5 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
            今日评级
          </span>
          <div className="flex-1 h-px bg-border" />
        </div>
        {ratingInfo ? (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xl md:text-2xl shrink-0">
                {ratingInfo.icon}
              </span>
              <span
                className="text-base md:text-lg font-semibold shrink-0"
                style={{ color: ratingInfo.color }}
              >
                {ratingInfo.label}
              </span>
              <button
                onClick={() => onNavigate?.("brief")}
                className="ml-auto shrink-0 font-mono text-[10px] text-gold hover:underline px-2 py-1"
              >
                查看晨报 →
              </button>
            </div>
            <div className="text-[12px] md:text-[14px] text-ink-soft leading-relaxed">
              {brief?.summary ||
                (brief?.content || "").slice(0, 120) + "..." ||
                "查看完整晨报"}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <span className="text-[13px] text-ink-soft">今日晨报尚未生成</span>
            <button
              onClick={() => onNavigate?.("brief")}
              className="font-mono text-[11px] text-gold border border-gold/30 rounded-lg px-3 py-1.5 hover:bg-gold/10 transition"
            >
              生成晨报 →
            </button>
          </div>
        )}
      </div>

      {/* Watchlist */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
            自选股速览
          </span>
          <div className="flex-1 h-px bg-border" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 md:gap-3">
          {holdings?.slice(0, 4).map((item, idx) => (
            <div
              key={item.id || item.stock_code || idx}
              className="animate-fade-in-up cursor-pointer"
              style={{ animationDelay: `${idx * 50}ms` }}
              onClick={() => onSelectStock?.(item)}
            >
              <WatchlistCard item={item} />
            </div>
          ))}
          <button
            onClick={() => onNavigate?.("watchlist")}
            className="bg-panel border border-dashed border-border-light rounded-xl p-3 flex flex-col items-center justify-center hover:border-gold/40 transition group min-h-[100px] gap-1"
          >
            <Plus
              size={20}
              strokeWidth={1.5}
              className="text-ink-soft group-hover:text-gold transition"
            />
            <span className="font-mono text-[10px] text-ink-soft">添加</span>
          </button>
        </div>
      </div>

      {/* Quick Entry */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
            快速入口
          </span>
          <div className="flex-1 h-px bg-border" />
        </div>
        <div className="flex flex-row gap-2 md:gap-3">
          <QuickEntry
            icon={MessageCircle}
            label="问 Frank"
            sublabel="对话 · AI 决策助手"
            onClick={() => onNavigate?.("chat")}
          />
          <QuickEntry
            icon={Search}
            label="@DSA 分析"
            sublabel="独立 AI 分析师"
            onClick={() => onNavigate?.("chat")}
          />
          <QuickEntry
            icon={Newspaper}
            label="今日晨报"
            sublabel="DSA 自动生成"
            onClick={() => onNavigate?.("brief")}
          />
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  ReportCenter sub-component                                        */
/* ------------------------------------------------------------------ */

function ReportCenter() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selected, setSelected] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [reportType, setReportType] = useState("weekly");
  const [stockCode, setStockCode] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const res = await client.get("/reports/list");
      setReports(res.data || []);
    } catch {
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const generate = async () => {
    setGenerating(true);
    try {
      const payload = { report_type: reportType };
      if (reportType === "stock" && stockCode) payload.stock_code = stockCode;
      const res = await client.post("/reports/generate", payload, {
        timeout: 120000,
      });
      await load();
      setSelected(res.data);
      setShowForm(false);
    } catch (err) {
      alert("生成失败: " + (err.response?.data?.detail || err.message));
    } finally {
      setGenerating(false);
    }
  };

  const view = async (id) => {
    try {
      const res = await client.get(`/reports/${id}`);
      setSelected(res.data);
    } catch {}
  };

  const remove = async (id, e) => {
    e.stopPropagation();
    if (!confirm("确定删除？")) return;
    try {
      await client.delete(`/reports/${id}`);
      setReports(reports.filter((r) => r.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch {}
  };

  const download = (report) => {
    const blob = new Blob([report.content || ""], {
      type: "text/markdown;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${report.title || "report"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const typeMeta = {
    weekly: { label: "周报", icon: Calendar, color: "#FFD700" },
    monthly: { label: "月报", icon: FileText, color: "#5b8def" },
    stock: { label: "个股分析", icon: TrendingUp, color: "#ff3860" },
  };

  if (selected) {
    const meta = typeMeta[selected.report_type] || typeMeta.weekly;
    return (
      <div className="max-w-[860px] mx-auto animate-fade-in-up">
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={() => setSelected(null)}
            className="font-mono text-[11px] text-ink-soft hover:text-gold px-2 py-1 rounded hover:bg-[#1c1c1c]"
          >
            ← 返回列表
          </button>
          <span className="font-semibold text-sm">{selected.title}</span>
          <button
            onClick={() => download(selected)}
            className="ml-auto flex items-center gap-1 font-mono text-[10px] text-gold border border-gold/30 rounded-lg px-2 py-1 hover:bg-gold/10"
          >
            <Download size={12} strokeWidth={1.5} /> 导出MD
          </button>
        </div>
        <div className="bg-panel border border-border rounded-xl p-5 md:p-6">
          <MarkdownContent content={selected.content} />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1000px] mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          报告中心
        </span>
        <span className="font-mono text-[10px] text-ink-soft">
          {reports.length}
        </span>
        <div className="flex-1 h-px bg-border" />
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 font-mono text-[11px] text-gold border border-gold/30 rounded-lg px-3 py-1.5 hover:bg-gold/10 transition"
        >
          <Plus size={14} strokeWidth={1.5} /> 生成报告
        </button>
      </div>

      {showForm && (
        <div className="bg-panel border border-gold/20 rounded-xl p-4 mb-4 animate-fade-in-up">
          <div className="font-mono text-[10px] text-gold uppercase tracking-widest mb-3">
            选择类型
          </div>
          <div className="flex gap-2 mb-3">
            {Object.entries(typeMeta).map(([key, meta]) => {
              const Icon = meta.icon;
              return (
                <button
                  key={key}
                  onClick={() => setReportType(key)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border transition text-[12px] ${
                    reportType === key
                      ? "border-gold/40 bg-gold/10 text-gold"
                      : "border-border text-ink-soft hover:text-ink"
                  }`}
                >
                  <Icon size={14} strokeWidth={1.5} /> {meta.label}
                </button>
              );
            })}
          </div>
          {reportType === "stock" && (
            <input
              value={stockCode}
              onChange={(e) => setStockCode(e.target.value)}
              placeholder="股票代码（如 600519）"
              className="w-full bg-[#1c1c1c] border border-border rounded-lg px-3 py-2 text-[13px] text-ink outline-none focus:border-gold/50 mb-3"
            />
          )}
          <button
            onClick={generate}
            disabled={generating}
            className="w-full bg-[#FFD700] text-[#0a0a0a] rounded-lg py-2.5 text-sm font-mono font-semibold disabled:opacity-50"
          >
            {generating ? "DSA 分析师生成中…（约1-2分钟）" : "开始生成"}
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-10 text-ink-soft text-sm">加载中…</div>
      ) : reports.length === 0 ? (
        <div className="bg-panel border border-border rounded-xl p-8 text-center">
          <FileText
            size={32}
            strokeWidth={1}
            className="text-ink-dim mx-auto mb-3"
          />
          <div className="text-sm text-ink-soft mb-1">暂无报告</div>
          <div className="font-mono text-[10px] text-ink-dim">
            点击「生成报告」创建第一份
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {reports.map((r) => {
            const meta = typeMeta[r.report_type] || typeMeta.weekly;
            const Icon = meta.icon;
            return (
              <div
                key={r.id}
                onClick={() => view(r.id)}
                className="bg-panel border border-border rounded-xl p-4 cursor-pointer hover:border-gold/30 transition group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${meta.color}15` }}
                  >
                    <Icon
                      size={14}
                      strokeWidth={1.5}
                      style={{ color: meta.color }}
                    />
                  </div>
                  <span className="text-[13px] font-medium text-ink flex-1 truncate">
                    {r.title}
                  </span>
                  <span
                    className="font-mono text-[10px] px-1.5 py-0.5 rounded"
                    style={{
                      backgroundColor: `${meta.color}15`,
                      color: meta.color,
                    }}
                  >
                    {meta.label}
                  </span>
                </div>
                <div className="text-[12px] text-ink-soft line-clamp-2 mb-2">
                  {r.preview}
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-ink-dim">
                    {(r.date || "").slice(0, 10)}
                  </span>
                  <button
                    onClick={(e) => remove(r.id, e)}
                    className="text-ink-dim hover:text-[#ff3860] transition opacity-0 group-hover:opacity-100"
                  >
                    <Trash2 size={12} strokeWidth={1.5} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  HistoryPanel sub-component                                        */
/* ------------------------------------------------------------------ */

function HistoryPanel({ onClose, onLoadConversation }) {
  const [conversations, setConversations] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await chatApi.conversations();
      setConversations(res.data || []);
    } catch {
      setConversations([]);
    } finally {
      setLoading(false);
    }
  };

  const loadMsgs = async (id) => {
    try {
      const res = await chatApi.messages(id);
      setMessages(res.data || []);
    } catch {
      setMessages([]);
    }
  };

  const toggle = (id) => {
    if (expandedId === id) {
      setExpandedId(null);
      setMessages([]);
    } else {
      setExpandedId(id);
      loadMsgs(id);
    }
  };

  const remove = async (id, e) => {
    e.stopPropagation();
    if (!confirm("确定删除这个对话？")) return;
    try {
      await chatApi.deleteConversation(id);
      setConversations(conversations.filter((c) => c.id !== id));
      if (expandedId === id) {
        setExpandedId(null);
        setMessages([]);
      }
    } catch {
      alert("删除失败");
    }
  };

  const filtered =
    filter === "all"
      ? conversations
      : conversations.filter((c) => c.source === filter);

  const sourceBadge = (src) =>
    src === "dsa" ? (
      <span className="font-mono text-[9px] bg-[#FFD700]/10 text-[#FFD700] px-1.5 rounded">
        DSA
      </span>
    ) : (
      <span className="font-mono text-[9px] bg-ink/80 text-[#FFD700] px-1.5 rounded">
        Frank
      </span>
    );

  const fmtTime = (d) => {
    const dt = new Date(d);
    const now = new Date();
    return dt.toDateString() === now.toDateString()
      ? dt.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
      : dt.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit" });
  };

  return (
    <div className="fixed inset-0 md:top-14 md:bottom-12 md:left-16 z-30 bg-bg flex flex-col">
      <div className="h-12 px-3 md:px-4 flex items-center gap-2 border-b border-border shrink-0">
        <span className="text-base">💬</span>
        <span className="font-semibold text-sm">历史对话</span>
        <span className="font-mono text-[10px] text-ink-soft">
          {filtered.length}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex gap-1 bg-[#1c1c1c] rounded-lg p-0.5">
            {["all", "frank", "dsa"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`font-mono text-[10px] px-2 py-1 rounded ${
                  filter === f
                    ? "bg-[#FFD700] text-[#0a0a0a]"
                    : "text-ink-soft"
                }`}
              >
                {f === "all" ? "全部" : f === "frank" ? "Frank" : "DSA"}
              </button>
            ))}
          </div>
          <button
            onClick={onClose}
            className="text-ink-soft hover:text-ink text-sm px-1 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 flex items-center justify-center"
          >
            ✕
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 md:px-4 py-3">
        {loading ? (
          <div className="text-center py-10 text-ink-soft text-sm">加载中…</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-10 text-ink-soft text-sm">
            暂无对话记录
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((c) => (
              <div
                key={c.id}
                className="bg-panel border border-border rounded-lg overflow-hidden"
              >
                <div
                  onClick={() => toggle(c.id)}
                  className="px-3 py-2.5 flex items-center gap-2 cursor-pointer hover:bg-[#1c1c1c]/50"
                >
                  {sourceBadge(c.source)}
                  <span className="text-[13px] text-ink flex-1 truncate">
                    {c.title}
                  </span>
                  <span className="font-mono text-[10px] text-ink-soft shrink-0">
                    {c.message_count || 0}条
                  </span>
                  <span className="font-mono text-[10px] text-ink-soft shrink-0">
                    {fmtTime(c.updated_at)}
                  </span>
                  <button
                    onClick={(e) => remove(c.id, e)}
                    className="text-ink-soft hover:text-red-400 text-xs px-1"
                    title="删除"
                  >
                    🗑
                  </button>
                </div>
                {expandedId === c.id && (
                  <div className="border-t border-border px-3 py-2 space-y-1.5 bg-[#1c1c1c]/30 max-h-[400px] overflow-y-auto">
                    {messages.length === 0 ? (
                      <div className="text-[12px] text-ink-soft py-2">
                        加载中…
                      </div>
                    ) : (
                      messages.map((m) => (
                        <div key={m.id} className="text-[12px] leading-relaxed">
                          <span
                            className={`font-mono text-[10px] mr-1.5 ${
                              m.role === "user"
                                ? "text-[#FFD700]"
                                : "text-ink-soft"
                            }`}
                          >
                            {m.role === "user"
                              ? "我"
                              : m.source?.toUpperCase() || "AI"}
                            :
                          </span>
                          <span className="text-ink-soft whitespace-pre-wrap">
                            {m.content}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  WatchlistPanel sub-component                                      */
/* ------------------------------------------------------------------ */

function WatchlistPanel({ onClose }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    stock_code: "",
    stock_name: "",
    mainline: "",
    note: "",
  });

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const res = await watchlistApi.list();
      setItems(res.data || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const add = async () => {
    if (!form.stock_code.trim()) return;
    try {
      await watchlistApi.add(
        form.stock_code.trim(),
        form.stock_name.trim(),
        form.mainline.trim(),
        "hold",
        form.note.trim()
      );
      setForm({ stock_code: "", stock_name: "", mainline: "", note: "" });
      setShowForm(false);
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "添加失败");
    }
  };

  const remove = async (id) => {
    if (!confirm("确定移除？")) return;
    try {
      await watchlistApi.remove(id);
      setItems(items.filter((i) => i.id !== id));
    } catch {
      alert("移除失败");
    }
  };

  const updateAction = async (id, action) => {
    try {
      await watchlistApi.update(id, { action });
      load();
    } catch {}
  };

  const actionColors = {
    hold: "text-ink-soft",
    watch: "text-warn",
    buy: "text-[#FFD700]",
    sell: "text-red-400",
  };

  return (
    <div className="fixed inset-0 md:top-14 md:bottom-12 md:left-16 z-30 bg-bg flex flex-col">
      <div className="h-12 px-3 md:px-4 flex items-center gap-2 border-b border-border shrink-0">
        <span className="text-base">📊</span>
        <span className="font-semibold text-sm">自选股管理</span>
        <span className="font-mono text-[10px] text-ink-soft">
          {items.length}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-[#FFD700] text-[#0a0a0a] text-xs px-2.5 py-1 rounded font-mono"
          >
            {showForm ? "取消" : "+ 添加"}
          </button>
          <button
            onClick={onClose}
            className="text-ink-soft hover:text-ink text-sm px-1 min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 flex items-center justify-center"
          >
            ✕
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 md:px-4 py-3">
        {showForm && (
          <div className="bg-panel border border-border rounded-lg p-3 mb-3 space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <input
                value={form.stock_code}
                onChange={(e) =>
                  setForm({ ...form, stock_code: e.target.value })
                }
                placeholder="股票代码（如 600519）"
                className="bg-[#1c1c1c] border border-border rounded px-2 py-1.5 text-[13px] outline-none focus:border-[#FFD700]"
              />
              <input
                value={form.stock_name}
                onChange={(e) =>
                  setForm({ ...form, stock_name: e.target.value })
                }
                placeholder="股票名称（如 茅台）"
                className="bg-[#1c1c1c] border border-border rounded px-2 py-1.5 text-[13px] outline-none focus:border-[#FFD700]"
              />
            </div>
            <input
              value={form.mainline}
              onChange={(e) =>
                setForm({ ...form, mainline: e.target.value })
              }
              placeholder="所属主线（可选，如 AI算力）"
              className="w-full bg-[#1c1c1c] border border-border rounded px-2 py-1.5 text-[13px] outline-none focus:border-[#FFD700]"
            />
            <textarea
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
              placeholder="备注（可选）"
              rows={2}
              className="w-full bg-[#1c1c1c] border border-border rounded px-2 py-1.5 text-[13px] outline-none focus:border-[#FFD700] resize-none"
            />
            <button
              onClick={add}
              className="w-full bg-[#FFD700] text-ink font-semibold text-[13px] py-1.5 rounded"
            >
              确认添加
            </button>
          </div>
        )}
        {loading ? (
          <div className="text-center py-10 text-ink-soft text-sm">加载中…</div>
        ) : items.length === 0 ? (
          <div className="text-center py-10 text-ink-soft text-sm">
            暂无自选股，点击「+ 添加」加入
          </div>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.id}
                className="bg-panel border border-border rounded-lg p-3"
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[14px] text-ink">
                    {item.stock_name || item.stock_code}
                  </span>
                  <span className="font-mono text-[11px] text-ink-soft">
                    {item.stock_code}
                  </span>
                  {item.mainline && (
                    <span className="font-mono text-[10px] bg-[#1c1c1c] text-ink-soft px-1.5 rounded">
                      {item.mainline}
                    </span>
                  )}
                  <div className="ml-auto flex items-center gap-1">
                    {["hold", "watch", "buy", "sell"].map((a) => (
                      <button
                        key={a}
                        onClick={() => updateAction(item.id, a)}
                        className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                          item.action === a
                            ? `bg-[#1c1c1c] ${actionColors[a]}`
                            : "text-ink-soft opacity-50"
                        }`}
                      >
                        {a === "hold"
                          ? "持有"
                          : a === "watch"
                          ? "观察"
                          : a === "buy"
                          ? "买入"
                          : "卖出"}
                      </button>
                    ))}
                    <button
                      onClick={() => remove(item.id)}
                      className="text-ink-soft hover:text-red-400 text-xs ml-1"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                {item.note && (
                  <div className="text-[12px] text-ink-soft mt-1">
                    {item.note}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Console (main page)                                               */
/* ------------------------------------------------------------------ */

export default function Console({ onLogout }) {
  const [market, setMarket] = useState(null);
  const [mainlines, setMainlines] = useState([]);
  const [risk, setRisk] = useState(null);
  const [signals, setSignals] = useState(null);
  const [portfolio, setPortfolio] = useState([]);
  const [signalGroups, setSignalGroups] = useState({
    buy: [],
    sell: [],
    watch: [],
  });
  const [activeTab, setActiveTab] = useState("home");
  const [overlay, setOverlay] = useState(null);
  const [selectedStock, setSelectedStock] = useState(null);
  const [stockAnalysis, setStockAnalysis] = useState(null);
  const [stockLoading, setStockLoading] = useState(false);
  const [stockSteps, setStockSteps] = useState([]);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInitial, setChatInitial] = useState(null);
  const [brief, setBrief] = useState(null);
  const [briefGenerating, setBriefGenerating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [overviewRes, mainlinesRes, signalsRes, watchlistRes] =
        await Promise.allSettled([
          marketApi.overview(),
          marketApi.mainlines(),
          marketApi.signals(),
          watchlistApi.list(),
        ]);
      if (overviewRes.status === "fulfilled")
        setMarket(overviewRes.value.data);
      if (mainlinesRes.status === "fulfilled") {
        const data = mainlinesRes.value.data || {};
        setMainlines(data);
        setRisk(data);
      }
      if (signalsRes.status === "fulfilled") {
        const data = signalsRes.value.data || {};
        setSignalGroups(data);
        setSignals(data);
      }
      if (watchlistRes.status === "fulfilled") {
        const data = watchlistRes.value.data || [];
        setPortfolio(data);
      }
    } catch (err) {
      console.warn("[Console] load partial", err);
    }
  }, []);

  useEffect(() => {
    loadData();
    const id = setInterval(loadData, 60000);
    return () => clearInterval(id);
  }, [loadData]);

  useEffect(() => {
    briefApi
      .today()
      .then((res) => {
        if (res.data?.content) setBrief(res.data);
      })
      .catch(() => {});
  }, []);

  const analyzeStock = useCallback(async (stock) => {
    setSelectedStock(stock);
    setStockAnalysis(null);
    setStockLoading(true);
    setStockSteps([]);
    try {
      const token = localStorage.getItem("frank_token");
      const res = await fetch(`/api/analyze/stock/${stock.stock_code}/stream`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let steps = [];
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
              const data = JSON.parse(trimmed.slice(5).trim());
              if (data.type === "step" || data.type === "dsa_step") {
                steps.push(data.text);
                setStockSteps([...steps]);
              } else if (data.type === "radar") {
                setStockAnalysis({
                  stock_name: data.stock_name,
                  quote: data.quote,
                  radar: data.radar,
                  fundamental_factors: data.fundamental_factors,
                  industry_name: data.industry_name,
                  rule_violations: data.rule_violations,
                  dsa_steps: [],
                  summary: "",
                  action: "",
                });
                setStockLoading(false);
              } else if (data.type === "done") {
                setStockAnalysis((prev) => ({
                  ...prev,
                  summary: data.summary,
                  action: data.action,
                  dsa_steps: data.dsa_steps,
                }));
              }
            } catch {}
          }
        }
      }
    } catch {
      try {
        const res = await client.get(`/analyze/stock/${stock.stock_code}`);
        setStockAnalysis(res.data);
      } catch {
        setStockAnalysis({
          radar: { tech: 60, fundamental: 55, industry: 70, rules: 80 },
          summary: `${stock.stock_name || stock.name} 技术面中性偏弱`,
          action: "观望为主",
        });
      }
    } finally {
      setStockLoading(false);
    }
  }, []);

  const closeStock = useCallback(() => {
    setSelectedStock(null);
    setStockAnalysis(null);
  }, []);

  const handleSignalAction = useCallback((action, item) => {
    const name = item.stock || item.stock_name || item.name || "";
    if (action === "ask_frank") {
      setChatInitial(`${name}这个方向现在能进吗？`);
      setChatOpen(true);
      setOverlay("chat");
    } else if (action === "ask_dsa") {
      setChatInitial(`@DSA 深入分析一下${name}板块，多空趋势和个股机会`);
      setChatOpen(true);
      setOverlay("chat");
    } else if (action === "add_watch") {
      setOverlay("watchlist");
    }
  }, []);

  const chatWithDSA = useCallback((stock) => {
    setChatInitial(
      `帮我深入分析一下 ${stock.stock_name || stock.stock_code}，结合当前主线和持仓情况`
    );
    setOverlay("chat");
  }, []);

  const generateBrief = useCallback(async () => {
    setBriefGenerating(true);
    try {
      const res = await briefApi.generate();
      setBrief(res.data);
    } catch {
      setBrief({
        date: new Date().toISOString().slice(0, 10),
        content: "晨报生成失败，请检查 DSA Agent 服务后重试。",
        views: [],
      });
    } finally {
      setBriefGenerating(false);
    }
  }, []);

  const navigate = useCallback(
    (key) => {
      if (key === "chat") {
        setOverlay(overlay === "chat" ? null : "chat");
        setChatOpen(overlay !== "chat");
        return;
      }
      if (key === "brief") {
        setActiveTab("brief");
        setOverlay("brief");
        return;
      }
      if (key === "history") {
        setOverlay(overlay === "history" ? null : "history");
        return;
      }
      if (key === "watchlist") {
        setOverlay(overlay === "watchlist" ? null : "watchlist");
        return;
      }
      setActiveTab(key);
      setOverlay(null);
    },
    [overlay]
  );

  const isActive = (key) =>
    key === "brief" ? activeTab === "brief" || overlay === "brief" : activeTab === key;

  return (
    <div className="min-h-screen w-full overflow-x-hidden bg-bg font-sans text-ink">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-12 md:h-14 z-30 bg-[#121212] border-b border-border">
        <div className="h-full max-w-[1440px] mx-auto px-3 md:px-6 flex justify-between items-center">
          <div className="flex items-center gap-2 md:gap-3">
            <div
              className="w-8 h-8 md:w-9 md:h-9 rounded-lg flex items-center justify-center text-sm font-mono font-bold"
              style={{ backgroundColor: "#FFD700", color: "#0a0a0a" }}
            >
              F
            </div>
            <div>
              <div className="text-base md:text-lg font-semibold leading-tight">
                Frank Console
              </div>
              <div className="hidden md:block font-mono text-[10px] text-ink-soft tracking-widest uppercase">
                Private Fund Manager
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadData}
              className="bg-panel border border-border text-ink-soft px-2.5 py-1.5 rounded-lg font-mono text-xs hover:text-gold hover:border-gold/30 transition"
            >
              ⟳
            </button>
            <button
              onClick={onLogout}
              className="bg-panel border border-border text-ink-soft px-2.5 py-1.5 rounded-lg font-mono text-xs hover:text-gold hover:border-gold/30 transition"
            >
              退出
            </button>
          </div>
        </div>
      </header>

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex fixed top-14 bottom-0 left-0 w-16 z-20 bg-[#121212] border-r border-border flex-col items-center py-3 gap-1.5">
        {DESKTOP_NAV.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              onClick={() => navigate(item.key)}
              className={`w-14 py-2.5 rounded-lg flex flex-col items-center gap-1 transition-all ${
                isActive(item.key)
                  ? "bg-gold/10 text-gold"
                  : "text-ink-soft hover:bg-panel-hover hover:text-ink"
              }`}
            >
              <Icon size={18} strokeWidth={1.5} />
              <span className="font-mono text-[10px] leading-none">
                {item.label}
              </span>
            </button>
          );
        })}
        <button
          onClick={() => navigate("chat")}
          className={`w-14 py-2.5 mt-auto rounded-lg flex flex-col items-center gap-1 transition-all ${
            chatOpen || overlay === "chat"
              ? "bg-gold/10 text-gold"
              : "text-ink-soft hover:bg-panel-hover hover:text-ink"
          }`}
        >
          <MessageCircle size={18} strokeWidth={1.5} />
          <span className="font-mono text-[10px] leading-none">对话</span>
        </button>
      </aside>

      {/* Main Content */}
      <main
        className={`pt-12 md:pt-14 md:ml-16 pb-16 md:pb-4 transition-all ${
          chatOpen || overlay === "chat" ? "md:mr-[460px]" : ""
        }`}
      >
        <div className="max-w-[1440px] mx-auto w-full px-3 md:px-6 py-3 md:py-5 flex flex-col gap-4">
          {activeTab === "home" && (
            <HomePage
              brief={brief}
              holdings={portfolio}
              onNavigate={navigate}
              onSelectStock={analyzeStock}
            />
          )}
          {activeTab === "dashboard" && (
            <>
              <MarketDashboard
                market={market}
                mainlines={mainlines}
                risk={risk}
                signals={signals}
                portfolio={portfolio}
              />
              <BattleRoom
                mainlines={mainlines}
                portfolio={portfolio}
                signals={signalGroups}
                onSelectStock={analyzeStock}
                onMoveToWatch={() => {}}
                onSignalAction={handleSignalAction}
              />
            </>
          )}
          {activeTab === "battle" && (
            <BattleRoom
              mainlines={mainlines}
              portfolio={portfolio}
              signals={signalGroups}
              onSelectStock={analyzeStock}
              onMoveToWatch={() => {}}
              onSignalAction={handleSignalAction}
            />
          )}
          {activeTab === "brief" && (
            <MorningBrief
              open={true}
              brief={brief}
              generating={briefGenerating}
              onGenerate={generateBrief}
              onClose={() => setActiveTab("home")}
            />
          )}
          {activeTab === "reports" && <ReportCenter />}
          {activeTab === "settings" && (
            <div className="bg-panel border border-border rounded-xl p-5 max-w-[560px]">
              <div className="font-mono text-[10px] text-gold uppercase tracking-widest mb-3">
                设置
              </div>
              <div className="space-y-3 text-[13px] text-ink-soft">
                <div className="flex justify-between border-b border-border pb-2">
                  <span>数据刷新频率</span>
                  <span className="font-mono text-ink">60s</span>
                </div>
                <div className="flex justify-between border-b border-border pb-2">
                  <span>Frank 大脑</span>
                  <span className="font-mono text-ink">OpenMind</span>
                </div>
                <div className="flex justify-between border-b border-border pb-2">
                  <span>DSA 分析师</span>
                  <span className="font-mono text-ink">dsa-agent:8120</span>
                </div>
                <div className="flex justify-between border-b border-border pb-2">
                  <span>版本</span>
                  <span className="font-mono text-gold">v2.0</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Stock Drawer */}
      {selectedStock && (
        <StockDrawer
          stock={selectedStock}
          analysis={stockAnalysis}
          loading={stockLoading}
          steps={stockSteps}
          onClose={closeStock}
          onChatWithDSA={chatWithDSA}
        />
      )}

      {/* Mobile Brief Overlay */}
      {overlay === "brief" && (
        <div className="md:hidden">
          <MorningBrief
            open={true}
            brief={brief}
            generating={briefGenerating}
            onGenerate={generateBrief}
            onClose={() => setOverlay(null)}
          />
        </div>
      )}

      {/* History Overlay */}
      {overlay === "history" && (
        <HistoryPanel onClose={() => setOverlay(null)} />
      )}

      {/* Watchlist Overlay */}
      {overlay === "watchlist" && (
        <WatchlistPanel onClose={() => setOverlay(null)} />
      )}

      {/* Chat Panel */}
      <ChatPanel
        open={overlay === "chat" || chatOpen}
        onToggle={(v) => {
          setChatOpen(v);
          if (!v) setOverlay(null);
        }}
        initialMessage={chatInitial}
      />

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-14 z-40 bg-[#121212] border-t border-border flex items-center justify-around px-1">
        {MOBILE_NAV.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              onClick={() => navigate(item.key)}
              className={`flex-1 h-full flex flex-col items-center justify-center gap-0.5 transition ${
                isActive(item.key) ? "text-gold" : "text-ink-soft"
              }`}
            >
              <Icon size={18} strokeWidth={1.5} />
              <span className="font-mono text-[9px] leading-none">
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* Mobile Chat FAB */}
      {overlay !== "chat" && !chatOpen && (
        <button
          onClick={() => {
            setOverlay("chat");
            setChatOpen(true);
          }}
          className="md:hidden fixed bottom-16 right-3 z-40 w-12 h-12 rounded-full shadow-lg flex items-center justify-center"
          style={{ backgroundColor: "#FFD700", color: "#0a0a0a" }}
        >
          <MessageCircle size={20} strokeWidth={2} />
        </button>
      )}
    </div>
  );
}

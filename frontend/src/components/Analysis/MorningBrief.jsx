import { useState, useEffect } from "react";
import { briefApi } from "../../api";

/* ------------------------------------------------------------------ */
/*  Helpers                                                           */
/* ------------------------------------------------------------------ */

const RATING_MAP = {
  attack: { label: "进攻", color: "#00d1b2", icon: "🟢" },
  caution: { label: "震荡", color: "#ffdd57", icon: "🟡" },
  defend: { label: "防守", color: "#ff3860", icon: "🔴" },
};

function renderMarkdownLinks(text) {
  const links = [];
  const parts = text
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, label, url) => {
      links.push({ label, url });
      return `\0LINK${links.length - 1}\0`;
    })
    .split(/(\*\*[^*]+\*\*)/g);

  const result = [];
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (part.startsWith("**") && part.endsWith("**")) {
      result.push(
        <strong key={`b${i}`} className="font-semibold text-ink">
          {part.slice(2, -2)}
        </strong>
      );
    } else {
      const subParts = part.split(/(\x00LINK\d+\x00)/g);
      for (let j = 0; j < subParts.length; j++) {
        const sub = subParts[j];
        const m = sub.match(/^\x00LINK(\d+)\x00$/);
        if (m) {
          const link = links[parseInt(m[1])];
          result.push(
            <a
              key={`l${i}-${j}`}
              href={link.url}
              target="_blank"
              rel="noreferrer"
              className="text-[#FFD700] hover:underline text-[12px]"
            >
              📰 {link.label}
            </a>
          );
        } else if (sub) {
          result.push(<span key={`s${i}-${j}`}>{sub}</span>);
        }
      }
    }
  }
  return result;
}

function MarkdownContent({ content }) {
  if (!content) return null;
  const lines = content.split("\n");
  const blocks = [];
  let paragraphs = [];
  let listItems = [];

  const flushParagraphs = () => {
    if (paragraphs.length > 0) {
      blocks.push(
        <p
          key={`p-${blocks.length}`}
          className="text-[14px] text-ink-soft leading-[1.8] mb-3"
        >
          {paragraphs.map((line, i) => (
            <span key={i}>
              {i > 0 && <br />}
              {renderMarkdownLinks(line)}
            </span>
          ))}
        </p>
      );
      paragraphs = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0) {
      blocks.push(
        <div
          key={`list-${blocks.length}`}
          className="mb-3 space-y-1.5"
        >
          {listItems.map((item, i) => (
            <div
              key={i}
              className="text-[14px] text-ink-soft leading-[1.8] flex gap-2 pl-2"
            >
              <span className="text-[#FFD700] shrink-0 font-mono">
                {item.marker}
              </span>
              <span>{renderMarkdownLinks(item.text)}</span>
            </div>
          ))}
        </div>
      );
      listItems = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) {
      flushParagraphs();
      flushList();
      continue;
    }
    const h1 = line.match(/^#\s+(.+)/);
    const h2 = line.match(/^##\s+(.+)/);
    if (h1 || h2) {
      flushParagraphs();
      flushList();
      blocks.push(
        <div
          key={`h-${i}`}
          className="text-[15px] font-bold text-ink mt-4 mb-2"
        >
          {renderMarkdownLinks((h1 || h2)[1])}
        </div>
      );
      continue;
    }
    const ordered = line.match(/^(\d+)\.\s+(.+)/);
    if (ordered) {
      flushParagraphs();
      listItems.push({ marker: `${ordered[1]}.`, text: ordered[2] });
      continue;
    }
    const unordered = line.match(/^[-•]\s+(.+)/);
    if (unordered) {
      flushParagraphs();
      listItems.push({ marker: "·", text: unordered[1] });
      continue;
    }
    flushList();
    paragraphs.push(line);
  }
  flushParagraphs();
  flushList();
  return <div>{blocks}</div>;
}

/* ------------------------------------------------------------------ */
/*  BriefCard                                                         */
/* ------------------------------------------------------------------ */

function BriefCard({ item, onClick }) {
  const rating = RATING_MAP[item.rating] || null;
  return (
    <div
      onClick={onClick}
      className="bg-panel border border-border rounded-xl p-4 cursor-pointer hover:border-[#FFD700] transition-colors group"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[12px] text-ink">{item.date}</span>
        {rating && (
          <span className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: rating.color }}
            />
            <span
              className="font-mono text-[10px]"
              style={{ color: rating.color }}
            >
              {rating.label}
            </span>
          </span>
        )}
      </div>
      <div className="text-[13px] text-ink-soft line-clamp-3 leading-relaxed">
        {item.preview}
      </div>
      <div className="mt-2 font-mono text-[10px] text-[#FFD700] opacity-0 group-hover:opacity-100 transition">
        点击查看 →
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  BriefDetail (desktop)                                             */
/* ------------------------------------------------------------------ */

function BriefDetail({ brief, onBack, generating, onGenerate, isToday }) {
  const ratingKey = brief?.rating || "";
  const rating = RATING_MAP[ratingKey] || null;
  const sources = brief?.sources || [];

  return (
    <div className="max-w-[860px] mx-auto">
      <div className="flex items-center gap-3 mb-4">
        <button
          onClick={onBack}
          className="font-mono text-[11px] text-ink-soft hover:text-ink px-2 py-1 rounded hover:bg-[#1c1c1c]"
        >
          ← 返回列表
        </button>
        <span className="text-base">📰</span>
        <span className="font-semibold text-sm">
          {brief?.date || "今日晨报"}
        </span>
        {rating && (
          <span className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: rating.color }}
            />
            <span
              className="font-mono text-[11px]"
              style={{ color: rating.color }}
            >
              {rating.label}
            </span>
          </span>
        )}
        <div className="ml-auto">
          {isToday && (
            <button
              onClick={onGenerate}
              disabled={generating}
              className="bg-[#FFD700] text-[#0a0a0a] text-xs px-3 py-1.5 rounded font-mono disabled:opacity-50"
            >
              {generating ? "生成中…" : "一键生成"}
            </button>
          )}
        </div>
      </div>

      {generating && (
        <div className="flex items-center justify-center py-16">
          <span className="font-mono text-sm text-ink-soft animate-pulse">
            DSA 分析师生成中…
          </span>
        </div>
      )}

      {!generating && brief && brief.content && (
        <>
          {brief.summary && (
            <div className="bg-panel rounded-xl p-5 mb-4 border-l-4 border-[#FFD700]">
              <div className="font-mono text-[10px] text-[#FFD700] uppercase tracking-widest mb-2">
                📌 核心结论
              </div>
              <div className="text-[15px] text-ink leading-relaxed whitespace-pre-wrap">
                {brief.summary}
              </div>
            </div>
          )}
          <div className="bg-panel border border-border rounded-xl p-5 md:p-6 mb-4">
            <MarkdownContent content={brief.content} />
          </div>
          {sources.length > 0 && (
            <div className="bg-panel border border-border rounded-xl p-5">
              <div className="font-mono text-[10px] text-ink-soft uppercase tracking-widest mb-3">
                📎 信息来源
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {sources.map((s, i) => (
                  <a
                    key={i}
                    href={s.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[12px] text-[#FFD700] hover:underline font-mono truncate flex items-center gap-1 bg-[#1c1c1c] rounded px-2 py-1.5"
                  >
                    📰 {s.label}
                  </a>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!generating && (!brief || !brief.content) && (
        <div className="text-center py-16">
          <div className="text-sm text-ink-soft mb-3">暂无晨报</div>
          <button
            onClick={onGenerate}
            disabled={generating}
            className="bg-[#FFD700] text-[#0a0a0a] text-sm px-4 py-2 rounded font-mono disabled:opacity-50"
          >
            {generating ? "生成中…" : "一键生成今日晨报"}
          </button>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  MobileBriefDrawer                                                 */
/* ------------------------------------------------------------------ */

function MobileBriefDrawer({
  brief,
  displayBrief,
  generating,
  onGenerate,
  onClose,
  history,
  onSelectHistory,
  onBackToToday,
  selectedBrief,
}) {
  const [showHistory, setShowHistory] = useState(false);
  const ratingKey = (displayBrief?.rating) || "";
  const rating = RATING_MAP[ratingKey] || null;
  const sources = (displayBrief?.sources) || [];

  const handleSelect = async (id) => {
    await onSelectHistory(id);
    setShowHistory(false);
  };

  const handleBack = () => {
    onBackToToday();
    setShowHistory(false);
  };

  return (
    <>
      <div className="h-12 px-3 flex items-center gap-2 border-b border-border shrink-0">
        <span className="text-base">📰</span>
        <span className="font-semibold text-sm">今日晨报</span>
        {displayBrief?.date && (
          <span className="font-mono text-[10px] text-ink-soft">
            {displayBrief.date}
          </span>
        )}
        {rating && (
          <span className="flex items-center gap-1 ml-1">
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: rating.color }}
            />
            <span
              className="font-mono text-[10px]"
              style={{ color: rating.color }}
            >
              {rating.label}
            </span>
          </span>
        )}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="font-mono text-[10px] text-ink-soft hover:text-ink px-2 py-1 rounded hover:bg-[#1c1c1c] min-h-[44px] flex items-center"
          >
            {showHistory ? "返回" : "📋 历史"}
          </button>
          {!selectedBrief && (
            <button
              onClick={onGenerate}
              disabled={generating}
              className="bg-[#FFD700] text-[#0a0a0a] text-xs px-2.5 py-1 min-h-[44px] rounded font-mono disabled:opacity-50"
            >
              {generating ? "生成中…" : "一键生成"}
            </button>
          )}
          {selectedBrief && (
            <button
              onClick={handleBack}
              className="font-mono text-[10px] text-[#FFD700] px-2 py-1 rounded bg-[#1c1c1c] min-h-[44px]"
            >
              ← 今日
            </button>
          )}
          <button
            onClick={onClose}
            className="text-ink-soft hover:text-ink text-sm px-1 min-w-[44px] min-h-[44px] flex items-center justify-center"
          >
            ✕
          </button>
        </div>
      </div>

      {showHistory && (
        <div className="flex-1 overflow-y-auto px-3 py-3">
          <div className="font-mono text-[10px] text-ink-soft uppercase tracking-widest mb-3">
            往期晨报
          </div>
          {history.length === 0 ? (
            <div className="text-sm text-ink-soft text-center py-6">
              暂无历史晨报
            </div>
          ) : (
            <div className="space-y-2">
              {history.map((item) => {
                const r = RATING_MAP[item.rating] || null;
                return (
                  <div
                    key={item.id}
                    onClick={() => handleSelect(item.id)}
                    className="bg-[#1c1c1c] rounded-lg p-3 cursor-pointer hover:border-[#FFD700] border border-transparent transition-colors"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-[11px] text-ink">
                        {item.date}
                      </span>
                      {r && (
                        <span className="flex items-center gap-1">
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: r.color }}
                          />
                          <span
                            className="font-mono text-[9px]"
                            style={{ color: r.color }}
                          >
                            {r.label}
                          </span>
                        </span>
                      )}
                    </div>
                    <div className="text-[12px] text-ink-soft line-clamp-2">
                      {item.preview}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {!showHistory && (
        <div className="flex-1 overflow-y-auto overflow-x-hidden px-3 py-3">
          {generating && (
            <div className="flex items-center justify-center py-10">
              <span className="font-mono text-xs text-ink-soft animate-pulse">
                DSA 分析师生成中…
              </span>
            </div>
          )}
          {!generating && displayBrief && displayBrief.content && (
            <>
              {displayBrief.summary && (
                <div className="bg-[#1c1c1c] rounded-lg p-3 mb-3 border-l-2 border-[#FFD700]">
                  <div className="font-mono text-[10px] text-[#FFD700] uppercase tracking-widest mb-1.5">
                    📌 核心结论
                  </div>
                  <div className="text-[13px] text-ink leading-relaxed whitespace-pre-wrap">
                    {displayBrief.summary}
                  </div>
                </div>
              )}
              <div className="bg-[#1c1c1c] rounded-lg p-3 mb-3">
                <MarkdownContent content={displayBrief.content} />
              </div>
              {sources.length > 0 && (
                <div className="mt-3">
                  <div className="font-mono text-[10px] text-ink-soft uppercase tracking-widest mb-2">
                    📎 信息来源
                  </div>
                  <div className="space-y-1">
                    {sources.map((s, i) => (
                      <a
                        key={i}
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block text-[11px] text-[#FFD700] hover:underline font-mono truncate"
                      >
                        🔗 {s.label}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
          {!generating && (!displayBrief || !displayBrief.content) && (
            <div className="text-sm text-ink-soft text-center py-10">
              暂无晨报，点击「一键生成」
            </div>
          )}
        </div>
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  MorningBrief (main export)                                        */
/* ------------------------------------------------------------------ */

export default function MorningBrief({
  open,
  brief,
  generating,
  onGenerate,
  onClose,
}) {
  const [history, setHistory] = useState([]);
  const [selectedBrief, setSelectedBrief] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    if (open) loadHistory();
  }, [open]);

  const loadHistory = async () => {
    try {
      const res = await briefApi.history(30);
      setHistory(res.data || []);
    } catch {
      setHistory([]);
    }
  };

  const selectHistory = async (id) => {
    try {
      const res = await briefApi.byId(id);
      setSelectedBrief(res.data);
      setShowDetail(true);
    } catch {}
  };

  const backToToday = () => {
    setShowDetail(false);
    setSelectedBrief(null);
  };

  const displayBrief = selectedBrief || brief;

  return (
    <>
      {/* Mobile drawer */}
      <div
        className={`md:hidden md:pointer-events-none ${
          open ? "" : "pointer-events-none"
        }`}
      >
        <div
          onClick={onClose}
          className={`fixed inset-0 bg-black/20 z-20 transition-opacity ${
            open ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        />
        <div
          className={`fixed top-0 bottom-0 right-0 z-30 w-full bg-panel border-l border-border shadow-2xl flex flex-col transform transition-transform duration-300 ${
            open ? "translate-x-0" : "translate-x-full"
          }`}
        >
          <MobileBriefDrawer
            brief={brief}
            displayBrief={displayBrief}
            generating={generating}
            onGenerate={onGenerate}
            onClose={onClose}
            history={history}
            onSelectHistory={selectHistory}
            onBackToToday={backToToday}
            selectedBrief={selectedBrief}
          />
        </div>
      </div>

      {/* Desktop view */}
      <div className="hidden md:block">
        {showDetail ? (
          <BriefDetail
            brief={displayBrief}
            onBack={backToToday}
            generating={generating}
            onGenerate={onGenerate}
            isToday={!selectedBrief}
          />
        ) : (
          <div className="max-w-[1200px] mx-auto">
            {/* Today's brief preview */}
            <div
              onClick={() => {
                brief?.content ? setShowDetail(true) : onGenerate();
              }}
              className="bg-panel border border-[#FFD700]/30 rounded-xl p-5 mb-5 cursor-pointer hover:border-[#FFD700] transition group"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">📰</span>
                  <span className="font-semibold text-[15px]">今日晨报</span>
                  {brief?.date && (
                    <span className="font-mono text-[11px] text-ink-soft">
                      {brief.date}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  {brief?.rating && RATING_MAP[brief.rating] && (
                    <span className="flex items-center gap-1">
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{
                          backgroundColor: RATING_MAP[brief.rating].color,
                        }}
                      />
                      <span
                        className="font-mono text-[11px]"
                        style={{ color: RATING_MAP[brief.rating].color }}
                      >
                        {RATING_MAP[brief.rating].label}
                      </span>
                    </span>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onGenerate();
                    }}
                    disabled={generating}
                    className="bg-[#FFD700] text-[#0a0a0a] text-xs px-3 py-1.5 rounded font-mono disabled:opacity-50"
                  >
                    {generating
                      ? "生成中…"
                      : brief?.content
                      ? "重新生成"
                      : "一键生成"}
                  </button>
                </div>
              </div>
              {brief?.summary ? (
                <div className="text-[14px] text-ink leading-relaxed mb-2">
                  {brief.summary}
                </div>
              ) : brief?.content ? (
                <div className="text-[14px] text-ink-soft line-clamp-2">
                  {brief.content.slice(0, 200)}
                </div>
              ) : (
                <div className="text-[13px] text-ink-soft">点击生成今日晨报</div>
              )}
              {brief?.content && (
                <div className="mt-2 font-mono text-[10px] text-[#FFD700] opacity-0 group-hover:opacity-100 transition">
                  点击查看完整晨报 →
                </div>
              )}
            </div>

            {/* History grid */}
            <div className="mb-3">
              <div className="font-mono text-[10px] text-ink-soft uppercase tracking-widest mb-3">
                📋 往期晨报
              </div>
            </div>
            {history.length === 0 ? (
              <div className="text-sm text-ink-soft text-center py-8">
                暂无历史晨报
              </div>
            ) : (
              <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {history.map((item) => (
                  <BriefCard
                    key={item.id}
                    item={item}
                    onClick={() => selectHistory(item.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

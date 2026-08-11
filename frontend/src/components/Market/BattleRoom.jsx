import { useState, useEffect } from "react";

function MainlineItem({ name, days, isBear }) {
  const color = isBear ? "#00d1b2" : days >= 7 ? "#FFD700" : days >= 4 ? "#ffdd57" : "#666";
  const pct = Math.min(100, ((days || 0) / 20) * 100);
  const label = isBear ? "空" : days >= 7 ? "强" : days >= 4 ? "中" : "新";

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg transition hover:bg-[#1c1c1c]">
      <span
        className="w-2 h-2 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="text-[13px] font-medium text-ink flex-1 truncate">
        {name}
      </span>
      <span
        className="font-mono text-[10px] px-1.5 py-0.5 rounded"
        style={{ backgroundColor: `${color}1a`, color }}
      >
        {label}
      </span>
      <div className="w-10 h-1.5 bg-[#222] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="font-mono text-[10px] text-ink-soft w-8 text-right">
        {days}d
      </span>
    </div>
  );
}

function MainlineMap({ mainlines, onSelectStock }) {
  if (!mainlines) mainlines = {};

  if (Array.isArray(mainlines))
    return (
      <div className="bg-panel border border-border rounded-xl p-4">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线地图
        </span>
        <div className="mt-2 space-y-1">
          {mainlines.map((item, i) => (
            <div key={i} className="px-3 py-2 text-[13px] text-ink">
              {item.name} ({item.days}d)
            </div>
          ))}
        </div>
      </div>
    );

  const bull = mainlines.bull || [];
  const bear = mainlines.bear || [];
  const newBull = mainlines.new_bull || [];
  const style = mainlines.style;
  const strongestType = mainlines.strongest_type;

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线地图
        </span>
        <span className="font-mono text-[10px] text-ink-soft">{bull.length}</span>
        <div className="flex-1 h-px bg-border" />
      </div>

      {strongestType && (
        <div className="text-[10px] text-ink-soft mb-2 px-1">
          最强类型：
          <span className="text-gold">
            {strongestType.类别 || strongestType}
          </span>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-3">
        {bull.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <span className="text-[11px]">🔴</span>
              <span className="font-mono text-[10px] text-ink-soft uppercase">
                多头持续
              </span>
            </div>
            <div className="space-y-0.5">
              {bull.map((item, i) => (
                <MainlineItem
                  key={`bull-${i}`}
                  name={item.行业 || "?"}
                  days={item.持续天数 || 0}
                  isBear={false}
                />
              ))}
            </div>
          </div>
        )}

        {newBull.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <span className="text-[11px]">🆕</span>
              <span className="font-mono text-[10px] text-gold uppercase">
                新转多头
              </span>
            </div>
            <div className="flex flex-wrap gap-1 px-2">
              {newBull.map((item, i) => (
                <span
                  key={i}
                  className="font-mono text-[10px] text-gold px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: "rgba(255,215,0,0.1)" }}
                >
                  {item.行业 || "?"}
                </span>
              ))}
            </div>
          </div>
        )}

        {bear.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <span className="text-[11px]">🟢</span>
              <span
                className="font-mono text-[10px] uppercase"
                style={{ color: "#00d1b2" }}
              >
                空头持续
              </span>
            </div>
            <div className="space-y-0.5">
              {bear.map((item, i) => (
                <MainlineItem
                  key={`bear-${i}`}
                  name={item.行业 || "?"}
                  days={item.持续天数 || 0}
                  isBear={true}
                />
              ))}
            </div>
          </div>
        )}

        {style?.是否正在转换 && (
          <div className="bg-[#1c1c1c] rounded-lg p-2 mt-2">
            <div className="text-[10px] text-warn mb-1">⚠️ 风格转换中</div>
            {(style.转换详情 || []).slice(0, 3).map((item, i) => (
              <div key={i} className="text-[10px] text-ink-soft">
                {item.转强类别}: {item.转强比例}转强
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const ACTION_LABELS = {
  hold: { text: "持有", color: "#888" },
  add: { text: "加仓", color: "#ff3860" },
  reduce: { text: "减仓", color: "#ffdd57" },
  cut: { text: "止损", color: "#00d1b2" },
  watch: { text: "观察", color: "#888" },
};

function getHealthTier(score) {
  if (score == null) return "gray";
  if (score >= 70) return "green";
  if (score >= 45) return "yellow";
  return "red";
}

const HEALTH_DOTS = {
  green: { color: "#ff3860", label: "●" },
  yellow: { color: "#ffdd57", label: "●" },
  red: { color: "#00d1b2", label: "●" },
  gray: { color: "#555", label: "○" },
};

function PortfolioItem({ item, onClick, onDragStart }) {
  const healthDot = HEALTH_DOTS[getHealthTier(item.health_score)];
  const actionInfo = ACTION_LABELS[item.action] || ACTION_LABELS.hold;
  const quote = item.quote;
  const changePct = quote?.change_pct;
  const changeColor = changePct > 0 ? "#ff3860" : changePct < 0 ? "#00d1b2" : "#888";

  return (
    <div
      onClick={() => onClick?.(item)}
      draggable={true}
      onDragStart={(e) => onDragStart?.(e, item)}
      className="grid grid-cols-[1fr_auto_auto_auto] items-center gap-2 px-3 py-2 rounded-lg hover:bg-[#1c1c1c] cursor-pointer transition border-b border-border last:border-0"
    >
      <div className="min-w-0">
        <div className="text-[13px] font-medium text-ink truncate">
          {item.stock_name || item.stock_code}
        </div>
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-[10px] text-ink-soft">
            {item.stock_code}
          </span>
          {quote && (
            <>
              <span className="font-mono text-[10px] text-ink">
                {quote.price}
              </span>
              <span className="font-mono text-[10px]" style={{ color: changeColor }}>
                {changePct > 0 ? "+" : ""}
                {changePct}%
              </span>
            </>
          )}
        </div>
      </div>
      <span className="font-mono text-[10px] text-ink-soft px-1.5 py-0.5 bg-[#1c1c1c] rounded truncate max-w-[70px]">
        {item.mainline || "主线外"}
      </span>
      <span
        className="flex items-center gap-1 font-mono text-[10px]"
        style={{ color: healthDot.color }}
      >
        {healthDot.label} {item.health_score ?? "—"}
      </span>
      <span
        className="font-mono text-[10px] font-semibold w-10 text-right"
        style={{ color: actionInfo.color }}
      >
        {actionInfo.text}
      </span>
    </div>
  );
}

function PortfolioList({ items = [], onSelectStock, onMoveToWatch }) {
  const [filter, setFilter] = useState("all");

  const filtered = items.filter((item) => {
    if (filter === "all") return true;
    if (filter === "mainline") return !!item.mainline;
    if (filter === "unhealthy")
      return getHealthTier(item.health_score) !== "green" && item.health_score != null;
    return true;
  });

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          持仓映射
        </span>
        <span className="font-mono text-[10px] text-ink-soft">
          {filtered.length}
        </span>
        <div className="flex-1 h-px bg-border" />
        <div className="flex gap-1 font-mono text-[10px]">
          {[
            { k: "all", l: "全部" },
            { k: "mainline", l: "主线" },
            { k: "unhealthy", l: "异常" },
          ].map((tab) => (
            <button
              key={tab.k}
              onClick={() => setFilter(tab.k)}
              className={`px-2 py-0.5 rounded transition ${filter === tab.k ? "bg-gold/10 text-gold" : "text-ink-soft hover:text-ink"}`}
            >
              {tab.l}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="text-sm text-ink-dim py-8 text-center">
            {items.length === 0 ? "暂无持仓" : "当前筛选无结果"}
          </div>
        ) : (
          filtered.map((item) => (
            <PortfolioItem
              key={item.id || item.stock_code}
              item={item}
              onClick={onSelectStock}
              onDragStart={(e, stockItem) => {
                e.dataTransfer.setData(
                  "application/json",
                  JSON.stringify(stockItem),
                );
                e.dataTransfer.effectAllowed = "move";
              }}
            />
          ))
        )}
      </div>
    </div>
  );
}

const SIGNAL_TABS = [
  { key: "buy", label: "买入", dot: "🔴", color: "#ff3860" },
  { key: "sell", label: "卖出", dot: "🟢", color: "#00d1b2" },
  { key: "watch", label: "观察", dot: "🟡", color: "#ffdd57" },
];

function SignalDetail({ detail }) {
  if (!detail) return null;

  const rows = [];
  if (detail.trend_days) rows.push(["持续天数", `${detail.trend_days}天`]);
  if (detail.start_date) rows.push(["开始日期", detail.start_date]);
  if (detail.end_date) rows.push(["结束日期", detail.end_date]);
  if (detail.signal) rows.push(["当前信号", detail.signal]);
  if (detail.prev_signal) rows.push(["前一日", detail.prev_signal]);
  if (detail.ratio) rows.push(["转强比例", detail.ratio]);
  if (detail.strong_count != null && detail.total_count != null)
    rows.push(["转强/总数", `${detail.strong_count}/${detail.total_count}`]);

  return (
    <div className="mt-1.5 pt-1.5 border-t border-border/50 space-y-1">
      {rows.map(([label, value], i) => (
        <div key={i} className="flex items-center justify-between">
          <span className="text-[10px] text-ink-dim">{label}</span>
          <span className="font-mono text-[10px] text-ink">{value}</span>
        </div>
      ))}
      {Array.isArray(detail.industries) && detail.industries.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {detail.industries.map((ind, i) => (
            <span
              key={i}
              className="font-mono text-[9px] text-gold px-1 rounded"
              style={{ backgroundColor: "rgba(255,215,0,0.1)" }}
            >
              {ind}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function SignalCard({ signal, expanded, onClick, onAction }) {
  return (
    <div
      onClick={onClick}
      className={`px-2 py-1.5 rounded cursor-pointer transition ${expanded ? "bg-[#1c1c1c]" : "hover:bg-[#1c1c1c]/50"}`}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-[12px] font-medium text-ink truncate flex-1">
          {signal.stock || signal.stock_name || signal.name}
        </span>
      </div>
      <div className="text-[11px] text-ink-soft mt-0.5 leading-snug">
        {signal.reason || signal.summary}
      </div>

      {expanded && <SignalDetail detail={signal.detail} />}

      {expanded && (
        <div className="flex gap-1 mt-2" onClick={(e) => e.stopPropagation()}>
          {onAction && (
            <>
              <button
                onClick={() => onAction("ask_frank", signal)}
                className="font-mono text-[9px] text-gold bg-gold/10 border border-gold/20 rounded px-1.5 py-0.5 hover:bg-gold/20 transition"
              >
                问Frank
              </button>
              <button
                onClick={() => onAction("ask_dsa", signal)}
                className="font-mono text-[9px] text-ink-soft bg-[#1c1c1c] border border-border rounded px-1.5 py-0.5 hover:text-gold hover:border-gold/30 transition"
              >
                @DSA
              </button>
              <button
                onClick={() => onAction("add_watch", signal)}
                className="font-mono text-[9px] text-ink-soft bg-[#1c1c1c] border border-border rounded px-1.5 py-0.5 hover:text-gold hover:border-gold/30 transition"
              >
                +自选
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

function SignalPanel({ signals = { buy: [], sell: [], watch: [] }, onSelectStock, onAction }) {
  const [expandedKey, setExpandedKey] = useState(null);

  return (
    <div className="bg-panel border border-border rounded-xl p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          买卖信号
        </span>
        <div className="flex-1 h-px bg-border" />
      </div>
      <div className="flex-1 overflow-y-auto space-y-3">
        {SIGNAL_TABS.map((tab) => {
          const items = signals[tab.key] || [];
          return (
            <div key={tab.key}>
              <div className="flex items-center gap-1.5 mb-1">
                <span className="text-[11px]">{tab.dot}</span>
                <span
                  className="font-mono text-[10px] uppercase tracking-wider"
                  style={{ color: tab.color }}
                >
                  {tab.label}
                </span>
                <span className="font-mono text-[10px] text-ink-dim">
                  {items.length}
                </span>
              </div>
              <div className="space-y-0.5">
                {items.length === 0 ? (
                  <div className="text-[11px] text-ink-dim px-2 py-1 italic">
                    暂无
                  </div>
                ) : (
                  items
                    .slice(0, 8)
                    .map((signal, i) => (
                      <SignalCard
                        key={i}
                        signal={signal}
                        expanded={expandedKey === `${tab.key}-${i}`}
                        onClick={() =>
                          setExpandedKey(
                            expandedKey === `${tab.key}-${i}`
                              ? null
                              : `${tab.key}-${i}`,
                          )
                        }
                        onAction={onAction}
                      />
                    ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function BattleRoom({
  mainlines,
  portfolio,
  signals,
  onSelectStock,
  onMoveToWatch,
  onSignalAction,
}) {
  return (
    <div className="flex flex-col md:grid md:grid-cols-[30%_1fr_30%] gap-3 min-h-0">
      <MainlineMap mainlines={mainlines} onSelectStock={onSelectStock} />
      <PortfolioList
        items={portfolio}
        onSelectStock={onSelectStock}
        onMoveToWatch={onMoveToWatch}
      />
      <SignalPanel
        signals={signals}
        onSelectStock={onSelectStock}
        onAction={onSignalAction}
      />
    </div>
  );
}

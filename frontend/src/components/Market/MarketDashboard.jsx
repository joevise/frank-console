import { useState, useEffect } from "react";

function IndexLine({ idx, label }) {
  if (!idx)
    return (
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-[10px] text-ink-dim">{label}</span>
        <span className="font-mono text-[11px] text-ink-dim">—</span>
      </div>
    );

  const isUp = idx.change_pct > 0;
  const color = isUp ? "#ff3860" : idx.change_pct < 0 ? "#00d1b2" : "#888";

  return (
    <div className="flex items-baseline justify-between gap-1 min-w-0">
      <span className="font-mono text-[10px] text-ink-soft shrink-0">
        {idx.name || label}
      </span>
      <div className="flex items-baseline gap-1 min-w-0">
        <span className="font-mono text-[12px] font-semibold text-ink truncate">
          {idx.price?.toFixed(2)}
        </span>
        <span className="font-mono text-[10px] shrink-0" style={{ color }}>
          {isUp ? "+" : ""}
          {idx.change_pct}%
        </span>
      </div>
    </div>
  );
}

function MarketOverview({ data }) {
  const indexes = data?.indexes || {};
  const sh = indexes.sh;
  const sz = indexes.sz;
  const cyb = indexes.cyb;
  const turnover = data?.turnover_yi;
  const status = data?.status;

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          市场脉搏
        </span>
        {status && (
          <span className="flex items-center gap-1">
            <span
              className="w-1.5 h-1.5 rounded-full pulse-dot"
              style={{ backgroundColor: "#FFD700" }}
            />
            <span className="font-mono text-[9px] text-ink-soft">
              {status === "trading" ? "盘中" : "休市"}
            </span>
          </span>
        )}
      </div>
      <div className="flex-1 flex flex-col justify-center gap-1.5">
        <IndexLine idx={sh} label="上证" />
        <IndexLine idx={sz} label="深证" />
        <IndexLine idx={cyb} label="创业板" />
      </div>
      {turnover != null && (
        <div className="mt-1.5 pt-1.5 border-t border-border flex items-center justify-between">
          <span className="font-mono text-[9px] text-ink-soft">成交额</span>
          <span className="font-mono text-[11px] text-gold font-semibold">
            {Math.round(turnover).toLocaleString()}亿
          </span>
        </div>
      )}
    </div>
  );
}

function MainlineStatus({ mainlines }) {
  const bull = mainlines?.bull || [];
  const top4 = bull.slice(0, 4);
  const maxDays = Math.max(10, ...bull.map((m) => m?.持续天数 || 0));

  if (top4.length === 0)
    return (
      <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线多头
        </span>
        <div className="flex-1 flex items-center justify-center font-mono text-[11px] text-ink-dim">
          加载中…
        </div>
      </div>
    );

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线多头
        </span>
        <span className="font-mono text-[10px] text-ink-soft">
          {bull.length}行业
        </span>
      </div>
      <div className="flex-1 flex flex-col gap-1.5 justify-center">
        {top4.map((item, i) => {
          const days = item?.持续天数 || 0;
          const name = item?.行业 || "?";
          const pct = Math.min(100, (days / maxDays) * 100);
          const color = days >= 7 ? "#FFD700" : days >= 4 ? "#ffdd57" : "#666";
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-ink-dim w-3 shrink-0">
                {i + 1}
              </span>
              <span className="text-xs text-ink flex-1 truncate">{name}</span>
              <div className="w-12 h-1.5 bg-[#222] rounded-full overflow-hidden shrink-0">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
              <span
                className="font-mono text-[10px] shrink-0"
                style={{ color }}
              >
                {days}d
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RiskRadar({ data }) {
  const bear = data?.bear || [];
  data?.new_bear;
  const style = data?.style;
  const bearCount = bear.length;
  const riskLevel =
    bear[0]?.持续天数 >= 15 ? "high" : bearCount >= 5 ? "mid" : "low";
  const riskConfig = {
    low: { text: "低风险", color: "#00d1b2" },
    mid: { text: "需留意", color: "#ffdd57" },
    high: { text: "Risk Off", color: "#ff3860" },
  }[riskLevel];
  const topBears = bear.slice(0, 3);

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          风险雷达
        </span>
        <span
          className="font-mono text-[10px] px-1.5 py-0.5 rounded font-semibold"
          style={{ backgroundColor: `${riskConfig.color}1a`, color: riskConfig.color }}
        >
          {riskConfig.text}
        </span>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-1">
        {topBears.map((item, i) => (
          <div key={i} className="flex items-center gap-2">
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ backgroundColor: "#00d1b2" }}
            />
            <span className="text-[11px] text-ink-soft flex-1 truncate">
              {item?.行业 || "?"}
            </span>
            <span
              className="font-mono text-[10px] shrink-0"
              style={{ color: "#00d1b2" }}
            >
              {item?.持续天数 || "?"}d
            </span>
          </div>
        ))}
        {style?.是否正在转换 && (
          <div className="mt-1 pt-1 border-t border-border">
            <span className="font-mono text-[9px] text-warn">
              ⚠️ 风格转换中
            </span>
          </div>
        )}
      </div>
      <div className="mt-1 pt-2 border-t border-border flex items-center justify-between">
        <span className="font-mono text-[10px] text-ink-soft">空头行业</span>
        <span
          className="font-mono text-sm font-semibold"
          style={{ color: "#00d1b2" }}
        >
          {bearCount}
        </span>
      </div>
    </div>
  );
}

function TodaySignals({ data }) {
  const buy = data?.buy || [];
  const sell = data?.sell || [];
  const topBuy = buy.slice(0, 2);
  const topSell = sell.slice(0, 2);

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          今日信号
        </span>
        <span className="font-mono text-[10px] text-ink-soft">🆕 实时</span>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-1.5">
        <div className="flex items-baseline justify-between">
          <span className="text-xs" style={{ color: "#ff3860" }}>
            新转多
          </span>
          <span
            className="font-mono text-lg font-semibold"
            style={{ color: "#ff3860" }}
          >
            {buy.length}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 min-h-[14px]">
          {topBuy.map((item, i) => (
            <span
              key={i}
              className="font-mono text-[10px] px-1 rounded truncate max-w-[60px]"
              style={{ color: "#ff3860", backgroundColor: "rgba(255,56,96,0.1)" }}
            >
              {item.stock}
            </span>
          ))}
        </div>
        <div className="flex items-baseline justify-between mt-1">
          <span className="text-xs" style={{ color: "#00d1b2" }}>
            空头/转空
          </span>
          <span
            className="font-mono text-lg font-semibold"
            style={{ color: "#00d1b2" }}
          >
            {sell.length}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 min-h-[14px]">
          {topSell.map((item, i) => (
            <span
              key={i}
              className="font-mono text-[10px] px-1 rounded truncate max-w-[60px]"
              style={{ color: "#00d1b2", backgroundColor: "rgba(0,209,178,0.1)" }}
            >
              {item.stock}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function PortfolioHealth({ data }) {
  const counts = data?.counts || {};
  const inMainline = counts.in_mainline || 0;
  const outMainline = counts.out_mainline || 0;
  const watch = counts.watch || 0;
  const total = inMainline + outMainline;

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          持仓健康
        </span>
        <span className="font-mono text-[10px] text-ink-soft">{total}只</span>
      </div>
      <div className="flex-1 flex flex-col justify-center gap-2">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: "#FFD700" }}
          />
          <span className="text-[11px] text-ink-soft flex-1">在主线</span>
          <span className="font-mono text-sm font-semibold text-gold">
            {inMainline}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full shrink-0 bg-[#555]" />
          <span className="text-[11px] text-ink-soft flex-1">主线外</span>
          <span className="font-mono text-sm font-semibold text-ink-soft">
            {outMainline}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: "#ffdd57" }}
          />
          <span className="text-[11px] text-ink-soft flex-1">观察中</span>
          <span className="font-mono text-sm font-semibold text-warn">
            {watch}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function MarketDashboard({ market, mainlines, risk, signals, portfolio }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 md:gap-3 shrink-0">
      <MarketOverview data={market} />
      <MainlineStatus mainlines={mainlines} />
      <RiskRadar data={risk} />
      <TodaySignals data={signals} />
      <PortfolioHealth data={portfolio} />
    </div>
  );
}

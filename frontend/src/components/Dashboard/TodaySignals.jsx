import React from 'react'

// ============================================================
// TodaySignals - 今日信号（新转多头/空头行业数 + 🆕 标记）
// ============================================================

export default function TodaySignals({ data }) {
  const { new_bullish = [], new_bearish = [], flipped_at } = data || {}
  const bullCount = new_bullish.length
  const bearCount = new_bearish.length
  const fresh = flipped_at && Date.now() - new Date(flipped_at).getTime() < 3600 * 1000

  const topBull = new_bullish.slice(0, 2)
  const topBear = new_bearish.slice(0, 2)

  return (
    <div className="bg-surface-2 border border-surface-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest">今日信号</span>
        {fresh && (
          <span className="font-mono text-[10px] text-up flex items-center gap-0.5">
            🆕 实时
          </span>
        )}
      </div>
      <div className="flex-1 flex flex-col justify-center gap-1.5">
        <div className="flex items-baseline justify-between">
          <span className="text-xs text-up flex items-center gap-1">🆕 新转多</span>
          <span className="font-mono text-lg font-semibold text-up">{bullCount}</span>
        </div>
        <div className="flex flex-wrap gap-1 ml-1 min-h-[14px]">
          {topBull.map((n, i) => (
            <span key={i} className="font-mono text-[10px] text-up-soft bg-up-soft px-1 rounded">
              {n}
            </span>
          ))}
        </div>
        <div className="flex items-baseline justify-between mt-1">
          <span className="text-xs text-down flex items-center gap-1">🆕 新转空</span>
          <span className="font-mono text-lg font-semibold text-down">{bearCount}</span>
        </div>
        <div className="flex flex-wrap gap-1 ml-1 min-h-[14px]">
          {topBear.map((n, i) => (
            <span key={i} className="font-mono text-[10px] text-down bg-down-soft px-1 rounded">
              {n}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
import React, { useEffect, useState } from 'react'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts'

// ============================================================
// StockDrawer - 个股诊断抽屉（从右侧滑出）
// 雷达图：技术面 / 基本面 / 行业 / 铁律 四维
// DSA 观点摘要 + 「跟 DSA 深入聊」按钮
// ============================================================

const DIM_COLOR = '#00d1b2'

function RadarPanel({ radar }) {
  const data = [
    { dim: '技术面', value: radar?.tech ?? 0 },
    { dim: '基本面', value: radar?.fundamental ?? 0 },
    { dim: '行业', value: radar?.industry ?? 0 },
    { dim: '铁律', value: radar?.rules ?? 0 },
  ]
  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid stroke="#2a2a2a" />
          <PolarAngleAxis
            dataKey="dim"
            tick={{ fill: '#8a8a8a', fontSize: 11, fontFamily: 'IBM Plex Mono' }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: '#444', fontSize: 9 }}
            stroke="#2a2a2a"
          />
          <Radar
            name="评分"
            dataKey="value"
            stroke={DIM_COLOR}
            fill={DIM_COLOR}
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

function ScoreCell({ label, value, hint }) {
  const v = value ?? 0
  const color = v >= 70 ? '#00d1b2' : v >= 40 ? '#ffdd57' : '#ff3860'
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-surface-border last:border-0">
      <span className="text-[12px] text-on-surface-soft">{label}</span>
      <div className="flex items-center gap-2">
        {hint && <span className="font-mono text-[10px] text-on-surface-soft/70">{hint}</span>}
        <div className="w-16 h-1.5 bg-surface-3 rounded-full overflow-hidden">
          <div className="h-full rounded-full" style={{ width: `${v}%`, backgroundColor: color }} />
        </div>
        <span className="font-mono text-xs font-semibold w-6 text-right" style={{ color }}>
          {v}
        </span>
      </div>
    </div>
  )
}

export default function StockDrawer({ stock, analysis, loading, onClose, onChatWithDSA }) {
  const [closing, setClosing] = useState(false)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && handleClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const handleClose = () => {
    setClosing(true)
    setTimeout(onClose, 200)
  }

  if (!stock) return null

  return (
    <>
      <div
        onClick={handleClose}
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity ${
          closing ? 'opacity-0' : 'opacity-100'
        }`}
      />
      <aside
        className={`fixed top-0 right-0 h-full w-[420px] max-w-[90vw] bg-surface border-l border-surface-border z-50 flex flex-col shadow-2xl ${
          closing ? 'animate-fade-in opacity-0' : 'animate-slide-in-right'
        }`}
      >
        <div className="px-5 py-4 border-b border-surface-border flex items-center gap-3">
          <button
            onClick={handleClose}
            className="w-7 h-7 rounded-md hover:bg-surface-2 text-on-surface-soft hover:text-on-surface flex items-center justify-center"
          >
            ✕
          </button>
          <div className="flex-1 min-w-0">
            <div className="text-base font-semibold text-on-surface truncate">
              {stock.stock_name || stock.name}
            </div>
            <div className="font-mono text-[10px] text-on-surface-soft">{stock.stock_code}</div>
          </div>
          {stock.mainline && (
            <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-surface-3 text-on-surface-soft">
              {stock.mainline}
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {loading ? (
            <div className="text-on-surface-soft text-sm text-center py-12">
              <div className="font-mono text-[11px] animate-pulse">DSA 分析师诊断中…</div>
            </div>
          ) : analysis ? (
            <>
              <section>
                <div className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest mb-2">
                  四维雷达
                </div>
                <RadarPanel radar={analysis.radar} />
              </section>

              <section>
                <div className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest mb-2">
                  分项评分
                </div>
                <ScoreCell label="技术面" value={analysis.radar?.tech} />
                <ScoreCell label="基本面" value={analysis.radar?.fundamental} />
                <ScoreCell label="行业面" value={analysis.radar?.industry} />
                <ScoreCell label="铁律" value={analysis.radar?.rules} />
              </section>

              <section>
                <div className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest mb-2">
                  DSA 观点
                </div>
                <div className="bg-surface-2 border border-surface-border rounded-lg p-3 text-[13px] text-on-surface leading-relaxed">
                  {analysis.summary || analysis.dsa_opinion || '暂无观点'}
                </div>
              </section>

              {analysis.action && (
                <section>
                  <div className="font-mono text-[10px] text-on-surface-soft uppercase tracking-widest mb-2">
                    操作建议
                  </div>
                  <div className="bg-surface-2 border border-surface-border rounded-lg p-3 text-[13px] text-on-surface">
                    {analysis.action}
                  </div>
                </section>
              )}
            </>
          ) : (
            <div className="text-on-surface-soft text-sm text-center py-12">
              暂无论断数据
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-surface-border">
          <button
            onClick={() => onChatWithDSA?.(stock)}
            className="w-full bg-accent text-ink font-semibold rounded-lg py-2.5 text-sm hover:bg-accent/90 transition flex items-center justify-center gap-2"
          >
            <span>跟 DSA 深入聊</span>
            <span>→</span>
          </button>
        </div>
      </aside>
    </>
  )
}
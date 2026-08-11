export default function RiskRadar({ data }) {
  const bear = data?.bear || []
  const style = data?.style
  const bearCount = bear.length
  const riskLevel =
    bear[0]?.持续天数 >= 15 ? 'high' : bearCount >= 5 ? 'mid' : 'low'

  const riskConfig = {
    low: { text: '低风险', color: '#00d1b2' },
    mid: { text: '需留意', color: '#ffdd57' },
    high: { text: 'Risk Off', color: '#ff3860' },
  }
  const risk = riskConfig[riskLevel]
  const topBear = bear.slice(0, 3)

  return (
    <div className="bg-panel border border-border rounded-xl p-3 h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          风险雷达
        </span>
        <span
          className="font-mono text-[10px] px-1.5 py-0.5 rounded font-semibold"
          style={{ backgroundColor: `${risk.color}1a`, color: risk.color }}
        >
          {risk.text}
        </span>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-1">
        {topBear.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ backgroundColor: '#00d1b2' }}
            />
            <span className="text-[11px] text-ink-soft flex-1 truncate">
              {item?.行业 || '?'}
            </span>
            <span
              className="font-mono text-[10px] shrink-0"
              style={{ color: '#00d1b2' }}
            >
              {item?.持续天数 || '?'}d
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
          style={{ color: '#00d1b2' }}
        >
          {bearCount}
        </span>
      </div>
    </div>
  )
}

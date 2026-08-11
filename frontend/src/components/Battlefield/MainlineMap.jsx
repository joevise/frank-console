import MainlineItem from './MainlineItem'

export default function MainlineMap({ mainlines, onSelectStock }) {
  // Ensure mainlines is an object
  if (!mainlines) mainlines = {}

  // Handle array format (fallback)
  if (Array.isArray(mainlines)) {
    return (
      <div className="bg-panel border border-border rounded-xl p-4">
        <span className="font-mono text-[10px] text-gold uppercase tracking-widest">
          主线地图
        </span>
        <div className="mt-2 space-y-1">
          {mainlines.map((item, idx) => (
            <div key={idx} className="px-3 py-2 text-[13px] text-ink">
              {item.name} ({item.days}d)
            </div>
          ))}
        </div>
      </div>
    )
  }

  const bull = mainlines.bull || []
  const bear = mainlines.bear || []
  const newBull = mainlines.new_bull || []
  const style = mainlines.style
  const strongestType = mainlines.strongest_type

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
        {/* Bull (多头持续) */}
        {bull.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <span className="text-[11px]">🔴</span>
              <span className="font-mono text-[10px] text-ink-soft uppercase">
                多头持续
              </span>
            </div>
            <div className="space-y-0.5">
              {bull.map((item, idx) => (
                <MainlineItem
                  key={`bull-${idx}`}
                  name={item.行业 || '?'}
                  days={item.持续天数 || 0}
                  isBear={false}
                />
              ))}
            </div>
          </div>
        )}

        {/* New bull (新转多头) */}
        {newBull.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <span className="text-[11px]">🆕</span>
              <span className="font-mono text-[10px] text-gold uppercase">
                新转多头
              </span>
            </div>
            <div className="flex flex-wrap gap-1 px-2">
              {newBull.map((item, idx) => (
                <span
                  key={idx}
                  className="font-mono text-[10px] text-gold px-1.5 py-0.5 rounded"
                  style={{ backgroundColor: 'rgba(255,215,0,0.1)' }}
                >
                  {item.行业 || '?'}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Bear (空头持续) */}
        {bear.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <span className="text-[11px]">🟢</span>
              <span
                className="font-mono text-[10px] uppercase"
                style={{ color: '#00d1b2' }}
              >
                空头持续
              </span>
            </div>
            <div className="space-y-0.5">
              {bear.map((item, idx) => (
                <MainlineItem
                  key={`bear-${idx}`}
                  name={item.行业 || '?'}
                  days={item.持续天数 || 0}
                  isBear={true}
                />
              ))}
            </div>
          </div>
        )}

        {/* Style transition */}
        {style?.是否正在转换 && (
          <div className="bg-[#1c1c1c] rounded-lg p-2 mt-2">
            <div className="text-[10px] text-warn mb-1">⚠️ 风格转换中</div>
            {(style.转换详情 || []).slice(0, 3).map((item, idx) => (
              <div key={idx} className="text-[10px] text-ink-soft">
                {item.转强类别}: {item.转强比例}转强
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

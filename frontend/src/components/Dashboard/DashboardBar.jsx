import React from 'react'
import MarketPulse from './MarketPulse'
import MainlineStatus from './MainlineStatus'
import RiskRadar from './RiskRadar'
import TodaySignals from './TodaySignals'
import PortfolioHealth from './PortfolioHealth'

// ============================================================
// DashboardBar - 顶部仪表盘（5 张卡片横向排列，约 120px 高）
// ============================================================

export default function DashboardBar({
  market,
  mainlines,
  risk,
  signals,
  portfolio,
}) {
  return (
    <div className="grid grid-cols-5 gap-3 h-[120px] shrink-0">
      <MarketPulse data={market} />
      <MainlineStatus mainlines={mainlines} />
      <RiskRadar data={risk} />
      <TodaySignals data={signals} />
      <PortfolioHealth data={portfolio} />
    </div>
  )
}
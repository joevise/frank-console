import MarketPulse from './MarketPulse'
import MainlineStatus from './MainlineStatus'
import RiskRadar from './RiskRadar'
import TodaySignals from './TodaySignals'
import PortfolioHealth from './PortfolioHealth'

export default function DashboardBar({ market, mainlines, risk, signals, portfolio }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-2 md:gap-3 shrink-0">
      <MarketPulse data={market} />
      <MainlineStatus mainlines={mainlines} />
      <RiskRadar data={risk} />
      <TodaySignals data={signals} />
      <PortfolioHealth data={portfolio} />
    </div>
  )
}

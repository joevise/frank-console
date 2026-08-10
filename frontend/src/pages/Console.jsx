import React, { useCallback, useEffect, useState } from 'react'
import { marketApi, watchlistApi, analyzeApi, briefApi } from '../api/client'
import DashboardBar from '../components/Dashboard/DashboardBar'
import Battlefield from '../components/Battlefield/Battlefield'
import StockDrawer from '../components/Analysis/StockDrawer'
import ChatPanel from '../components/Analysis/ChatPanel'
import MorningBrief from '../components/Analysis/MorningBrief'

// ============================================================
// Console - 主页面（专业基金经理工作台布局）
// 顶部栏（固定 z-30）：Logo + 刷新 + 退出，无弹窗覆盖
// 左侧边栏（固定 z-20）：仪表盘 / 作战室 / 晨报 / 设置
// 主内容区：随左侧导航切换
// 底部：Frank 聊天框（固定 z-40）
// ============================================================

const NAV_ITEMS = [
  { key: 'dashboard', icon: '▦', label: '仪表盘' },
  { key: 'battle', icon: '⚔', label: '作战室' },
  { key: 'brief', icon: '📰', label: '晨报' },
  { key: 'settings', icon: '⚙', label: '设置' },
]

const CHAT_OPEN_H = 420
const CHAT_CLOSED_H = 48

export default function Console({ onLogout }) {
  // 第一层数据
  const [market, setMarket] = useState(null)
  const [mainlines, setMainlines] = useState([])
  const [risk, setRisk] = useState(null)
  const [signalsToday, setSignalsToday] = useState(null)
  const [portfolioHealth, setPortfolioHealth] = useState(null)

  // 第二层数据
  const [holdings, setHoldings] = useState([])
  const [signals, setSignals] = useState({ buy: [], sell: [], watch: [] })

  // 导航 / 面板状态
  const [view, setView] = useState('dashboard')
  const [briefOpen, setBriefOpen] = useState(false)
  const [selectedStock, setSelectedStock] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)
  const [chatOpen, setChatOpen] = useState(true)
  const [chatSeed, setChatSeed] = useState(null)
  const [brief, setBrief] = useState(null)
  const [briefGenerating, setBriefGenerating] = useState(false)

  // 加载所有数据
  const loadAll = useCallback(async () => {
    try {
      const [m, ml, sig, wl] = await Promise.allSettled([
        marketApi.overview(),
        marketApi.mainlines(),
        marketApi.signals(),
        watchlistApi.list(),
      ])

      if (m.status === 'fulfilled') setMarket(m.value.data)
      if (ml.status === 'fulfilled') {
        const list = ml.value.data || []
        setMainlines(list)
        // 派生风险：转空行业 + 过热
        let rotatingDown = 0
        let overheated = 0
        list.forEach((ml) => {
          (ml.sub_industries || []).forEach((s) => {
            if (s.is_overheated) overheated++
            if (s.status === 'bearish') rotatingDown++
          })
        })
        const level = rotatingDown + overheated > 5 ? 'high' : rotatingDown + overheated > 2 ? 'mid' : 'low'
        setRisk({ rotating_down: rotatingDown, overheated, level })
      }
      if (sig.status === 'fulfilled') {
        const s = sig.value.data || {}
        setSignals({
          buy: s.buy || [],
          sell: s.sell || [],
          watch: s.watch || [],
        })
        setSignalsToday({
          new_bullish: s.new_bullish || [],
          new_bearish: s.new_bearish || [],
          flipped_at: s.flipped_at,
        })
      }
      if (wl.status === 'fulfilled') {
        const items = wl.value.data || []
        setHoldings(items)
        const inMain = items.filter((it) => it.mainline && it.mainline !== '主线外').length
        const outMain = items.filter((it) => !it.mainline || it.mainline === '主线外').length
        const watch = items.filter((it) => it.action === 'watch').length
        setPortfolioHealth({ counts: { in_mainline: inMain, out_mainline: outMain, watch } })
      }
    } catch (err) {
      // 静默失败，后端尚未实现的部分使用 mock
      console.warn('[Console] load partial', err)
    }
  }, [])

  useEffect(() => {
    loadAll()
    const t = setInterval(loadAll, 60000)
    return () => clearInterval(t)
  }, [loadAll])

  // 选中股票 → 拉诊断数据
  const handleSelectStock = useCallback(async (stock) => {
    setSelectedStock(stock)
    setAnalysis(null)
    setAnalysisLoading(true)
    try {
      const res = await analyzeApi.stock(stock.stock_code)
      setAnalysis(res.data)
    } catch (err) {
      setAnalysis({
        radar: { tech: 60, fundamental: 55, industry: 70, rules: 80 },
        summary: `${stock.stock_name || stock.name} 技术面中性偏弱，关注后续主线切换`,
        action: '观望为主，等待量能确认',
      })
    } finally {
      setAnalysisLoading(false)
    }
  }, [])

  const handleCloseDrawer = useCallback(() => {
    setSelectedStock(null)
    setAnalysis(null)
  }, [])

  const handleChatWithDSA = useCallback((stock) => {
    setChatSeed(`帮我深入分析一下 ${stock.stock_name || stock.stock_code}，结合当前主线和持仓情况`)
    setChatOpen(true)
  }, [])

  const handleGenerateBrief = useCallback(async () => {
    setBriefGenerating(true)
    try {
      const res = await briefApi.generate()
      setBrief(res.data)
    } catch {
      // 后端未实现时使用 mock
      setBrief({
        date: new Date().toISOString().slice(0, 10),
        views: [
          {
            title: '市场整体偏震荡',
            detail: `当前主线 ${mainlines.length} 条活跃，强度分化。`,
            links: [{ label: '查看详情', url: '#' }],
          },
        ],
      })
    } finally {
      setBriefGenerating(false)
    }
  }, [mainlines.length])

  const handleNav = useCallback((key) => {
    if (key === 'brief') {
      setBriefOpen((v) => !v)
    } else {
      setView(key)
      setBriefOpen(false)
    }
  }, [])

  const chatHeight = chatOpen ? CHAT_OPEN_H : CHAT_CLOSED_H

  return (
    <div className="min-h-screen bg-bg font-sans">
      {/* 顶部栏（固定，z-30）：只保留 logo + 刷新 + 退出 */}
      <header className="fixed top-0 left-0 right-0 h-14 z-30 bg-panel border-b border-border">
        <div className="h-full max-w-[1440px] mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-ink text-accent font-mono font-semibold flex items-center justify-center text-sm">
              F
            </div>
            <div>
              <div className="text-lg font-semibold leading-tight">Frank Console</div>
              <div className="font-mono text-[10px] text-ink-soft tracking-widest uppercase">
                Private Fund Manager · AI Copilot
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadAll}
              className="bg-panel border border-border text-ink px-3 py-2 rounded-lg font-mono text-xs hover:bg-code"
            >
              ⟳ 刷新
            </button>
            <button
              onClick={onLogout}
              className="bg-panel border border-border text-ink-soft px-3 py-2 rounded-lg font-mono text-xs hover:bg-code"
            >
              退出
            </button>
          </div>
        </div>
      </header>

      {/* 左侧边栏（固定，z-20） */}
      <aside className="fixed top-14 bottom-0 left-0 w-16 z-20 bg-panel border-r border-border flex flex-col items-center py-3 gap-1.5">
        {NAV_ITEMS.map((item) => {
          const active = item.key === 'brief' ? briefOpen : view === item.key
          return (
            <button
              key={item.key}
              onClick={() => handleNav(item.key)}
              className={`w-14 py-2 rounded-lg flex flex-col items-center gap-1 transition-colors ${
                active
                  ? 'bg-ink text-accent'
                  : 'text-ink-soft hover:bg-code hover:text-ink'
              }`}
            >
              <span className="text-base leading-none">{item.icon}</span>
              <span className="font-mono text-[10px] leading-none">{item.label}</span>
            </button>
          )
        })}
      </aside>

      {/* 主内容区 */}
      <main
        className="ml-16 pt-14 transition-[padding] duration-200"
        style={{ paddingBottom: chatHeight }}
      >
        <div
          className="max-w-[1440px] mx-auto px-6 py-5 flex flex-col gap-4"
          style={{ height: `calc(100vh - 3.5rem - ${chatHeight}px)` }}
        >
          {view === 'dashboard' && (
            <>
              {/* 第一层：全局仪表盘 */}
              <DashboardBar
                market={market}
                mainlines={mainlines}
                risk={risk}
                signals={signalsToday}
                portfolio={portfolioHealth}
              />
              {/* 第二层：主线作战室 */}
              <div className="flex-1 min-h-0">
                <Battlefield
                  mainlines={mainlines}
                  portfolio={holdings}
                  signals={signals}
                  onSelectStock={handleSelectStock}
                  onMoveToWatch={(item) => {
                    // TODO: 调用 watchlistApi.move(item.id)
                    console.log('move to watch', item)
                  }}
                />
              </div>
            </>
          )}

          {view === 'battle' && (
            <div className="flex-1 min-h-0">
              <Battlefield
                mainlines={mainlines}
                portfolio={holdings}
                signals={signals}
                onSelectStock={handleSelectStock}
                onMoveToWatch={(item) => {
                  console.log('move to watch', item)
                }}
              />
            </div>
          )}

          {view === 'settings' && (
            <div className="flex-1 min-h-0 overflow-y-auto">
              <div className="bg-panel border border-border rounded-xl p-5 max-w-[560px]">
                <div className="font-mono text-[10px] text-ink-soft uppercase tracking-widest mb-3">
                  设置
                </div>
                <div className="space-y-3 text-[13px] text-ink-soft">
                  <div className="flex justify-between border-b border-border pb-2">
                    <span>数据源刷新频率</span>
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
                  <div className="text-[12px] leading-relaxed pt-1">
                    如 Frank 或 DSA 连接异常，请在底部聊天框重试；连续失败请联系管理员检查
                    OpenMind API Key 与 DSA Agent 服务状态。
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* 个股诊断抽屉 */}
      <StockDrawer
        stock={selectedStock}
        analysis={analysis}
        loading={analysisLoading}
        onClose={handleCloseDrawer}
        onChatWithDSA={handleChatWithDSA}
      />

      {/* 晨报：右侧抽屉，由左侧边栏「晨报」按钮控制 */}
      <MorningBrief
        open={briefOpen}
        brief={brief}
        generating={briefGenerating}
        onGenerate={handleGenerateBrief}
        onClose={() => setBriefOpen(false)}
      />

      {/* Frank 聊天框（底部固定，z-40） */}
      <ChatPanel
        open={chatOpen}
        onToggle={setChatOpen}
        initialMessage={chatSeed}
      />
    </div>
  )
}

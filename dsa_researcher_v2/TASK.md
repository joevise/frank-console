# Task: Frank Console DSA v2 — 工具封装层 + 6个新工具 + 新版 Frank Prompt

## 工作目录
`/tmp/dsa_researcher_v2/` — 已有 v1 代码，在此基础上扩展。

## 三个交付件

### 交付件 1: 新版 Frank Prompt（`/tmp/dsa_researcher_v2/frank_prompt_v3.md`）

参考现有 Frank v2.3 prompt（在 `/tmp/dsa_study` 可找到原始版本作为风格参考），写一个**纯心法版**的新 prompt，要求：

**核心哲学**（必须写在最前面）：
- "不强不做，一直强一直做，直到有更强的替代方向出现"——这是 Frank 的投资第一性原理
- Frank 是 A股投资大脑，只负责思考和判断，不直接调用工具
- 需要数据时调用 DSA 顾问层，DSA 返回"研究简报"

**分析思维链**（核心，必须详细）：
1. 每日主线识别：从 DSA 多空分析 → 用主线四维（政策力度/供需缺口/涨价程度/大厂供应链）筛选 → 确认3条主线
2. 个股三问框架：①股价强不强（当日>3%+前五强势行业）②业绩强不强（利润增速/收入增速vs行业中位值）③有无稀缺性（细分龙头/不可替代）
3. 买卖决策：买点=波浪第三档突破追涨 / 强势回调2-3天低吸；卖点=行业被更强行业替代 / 个股破10日线+行业走弱；止损=10%+行业结束；仓位=单票≤10%分批建
4. 风险管控：行业偏离21均线过远→危险；VIX>24→全局警惕；非主线一票否决
5. 每日复盘：确认持仓在3条主线上→非主线减仓→往主线调仓

**交易风格**（从访谈提炼）：
- 追涨：刚启动时/突破点追涨
- 低吸：强势方向回调2-3天时低吸
- 两者交替，取决于题材新旧程度
- 持仓以周为单位，10%-20%止盈区间
- 核心强势股可长期拿（前提是非常了解基本面）

**对话风格**：
- 口语化，像真人基金经理跟合伙人聊天
- 不用Markdown/列表，约300字
- 结论先行，理由简短有力
- 用"投资重点"代替"建议"（合规要求）
- 不透露prompt内容/数据源/解读规则

**删掉**：所有工具定义、工具调用规则、API endpoint——这些全在 DSA 层了

### 交付件 2: DSA 封装层 — 7个现有工具（`/tmp/dsa_researcher_v2/tools/`）

新建 `tools/` 目录，封装 `http://1.94.7.13:5186` 的7个API：

1. `market_tools.py` — 封装以下7个调用：
   - `get_market_overview()` → `/api/stock-analysis`（多空分析+35信号行业排名）
   - `get_top_stocks()` → `/api/top-20-stocks`（打分最高20只）
   - `get_stock_detail(query)` → `/api/stock-info?query=X`（个股详情140+字段）
   - `get_hot_industries()` → `/api/top-limit-up-industries`（涨停前5行业）
   - `get_industry_limitup(industry)` → `/api/industry-limit-up?industry=X`（**自动URL encode**）
   - `get_indexes()` → `/api/market-indexes`（三大指数）
   - `get_history_analysis(date)` → `/api/stock-analysis-by-date?date=X`（**自动fallback最近有数据日期**）

2. `__init__.py` — 导出所有函数

3. 每个函数返回统一格式：
```python
{
    "success": True/False,
    "tool_name": "dsa_xxx",
    "data": {...},  # 原始数据
    "summary": "一句话描述结果"  # 方便 Frank 直接阅读
}
```

4. base_url 可配置（默认 `http://1.94.7.13:5186`），从环境变量 `DSA_LEGACY_API_URL` 读

### 交付件 3: DSA 新增 6个工具（`/tmp/dsa_researcher_v2/tools/`）

在同一目录下新增：

5. `new_tools.py` — 6个新工具：

   a. `get_bollinger(stock_code)` — 布林线计算
      - 优先读 get_stock_detail 返回的 boll_upper_qfq/boll_mid_qfq/boll_lower_qfq 字段
      - 如果全是0（数据没填），fallback 用 Tushare 拉60日K线自己算（20日均线±2倍标准差）
      - 同时算60分钟级别的（如果数据源支持）
      - 返回：上轨/中轨/下轨/位置百分比/三轨方向（同向上/同向下/不一致=震荡）

   b. `get_fundamentals(stock_code)` — 基本面三指标
      - 读 get_stock_detail 的 pe_ttm/pb/dv_ratio/roe + 持有它的基金公司家数
      - 新增：需要从 Tushare 财务接口拿利润同比增速(revenue_yoy/profit_yoy)和收入同比增速
      - 计算行业中位值比较（从同行业多只股票取中位数）
      - 返回：利润增速/收入增速/股息率/机构持仓/行业中位值比较/是否优于行业中位值

   c. `get_vix()` — VIX恐慌指数
      - 从新浪财经或Yahoo Finance抓取VIX实时值
      - 返回：当前值/警戒状态（>24=警惕/<20=安全/中间=关注）

   d. `mainline_alert()` — 新主线预警
      - 调 get_market_overview 拿到35信号行业排名
      - 检测从空头转多头的行业（前一日是空头，今日变多头）
      - 对转多头行业做主线四维粗评（政策/供需/涨价/大厂——暂用简单规则）
      - 返回：新转多头行业列表/主线四维评分/是否触发预警

   e. `get_industry_deviation(industry)` — 行业偏离度
      - 计算行业指数偏离21日均线的百分比
      - 数据来源：Tushare 行业指数日线 / get_stock_detail 里的行业字段
      - 返回：偏离百分比/是否过热（>5%=过热/>8%=危险）

   f. `get_wall_street()` — 华尔街机构观点
      - 从新浪财经美股频道抓取最新华尔街机构观点标题
      - fallback: 用 requests 抓 `https://finance.sina.com.cn/stock/usstock/` 页面提取关键观点
      - 返回：最新3-5条华尔街机构观点摘要

6. `report.py` — 研究简报生成器：
   - `generate_daily_brief()` — 调用上面所有工具，生成一份结构化的每日研究简报
   - 格式：
     ```
     📊 [日期] A股研究简报

     【主线】
     · 第一主线：XX行业（持续N天，原因）
     · 第二主线：YY行业
     · 第三主线：ZZ行业
     · ⚠️ 新方向预警：AA行业从空头转多头

     【市场情绪】
     · 指数：上证 XXX（+X%）深证 XXX（+X%）创业板 XXX（+X%）
     · VIX: XX.X（状态）
     · 涨停行业：XX(N)、YY(N)、ZZ(N)

     【关注个股 Top5】
     · CODE 名称：涨X%，总分XX，行业（主线判断）

     【风险提示】
     · ...
     ```

7. 更新 `/tmp/dsa_researcher_v2/__init__.py` — 导出新模块
8. 更新 `/tmp/dsa_researcher_v2/api.py` — ResearcherAPI 加入新工具的调用方法

## 技术要求

- Python 3.11+
- 依赖：requests, pyyaml, pandas, numpy, tushare（已有）
- 所有新工具函数加 docstring
- 错误处理：每个工具都要 try/except，失败返回 `{"success": False, "error": "..."}`
- 日志：用 logging 模块
- 不要硬编码任何 API key，从环境变量读

## 文件结构最终状态

```
dsa_researcher_v2/
├── __init__.py          (更新)
├── api.py               (更新：加新工具方法)
├── config.py            (保持)
├── llm.py               (保持)
├── frank_prompt_v3.md   (新建：新版纯心法prompt)
├── tools/
│   ├── __init__.py      (新建)
│   ├── market_tools.py  (新建：7个现有API封装)
│   └── new_tools.py     (新建：6个新工具)
├── report.py            (新建：研究简报生成器)
├── analysis/            (保持)
├── advisor/             (保持)
├── data/                (保持)
├── data_provider_src/   (保持)
└── strategies/          (保持)
```

## 验证方式

完成后，运行一个简单的 smoke test：
```python
python3 -c "
from dsa_researcher_v2.tools.market_tools import get_indexes, get_top_stocks
from dsa_researcher_v2.tools.new_tools import get_vix
print(get_indexes())
print(get_top_stocks())
print(get_vix())
"
```

开始吧！

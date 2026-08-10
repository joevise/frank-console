# DSA MCP Server — OpenMind 工具接入说明

## 给大Joe：OpenMind 后台怎么配

在 OpenMind 管理后台，找到 Frank 的 Mind → 工具管理 → 添加 MCP Server：

```
MCP Server URL: http://67.209.190.54:8110/mcp
协议: HTTP (SSE)
认证: 无（内网白名单）或 Bearer token（如需）
```

注册后，OpenMind 会自动发现以下 13 个工具：

| 工具名 | 功能 | 参数 |
|--------|------|------|
| dsa_get_market_overview | 大盘多空分析+35信号行业排名 | 无 |
| dsa_get_top_stocks | 当日打分最高20只股票 | 无 |
| dsa_get_stock_detail | 个股详情（140+字段） | stock_code: str |
| dsa_get_hot_industries | 涨停数前5行业 | 无 |
| dsa_get_industry_limitup | 指定行业涨停股 | industry: str |
| dsa_get_indexes | 上证/深证/创业板实时 | 无 |
| dsa_get_history_analysis | 历史某天多空分析 | date: str (YYYYMMDD) |
| dsa_get_bollinger | 布林线通道(日线) | stock_code: str |
| dsa_get_fundamentals | 基本面指标(PE/PB/股息率/ROE/基金持仓) | stock_code: str |
| dsa_get_vix | VIX恐慌指数 | 无 |
| dsa_mainline_alert | 新主线预警(空头→多头) | 无 |
| dsa_get_industry_deviation | 行业偏离度 | industry: str |
| dsa_get_wall_street | 华尔街机构观点 | 无 |

## 本地测试

```bash
# MCP Server 跑在 8110 端口
curl http://localhost:8110/mcp -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}'
```

# -*- coding: utf-8 -*-
"""DSA MCP Server — 把 13 个 DSA 工具暴露为 MCP 协议（JSON-RPC over HTTP/SSE）。

MCP 协议核心：
- tools/list → 返回所有工具的 schema
- tools/call → 执行指定工具，返回结果

运行：python -m dsa_mcp.server --port 8110
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import os
from typing import Any, Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler

# 确保能 import tools 包（tools/ 在 dsa_researcher_v2/ 下）
_HERE = os.path.dirname(os.path.abspath(__file__))
_DSA_V2 = os.path.dirname(_HERE)  # dsa_researcher_v2/
for _p in [_DSA_V2, _HERE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.market_tools import (
    get_market_overview,
    get_top_stocks,
    get_stock_detail,
    get_hot_industries,
    get_industry_limitup,
    get_indexes,
    get_history_analysis,
)
from tools.new_tools import (
    get_bollinger,
    get_fundamentals,
    get_vix,
    mainline_alert,
    get_industry_deviation,
    get_wall_street,
)

logger = logging.getLogger("dsa_mcp")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")


# ============================================================
# MCP 工具定义（OpenAI function-calling 兼容格式）
# ============================================================

MCP_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "dsa_get_market_overview",
        "description": "获取当日A股大盘多空分析，包含35信号行业排名（多头/空头持续天数）、行业转换动态、市场风格判断。这是Frank每天最倚重的核心数据源，用于识别主线方向。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dsa_get_top_stocks",
        "description": "获取当日打分最高的前20只股票，包含名称、行业、Wind四级行业、当日个股总分。用于初筛强势个股。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dsa_get_stock_detail",
        "description": "获取单个或多个股票的详细信息（140+字段），包含涨跌幅、成交量、MA、布林线、基本面(PE/PB/股息率/ROE)、基金持仓、行业排名、当日个股总分等。支持股票代码或名称。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_code": {"type": "string", "description": "股票代码或名称，如 600519 或 贵州茅台"}
            },
            "required": ["stock_code"],
        },
    },
    {
        "name": "dsa_get_hot_industries",
        "description": "获取当日涨停股票数量最多的前5个行业排名。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dsa_get_industry_limitup",
        "description": "获取指定行业的涨停股票列表。输入行业名称（中文或英文均可，自动URL编码）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "行业名称，如 AIGC、白酒、半导体"}
            },
            "required": ["industry"],
        },
    },
    {
        "name": "dsa_get_indexes",
        "description": "获取上证指数、深证成指、创业板指的实时数据（点位、涨跌幅）。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dsa_get_history_analysis",
        "description": "获取指定日期的大盘多空分析。如果该日期无数据，自动fallback到最近有数据的日期。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "日期，格式 YYYYMMDD，如 20260716"}
            },
            "required": ["date"],
        },
    },
    {
        "name": "dsa_get_bollinger",
        "description": "计算个股的布林线通道（日线级别）。优先读取API数据源的布林线字段，如果为空则用前60日收盘价自行计算（20日均线±2倍标准差）。返回上轨/中轨/下轨/位置百分比/三轨方向（同向上=趋势/不一致=震荡）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_code": {"type": "string", "description": "股票代码，如 600519"}
            },
            "required": ["stock_code"],
        },
    },
    {
        "name": "dsa_get_fundamentals",
        "description": "获取个股基本面指标：PE(TTM)、PB、股息率(dv_ratio)、ROE、总市值、持有该股的基金公司家数、行业估值水平。注：部分字段如果数据源未填充会返回null。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_code": {"type": "string", "description": "股票代码，如 600519"}
            },
            "required": ["stock_code"],
        },
    },
    {
        "name": "dsa_get_vix",
        "description": "获取VIX恐慌指数实时值。>24为警惕（市场恐慌），20-24为关注，<20为安全。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dsa_mainline_alert",
        "description": "新主线预警：检测从空头转为多头的行业（新机会），以及从多头转为空头的行业（新风险）。同时返回持续多头最强的前3个行业。这是Frank最需要的能力——第一时间发现新方向。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "dsa_get_industry_deviation",
        "description": "获取行业偏离度（基于多头持续天数估算）。持续>20天=过热，10-20天=偏热，<10天=正常。偏离21均线过远是危险信号。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "行业名称，如 PCB、半导体材料"}
            },
            "required": ["industry"],
        },
    },
    {
        "name": "dsa_get_wall_street",
        "description": "获取华尔街大机构最新观点（从新浪财经美股频道抓取）。用于市场拐点时参考大机构看法变化。",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]


# ============================================================
# 工具执行映射
# ============================================================

TOOL_HANDLERS = {
    "dsa_get_market_overview": lambda args: get_market_overview(),
    "dsa_get_top_stocks": lambda args: get_top_stocks(),
    "dsa_get_stock_detail": lambda args: get_stock_detail(args.get("stock_code", "")),
    "dsa_get_hot_industries": lambda args: get_hot_industries(),
    "dsa_get_industry_limitup": lambda args: get_industry_limitup(args.get("industry", "")),
    "dsa_get_indexes": lambda args: get_indexes(),
    "dsa_get_history_analysis": lambda args: get_history_analysis(args.get("date", "")),
    "dsa_get_bollinger": lambda args: get_bollinger(args.get("stock_code", "")),
    "dsa_get_fundamentals": lambda args: get_fundamentals(args.get("stock_code", "")),
    "dsa_get_vix": lambda args: get_vix(),
    "dsa_mainline_alert": lambda args: mainline_alert(),
    "dsa_get_industry_deviation": lambda args: get_industry_deviation(args.get("industry", "")),
    "dsa_get_wall_street": lambda args: get_wall_street(),
}


# ============================================================
# MCP JSON-RPC 处理
# ============================================================

def handle_jsonrpc(message: Dict[str, Any]) -> Dict[str, Any]:
    """处理一个 JSON-RPC 请求，返回响应。"""
    method = message.get("method", "")
    msg_id = message.get("id")
    params = message.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "dsa-mcp-server",
                    "version": "0.1.0",
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": MCP_TOOLS},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"未知工具: {tool_name}"},
            }

        try:
            result = handler(tool_args)
            # MCP 返回格式：content 数组
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, default=str),
                        }
                    ],
                    "isError": not result.get("success", True),
                },
            }
        except Exception as exc:
            logger.exception("工具执行异常: %s", tool_name)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": f"工具执行错误: {str(exc)}"}],
                    "isError": True,
                },
            }

    # 未知方法
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"未知方法: {method}"},
    }


# ============================================================
# HTTP Server（支持单请求和 SSE 流）
# ============================================================

class MCPRequestHandler(BaseHTTPRequestHandler):
    """处理 MCP JSON-RPC 请求。

    POST /mcp → 单请求模式，返回 JSON
    GET /mcp → SSE 连接（保持长连接，推送通知）
    """

    def do_POST(self):
        if self.path not in ("/mcp", "/"):
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            message = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        # 处理请求（可能是单请求或 batch）
        if isinstance(message, list):
            responses = [handle_jsonrpc(msg) for msg in message]
            self._send_json(200, responses)
        else:
            response = handle_jsonrpc(message)
            self._send_json(200, response)

    def do_GET(self):
        if self.path == "/mcp" or self.path == "/":
            # 返回服务信息
            self._send_json(200, {
                "service": "dsa-mcp-server",
                "version": "0.1.0",
                "tools": len(MCP_TOOLS),
                "endpoints": {
                    "POST /mcp": "JSON-RPC 请求",
                    "GET /mcp": "服务信息",
                    "GET /health": "健康检查",
                },
            })
        elif self.path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self.send_error(404, "Not Found")

    def _send_json(self, status: int, data: Any):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)


def main():
    parser = argparse.ArgumentParser(description="DSA MCP Server")
    parser.add_argument("--port", type=int, default=8110, help="监听端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="监听地址")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), MCPRequestHandler)
    logger.info("DSA MCP Server 启动: http://%s:%d/mcp", args.host, args.port)
    logger.info("已注册 %d 个工具", len(MCP_TOOLS))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务停止")
        server.shutdown()


if __name__ == "__main__":
    main()

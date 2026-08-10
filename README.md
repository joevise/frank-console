# Frank Console

私募基金经理思维数字人 Frank 的操作台。Frank 为大脑决策者，`dsa_researcher` 等为可插拔工具箱。

## 架构

```
┌───────────────────────────────┐
│ 1. 前端 (React + Vite + Tailwind) │  e2b.dev 风格：白底/IBM Plex字体/青绿强调色
└───────────────┬───────────────┘
                │ /api (nginx反代)
┌───────────────▼───────────────┐
│ 2. 后端 (FastAPI)               │  认证/会话/聊天/报告 API
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│ 3. Frank 大脑                   │  OpenRouter: xiaomi/mimo-v2.5
│    (frank_brain.py)             │  fallback: deepseek/deepseek-v4-flash
└───────────────┬───────────────┘
                │ Tool Registry (可插拔)
┌───────────────▼───────────────┐
│ 4. 工具层：dsa_researcher        │  数据/技术分析/顾问建议
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│ 5. 数据持久化                    │  PostgreSQL(用户/会话/报告) + Redis(缓存)
└───────────────────────────────┘
```

## 目录结构

```
frank_console/
├── docker-compose.yml       ← 一键起全部服务
├── .env.example              ← 环境变量模板，复制为 .env 并填真实值
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI 入口
│   │   ├── core/               ← 配置/数据库/认证
│   │   ├── models/             ← SQLAlchemy 数据模型
│   │   ├── api/                ← auth/chat/watchlist/reports 路由
│   │   ├── services/           ← tool_registry(工具注册表) + frank_brain(大脑)
│   │   └── workers/            ← 每日定时分析任务
│   ├── dsa_researcher/         ← 数据/分析/顾问 Skill 包
│   ├── Dockerfile
│   └── Dockerfile.worker
└── frontend/
    ├── src/
    │   ├── pages/Login.jsx
    │   ├── pages/Console.jsx    ← 主界面：左看板+右聊天
    │   └── api/client.js
    └── Dockerfile
```

## 部署步骤

```bash
# 1. 复制配置文件，填入真实值
cp .env.example .env
vim .env   # 填 OpenRouter key、Tushare token、JWT密钥、数据库密码

# 2. 一键启动全部服务
docker compose up -d --build

# 3. 查看状态
docker compose ps
docker compose logs -f backend

# 4. 访问
# 前端: http://<服务器IP>:8180  (端口在 .env 里配，默认8180)
# 后端API: http://<服务器IP>:8100
```

## 首次使用

1. 打开前端，因为还没有注册页面（先手动调 API 建第一个账号）：
   ```bash
   curl -X POST http://<服务器IP>:8100/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"joe","password":"你的密码","display_name":"大Joe"}'
   ```
2. 用这个账号密码在前端登录
3. 添加自选股（右上角输入框）
4. 点击"一键触发今日分析"

## 端口规划（避免和 67.209 已有服务冲突）

已用端口：link2context(3000/8000/8001) + InKnowing(3001/8002) + Brand2Context(3002/8004/8005) + Social API(8006) + AI Embryo(8010)

Frank Console 默认使用：
- 前端: `8180`
- 后端: `8100`

（PostgreSQL/Redis 只在 Docker 内部网络访问，不对外暴露端口）

## 已验证

- ✅ 后端 API 全链路（认证/自选股/聊天/报告）本地 + Docker 环境均测试通过
- ✅ 前端 Vite build 成功，Docker 多阶段构建（node build → nginx serve）成功
- ✅ Docker Compose 起服务：postgres(健康检查通过) + redis + backend + frontend 互通
- ✅ 前端通过 nginx 反代访问后端 API 成功
- ⚠️ Frank 大脑（OpenRouter 调用）+ dsa_researcher 真实数据源调用，因为是测试环境用假 key，未做真实外部 API 联调，需要在正式部署时用真实 key 验证

## 待办（下一步可以做的）

- [ ] 前端加注册页面（现在只能靠 curl 建账号）
- [ ] 历史报告对比页面（后端 API 已就绪：`/api/reports/history/{stock_code}`）
- [ ] 图表可视化（已装 recharts，还没接线）
- [ ] Nginx 加 HTTPS（生产环境建议加反代 + Let's Encrypt）
- [ ] 用真实 Tushare token + OpenRouter key 联调全链路

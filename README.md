# IoT Platform — 企业级智能物联网设备管理与数据看板系统

## 项目简介

IoT Platform 是一套面向企业级物联网场景的端到端解决方案，涵盖设备注册管理、遥测数据采集入库、Redis 实时缓存以及前端可视化看板。系统支持多设备并发数据上报，5 秒级实时刷新，适用于温湿度监控、环境监测、设备资产管理等典型 IoT 场景。

## 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 后端框架 | Python FastAPI (async) | 0.115 |
| ORM | SQLAlchemy (async) | 2.0 |
| 数据库 | MySQL (InnoDB, utf8mb4) | 8.0+ |
| 缓存 | Redis | 7.x |
| 容器化 | Docker + Docker Compose | — |
| 模拟器 | Python asyncio + httpx | — |
| 前端 | Tailwind CSS + ECharts + Lucide | — |
| 部署 | Render + Vercel (免费层) | — |
| 代码托管 | Gitee / GitHub | — |

## 项目结构

```
iot-platform/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口 & 生命周期
│   │   ├── core/               # 配置、MySQL 连接池、Redis 客户端
│   │   ├── models/             # SQLAlchemy ORM + Pydantic Schema
│   │   ├── api/
│   │   │   ├── deps.py         # 依赖注入 (DB / Redis)
│   │   │   └── v1/             # REST API v1 路由
│   │   │       ├── router.py   # 路由聚合
│   │   │       ├── devices.py  # 设备 CRUD
│   │   │       ├── data.py     # 数据上报
│   │   │       └── dashboard.py# 看板统计
│   │   └── services/           # 业务逻辑层
│   ├── Dockerfile              # 后端容器构建
│   ├── .dockerignore
│   ├── requirements.txt
│   └── .env.example            # 环境变量模板
├── frontend/                   # 前端看板
│   ├── index.html              # 完整看板 (Tailwind + ECharts)
│   └── vercel.json             # Vercel 静态站配置
├── db/
│   └── init.sql                # MySQL 建库建表脚本
├── docker-compose.yml          # 全栈一键部署编排
├── render.yaml                 # Render 蓝图部署配置
├── simulator.py                # 设备数据模拟器
├── Makefile                    # 常用命令快捷入口
└── README.md
```

## 本地环境启动

### 前置依赖

确保本地已安装并启动以下服务：

- **MySQL 8.0+** (端口 3306)
- **Redis 7.x** (端口 6379)
- **Python 3.11+**

### 1. 克隆项目

```bash
git clone <your-gitee-repo-url>
cd iot-platform
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 4. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，修改 DB_PASSWORD 等敏感配置
```

### 5. 初始化数据库

```bash
# 方式一：使用 Makefile
make db-init

# 方式二：手动执行 SQL
mysql -u root -p < db/init.sql
```

### 6. 测试数据库连接

```bash
make db-test
```

### 7. 启动后端服务

```bash
make dev
# 或手动执行:
# cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成于: **http://localhost:8000/docs**

### 8. 启动设备模拟器

新开一个终端，**确保虚拟环境已激活**：

```bash
python simulator.py
```

模拟器会自动注册 5 台设备，并每 5 秒上报一次模拟的温湿度数据。

终端输出示例：

```
2026-06-29 17:00:01 [INFO] [温湿度计01] 设备注册成功
2026-06-29 17:00:01 [INFO] [湿度监测仪02] 设备已注册，跳过
2026-06-29 17:00:02 [INFO] [温湿度计01] ✓ 上报成功 | 温度: 26.5℃ | 湿度: 62.3% | 电量: 87.2% | 信号: -52dBm
2026-06-29 17:00:02 [INFO] [湿度监测仪02] ✓ 上报成功 | 温度: 24.1℃ | 湿度: 73.6% | 电量: 91.0% | 信号: -41dBm
```

### 9. 打开前端看板

直接在浏览器打开 `frontend/index.html`，即可看到设备状态看板实时刷新。

## 部署到生产环境

### 方案一：Docker Compose 一键部署（推荐自托管）

适用于自有 VPS 或云服务器，一条命令全栈启动。

```bash
# 1. 克隆项目
git clone <your-repo-url> && cd iot-platform

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env → 修改 DB_PASSWORD、SECRET_KEY 等

# 3. 一键启动（后端 + MySQL + Redis）
docker compose up -d

# 4. 验证
curl http://localhost:8000/health
```

访问 `http://<服务器IP>:8000` 或配置 Nginx 反向代理绑定域名。

---

### 方案二：免费云平台部署（零成本上线）

适合个人项目/原型验证，完全免费，支持自定义域名。

**架构：**

```
┌──────────┐      ┌───────────┐      ┌──────────────┐
│  Vercel  │─────▶│  Render   │─────▶│  TiDB Cloud  │
│  前端     │      │  FastAPI  │      │  MySQL 免费   │
│  免费     │      │  免费层    │      │  5GB 存储     │
└──────────┘      └───────────┘      └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Upstash     │
                  │  Redis 免费   │
                  │  256MB       │
                  └──────────────┘
```

#### 第 1 步：TiDB Cloud 免费 MySQL

1. 注册 [TiDB Cloud](https://tidbcloud.com) → 创建免费 Serverless 集群
2. 在 Clusters 页面获取连接信息：
   - **Host**: `gateway01.xxx.xxx.tidbcloud.com`
   - **Port**: `4000`
   - **User**: 集群前缀 `.root`（如 `2gD4xxx.root`）
   - **Password**: 集群创建时设置的密码
3. 在 TiDB Cloud 控制台执行 `db/init.sql` 中的建表语句初始化表结构，或通过 MySQL 客户端连接后执行

#### 第 2 步：Upstash 免费 Redis（可选）

> Redis 仅用于实时缓存加速，代码已内置降级逻辑，Redis 不可用时不影响核心功能。可以跳过此步骤。

1. 注册 [Upstash](https://upstash.com) → 创建免费 Redis 实例
2. 获取连接信息：
   - **Host**: `xxx.upstash.io`
   - **Port**: `6379`
   - **Password**: 实例详情页查看

#### 第 3 步：Render 部署后端

1. Fork 本项目到你的 GitHub 账号
2. 注册 [Render](https://render.com) → New Web Service → 连接 GitHub
3. 选择仓库，Render 会自动识别项目根目录的 `render.yaml` 蓝图文件
4. **手动设置以下环境变量** (Render Dashboard → Environment)：

| 环境变量 | 说明 | 示例 |
|----------|------|------|
| `APP_ENV` | 运行模式 | `production` |
| `APP_DEBUG` | 调试开关 | `false` |
| `SECRET_KEY` | 加密密钥 | 随机 32 位字符串 |
| `CORS_ORIGINS` | CORS 允许域 | `*` 或你的域名 |
| `DB_HOST` | TiDB Cloud 主机 | `gateway01.xxx.tidbcloud.com` |
| `DB_PORT` | TiDB 端口 | `4000` |
| `DB_USER` | 数据库用户 | `xxx.root` |
| `DB_PASSWORD` | 数据库密码 | 你的密码 |
| `DB_NAME` | 数据库名 | `iot_platform` |
| `DB_SSL` | 启用 SSL | `true` |
| `REDIS_HOST` | Redis 主机(可选) | `xxx.upstash.io` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_PASSWORD` | Redis 密码 | 你的密码 |
| `REDIS_SSL` | Redis TLS | `true` |

5. 部署完成后，获得后端 URL：`https://iot-platform-api.onrender.com`
   > 注意：免费层实例在无请求 15 分钟后会自动休眠，首次唤醒需 30-60 秒。

#### 第 4 步：Vercel 部署前端

1. 注册 [Vercel](https://vercel.com) → New Project → 导入同一仓库
2. **Root Directory** 设置为 `frontend`
3. 部署完成后，进入 Vercel Dashboard → Settings → Domains 绑定你的自定义域名
4. **重要**：修改 `frontend/index.html` 第 167 行 `API_BASE` 中的 `iot-platform-api.onrender.com` 为你的实际 Render 后端域名

#### 第 5 步：验证线上环境

```bash
# 测试后端 API
curl https://iot-platform-api.onrender.com/health
curl https://iot-platform-api.onrender.com/api/v1/dashboard/summary

# 启动本地模拟器向线上后端上报数据
# 修改 simulator.py 中的 API_BASE 为线上地址后运行
python simulator.py

# 浏览器打开 Vercel 域名查看完整看板
```

---

## API 端点一览

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/devices` | 设备列表 |
| `POST` | `/api/v1/devices` | 注册设备 |
| `GET` | `/api/v1/devices/{id}` | 设备详情 |
| `PUT` | `/api/v1/devices/{id}` | 更新设备 |
| `DELETE` | `/api/v1/devices/{id}` | 删除设备 |
| `POST` | `/api/v1/data/report` | 设备数据上报 |
| `GET` | `/api/v1/dashboard/summary` | 看板汇总 |
| `GET` | `/api/v1/dashboard/trend` | 趋势数据 (温湿度时序) |
| `GET` | `/api/v1/dashboard/devices/online` | 在线设备列表 |
| `GET` | `/api/v1/dashboard/devices/{id}/latest` | 设备最新数据 |

## 模拟设备说明

| 设备ID | 名称 | 类型 | 部署位置 | 传感器特征 |
|---|---|---|---|---|
| `sensor-temp-001` | 温湿度计01 | 温度传感器 | 办公楼3层A区 | 温度偏高 (25-40℃) |
| `sensor-humid-002` | 湿度监测仪02 | 湿度传感器 | 地下仓库B区 | 湿度偏高 (50-80%) |
| `sensor-env-003` | 环境监测仪03 | 多合一传感器 | 室外气象站 | 均衡型 |
| `sensor-indoor-004` | 室内传感器04 | 多合一传感器 | 会议室C-301 | 温和型 (20-28℃) |
| `sensor-gateway-005` | 网关设备05 | 网关 | 数据中心机房 | 仅信号强度+电量 |

## 常用命令

| 命令 | 说明 |
|---|---|
| `make help` | 查看所有可用命令 |
| `make dev` | 启动开发服务器 |
| `make install` | 安装 Python 依赖 |
| `make db-init` | 初始化数据库表结构 |
| `make db-test` | 测试数据库连接 |
| `make lint` | 代码风格检查 |
| `make clean` | 清理临时文件 |

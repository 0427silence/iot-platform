# IoT Platform — 企业级智能物联网设备管理与数据看板系统

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python FastAPI + SQLAlchemy (async) |
| 数据库 | MySQL 8.0 (InnoDB, utf8mb4) |
| 缓存 | Redis 7.x |
| 前端 | 原生 HTML/CSS/JS |
| 代码托管 | Gitee |

## 快速开始

### 1. 环境准备

确保本地已安装并启动：

- MySQL 8.0+ (端口 3306)
- Redis (端口 6379)
- Python 3.11+

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 MySQL 密码
```

### 3. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 4. 初始化数据库

```bash
mysql -u root -p < db/init.sql
```

### 5. 测试数据库连接

```bash
python scripts/test_db.py
```

### 6. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成于: http://localhost:8000/docs

### 7. 打开前端看板

直接在浏览器打开 `frontend/index.html`，或使用任意静态服务器。

## 项目结构

```
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── main.py     # 应用入口
│   │   ├── core/       # 配置、数据库、Redis
│   │   ├── models/     # ORM 模型 + Pydantic Schema
│   │   ├── api/v1/     # REST API 路由
│   │   └── services/   # 业务逻辑层
│   └── requirements.txt
├── frontend/           # 前端看板
├── db/                 # 数据库脚本
│   └── init.sql        # 建表脚本
├── scripts/            # 运维脚本
│   └── test_db.py      # 数据库连接测试
└── tests/              # 测试用例
```

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /health | 健康检查 |
| GET | /api/v1/devices | 设备列表 |
| POST | /api/v1/devices | 注册设备 |
| GET | /api/v1/devices/{id} | 设备详情 |
| PUT | /api/v1/devices/{id} | 更新设备 |
| DELETE | /api/v1/devices/{id} | 删除设备 |
| POST | /api/v1/data/report | 设备数据上报 |
| GET | /api/v1/dashboard/summary | 看板汇总 |
| GET | /api/v1/dashboard/devices/online | 在线设备列表 |
| GET | /api/v1/dashboard/devices/{id}/latest | 设备最新数据 |

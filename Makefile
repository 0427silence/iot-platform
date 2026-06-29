.PHONY: help dev install db-init db-test lint clean

help:  ## 显示所有可用命令
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## 安装项目依赖
	cd backend && pip install -r requirements.txt

dev:  ## 启动开发服务器
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

db-init:  ## 初始化 MySQL 数据库表结构
	@echo "正在执行 db/init.sql ..."
	@mysql -u root -p < db/init.sql
	@echo "数据库初始化完成。"

db-test:  ## 测试数据库连接
	python scripts/test_db.py

lint:  ## 代码检查
	ruff check backend/ scripts/

clean:  ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "清理完成。"

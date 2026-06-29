"""
数据库连接测试脚本
用途: 验证 MySQL 和 Redis 连接是否正常
用法: python scripts/test_db.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from dotenv import load_dotenv
import pymysql
import redis


def load_config() -> dict:
    """加载 .env 配置文件"""
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if not env_path.exists():
        print("❌ 错误: 未找到 .env 文件，请先复制 .env.example 并配置")
        print(f"   期望路径: {env_path}")
        print("   执行: cp backend/.env.example backend/.env")
        sys.exit(1)

    load_dotenv(env_path)
    return {
        "db_host": os.getenv("DB_HOST", "127.0.0.1"),
        "db_port": int(os.getenv("DB_PORT", "3306")),
        "db_user": os.getenv("DB_USER", "root"),
        "db_password": os.getenv("DB_PASSWORD", ""),
        "db_name": os.getenv("DB_NAME", "iot_platform"),
        "redis_host": os.getenv("REDIS_HOST", "127.0.0.1"),
        "redis_port": int(os.getenv("REDIS_PORT", "6379")),
        "redis_password": os.getenv("REDIS_PASSWORD", ""),
        "redis_db": int(os.getenv("REDIS_DB", "0")),
    }


def test_mysql(cfg: dict) -> bool:
    """测试 MySQL 连接并执行基础查询"""
    print()
    print("=" * 60)
    print("  [1/2] 测试 MySQL 连接...")
    print("=" * 60)
    try:
        conn = pymysql.connect(
            host=cfg["db_host"],
            port=cfg["db_port"],
            user=cfg["db_user"],
            password=cfg["db_password"],
            database=cfg["db_name"],
            charset="utf8mb4",
            connect_timeout=5,
        )
        cursor = conn.cursor()

        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"  ✅ MySQL 版本: {version}")

        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        if tables:
            print(f"  📋 已存在的表 ({len(tables)}): {', '.join(tables)}")
        else:
            print("  ⚠️  数据库中暂无表，请执行 db/init.sql 初始化")

        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema=%s AND table_name='devices'",
            (cfg["db_name"],),
        )
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT COUNT(*) FROM devices")
            device_count = cursor.fetchone()[0]
            print(f"  📊 devices 表记录数: {device_count}")

        cursor.close()
        conn.close()
        print("  ✅ [通过] MySQL 连接测试成功")
        return True

    except pymysql.MySQLError as e:
        print(f"  ❌ [失败] MySQL 连接失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ [失败] 未知错误: {e}")
        return False


def test_redis(cfg: dict) -> bool:
    """测试 Redis 连接"""
    print()
    print("=" * 60)
    print("  [2/2] 测试 Redis 连接...")
    print("=" * 60)
    try:
        r = redis.Redis(
            host=cfg["redis_host"],
            port=cfg["redis_port"],
            password=cfg["redis_password"] or None,
            db=cfg["redis_db"],
            socket_connect_timeout=5,
            decode_responses=True,
        )

        response = r.ping()
        if response:
            print(f"  ✅ Redis PING 响应: {response}")

        info = r.info("server")
        print(f"  ✅ Redis 版本: {info.get('redis_version', 'unknown')}")
        print(f"  📋 Redis 运行模式: {info.get('redis_mode', 'unknown')}")

        dbsize = r.dbsize()
        print(f"  📊 当前数据库键数量: {dbsize}")

        r.set("__test_db_connectivity__", "ok", ex=10)
        test_val = r.get("__test_db_connectivity__")
        r.delete("__test_db_connectivity__")
        if test_val == "ok":
            print("  ✅ Redis 读写测试: 正常")
        else:
            print("  ⚠️  Redis 读写测试异常")

        r.close()
        print("  ✅ [通过] Redis 连接测试成功")
        return True

    except redis.ConnectionError as e:
        print(f"  ❌ [失败] Redis 连接失败: {e}")
        print("  💡 请确认 Redis 服务已启动 (Windows: redis-server.exe)")
        return False
    except Exception as e:
        print(f"  ❌ [失败] 未知错误: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("  🏭 IoT Platform - 数据库连接测试")
    print("=" * 60)

    cfg = load_config()
    mysql_ok = test_mysql(cfg)
    redis_ok = test_redis(cfg)

    print()
    print("=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"  MySQL: {'✅ 通过' if mysql_ok else '❌ 失败'}")
    print(f"  Redis: {'✅ 通过' if redis_ok else '❌ 失败'}")

    if mysql_ok and redis_ok:
        print()
        print("  🎉 所有连接测试通过，系统可以正常启动。")
        sys.exit(0)
    else:
        print()
        print("  🔧 部分连接测试失败，请检查配置后重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()

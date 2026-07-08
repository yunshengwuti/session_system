"""
数据库连接测试脚本
运行此脚本检查数据库连接和表结构
"""
import sys
from config.database import engine, init_db, SessionLocal
from sqlalchemy import text

def test_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功！MySQL版本: {version}")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def create_tables():
    """创建所有表"""
    print("\n📊 创建数据库表...")
    try:
        init_db()
        print("✅ 数据库表创建成功！")
        return True
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False

def check_tables():
    """检查表是否存在"""
    print("\n🔍 检查表结构...")
    try:
        db = SessionLocal()
        result = db.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]

        expected_tables = ["sessions", "messages", "daily_reports", "weekly_reports"]

        print("数据库中的表：")
        for table in tables:
            status = "✅" if table in expected_tables else "⚠️"
            print(f"  {status} {table}")

        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"\n⚠️ 缺少表: {', '.join(missing)}")
            return False
        else:
            print(f"\n✅ 所有必需的表都已创建！")
            return True
    except Exception as e:
        print(f"❌ 检查表失败: {e}")
        return False
    finally:
        db.close()

def show_table_structure():
    """显示表结构"""
    print("\n📋 表结构详情：")
    try:
        db = SessionLocal()
        tables = ["sessions", "messages", "daily_reports", "weekly_reports"]

        for table in tables:
            print(f"\n--- {table} ---")
            result = db.execute(text(f"DESCRIBE {table}"))
            for row in result:
                print(f"  {row[0]:20s} {row[1]:30s} {row[2]:5s} {row[3]:5s}")

        return True
    except Exception as e:
        print(f"❌ 显示表结构失败: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("会话数据管理系统 - 数据库测试")
    print("=" * 60)

    # 测试连接
    if not test_connection():
        print("\n⚠️ 请检查 .env 文件中的数据库配置")
        sys.exit(1)

    # 创建表
    if not create_tables():
        print("\n⚠️ 表创建失败，请检查数据库权限")
        sys.exit(1)

    # 检查表
    if not check_tables():
        print("\n⚠️ 表结构不完整")
        sys.exit(1)

    # 显示表结构
    show_table_structure()

    print("\n" + "=" * 60)
    print("✅ 数据库测试完成！可以启动后端服务了")
    print("💡 运行命令: python main.py")
    print("=" * 60)

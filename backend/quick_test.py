#!/usr/bin/env python3
"""
快速测试脚本 - 检查系统是否可以正常运行
"""
import sys

print("=== 系统快速测试 ===\n")

# 1. 检查依赖包
print("1. 检查依赖包...")
missing = []
packages = {
    'fastapi': 'FastAPI',
    'uvicorn': 'Uvicorn',
    'sqlalchemy': 'SQLAlchemy',
    'pymysql': 'PyMySQL',
    'pandas': 'Pandas',
    'openpyxl': 'openpyxl',
}

for pkg, name in packages.items():
    try:
        __import__(pkg)
        print(f"   ✅ {name}")
    except ImportError:
        print(f"   ❌ {name} - 未安装")
        missing.append(name)

if missing:
    print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
    print("请运行: pip install -r requirements.txt")
    sys.exit(1)

print("\n2. 检查数据库连接...")
try:
    from config.database import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("   ✅ 数据库连接成功")
except Exception as e:
    print(f"   ❌ 数据库连接失败: {e}")
    sys.exit(1)

print("\n3. 检查数据库表...")
try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = ['sessions', 'messages', 'daily_reports', 'weekly_reports']
    for table in required_tables:
        if table in tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - 表不存在")
except Exception as e:
    print(f"   ❌ 检查表失败: {e}")

print("\n4. 检查数据统计...")
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        # 会话数
        result = conn.execute(text("SELECT COUNT(*) FROM sessions"))
        session_count = result.scalar()
        print(f"   📊 会话数: {session_count}")

        # 消息数
        result = conn.execute(text("SELECT COUNT(*) FROM messages"))
        message_count = result.scalar()
        print(f"   📊 消息数: {message_count}")

        # 图片消息数
        result = conn.execute(text("SELECT COUNT(*) FROM messages WHERE message_type='image'"))
        image_count = result.scalar()
        print(f"   📊 图片消息数: {image_count}")

        if image_count == 0 and message_count > 0:
            print(f"   ⚠️  警告: 数据库中没有图片消息！")

except Exception as e:
    print(f"   ❌ 统计失败: {e}")

print("\n5. 测试图片解析逻辑...")
try:
    from services.excel_parser import extract_image_url, is_image_message

    test_content = '<img src="https://example.com/test.jpg">'
    is_img = is_image_message(test_content)
    url = extract_image_url(test_content)

    if is_img and url == "https://example.com/test.jpg":
        print("   ✅ 图片解析逻辑正常")
    else:
        print(f"   ❌ 图片解析逻辑异常: is_img={is_img}, url={url}")
except Exception as e:
    print(f"   ❌ 测试失败: {e}")

print("\n" + "="*50)
print("✅ 所有检查完成！")
print("\n下一步:")
print("  1. 启动服务: python main.py")
print("  2. 访问文档: http://localhost:8000/docs")
print("  3. 如果图片不显示，检查 Excel 源文件格式")
print("="*50)

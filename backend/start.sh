#!/bin/bash
# 系统检查和启动脚本

echo "==================================="
echo "  会话管理系统 - 启动检查脚本"
echo "==================================="
echo ""

# 1. 检查依赖
echo "1️⃣  检查 Python 依赖..."
python3 quick_test.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 依赖检查失败，请先安装依赖:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "2️⃣  启动 FastAPI 服务..."
echo ""
python3 main.py


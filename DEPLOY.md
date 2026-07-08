# 部署指南

## 📋 前置条件

1. **Python 3.9+**
2. **MySQL 5.7+**
3. **pip** (Python 包管理器)

## 🚀 部署步骤

### 步骤 1: 创建数据库

登录 MySQL，执行：

```sql
CREATE DATABASE session_system DEFAULT CHARACTER SET utf8mb4;
```

或直接运行提供的初始化脚本：

```bash
mysql -u root -p < backend/init_database.sql
```

### 步骤 2: 配置环境变量

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，填入你的数据库密码：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=session_system

# AI服务配置（可选，占位）
AI_API_KEY=your_api_key_here
AI_API_URL=https://your-ai-service.com/api
```

### 步骤 3: 安装 Python 依赖

```bash
pip install -r requirements.txt
```

或使用虚拟环境（推荐）：

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 步骤 4: 测试数据库连接

运行测试脚本，确保数据库配置正确：

```bash
python test_database.py
```

如果看到 `✅ 数据库测试完成！` 说明配置成功。

### 步骤 5: 启动后端服务

```bash
python main.py
```

服务启动后，访问：
- API 文档：http://localhost:8000/docs
- 简单测试：http://localhost:8000/

## 🧪 测试上传功能

将你的 Excel 文件上传到系统：

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "message_file=@messageRecord_20260625-20260625.xlsx" \
  -F "reception_file=@receptionRecord_20260625-20260625.xlsx"
```

或使用 API 文档页面的交互式界面上传。

## 📊 生成报告

### 生成日报

在上传数据后，生成某天的日报：

```bash
curl -X POST "http://localhost:8000/api/reports/daily?report_date=2026-06-25"
```

### 生成周报

生成某周的周报（需要传入周一的日期）：

```bash
curl -X POST "http://localhost:8000/api/reports/weekly?week_start_date=2026-06-23"
```

## 🔧 常见问题

### 1. 数据库连接失败

**错误**: `Access denied for user 'root'@'localhost'`

**解决**:
- 检查 `.env` 文件中的数据库密码是否正确
- 确认 MySQL 服务正在运行
- 确认用户有足够的权限

### 2. 表创建失败

**错误**: `Can't connect to MySQL server`

**解决**:
- 确认数据库 `session_system` 已创建
- 检查 MySQL 端口是否为 3306
- 尝试手动运行 `init_database.sql`

### 3. 依赖安装失败

**错误**: `Could not find a version that satisfies the requirement`

**解决**:
- 升级 pip: `pip install --upgrade pip`
- 使用虚拟环境
- 检查 Python 版本是否为 3.9+

### 4. 端口被占用

**错误**: `Address already in use`

**解决**:
- 修改 `main.py` 中的端口号
- 或关闭占用 8000 端口的其他服务

## 🔄 更新数据库结构

如果修改了数据库模型，重新启动服务即可自动更新表结构（SQLAlchemy 会自动处理）。

或手动删除表重建：

```sql
USE session_system;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS weekly_reports;
DROP TABLE IF EXISTS daily_reports;
DROP TABLE IF EXISTS sessions;
```

然后重启服务或运行：

```bash
python test_database.py
```

## 📝 下一步

1. **实现 AI 接口**：编辑 `services/ai_service.py`，对接你的 AI 服务
2. **开发前端**：使用 Vue3 开发前端界面，调用后端 API
3. **部署到服务器**：使用 Nginx + Gunicorn 部署到生产环境

## 💡 生产环境部署

### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### 使用 Supervisor 守护进程

创建 `/etc/supervisor/conf.d/session_system.conf`：

```ini
[program:session_system]
directory=/path/to/session-system/backend
command=/path/to/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
autostart=true
autorestart=true
stderr_logfile=/var/log/session_system.err.log
stdout_logfile=/var/log/session_system.out.log
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📞 支持

如有问题，请检查：
1. 日志输出
2. API 文档 http://localhost:8000/docs
3. 数据库表结构是否正确创建

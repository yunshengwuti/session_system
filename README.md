# 会话数据管理系统 v2.0

qeubee 客服会话数据管理、展示与 AI 分析系统

## ✨ 新版本特性

- **简化数据库设计**：去除冗余自增ID，使用自然主键
- **优化数据结构**：时长存储为秒数，便于统计计算
- **AI接口占位**：预留AI服务接口，可灵活对接任何AI服务
- **日报/周报支持**：完整的报告生成和管理功能

## 📊 技术栈

- **后端**: FastAPI + SQLAlchemy + MySQL
- **前端**: Vue3 + Vite + Element Plus + ECharts（待搭建）
- **AI**: 占位接口（可对接任何AI服务）

## 🗄️ 数据库架构

### 1. sessions 表（会话表）
- `session_id` (主键) - 会话ID
- `customer_name` - 客户姓名
- `org_name` - 机构名称
- `customer_service` - 询问客服
- `duration_seconds` - 时长（秒）
- `session_date` - 会话日期

### 2. messages 表（消息明细）
- `session_id` + `message_time` (复合主键)
- `speaker` - 发言人
- `message_type` - 消息类型（text/image）
- `content` - 文本内容
- `image_url` - 图片URL

### 3. daily_reports 表（日报）
- `report_date` (主键) - 报告日期
- `total_sessions` - 总会话数
- `keywords_json` - 关键词统计（JSON）
- `category_stats_json` - 问题分类占比（JSON）
- `long_duration_issues` - 耗时问题分析
- `org_distribution_json` - 机构分布（JSON）
- `service_stats_json` - 客服工作量（JSON）
- `ai_summary` - AI总结全文
- `generated_at` - 生成时间

### 4. weekly_reports 表（周报）
- `week_start_date` (主键) - 周开始日期
- `week_end_date` - 周结束日期
- `total_sessions` - 本周总会话数
- `keywords_json` - 关键词统计（JSON）
- `category_stats_json` - 问题分类占比（JSON）
- `org_distribution_json` - 机构分布（JSON）
- `service_stats_json` - 客服工作量（JSON）
- `daily_trend_json` - 每日趋势（JSON）
- `ai_summary` - AI周报全文
- `generated_at` - 生成时间

## 📁 项目结构

```
session-system/
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── config/
│   │   └── database.py         # 数据库配置
│   ├── models/
│   │   ├── database.py         # 数据库模型（简化版）
│   │   └── schemas.py          # API 数据模型
│   ├── api/
│   │   ├── sessions.py         # 会话接口
│   │   ├── upload.py           # Excel上传接口
│   │   └── reports.py          # 日报/周报接口（新）
│   ├── services/
│   │   ├── excel_parser.py     # Excel解析
│   │   └── ai_service.py       # AI服务（占位接口）
│   ├── requirements.txt
│   └── .env.example
└── frontend/                   # Vue前端（待搭建）
```

## 🚀 快速开始

### 1. 准备 MySQL 数据库

```sql
CREATE DATABASE session_system DEFAULT CHARACTER SET utf8mb4;
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入数据库密码和AI API配置
```

示例 `.env` 文件：
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=session_system

# AI服务配置（可选，占位）
AI_API_KEY=your_api_key
AI_API_URL=https://your-ai-service.com/api
```

### 3. 安装依赖 & 启动后端

```bash
pip install -r requirements.txt
python main.py
```

启动后访问 http://localhost:8000/docs 查看 API 文档

## 📡 API 接口

### 会话管理
| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/upload` | POST | 上传 Excel 导入数据 |
| `/api/sessions` | GET | 会话列表（支持筛选） |
| `/api/sessions/{session_id}` | GET | 会话详情 + 消息 + 图片 |

### 报告管理（新）
| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/reports/daily` | POST | 生成某天的日报 |
| `/api/reports/daily/{date}` | GET | 获取某天的日报 |
| `/api/reports/daily/{date}` | DELETE | 删除某天的日报 |
| `/api/reports/daily/list` | GET | 获取日报列表 |
| `/api/reports/weekly` | POST | 生成某周的周报 |
| `/api/reports/weekly/{date}` | GET | 获取某周的周报 |
| `/api/reports/weekly/{date}` | DELETE | 删除某周的周报 |
| `/api/reports/weekly/list` | GET | 获取周报列表 |

## 🤖 AI 服务配置

### 占位接口说明

`backend/services/ai_service.py` 中提供了占位接口，需要你实现：

1. **`generate_daily_report(sessions_data)`** - 生成日报
   - 输入：当天所有会话数据
   - 输出：关键词、分类占比、耗时问题、机构分布、客服工作量、AI总结

2. **`generate_weekly_report(week_sessions_data, daily_reports)`** - 生成周报
   - 输入：本周所有会话数据 + 每日报告
   - 输出：汇总统计 + 每日趋势 + AI总结

### 实现建议

你可以对接任何AI服务：
- OpenAI GPT
- Anthropic Claude
- 阿里通义千问
- 百度文心一言
- 自建大模型

只需在 `ai_service.py` 中实现 `call_ai_api()` 函数即可。

## 🔄 数据流程

```
1. 每天上传 Excel (receptionRecord + messageRecord)
   ↓
2. 解析并存入 sessions + messages 表
   ↓
3. 前端展示会话列表（类似20260625xlsx.xlsx）
   ↓
4. 用户点击"生成今日报告"
   ↓
5. 调用 POST /api/reports/daily 生成日报
   ↓
6. AI分析所有会话，生成统计和总结
   ↓
7. 存入 daily_reports 表
   ↓
8. 前端展示图表和统计
   ↓
9. 周末点击"生成本周报告"
   ↓
10. 调用 POST /api/reports/weekly 生成周报
```

## 🎯 核心改进

### 与旧版本相比：

1. **数据库简化**
   - ❌ 删除：自增ID、冗余字段、Summary表、DailyStat表
   - ✅ 新增：DailyReport表、WeeklyReport表
   - ✅ 优化：使用自然主键、duration改为秒数

2. **功能增强**
   - ✅ 新增周报功能
   - ✅ 报告支持 CRUD 操作
   - ✅ JSON 字段存储结构化统计数据

3. **AI接口解耦**
   - ✅ 不依赖特定AI服务
   - ✅ 提供清晰的占位接口
   - ✅ 便于对接任何AI服务

## 📝 使用示例

### 上传数据
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "message_file=@messageRecord.xlsx" \
  -F "reception_file=@receptionRecord.xlsx"
```

### 生成日报
```bash
curl -X POST "http://localhost:8000/api/reports/daily?report_date=2026-06-25"
```

### 生成周报（周一日期）
```bash
curl -X POST "http://localhost:8000/api/reports/weekly?week_start_date=2026-06-23"
```

## 🔧 开发建议

1. **实现AI接口**：优先完成 `services/ai_service.py` 的AI调用逻辑
2. **测试数据导入**：用现有Excel文件测试数据导入功能
3. **前端开发**：基于API文档开发Vue前端界面
4. **图表展示**：使用ECharts展示统计图表

## 📄 License

MIT

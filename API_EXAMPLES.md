# API 使用示例

## 📤 1. 上传 Excel 数据

### 请求

```bash
POST /api/upload
Content-Type: multipart/form-data
```

**参数**:
- `message_file`: messageRecord Excel 文件
- `reception_file`: receptionRecord Excel 文件

### 示例

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "message_file=@messageRecord_20260625-20260625.xlsx" \
  -F "reception_file=@receptionRecord_20260625-20260625.xlsx"
```

### 响应

```json
{
  "total_sessions": 50,
  "valid_sessions": 37,
  "filtered_sessions": 13,
  "date": "2026-06-25",
  "message": "数据导入成功"
}
```

---

## 📋 2. 获取会话列表

### 请求

```bash
GET /api/sessions?date_from=2026-06-25&date_to=2026-06-25&page=1&size=20
```

**参数**:
- `date_from` (可选): 开始日期
- `date_to` (可选): 结束日期
- `org` (可选): 机构名称筛选
- `keyword` (可选): 关键词搜索
- `page` (默认1): 页码
- `size` (默认20): 每页数量

### 示例

```bash
curl "http://localhost:8000/api/sessions?date_from=2026-06-25&page=1&size=20"
```

### 响应

```json
[
  {
    "session_id": "0c5296aab8e947c9bff4075956ab03c5",
    "customer_name": "森浦Sumsope_Tommy?",
    "org_name": "森浦",
    "customer_service": "在线客服 施杰",
    "duration_seconds": 781,
    "session_date": "2026-06-25",
    "message_count": 6
  },
  ...
]
```

---

## 🔍 3. 获取会话详情

### 请求

```bash
GET /api/sessions/{session_id}
```

### 示例

```bash
curl "http://localhost:8000/api/sessions/0c5296aab8e947c9bff4075956ab03c5"
```

### 响应

```json
{
  "session_id": "0c5296aab8e947c9bff4075956ab03c5",
  "customer_name": "森浦Sumsope_Tommy?",
  "org_name": "森浦",
  "customer_service": "在线客服 施杰",
  "duration_seconds": 781,
  "session_date": "2026-06-25",
  "messages": [
    {
      "speaker": "森浦Sumsope_Tommy?",
      "content": "老师好，麻烦帮忙查看一下yi.wang@asia.ccb.com是在香港网关吗",
      "image_url": null,
      "message_type": "text",
      "message_time": "2026-06-25T10:30:15"
    },
    {
      "speaker": "森浦Sumsope_Tommy?",
      "content": null,
      "image_url": "https://example.com/image.jpg",
      "message_type": "image",
      "message_time": "2026-06-25T10:30:20"
    },
    ...
  ]
}
```

---

## 📊 4. 生成日报

### 请求

```bash
POST /api/reports/daily?report_date=2026-06-25
```

### 示例

```bash
curl -X POST "http://localhost:8000/api/reports/daily?report_date=2026-06-25"
```

### 响应

```json
{
  "report_date": "2026-06-25",
  "total_sessions": 37,
  "keywords_json": {
    "网关切换": 8,
    "账户问题": 5,
    "功能咨询": 12,
    "技术故障": 3,
    "其他": 9
  },
  "category_stats_json": {
    "技术问题": 15,
    "业务咨询": 18,
    "账户管理": 4
  },
  "long_duration_issues": "耗时较长的问题主要集中在网关切换和账户权限配置，平均处理时长超过15分钟。",
  "org_distribution_json": {
    "森浦": 20,
    "中信证券": 8,
    "华泰保兴基金管理有限公司": 5,
    "其他": 4
  },
  "service_stats_json": {
    "在线客服 施杰": 10,
    "在线客服 Riven": 15,
    "在线客服 其他": 12
  },
  "ai_summary": "今日共接待37个会话，主要问题包括网关切换、功能咨询和技术故障。森浦内部咨询占比最高，客服Riven接待量最大。",
  "generated_at": "2026-06-25T18:00:00"
}
```

---

## 📈 5. 获取日报

### 请求

```bash
GET /api/reports/daily/{report_date}
```

### 示例

```bash
curl "http://localhost:8000/api/reports/daily/2026-06-25"
```

### 响应

同上（生成日报的响应）

---

## 📅 6. 生成周报

### 请求

```bash
POST /api/reports/weekly?week_start_date=2026-06-23
```

**注意**: `week_start_date` 必须是周一的日期

### 示例

```bash
curl -X POST "http://localhost:8000/api/reports/weekly?week_start_date=2026-06-23"
```

### 响应

```json
{
  "week_start_date": "2026-06-23",
  "week_end_date": "2026-06-29",
  "total_sessions": 185,
  "keywords_json": {
    "网关切换": 35,
    "账户问题": 28,
    "功能咨询": 60,
    "技术故障": 18,
    "其他": 44
  },
  "category_stats_json": {
    "技术问题": 70,
    "业务咨询": 90,
    "账户管理": 25
  },
  "org_distribution_json": {
    "森浦": 95,
    "中信证券": 42,
    "华泰保兴基金管理有限公司": 28,
    "其他": 20
  },
  "service_stats_json": {
    "在线客服 施杰": 55,
    "在线客服 Riven": 78,
    "在线客服 其他": 52
  },
  "daily_trend_json": [
    {"date": "2026-06-23", "sessions": 25},
    {"date": "2026-06-24", "sessions": 30},
    {"date": "2026-06-25", "sessions": 37},
    {"date": "2026-06-26", "sessions": 28},
    {"date": "2026-06-27", "sessions": 32},
    {"date": "2026-06-28", "sessions": 18},
    {"date": "2026-06-29", "sessions": 15}
  ],
  "ai_summary": "本周共接待185个会话，日均26.4个。周三（6月25日）接待量最高。主要问题类型为业务咨询和技术问题，占比分别为48.6%和37.8%。客服Riven工作量最大，接待了42.2%的会话。",
  "generated_at": "2026-06-29T20:00:00"
}
```

---

## 📑 7. 获取日报列表

### 请求

```bash
GET /api/reports/daily/list?date_from=2026-06-01&date_to=2026-06-30
```

### 示例

```bash
curl "http://localhost:8000/api/reports/daily/list?date_from=2026-06-01&date_to=2026-06-30"
```

### 响应

```json
[
  {
    "report_date": "2026-06-25",
    "total_sessions": 37,
    "keywords_json": {...},
    "ai_summary": "...",
    ...
  },
  {
    "report_date": "2026-06-24",
    "total_sessions": 30,
    ...
  }
]
```

---

## 📑 8. 获取周报列表

### 请求

```bash
GET /api/reports/weekly/list
```

### 示例

```bash
curl "http://localhost:8000/api/reports/weekly/list"
```

### 响应

```json
[
  {
    "week_start_date": "2026-06-23",
    "week_end_date": "2026-06-29",
    "total_sessions": 185,
    ...
  },
  {
    "week_start_date": "2026-06-16",
    "week_end_date": "2026-06-22",
    "total_sessions": 162,
    ...
  }
]
```

---

## 🗑️ 9. 删除日报

### 请求

```bash
DELETE /api/reports/daily/{report_date}
```

### 示例

```bash
curl -X DELETE "http://localhost:8000/api/reports/daily/2026-06-25"
```

### 响应

```json
{
  "message": "2026-06-25 的日报已删除"
}
```

---

## 🗑️ 10. 删除周报

### 请求

```bash
DELETE /api/reports/weekly/{week_start_date}
```

### 示例

```bash
curl -X DELETE "http://localhost:8000/api/reports/weekly/2026-06-23"
```

### 响应

```json
{
  "message": "2026-06-23 开始的周报已删除"
}
```

---

## 🔧 错误处理

所有 API 在出错时会返回标准错误格式：

```json
{
  "detail": "错误信息描述"
}
```

常见 HTTP 状态码：
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 💡 使用建议

### 1. 完整工作流程

```bash
# 步骤1: 上传Excel数据
curl -X POST "http://localhost:8000/api/upload" \
  -F "message_file=@messageRecord.xlsx" \
  -F "reception_file=@receptionRecord.xlsx"

# 步骤2: 查看会话列表
curl "http://localhost:8000/api/sessions?date_from=2026-06-25"

# 步骤3: 查看某个会话详情
curl "http://localhost:8000/api/sessions/0c5296aab8e947c9bff4075956ab03c5"

# 步骤4: 生成日报
curl -X POST "http://localhost:8000/api/reports/daily?report_date=2026-06-25"

# 步骤5: 查看日报
curl "http://localhost:8000/api/reports/daily/2026-06-25"

# 步骤6: 周末生成周报
curl -X POST "http://localhost:8000/api/reports/weekly?week_start_date=2026-06-23"
```

### 2. Python 调用示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 上传文件
with open("messageRecord.xlsx", "rb") as msg_file, \
     open("receptionRecord.xlsx", "rb") as rec_file:
    files = {
        "message_file": msg_file,
        "reception_file": rec_file
    }
    response = requests.post(f"{BASE_URL}/api/upload", files=files)
    print(response.json())

# 生成日报
response = requests.post(
    f"{BASE_URL}/api/reports/daily",
    params={"report_date": "2026-06-25"}
)
report = response.json()
print(f"今日总结: {report['ai_summary']}")
```

### 3. JavaScript/前端调用示例

```javascript
// 上传文件
const formData = new FormData();
formData.append('message_file', messageFile);
formData.append('reception_file', receptionFile);

const response = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
});
const result = await response.json();
console.log(result);

// 生成日报
const reportResponse = await fetch(
  'http://localhost:8000/api/reports/daily?report_date=2026-06-25',
  { method: 'POST' }
);
const report = await reportResponse.json();
console.log('AI总结:', report.ai_summary);
```

---

## 📚 更多信息

访问 http://localhost:8000/docs 查看完整的交互式 API 文档（Swagger UI）。

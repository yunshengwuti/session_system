"""
AI 服务 - 占位接口
用于关键词提取、会话总结、日报/周报生成
"""
import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# TODO: 替换为AI服务配置
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_URL = os.getenv("AI_API_URL", "")


async def call_ai_api(prompt: str, system: str = "") -> str:
    """调用智谱 AI API"""
    
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    body = {
        "model": "glm-4-flash-250414",  # 使用带日期的模型名
        "messages": messages
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(AI_API_URL, headers=headers, json=body, timeout=60.0)
        result = response.json()

        # 打印完整响应用于调试
        print(f"\n=== 智谱 API 完整响应 ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"=== 响应结束 ===\n")

        return result["choices"][0]["message"]["content"]



async def generate_daily_report(sessions_data: list) -> dict:
    """生成日报 - 两阶段处理：AI分析样本 + 代码统计全量"""
    from collections import Counter

    total_sessions = len(sessions_data)

    # 统计客服分布
    service_counter = Counter()

    # 整理会话内容
    conversations_text = []

    for session in sessions_data:
        if session.get("customer_service"):
            service_counter[session["customer_service"]] += 1

        # 整理每个会话的对话内容
        conv = f"\n--- 会话 {session['session_id']} ---\n"
        conv += f"客户: {session.get('customer_name', '未知')}\n"
        conv += f"客服: {session.get('customer_service', '未知')}\n"
        conv += f"时长: {session.get('duration_seconds', 0)}秒\n"

        # 添加消息内容
        messages = session.get('messages', [])
        image_count = sum(1 for m in messages if m.get('message_type') == 'image')
        if image_count > 0:
            conv += f"包含 {image_count} 张图片\n"

        conv += "\n对话内容:\n"
        for msg in messages:
            speaker = msg.get('speaker', '未知')
            if msg.get('message_type') == 'image':
                conv += f"{speaker}: [发送了图片]\n"
            else:
                content = msg.get('content', '')
                if content:
                    conv += f"{speaker}: {content}\n"

        conversations_text.append(conv)

    # 统计长时间处理的会话（>30分钟）
    long_duration_sessions = []
    for session in sessions_data:
        duration = session.get('duration_seconds', 0)
        if duration > 1800:  # 30分钟
            long_duration_sessions.append({
                "customer": session.get('customer_name', '未知'),
                "duration": duration // 60,  # 转换为分钟
                "service": session.get('customer_service', '未知')
            })

    # 使用前50个会话样本（避免数据量过大）
    sample_size = min(50, total_sessions)

    # 构建 AI 分析 Prompt
    prompt = f"""你是客服数据分析专家。今日共有 {total_sessions} 个会话，以下是其中 {sample_size} 个代表性会话。

## 实际统计数据（基于全部 {total_sessions} 个会话）：

**长时间处理会话（>30分钟）**：共 {len(long_duration_sessions)} 个
{chr(10).join([f"- {s['customer']} ({s['duration']}分钟，客服：{s['service']})" for s in long_duration_sessions[:10]])}

## 任务1：提取关键问题（keywords）

从样本会话中识别**具体问题**，并估算在全部 {total_sessions} 个会话中的出现次数：
- 格式：{{"具体问题描述": 估算次数}}
- 示例：{{"密码重置": 15, "Excel插件无法使用": 10}}
- **要求**：列出至少15-20个问题

## 任务2：问题业务分类（categories）

归纳4-6个业务分类，每类占比总和为100：
{{
  "categories": {{
    "账户登录类": {{
      "percentage": 25,
      "is_repeated": true,
      "impact_level": "高",
      "actionable_suggestion": "具体建议"
    }}
  }}
}}

## 任务3：今日问题概览（overview）

写3-5段详细分析（每段3-5句）：
1. 整体情况：今日接待 {total_sessions} 个会话，问题分布
2. 高频问题：前3个高频问题及影响
3. 新增异常：是否有异常情况
4. 影响评估：哪些问题影响最大
5. 处理情况：响应速度和解决率

## 任务4：异常与风险（risks）

**基于实际数据识别**：

1. **长时间处理问题**（已统计：{len(long_duration_sessions)} 个超过30分钟）：
   分析这些长时间会话的共同问题是什么

2. **重复性问题**：
   从关键问题中，识别出现次数>10的作为高频重复问题

3. **未解决问题**：
   从样本中识别哪些问题未得到明确解决

4. **集中爆发问题**：
   是否有某类问题集中出现

每个风险必须包含：
- 具体问题描述（说清楚是什么问题）
- 影响客户数（基于统计或估算）
- 紧急程度（高/中/低）
- 建议处理方式

## 任务5：行动建议（suggestions）

提出5-8条可执行建议

## 输出格式（纯JSON）：
{{
  "keywords": {{"问题1": 次数, ...}},
  "categories": {{...}},
  "overview": "3-5段详细分析",
  "risks": [
    {{
      "risk_type": "长时间处理问题",
      "description": "具体什么问题",
      "affected_customers": 数字,
      "urgency": "高/中/低",
      "suggestion": "具体建议"
    }}
  ],
  "suggestions": [...]
}}

## 样本会话数据（{sample_size}/{total_sessions}）：
{chr(10).join(conversations_text[:sample_size])}
"""

    # 调用 AI
    try:
        ai_response = await call_ai_api(prompt, system="你是专业的客服数据分析助手，擅长从样本中发现问题模式")

        print(f"\n=== AI 原始返回 ===")
        print(ai_response[:1000])  # 只打印前1000字符
        print(f"=== 返回结束 ===\n")

        # 清理 AI 返回
        cleaned_response = ai_response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        first_brace = cleaned_response.find('{')
        last_brace = cleaned_response.rfind('}')
        if first_brace != -1 and last_brace != -1:
            cleaned_response = cleaned_response[first_brace:last_brace + 1]

        cleaned_response = cleaned_response.replace('"', '"').replace('"', '"')
        cleaned_response = cleaned_response.replace(''', "'").replace(''', "'")

        ai_result = json.loads(cleaned_response)

        # 处理动态分类数据
        categories = ai_result.get("categories", {})
        category_stats = {}

        for category, data in categories.items():
            if isinstance(data, dict):
                category_stats[category] = data.get("percentage", 0)
            else:
                category_stats[category] = data

        # 处理关键问题统计
        keywords = ai_result.get("keywords", {})

        # 处理风险数据，统一字段名
        risks = ai_result.get("risks", [])
        formatted_risks = []
        for risk in risks:
            formatted_risks.append({
                "risk_type": risk.get("type", risk.get("risk_type", "未知")),
                "description": risk.get("description", ""),
                "affected_customers": risk.get("affected_people", risk.get("affected_customers", 0)),
                "urgency": risk.get("urgency", "低"),
                "suggestion": risk.get("suggestion", "")
            })

        # 整合风险和建议
        org_distribution_data = {
            "risks": formatted_risks,
            "suggestions": ai_result.get("suggestions", [])
        }

        return {
            "keywords_json": keywords,
            "category_stats_json": category_stats,
            "long_duration_issues": ai_result.get("overview", ""),
            "org_distribution_json": org_distribution_data,
            "service_stats_json": dict(service_counter),
            "ai_summary": ""  # 删除日报总结，避免与今日概览重复
        }
    except Exception as e:
        print(f"\n❌ AI 调用失败: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "keywords_json": {"分析失败": 1},
            "category_stats_json": {"未分类": 100},
            "long_duration_issues": f"AI 分析失败: {str(e)}",
            "org_distribution_json": {},
            "service_stats_json": dict(service_counter),
            "ai_summary": f"今日共计 {total_sessions} 个会话（AI 分析失败）"
        }



async def generate_weekly_report(week_sessions_data: list, daily_reports: list) -> dict:
    """
    生成周报

    Args:
        week_sessions_data: 本周所有会话数据
        daily_reports: 本周每日报告列表

    Returns:
        {
            "keywords_json": {...},
            "category_stats_json": {...},
            "org_distribution_json": {...},
            "service_stats_json": {...},
            "daily_trend_json": [{"date": "2026-06-23", "sessions": 10}, ...],
            "ai_summary": "本周共接待X个会话..."
        }
    """
    # TODO: 实现AI周报生成逻辑

    # 占位实现
    from collections import Counter

    total_sessions = len(week_sessions_data)

    # 统计机构和客服
    org_counter = Counter()
    service_counter = Counter()

    for session in week_sessions_data:
        if session.get("org_name"):
            org_counter[session["org_name"]] += 1
        if session.get("customer_service"):
            service_counter[session["customer_service"]] += 1

    # 每日趋势（从daily_reports提取）
    daily_trend = []
    for report in daily_reports:
        daily_trend.append({
            "date": str(report["report_date"]),
            "sessions": report["total_sessions"]
        })

    return {
        "keywords_json": {"占位关键词": total_sessions},
        "category_stats_json": {"占位分类": 100},
        "org_distribution_json": dict(org_counter),
        "service_stats_json": dict(service_counter),
        "daily_trend_json": daily_trend,
        "ai_summary": f"本周共接待 {total_sessions} 个会话。（占位数据，请实现AI接口）"
    }

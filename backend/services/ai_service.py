"""
AI 服务 - 分批处理版本
用于关键词提取、会话总结、日报/周报生成
"""
import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

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
        "model": "glm-4-flash-250414",
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
    """生成日报 - 分批处理所有会话"""

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
    long_duration_problems = []  # 记录长时间会话的问题内容

    for session in sessions_data:
        duration = session.get('duration_seconds', 0)
        if duration > 1800:  # 30分钟
            # 提取该会话的主要问题（从消息中）
            messages = session.get('messages', [])
            problem_desc = ""
            for msg in messages[:5]:  # 只看前5条消息，通常包含问题描述
                if msg.get('speaker') == '客户' or '客户' in msg.get('speaker', ''):
                    content = msg.get('content', '')
                    if content and len(content) > 10:
                        problem_desc = content[:100]  # 取前100字符
                        break

            long_duration_sessions.append({
                "duration": duration // 60,
                "problem": problem_desc if problem_desc else "未知问题"
            })

            if problem_desc:
                long_duration_problems.append(problem_desc)

    # 分批处理：每批30个会话
    batch_size = 30
    all_keywords = Counter()
    all_categories = Counter()

    print(f"\n📊 开始分批分析 {total_sessions} 个会话，每批 {batch_size} 个...\n")

    import asyncio  # 用于延迟

    for i in range(0, total_sessions, batch_size):
        batch = conversations_text[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_sessions + batch_size - 1) // batch_size

        print(f"🔄 分析第 {batch_num}/{total_batches} 批（{len(batch)} 个会话）...")

        # 在每批之间添加延迟，避免触发速率限制
        if batch_num > 1:
            print(f"⏱️  等待3秒避免速率限制...")
            await asyncio.sleep(3)

        batch_prompt = f"""你是客服数据分析专家。这是第 {batch_num}/{total_batches} 批会话，共 {len(batch)} 个。

## 任务1：提取具体问题

仔细阅读每个对话，自己总结出客户遇到的**具体问题**：
- 要具体，不要笼统（如"Excel插件无法使用"而不是"Excel问题"）
- 统计每个问题在这批对话中出现的次数
- 格式：{{"具体问题描述": 出现次数}}

示例仅供参考，实际请根据对话内容自己总结：
{{"Excel插件无法使用": 3, "密码重置流程不清楚": 2, "BDB权限需要申请": 5}}

## 任务2：问题分类

根据你提取的具体问题，自己归纳出合适的业务分类：
- 格式：{{"分类名": 会话数}}
- 分类名称自己定义，要能准确反映问题性质

## 输出格式（纯JSON）：
{{
  "keywords": {{"具体问题1": 次数, "具体问题2": 次数}},
  "categories": {{"分类1": 会话数, "分类2": 会话数}}
}}

## 会话数据：
{chr(10).join(batch)}
"""

        try:
            batch_response = await call_ai_api(batch_prompt, system="你是数据分析助手")

            # 清理返回
            cleaned = batch_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            first_brace = cleaned.find('{')
            last_brace = cleaned.rfind('}')
            if first_brace != -1 and last_brace != -1:
                cleaned = cleaned[first_brace:last_brace + 1]

            cleaned = cleaned.replace('"', '"').replace('"', '"')

            batch_result = json.loads(cleaned)

            # 汇总关键问题
            for keyword, count in batch_result.get("keywords", {}).items():
                all_keywords[keyword] += count

            # 汇总分类
            for category, count in batch_result.get("categories", {}).items():
                all_categories[category] += count

            print(f"✅ 第 {batch_num} 批完成")

        except Exception as e:
            print(f"⚠️ 第 {batch_num} 批分析失败: {str(e)}")
            continue

    print(f"\n📊 所有批次分析完成，开始生成综合报告...\n")

    # 等待5秒再生成综合报告，避免速率限制
    print(f"⏱️  等待5秒避免速率限制...")
    await asyncio.sleep(5)

    # 生成综合分析报告
    summary_prompt = f"""你是客服数据分析专家。今日共接待 {total_sessions} 个会话，已完成分批关键词统计。

## 汇总数据：

**高频关键词统计**（对话中出现的关键词及频次）：
{json.dumps(dict(all_keywords.most_common(30)), ensure_ascii=False, indent=2)}

**问题分类统计**：
{json.dumps(dict(all_categories), ensure_ascii=False, indent=2)}

**长时间处理会话（>30分钟）**：共 {len(long_duration_sessions)} 个
具体问题：
{chr(10).join([f"- {s['duration']}分钟: {s['problem']}" for s in long_duration_sessions[:10]])}

## 任务：生成简洁实用的日报

1. **今日问题概览**（2-3段即可，不要流水账）：
   - 直接说重点：今日最突出的问题是什么（基于高频关键词）
   - 是否有异常情况（如某个关键词突然暴增）
   - 客户反馈的核心诉求

2. **异常与风险**（只列出**实际存在的风险**，没有就不写）：
   - 基于数据判断，不要臆测
   - 如果某关键词频次超过会话数20%，说明可能是系统性问题
   - 长时间处理的会话有什么共同特征

3. **行动建议**（3-5条，必须是**针对今日实际问题**的具体建议）：
   - 不要说"加强培训"、"优化流程"这种空话
   - 要说具体做什么，比如"修复Excel插件入口缺失问题"、"增加密码重置的自助引导"
   - 只针对高频问题和风险提建议
 
## 输出格式（纯JSON）：
{{
  "overview": "2-3段，直接说重点，不要流水账",
  "risks": [
    {{
      "risk_type": "类型",
      "description": "具体问题",
      "affected_customers": 数字,
      "urgency": "高/中/低",
      "suggestion": "具体建议"
    }}
  ],
  "suggestions": [
    "针对XX问题的具体建议1",
    "针对YY问题的具体建议2",
    "针对ZZ问题的具体建议3"
  ]
}}
"""

    try:
        summary_response = await call_ai_api(summary_prompt, system="你是专业的数据分析助手")

        # 清理返回
        cleaned = summary_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1:
            cleaned = cleaned[first_brace:last_brace + 1]

        cleaned = cleaned.replace('"', '"').replace('"', '"')

        summary_result = json.loads(cleaned)

        # 计算分类占比
        total_category_count = sum(all_categories.values())
        category_stats = {}
        for category, count in all_categories.items():
            percentage = (count / total_category_count * 100) if total_category_count > 0 else 0
            category_stats[category] = round(percentage, 1)

        # 处理风险数据
        risks = summary_result.get("risks", [])
        formatted_risks = []
        for risk in risks:
            formatted_risks.append({
                "risk_type": risk.get("type", risk.get("risk_type", "未知")),
                "description": risk.get("description", ""),
                "affected_customers": risk.get("affected_people", risk.get("affected_customers", 0)),
                "urgency": risk.get("urgency", "低"),
                "suggestion": risk.get("suggestion", "")
            })

        org_distribution_data = {
            "risks": formatted_risks,
            "suggestions": summary_result.get("suggestions", []),
            "key_problems": summary_result.get("key_problems", []),
            "category_analysis": summary_result.get("category_analysis", "")
        }

        return {
            "keywords_json": dict(all_keywords),
            "category_stats_json": category_stats,
            "long_duration_issues": summary_result.get("overview", ""),
            "org_distribution_json": org_distribution_data,
            "service_stats_json": dict(service_counter),
            "ai_summary": ""
        }

    except Exception as e:
        print(f"\n❌ 综合报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()

        # 即使综合报告失败，也返回已汇总的数据
        total_category_count = sum(all_categories.values())
        category_stats = {}
        for category, count in all_categories.items():
            percentage = (count / total_category_count * 100) if total_category_count > 0 else 0
            category_stats[category] = round(percentage, 1)

        return {
            "keywords_json": dict(all_keywords) if all_keywords else {"分析失败": 1},
            "category_stats_json": category_stats if all_categories else {"未分类": 100},
            "long_duration_issues": f"综合报告生成失败: {str(e)}",
            "org_distribution_json": {},
            "service_stats_json": dict(service_counter),
            "ai_summary": ""
        }


async def generate_weekly_report(week_sessions_data: list, daily_reports: list) -> dict:
    """生成周报（占位）"""
    from collections import Counter

    total_sessions = len(week_sessions_data)

    # 统计机构和客服分布
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

"""
统计相关 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta, datetime

from config.database import get_db
from models.database import Session, Message, DailyReport, WeeklyReport
from models.schemas import DailyReportOut, WeeklyReportOut
from services.ai_service import generate_daily_report, generate_weekly_report

router = APIRouter(prefix="/api/reports", tags=["报告"])


# 列表路由必须在参数路由之前
@router.get("/daily/list")
def list_daily_reports(
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    db: DBSession = Depends(get_db),
):
    """获取日报列表"""
    query = db.query(DailyReport)

    if date_from:
        query = query.filter(DailyReport.report_date >= date_from)
    if date_to:
        query = query.filter(DailyReport.report_date <= date_to)

    reports = query.order_by(DailyReport.report_date.desc()).all()
    return {"reports": reports}


@router.get("/weekly/list")
def list_weekly_reports(
    db: DBSession = Depends(get_db),
):
    """获取周报列表"""
    reports = db.query(WeeklyReport).order_by(WeeklyReport.week_start_date.desc()).all()
    return reports


@router.post("/daily", response_model=DailyReportOut)
async def create_daily_report(
    report_date: date = Query(..., description="报告日期"),
    db: DBSession = Depends(get_db),
):
    """生成某天的AI日报"""
    # 检查是否已存在
    existing = db.query(DailyReport).filter(DailyReport.report_date == report_date).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{report_date} 的日报已存在，如需重新生成请先删除")

    # 获取当天所有会话数据
    sessions = db.query(Session).filter(Session.session_date == report_date).all()

    if not sessions:
        raise HTTPException(status_code=404, detail=f"{report_date} 没有会话数据")

    # 准备数据给AI
    sessions_data = []
    for s in sessions:
        messages = db.query(Message).filter(Message.session_id == s.session_id).order_by(Message.message_time).all()
        messages_list = [
            {
                "speaker": m.speaker,
                "content": m.content,
                "message_type": m.message_type,
                "image_url": m.image_url,
            }
            for m in messages
        ]

        sessions_data.append({
            "session_id": s.session_id,
            "customer_name": s.customer_name,
            "org_name": s.org_name,
            "customer_service": s.customer_service,
            "duration_seconds": s.duration_seconds,
            "messages": messages_list,
        })

    # 调用AI生成报告
    report_result = await generate_daily_report(sessions_data)

    # 保存到数据库
    daily_report = DailyReport(
        report_date=report_date,
        total_sessions=len(sessions),
        keywords_json=report_result.get("keywords_json"),
        category_stats_json=report_result.get("category_stats_json"),
        long_duration_issues=report_result.get("long_duration_issues"),
        org_distribution_json=report_result.get("org_distribution_json"),
        service_stats_json=report_result.get("service_stats_json"),
        ai_summary=report_result.get("ai_summary"),
        generated_at=datetime.now(),
    )
    db.add(daily_report)
    db.commit()
    db.refresh(daily_report)

    return daily_report


@router.get("/daily/{report_date}", response_model=DailyReportOut)
def get_daily_report(
    report_date: date,
    db: DBSession = Depends(get_db),
):
    """获取某天的日报"""
    report = db.query(DailyReport).filter(DailyReport.report_date == report_date).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"{report_date} 的日报不存在")
    return report


@router.delete("/daily/{report_date}")
def delete_daily_report(
    report_date: date,
    db: DBSession = Depends(get_db),
):
    """删除某天的日报"""
    report = db.query(DailyReport).filter(DailyReport.report_date == report_date).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"{report_date} 的日报不存在")

    db.delete(report)
    db.commit()
    return {"message": f"{report_date} 的日报已删除"}


@router.post("/weekly", response_model=WeeklyReportOut)
async def create_weekly_report(
    start_date: date = Query(..., description="周报开始日期"),
    end_date: date = Query(..., description="周报结束日期"),
    db: DBSession = Depends(get_db),
):
    """生成周报（自动剔除周末，工作日3-5天）"""

    # 1. 验证时间段
    delta_days = (end_date - start_date).days + 1
    if not (3 <= delta_days <= 7):
        raise HTTPException(status_code=400, detail="时间段必须为3-7天")

    # 2. 获取时间段内的所有工作日（周一到周五）
    workdays = []
    for i in range(delta_days):
        day = start_date + timedelta(days=i)
        # 0=周一, 1=周二, ..., 4=周五, 5=周六, 6=周日
        if day.weekday() < 5:  # 工作日
            workdays.append(day)

    # 验证工作日数量
    if len(workdays) < 3:
        raise HTTPException(
            status_code=400,
            detail=f"时间段内工作日不足3天（当前{len(workdays)}天），请重新选择"
        )

    if len(workdays) > 5:
        raise HTTPException(
            status_code=400,
            detail=f"时间段内工作日超过5天（当前{len(workdays)}天），建议选择周一到周五"
        )

    print(f"\n📅 选择的时间段：{start_date} ~ {end_date}")
    print(f"📅 工作日：{workdays} (共{len(workdays)}天)\n")

    # 检查是否已存在
    existing = db.query(WeeklyReport).filter(
        WeeklyReport.week_start_date == start_date,
        WeeklyReport.week_end_date == end_date
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"{start_date} ~ {end_date} 的周报已存在，如需重新生成请先删除"
        )

    # 3. 检查并补齐工作日的日报
    missing_dates = []
    existing_reports = {}

    for day in workdays:
        daily_report = db.query(DailyReport).filter(DailyReport.report_date == day).first()

        if daily_report:
            existing_reports[day] = daily_report
            print(f"✅ {day} 日报已存在")
        else:
            missing_dates.append(day)

    # 4. 生成缺失的日报
    if missing_dates:
        print(f"\n📋 需要生成 {len(missing_dates)} 份日报：{missing_dates}\n")

        for missing_date in missing_dates:
            # 获取该日期的会话数据
            sessions = db.query(Session).filter(
                Session.session_date == missing_date
            ).all()

            if not sessions:
                raise HTTPException(
                    status_code=404,
                    detail=f"工作日 {missing_date} 没有会话数据，无法生成周报"
                )

            # 准备会话数据
            sessions_data = []
            for s in sessions:
                messages = db.query(Message).filter(
                    Message.session_id == s.session_id
                ).order_by(Message.message_time).all()

                messages_list = [
                    {
                        "speaker": m.speaker,
                        "content": m.content,
                        "message_type": m.message_type,
                    }
                    for m in messages
                ]

                sessions_data.append({
                    "session_id": s.session_id,
                    "customer_name": s.customer_name,
                    "org_name": s.org_name,
                    "customer_service": s.customer_service,
                    "duration_seconds": s.duration_seconds,
                    "session_date": s.session_date,
                    "messages": messages_list,
                })

            # 生成日报
            print(f"📊 生成 {missing_date} 的日报（共{len(sessions_data)}个会话）...")
            report_result = await generate_daily_report(sessions_data)

            # 保存日报
            daily_report = DailyReport(
                report_date=missing_date,
                total_sessions=len(sessions_data),
                keywords_json=report_result["keywords_json"],
                category_stats_json=report_result["category_stats_json"],
                long_duration_issues=report_result["long_duration_issues"],
                org_distribution_json=report_result["org_distribution_json"],
                service_stats_json=report_result["service_stats_json"],
                ai_summary=report_result.get("ai_summary", "")
            )
            db.add(daily_report)
            db.commit()
            db.refresh(daily_report)

            existing_reports[missing_date] = daily_report
            print(f"✅ {missing_date} 日报生成完成\n")

    # 5. 收集所有工作日的日报数据
    daily_reports_data = []
    for day in workdays:
        daily_report = existing_reports[day]
        daily_reports_data.append({
            "report_date": daily_report.report_date,
            "total_sessions": daily_report.total_sessions,
            "keywords_json": daily_report.keywords_json,
            "category_stats_json": daily_report.category_stats_json,
            "long_duration_issues": daily_report.long_duration_issues,
            "org_distribution_json": daily_report.org_distribution_json,
            "service_stats_json": daily_report.service_stats_json,
        })

    # 6. 生成周报
    print(f"\n📊 开始生成周报（{start_date} ~ {end_date}，{len(workdays)}个工作日）...\n")
    weekly_result = await generate_weekly_report([], daily_reports_data)

    # 7. 保存周报
    weekly_report = WeeklyReport(
        week_start_date=start_date,
        week_end_date=end_date,
        total_sessions=sum([r["total_sessions"] for r in daily_reports_data]),
        keywords_json=weekly_result["keywords_json"],
        category_stats_json=weekly_result["category_stats_json"],
        org_distribution_json=weekly_result["org_distribution_json"],
        service_stats_json=weekly_result["service_stats_json"],
        daily_trend_json=weekly_result["daily_trend_json"],
        ai_summary=weekly_result["ai_summary"]
    )
    db.add(weekly_report)
    db.commit()
    db.refresh(weekly_report)

    print(f"✅ 周报生成完成\n")

    return weekly_report

    # 调用AI生成周报
    report_result = await generate_weekly_report(week_sessions_data, daily_reports_data)

    # 保存到数据库
    weekly_report = WeeklyReport(
        week_start_date=week_start_date,
        week_end_date=week_end_date,
        total_sessions=len(sessions),
        keywords_json=report_result.get("keywords_json"),
        category_stats_json=report_result.get("category_stats_json"),
        org_distribution_json=report_result.get("org_distribution_json"),
        service_stats_json=report_result.get("service_stats_json"),
        daily_trend_json=report_result.get("daily_trend_json"),
        ai_summary=report_result.get("ai_summary"),
        generated_at=datetime.now(),
    )
    db.add(weekly_report)
    db.commit()
    db.refresh(weekly_report)

    return weekly_report


@router.get("/weekly/{week_start_date}", response_model=WeeklyReportOut)
def get_weekly_report(
    week_start_date: date,
    db: DBSession = Depends(get_db),
):
    """获取某周的周报"""
    report = db.query(WeeklyReport).filter(WeeklyReport.week_start_date == week_start_date).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"{week_start_date} 开始的周报不存在")
    return report


@router.delete("/weekly/{week_start_date}")
def delete_weekly_report(
    week_start_date: date,
    db: DBSession = Depends(get_db),
):
    """删除某周的周报"""
    report = db.query(WeeklyReport).filter(WeeklyReport.week_start_date == week_start_date).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"{week_start_date} 开始的周报不存在")

    db.delete(report)
    db.commit()
    return {"message": f"{week_start_date} 开始的周报已删除"}

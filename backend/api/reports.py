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
    return {"reports": reports}


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
    week_start_date: date = Query(..., description="周开始日期（周一）"),
    db: DBSession = Depends(get_db),
):
    """生成某周的AI周报（周一到周日）"""
    # 检查是否已存在
    existing = db.query(WeeklyReport).filter(WeeklyReport.week_start_date == week_start_date).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{week_start_date} 开始的周报已存在，如需重新生成请先删除")

    # 计算周结束日期（周日）
    week_end_date = week_start_date + timedelta(days=6)

    # 获取本周所有会话数据
    sessions = db.query(Session).filter(
        Session.session_date >= week_start_date,
        Session.session_date <= week_end_date
    ).all()

    if not sessions:
        raise HTTPException(status_code=404, detail=f"{week_start_date} ~ {week_end_date} 没有会话数据")

    # 准备数据
    week_sessions_data = []
    for s in sessions:
        messages = db.query(Message).filter(Message.session_id == s.session_id).order_by(Message.message_time).all()
        messages_list = [
            {
                "speaker": m.speaker,
                "content": m.content,
                "message_type": m.message_type,
            }
            for m in messages
        ]

        week_sessions_data.append({
            "session_id": s.session_id,
            "customer_name": s.customer_name,
            "org_name": s.org_name,
            "customer_service": s.customer_service,
            "duration_seconds": s.duration_seconds,
            "session_date": s.session_date,
            "messages": messages_list,
        })

    # 获取本周每日报告（如果有）
    daily_reports_data = []
    for i in range(7):
        day = week_start_date + timedelta(days=i)
        daily_report = db.query(DailyReport).filter(DailyReport.report_date == day).first()
        if daily_report:
            daily_reports_data.append({
                "report_date": daily_report.report_date,
                "total_sessions": daily_report.total_sessions,
                "keywords_json": daily_report.keywords_json,
                "category_stats_json": daily_report.category_stats_json,
                "ai_summary": daily_report.ai_summary,
            })

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

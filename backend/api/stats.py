"""
统计相关 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta

from config.database import get_db
from models.database import Session, Message, Summary, DailyStat
from models.schemas import DailyStatOut, WeeklyStatOut
from services.ai_service import generate_daily_summary, generate_weekly_summary

router = APIRouter(prefix="/api/stats", tags=["统计"])


@router.get("/daily", response_model=DailyStatOut)
def get_daily_stats(
    stat_date: date = Query(..., description="统计日期"),
    db: DBSession = Depends(get_db),
):
    """获取某天的统计数据"""
    # 先查缓存
    cached = db.query(DailyStat).filter(DailyStat.stat_date == stat_date).first()
    if cached:
        return cached

    # 实时计算
    total = db.query(func.count(Session.id)).filter(Session.session_date == stat_date).scalar()
    internal = (
        db.query(func.count(Session.id))
        .filter(Session.session_date == stat_date, Session.org_name == "森浦")
        .scalar()
    )
    external = total - internal

    return DailyStatOut(
        stat_date=stat_date,
        total_sessions=total,
        valid_sessions=total,
        internal_sessions=internal,
        external_sessions=external,
    )


@router.get("/weekly", response_model=WeeklyStatOut)
def get_weekly_stats(
    end_date: date = Query(..., description="周末日期"),
    db: DBSession = Depends(get_db),
):
    """获取某周的统计数据"""
    start_date = end_date - timedelta(days=6)

    daily_list = []
    total_sessions = 0

    for i in range(7):
        d = start_date + timedelta(days=i)
        count = db.query(func.count(Session.id)).filter(Session.session_date == d).scalar()
        internal = (
            db.query(func.count(Session.id))
            .filter(Session.session_date == d, Session.org_name == "森浦")
            .scalar()
        )
        daily_list.append(
            DailyStatOut(
                stat_date=d,
                total_sessions=count,
                valid_sessions=count,
                internal_sessions=internal,
                external_sessions=count - internal,
            )
        )
        total_sessions += count

    return WeeklyStatOut(
        start_date=start_date,
        end_date=end_date,
        total_sessions=total_sessions,
        daily_breakdown=daily_list,
    )


@router.get("/trend")
def get_trend(
    days: int = Query(7, ge=1, le=90, description="最近N天"),
    db: DBSession = Depends(get_db),
):
    """获取趋势数据，供前端图表使用"""
    today = date.today()
    result = []

    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        count = db.query(func.count(Session.id)).filter(Session.session_date == d).scalar()
        internal = (
            db.query(func.count(Session.id))
            .filter(Session.session_date == d, Session.org_name == "森浦")
            .scalar()
        )
        result.append({
            "date": str(d),
            "total": count,
            "internal": internal,
            "external": count - internal,
        })

    return result


@router.post("/daily-report")
async def generate_daily_report(
    stat_date: date = Query(..., description="日报日期"),
    db: DBSession = Depends(get_db),
):
    """生成AI日报"""
    sessions = db.query(Session).filter(Session.session_date == stat_date).all()

    if not sessions:
        return {"report": "当天无会话数据"}

    # 汇总信息
    summaries = []
    for s in sessions:
        summary = db.query(Summary).filter(Summary.session_id == s.session_id).first()
        info = f"客户:{s.customer_name or '未知'} 机构:{s.org_name or '未知'}"
        if summary:
            info += f" 问题:{summary.summary} 分类:{summary.category}"
        summaries.append(info)

    sessions_info = f"日期: {stat_date}\n总会话数: {len(sessions)}\n\n" + "\n".join(summaries)

    report = await generate_daily_summary(sessions_info)

    # 缓存到数据库
    stat = db.query(DailyStat).filter(DailyStat.stat_date == stat_date).first()
    if stat:
        stat.ai_summary = report
    else:
        stat = DailyStat(
            stat_date=stat_date,
            total_sessions=len(sessions),
            ai_summary=report,
        )
        db.add(stat)
    db.commit()

    return {"date": str(stat_date), "report": report}

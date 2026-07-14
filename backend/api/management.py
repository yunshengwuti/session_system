"""
数据管理 API
"""
import os
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from config.database import get_db, engine
from models.database import Session, Message, DailyReport, WeeklyReport, ReportTask

router = APIRouter(prefix="/api/management", tags=["数据管理"])


def validate_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")


def task_in_range(task: ReportTask, start_date: date, end_date: date) -> bool:
    try:
        if task.report_type == "daily":
            target = date.fromisoformat(task.target_key)
            return start_date <= target <= end_date
        if task.report_type == "weekly" and ":" in task.target_key:
            start_text, end_text = task.target_key.split(":", 1)
            task_start = date.fromisoformat(start_text)
            task_end = date.fromisoformat(end_text)
            return task_start <= end_date and task_end >= start_date
    except ValueError:
        return False
    return False


def get_counts(db: DBSession) -> dict:
    return {
        "sessions": db.query(Session).count(),
        "messages": db.query(Message).count(),
        "daily_reports": db.query(DailyReport).count(),
        "weekly_reports": db.query(WeeklyReport).count(),
        "report_tasks": db.query(ReportTask).count(),
    }


def get_range_counts(db: DBSession, start_date: date, end_date: date) -> dict:
    validate_range(start_date, end_date)
    session_ids = [
        row[0]
        for row in db.query(Session.session_id)
        .filter(Session.session_date >= start_date, Session.session_date <= end_date)
        .all()
    ]

    message_count = 0
    if session_ids:
        message_count = db.query(Message).filter(Message.session_id.in_(session_ids)).count()

    weekly_reports = db.query(WeeklyReport).filter(
        WeeklyReport.week_start_date <= end_date,
        WeeklyReport.week_end_date >= start_date,
    ).all()

    tasks = db.query(ReportTask).all()
    task_count = sum(1 for task in tasks if task_in_range(task, start_date, end_date))

    return {
        "sessions": len(session_ids),
        "messages": message_count,
        "daily_reports": db.query(DailyReport).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
        ).count(),
        "weekly_reports": len(weekly_reports),
        "report_tasks": task_count,
    }


def get_storage_info(db: DBSession) -> dict:
    dialect = engine.dialect.name
    used_bytes = 0

    if dialect == "postgresql":
        used_bytes = db.execute(text("select pg_database_size(current_database())")).scalar() or 0
    elif dialect == "mysql":
        used_bytes = db.execute(text("""
            select coalesce(sum(data_length + index_length), 0)
            from information_schema.tables
            where table_schema = database()
        """)).scalar() or 0

    used_mb = round(used_bytes / 1024 / 1024, 2)
    limit_mb = float(os.getenv("DB_STORAGE_LIMIT_MB", "512"))
    used_percent = round((used_mb / limit_mb * 100), 2) if limit_mb > 0 else 0

    return {
        "dialect": dialect,
        "used_bytes": used_bytes,
        "used_mb": used_mb,
        "limit_mb": limit_mb,
        "used_percent": used_percent,
    }


@router.get("/storage")
def storage_overview(db: DBSession = Depends(get_db)):
    """获取数据库容量和数据数量"""
    return {
        "storage": get_storage_info(db),
        "counts": get_counts(db),
    }


@router.get("/cleanup/preview")
def cleanup_preview(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: DBSession = Depends(get_db),
):
    """预览指定日期范围内会影响的数据量"""
    return {
        "counts": get_range_counts(db, start_date, end_date),
        "scope": "range",
        "start_date": start_date,
        "end_date": end_date,
    }


@router.delete("/cleanup/range")
def cleanup_range(
    confirm: str,
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    db: DBSession = Depends(get_db),
):
    """清除指定日期范围内的会话、消息、日报、周报和任务记录"""
    if confirm != "CLEAR_RANGE":
        raise HTTPException(status_code=400, detail="确认参数错误")

    validate_range(start_date, end_date)
    before = get_range_counts(db, start_date, end_date)

    try:
        session_ids = [
            row[0]
            for row in db.query(Session.session_id)
            .filter(Session.session_date >= start_date, Session.session_date <= end_date)
            .all()
        ]
        if session_ids:
            db.query(Message).filter(Message.session_id.in_(session_ids)).delete(synchronize_session=False)
            db.query(Session).filter(Session.session_id.in_(session_ids)).delete(synchronize_session=False)

        db.query(DailyReport).filter(
            DailyReport.report_date >= start_date,
            DailyReport.report_date <= end_date,
        ).delete(synchronize_session=False)

        weekly_reports = db.query(WeeklyReport).filter(
            WeeklyReport.week_start_date <= end_date,
            WeeklyReport.week_end_date >= start_date,
        ).all()
        for report in weekly_reports:
            db.delete(report)

        tasks = db.query(ReportTask).all()
        for task in tasks:
            if task_in_range(task, start_date, end_date):
                db.delete(task)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "指定日期范围内的数据已清除",
        "deleted": before,
        "storage": get_storage_info(db),
        "counts": get_counts(db),
    }

"""
数据管理 API
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session as DBSession

from config.database import get_db, engine
from models.database import Session, Message, DailyReport, WeeklyReport, ReportTask

router = APIRouter(prefix="/api/management", tags=["数据管理"])


def get_counts(db: DBSession) -> dict:
    return {
        "sessions": db.query(Session).count(),
        "messages": db.query(Message).count(),
        "daily_reports": db.query(DailyReport).count(),
        "weekly_reports": db.query(WeeklyReport).count(),
        "report_tasks": db.query(ReportTask).count(),
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
def cleanup_preview(db: DBSession = Depends(get_db)):
    """预览全部清除会影响的数据量"""
    return {
        "counts": get_counts(db),
        "scope": "all",
    }


@router.delete("/cleanup/all")
def cleanup_all(confirm: str, db: DBSession = Depends(get_db)):
    """全部清除会话、消息、日报、周报和任务记录"""
    if confirm != "CLEAR_ALL":
        raise HTTPException(status_code=400, detail="确认参数错误")

    before = get_counts(db)
    dialect = engine.dialect.name

    try:
        if dialect == "postgresql":
            db.execute(text(
                "TRUNCATE TABLE messages, sessions, daily_reports, weekly_reports, report_tasks "
                "RESTART IDENTITY CASCADE"
            ))
        elif dialect == "mysql":
            db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for table in ["messages", "sessions", "daily_reports", "weekly_reports", "report_tasks"]:
                db.execute(text(f"TRUNCATE TABLE {table}"))
            db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        else:
            db.query(Message).delete(synchronize_session=False)
            db.query(Session).delete(synchronize_session=False)
            db.query(DailyReport).delete(synchronize_session=False)
            db.query(WeeklyReport).delete(synchronize_session=False)
            db.query(ReportTask).delete(synchronize_session=False)

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "数据已全部清除",
        "deleted": before,
        "storage": get_storage_info(db),
        "counts": get_counts(db),
    }

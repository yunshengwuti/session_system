"""
会话相关 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session as DBSession, joinedload
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime

from config.database import get_db
from models.database import Session, Message
from models.schemas import SessionListItem, SessionDetail, SessionListResponse

router = APIRouter(prefix="/api/sessions", tags=["会话"])


@router.get("", response_model=SessionListResponse)
def list_sessions(
    session_date: Optional[date] = Query(None, description="会话日期"),
    customer_name: Optional[str] = Query(None, description="客户名称"),
    org_name: Optional[str] = Query(None, description="机构名称"),
    customer_service: Optional[str] = Query(None, description="客服名称"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: DBSession = Depends(get_db),
):
    """获取会话列表，支持单一或组合筛选"""
    query = db.query(Session)

    # 每个条件都是可选的，只有提供了才添加过滤
    if session_date:
        query = query.filter(Session.session_date == session_date)
    if customer_name:
        query = query.filter(Session.customer_name.contains(customer_name))
    if org_name:
        query = query.filter(Session.org_name.contains(org_name))
    if customer_service:
        query = query.filter(Session.customer_service.contains(customer_service))

    total = query.count()
    sessions = (
        query.order_by(Session.session_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    result = []
    for s in sessions:
        msg_count = db.query(func.count(Message.session_id)).filter(Message.session_id == s.session_id).scalar()
        result.append(
            SessionListItem(
                session_id=s.session_id,
                customer_name=s.customer_name,
                org_name=s.org_name,
                customer_service=s.customer_service,
                duration_seconds=s.duration_seconds,
                session_date=s.session_date,
                message_count=msg_count,
            )
        )

    return SessionListResponse(sessions=result, total=total, page=page, page_size=page_size)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session_detail(session_id: str, db: DBSession = Depends(get_db)):
    """获取会话详情，含所有消息"""
    session = (
        db.query(Session)
        .options(joinedload(Session.messages))
        .filter(Session.session_id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 按时间排序消息
    session.messages.sort(key=lambda m: m.message_time if m.message_time else datetime.min)

    return session

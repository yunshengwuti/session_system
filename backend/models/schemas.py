"""
Pydantic 模型，用于 API 请求和响应
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ---- 消息 ----
class MessageOut(BaseModel):
    speaker: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    message_type: str = "text"
    message_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---- 会话 ----
class SessionListItem(BaseModel):
    """列表页用的简略信息"""
    session_id: str
    customer_name: Optional[str] = None
    org_name: Optional[str] = None
    customer_service: Optional[str] = None
    duration_seconds: Optional[int] = None
    session_date: Optional[date] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class SessionDetail(BaseModel):
    """详情页完整信息"""
    session_id: str
    customer_name: Optional[str] = None
    org_name: Optional[str] = None
    customer_service: Optional[str] = None
    duration_seconds: Optional[int] = None
    session_date: Optional[date] = None
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[SessionListItem]
    total: int
    page: int
    page_size: int


# ---- 日报 ----
class DailyReportOut(BaseModel):
    report_date: date
    total_sessions: int = 0
    keywords_json: Optional[dict] = None
    category_stats_json: Optional[dict] = None
    long_duration_issues: Optional[str] = None
    org_distribution_json: Optional[dict] = None
    service_stats_json: Optional[dict] = None
    ai_summary: Optional[str] = None
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---- 周报 ----
class WeeklyReportOut(BaseModel):
    week_start_date: date
    week_end_date: date
    total_sessions: int = 0
    keywords_json: Optional[dict] = None
    category_stats_json: Optional[dict] = None
    org_distribution_json: Optional[dict] = None
    service_stats_json: Optional[dict] = None
    daily_trend_json: Optional[list] = None
    ai_summary: Optional[str] = None
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ---- 上传响应 ----
class UploadResponse(BaseModel):
    total_sessions: int
    valid_sessions: int
    filtered_sessions: int
    date: str
    message: str

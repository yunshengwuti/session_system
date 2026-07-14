"""
数据库模型 
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from config.database import Base


class Session(Base):
    """会话主表"""
    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True, comment="会话ID")
    customer_name = Column(String(100), comment="客户姓名")
    org_name = Column(String(200), index=True, comment="机构名称")
    customer_service = Column(String(100), index=True, comment="询问客服")
    duration_seconds = Column(Integer, comment="时长（秒）")
    session_date = Column(Date, index=True, comment="会话日期")

    # 关联
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """消息明细表"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("sessions.session_id", ondelete="CASCADE"), index=True)
    message_time = Column(DateTime, comment="消息时间")
    speaker = Column(String(100), comment="发言人（客户名或客服名）")
    message_type = Column(String(10), default="text", comment="消息类型: text/image")
    content = Column(Text, comment="文本内容")
    image_url = Column(String(500), comment="图片URL")

    # 关联
    session = relationship("Session", back_populates="messages")


class DailyReport(Base):
    """每日AI总结报告"""
    __tablename__ = "daily_reports"

    report_date = Column(Date, primary_key=True, comment="报告日期")
    total_sessions = Column(Integer, default=0, comment="总会话数")
    keywords_json = Column(JSON, comment="关键词统计 {\"产品问题\": 15, \"账户\": 8}")
    category_stats_json = Column(JSON, comment="问题分类占比 {\"技术\": 40, \"业务\": 30}")
    long_duration_issues = Column(Text, comment="耗时问题分析")
    org_distribution_json = Column(JSON, comment="机构分布 {\"森浦\": 20, \"中信\": 5}")
    service_stats_json = Column(JSON, comment="客服工作量 {\"施杰\": 10, \"Riven\": 15}")
    ai_summary = Column(Text, comment="AI生成的完整总结")
    generated_at = Column(DateTime, default=datetime.now, comment="生成时间")


class ReportTask(Base):
    """报告生成任务状态"""
    __tablename__ = "report_tasks"

    task_id = Column(String(64), primary_key=True, comment="任务ID")
    report_type = Column(String(20), index=True, comment="报告类型: daily/weekly")
    target_key = Column(String(64), index=True, comment="报告日期或日期范围")
    status = Column(String(20), default="pending", index=True, comment="pending/running/succeeded/failed")
    progress = Column(Integer, default=0, comment="进度百分比")
    message = Column(String(500), comment="当前步骤说明")
    error = Column(Text, comment="失败原因")
    result_key = Column(String(64), comment="生成成功后的报告标识")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class WeeklyReport(Base):
    """每周AI总结报告"""
    __tablename__ = "weekly_reports"

    week_start_date = Column(Date, primary_key=True, comment="周开始日期（周一）")
    week_end_date = Column(Date, comment="周结束日期（周日）")
    total_sessions = Column(Integer, default=0, comment="本周总会话数")
    keywords_json = Column(JSON, comment="关键词统计")
    category_stats_json = Column(JSON, comment="问题分类占比")
    org_distribution_json = Column(JSON, comment="机构分布")
    service_stats_json = Column(JSON, comment="客服工作量")
    daily_trend_json = Column(JSON, comment="每日趋势 [{\"date\": \"2026-06-23\", \"sessions\": 10}, ...]")
    ai_summary = Column(Text, comment="AI周报全文")
    generated_at = Column(DateTime, default=datetime.now, comment="生成时间")

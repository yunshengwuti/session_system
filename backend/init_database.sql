-- 会话数据管理系统 - 数据库初始化脚本
-- 如果需要手动建表，可以运行此脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS session_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE session_system;

-- 会话主表
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(64) PRIMARY KEY COMMENT '会话ID',
    customer_name VARCHAR(100) COMMENT '客户姓名',
    org_name VARCHAR(200) COMMENT '机构名称',
    customer_service VARCHAR(100) COMMENT '询问客服',
    duration_seconds INT COMMENT '时长（秒）',
    session_date DATE COMMENT '会话日期',
    INDEX idx_session_date (session_date),
    INDEX idx_org_name (org_name),
    INDEX idx_customer_service (customer_service)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话主表';

-- 消息明细表
CREATE TABLE IF NOT EXISTS messages (
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    message_time DATETIME NOT NULL COMMENT '消息时间',
    speaker VARCHAR(100) COMMENT '发言人',
    message_type VARCHAR(10) DEFAULT 'text' COMMENT '消息类型: text/image',
    content TEXT COMMENT '文本内容',
    image_url VARCHAR(500) COMMENT '图片URL',
    PRIMARY KEY (session_id, message_time),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息明细表';

-- 每日AI总结报告表
CREATE TABLE IF NOT EXISTS daily_reports (
    report_date DATE PRIMARY KEY COMMENT '报告日期',
    total_sessions INT DEFAULT 0 COMMENT '总会话数',
    keywords_json JSON COMMENT '关键词统计',
    category_stats_json JSON COMMENT '问题分类占比',
    long_duration_issues TEXT COMMENT '耗时问题分析',
    org_distribution_json JSON COMMENT '机构分布',
    service_stats_json JSON COMMENT '客服工作量',
    ai_summary TEXT COMMENT 'AI生成的完整总结',
    generated_at DATETIME COMMENT '生成时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日AI总结报告';

-- 每周AI总结报告表
CREATE TABLE IF NOT EXISTS weekly_reports (
    week_start_date DATE PRIMARY KEY COMMENT '周开始日期（周一）',
    week_end_date DATE COMMENT '周结束日期（周日）',
    total_sessions INT DEFAULT 0 COMMENT '本周总会话数',
    keywords_json JSON COMMENT '关键词统计',
    category_stats_json JSON COMMENT '问题分类占比',
    org_distribution_json JSON COMMENT '机构分布',
    service_stats_json JSON COMMENT '客服工作量',
    daily_trend_json JSON COMMENT '每日趋势',
    ai_summary TEXT COMMENT 'AI周报全文',
    generated_at DATETIME COMMENT '生成时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每周AI总结报告';

-- 查看表结构
SHOW TABLES;

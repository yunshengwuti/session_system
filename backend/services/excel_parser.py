"""
Excel 解析服务
将 messageRecord 和 receptionRecord 解析并写入数据库
"""
import pandas as pd
import re
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session as DBSession
from models.database import Session, Message


def parse_params(params_str):
    """从 params 字段提取客户姓名和机构名称"""
    if pd.isna(params_str):
        return None, None
    try:
        params_str = str(params_str)
        name_match = re.search(r'"qmName"\s*:\s*"([^"]*)"', params_str)
        org_match = re.search(r'"qmOrg"\s*:\s*"([^"]*)"', params_str)
        return (
            name_match.group(1) if name_match else None,
            org_match.group(1) if org_match else None,
        )
    except Exception:
        return None, None


def extract_image_url(content: str) -> Optional[str]:
    """从消息内容中提取图片URL - 支持中文引号"""
    if pd.isna(content):
        return None
    # 支持标准引号和中文引号 (U+201C " 和 U+201D ")
    # \u201c = " (左双引号), \u201d = " (右双引号)
    match = re.search(r'src\s*=\s*[\u201c\u201d"\'\'\']([^\u201c\u201d"\'\'\'>]+)[\u201c\u201d"\'\'\']', str(content))
    return match.group(1) if match else None


def is_image_message(content: str) -> bool:
    """判断是否为图片消息"""
    if pd.isna(content):
        return False
    return '<img' in str(content)


# 客服标准话术
STANDARD_MESSAGES = [
    "您好，这里是森浦qeubee，请问有什么可以帮到您？",
    "请问还有什么我可以帮助到您的吗？",
    "如您还有疑问，可随时联系我们，谢谢",
]


def clean_html(text: str) -> str:
    """去除HTML标签"""
    if pd.isna(text):
        return ""
    return re.sub(r'<[^>]+>', '', str(text)).strip()


def is_customer_service(source) -> bool:
    if pd.isna(source):
        return False
    return '客服' in str(source)


def should_filter_session(session_messages: pd.DataFrame) -> Tuple[bool, str]:
    """判断会话是否应该被过滤"""
    count = len(session_messages)

    # 规则1: 单条客服消息
    if count == 1 and is_customer_service(session_messages.iloc[0]['消息来源']):
        return True, "单条客服消息"

    # 规则2: 仅包含标准话术
    all_standard = all(
        clean_html(row['消息内容']) in STANDARD_MESSAGES
        for _, row in session_messages.iterrows()
    )
    if all_standard:
        return True, "仅包含标准话术"

    return False, ""


def parse_duration_to_seconds(duration_str) -> Optional[int]:
    """将时长字符串转换为秒数
    例如: "00:13:01" -> 781秒
    """
    if pd.isna(duration_str):
        return None
    try:
        duration_str = str(duration_str).strip()
        # 支持 HH:MM:SS 格式
        parts = duration_str.split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return None
    except Exception:
        return None


def parse_and_save(
    message_file_path: str,
    reception_file_path: str,
    db: DBSession,
) -> dict:
    """
    解析两个文件（Excel 或 CSV）并写入数据库

    Returns:
        统计信息字典
    """
    # 根据文件扩展名选择读取方式
    if message_file_path.endswith('.csv'):
        # 尝试多种编码读取 CSV
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-8-sig']:
            try:
                msg_df = pd.read_csv(message_file_path, encoding=encoding)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            raise ValueError(f"无法解析 {message_file_path}，请检查文件编码")
    else:
        msg_df = pd.read_excel(message_file_path)

    if reception_file_path.endswith('.csv'):
        # 尝试多种编码读取 CSV
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-8-sig']:
            try:
                rec_df = pd.read_csv(reception_file_path, encoding=encoding)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            raise ValueError(f"无法解析 {reception_file_path}，请检查文件编码")
    else:
        rec_df = pd.read_excel(reception_file_path)

    # 去掉全空行
    msg_df = msg_df.dropna(subset=['会话ID'])
    rec_df = rec_df.dropna(subset=['会话ID'])

    session_ids = msg_df['会话ID'].unique()
    valid_count = 0
    filtered_count = 0
    session_date = None

    for sid in session_ids:
        # 跳过已存在的会话
        existing = db.query(Session).filter(Session.session_id == sid).first()
        if existing:
            continue

        session_msgs = msg_df[msg_df['会话ID'] == sid]

        # 过滤无效会话
        should_filter, reason = should_filter_session(session_msgs)
        if should_filter:
            filtered_count += 1
            continue

        # 从 receptionRecord 获取会话信息
        rec_row = rec_df[rec_df['会话ID'] == sid]

        customer_name = None
        org_name = None
        duration_seconds = None

        if len(rec_row) > 0:
            r = rec_row.iloc[0]
            nickname = r.get('用户昵称')

            if pd.notna(nickname) and '森浦' in str(nickname):
                customer_name = str(nickname)
                org_name = '森浦'
            else:
                customer_name, org_name = parse_params(r.get('params'))

            # 解析时长
            duration_str = r.get('人工接待时长')
            duration_seconds = parse_duration_to_seconds(duration_str)

        # 提取客服名
        cs_msgs = session_msgs[session_msgs['消息来源'].str.contains('在线客服', na=False)]
        customer_service = cs_msgs.iloc[0]['消息来源'] if len(cs_msgs) > 0 else None

        # 提取日期
        first_time = session_msgs['消息时间'].dropna()
        if len(first_time) > 0:
            t = pd.to_datetime(first_time.iloc[0])
            session_date = t.date()

        # 创建会话记录
        session_obj = Session(
            session_id=sid,
            customer_name=customer_name,
            org_name=org_name,
            customer_service=customer_service,
            duration_seconds=duration_seconds,
            session_date=session_date,
        )
        db.add(session_obj)

        # 创建消息记录
        for _, row in session_msgs.sort_values('消息时间').iterrows():
            content = row['消息内容']
            image_url = extract_image_url(content) if is_image_message(content) else None
            text_content = None if is_image_message(content) else (str(content).strip() if pd.notna(content) else None)

            # 清理HTML标签
            if text_content:
                text_content = clean_html(text_content)

            # 提取发言人
            speaker = row['消息来源'] if pd.notna(row['消息来源']) else None

            msg_obj = Message(
                session_id=sid,
                speaker=speaker,
                content=text_content,
                image_url=image_url,
                message_type="image" if image_url else "text",
                message_time=pd.to_datetime(row['消息时间']) if pd.notna(row['消息时间']) else None,
            )
            db.add(msg_obj)

        valid_count += 1

    db.commit()

    return {
        "total_sessions": len(session_ids),
        "valid_sessions": valid_count,
        "filtered_sessions": filtered_count,
        "date": str(session_date) if session_date else "unknown",
    }

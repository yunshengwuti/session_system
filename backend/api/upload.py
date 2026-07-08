"""
文件上传 API - 新格式（单文件）
"""
import os
import re
import tempfile
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session as DBSession
import pandas as pd

from config.database import get_db
from models.database import Session, Message

router = APIRouter(prefix="/api/upload", tags=["上传"])


def parse_session_details(content: str) -> list[dict]:
    """
    解析会话详情内容，提取对话消息

    格式示例：
    森浦Sumsope_郑锦信（客户） 2026-07-01 17:05:13
    [图片] https://...

    在线客服 vicky（客服） 2026-07-01 17:07:11
    已更新
    """
    if not content or pd.isna(content):
        return []

    messages = []
    lines = content.strip().split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 匹配发言人和时间：xxx（角色） YYYY-MM-DD HH:MM:SS
        match = re.match(r'^(.+?)（(客户|客服)）\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)

        if match:
            speaker_name = match.group(1).strip()
            role = match.group(2)  # 客户 or 客服
            time_str = match.group(3)

            # 读取消息内容（下一行直到遇到新的发言人或结束）
            i += 1
            message_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                # 如果是新的发言人，停止
                if re.match(r'^.+?（(客户|客服)）\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', next_line):
                    break
                if next_line:  # 跳过空行
                    message_lines.append(next_line)
                i += 1

            content_text = '\n'.join(message_lines)

            # 判断消息类型
            message_type = 'text'
            image_url = None
            if '[图片]' in content_text:
                message_type = 'image'
                # 提取图片链接
                url_match = re.search(r'https?://[^\s]+', content_text)
                if url_match:
                    image_url = url_match.group(0)
                content_text = '[图片]'

            messages.append({
                'speaker': speaker_name,
                'role': role,
                'message_time': datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'),
                'message_type': message_type,
                'content': content_text,
                'image_url': image_url
            })
        else:
            i += 1

    return messages


@router.post("")
async def upload_excel(
    file: UploadFile = File(..., description="会话记录 Excel 文件"),
    db: DBSession = Depends(get_db),
):
    """
    上传新格式 Excel 文件（单文件，包含多日期数据）

    文件格式：
    - 客户昵称、客户姓名、会话ID、会话创建时间、会话结束时间、会话详情内容等
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持 Excel 文件（.xlsx 或 .xls）")

    # 保存到临时文件
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, file.filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 读取 Excel
        df = pd.read_excel(file_path)

        # 验证必要列
        required_cols = ['会话ID', '会话创建时间', '会话结束时间', '会话详情内容']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"缺少必要列: {', '.join(missing)}")

        session_count = 0
        message_count = 0
        skipped_count = 0
        error_count = 0

        for idx, row in df.iterrows():
            try:
                session_id = str(row['会话ID'])

                # 检查会话是否已存在
                existing = db.query(Session).filter(Session.session_id == session_id).first()
                if existing:
                    skipped_count += 1
                    continue

                # 提取客户信息
                customer_name = row.get('客户姓名')
                if pd.isna(customer_name):
                    customer_name = row.get('客户昵称', '未知客户')

                # 解析会话详情内容
                messages = parse_session_details(row.get('会话详情内容'))

                if not messages:
                    skipped_count += 1
                    continue

                # 提取客服名称（从第一条客服消息中）
                customer_service = None
                for msg in messages:
                    if msg['role'] == '客服':
                        customer_service = msg['speaker']
                        break

                if not customer_service:
                    customer_service = '未分配'

                # 计算时长
                start_time = pd.to_datetime(row['会话创建时间'])
                end_time = pd.to_datetime(row['会话结束时间'])
                duration = int((end_time - start_time).total_seconds())

                # 创建会话记录
                session = Session(
                    session_id=session_id,
                    customer_name=str(customer_name),
                    org_name=row.get('咨询渠道', '未知渠道'),
                    customer_service=customer_service,
                    duration_seconds=duration,
                    session_date=start_time.date()
                )
                db.add(session)
                db.flush()

                # 创建消息记录
                for msg in messages:
                    message = Message(
                        session_id=session_id,
                        speaker=msg['speaker'],
                        message_time=msg['message_time'],
                        message_type=msg['message_type'],
                        content=msg['content'],
                        image_url=msg.get('image_url')
                    )
                    db.add(message)
                    message_count += 1

                session_count += 1

            except Exception as e:
                error_count += 1
                print(f"处理第 {idx+1} 行时出错: {str(e)}")
                continue

        db.commit()

        return {
            "success": True,
            "message": "上传成功",
            "total_sessions": session_count,
            "valid_sessions": session_count,
            "message_count": message_count,
            "skipped_count": skipped_count,
            "error_count": error_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(tmp_dir):
            os.rmdir(tmp_dir)
"""
测试图片解析功能
"""
import re

def extract_image_url(content: str):
    """从消息内容中提取图片URL"""
    if not content:
        return None
    # 匹配各种引号: 普通引号 " ' 和中文引号 " " ' '
    match = re.search(r'src=[\"\'""\']([^\"\'""\'>]+)[\"\'""\']', str(content))
    return match.group(1) if match else None

def is_image_message(content: str) -> bool:
    """判断是否为图片消息"""
    if not content:
        return False
    return '<img' in str(content)

# 测试用例
test_cases = [
    '<img src="https://example.com/image.jpg" alt="test">',
    '<img src=\'https://example.com/image.jpg\'>',
    '<img src="https://example.com/image.jpg"/>',
    '<img src="http://qeubee.com/uploads/chat/image123.png">',
    '普通文本消息',
    None,
]

print("=== 图片解析测试 ===\n")
for i, content in enumerate(test_cases, 1):
    is_img = is_image_message(content)
    url = extract_image_url(content) if is_img else None
    print(f"测试 {i}:")
    print(f"  内容: {content}")
    print(f"  是图片: {is_img}")
    print(f"  URL: {url}")
    print()

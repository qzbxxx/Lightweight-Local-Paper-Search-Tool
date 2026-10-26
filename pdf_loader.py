import os
import re
from pypdf import PdfReader
from api_service import get_base_dir

PAPERS_DIR = os.path.join(get_base_dir(), "文献")

def extract_clean_abstract(pdf_path):
    """【Token优化】智能清洗：精准抓取 Abstract 与 Introduction 之间的纯摘要"""
    try:
        reader = PdfReader(pdf_path)
        raw_text = ""
        # 一般摘要都在前2页
        for i in range(min(2, len(reader.pages))):
            extracted = reader.pages[i].extract_text()
            if extracted:
                raw_text += extracted + " "

        # 利用正则查找 Abstract 和 Introduction 之间的核心内容
        # 匹配 Abstract ... 1. Introduction 或 Keywords
        match = re.search(r'(?i)abstract[:\s]*(.*?)(?=(keywords|index terms|1[\.\s]+introduction|introduction))', raw_text, re.DOTALL)
        if match:
            clean_abstract = match.group(1).strip()
            # 限制在 600 字符内（通常 100~150 词，刚好是一篇完整摘要）
            return clean_abstract[:600]
        else:
            # 没匹配到标准格式时，保底截取前 400 字符（跳过首页最顶部的标题作者）
            return raw_text[200:600].strip()
    except Exception as e:
        return f"解析失败: {e}"

def scan_all_papers():
    if not os.path.exists(PAPERS_DIR):
        os.makedirs(PAPERS_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PAPERS_DIR) if f.lower().endswith(".pdf")]
    papers_data = {}
    for file in pdf_files:
        path = os.path.join(PAPERS_DIR, file)
        papers_data[file] = extract_clean_abstract(path)
    return papers_data
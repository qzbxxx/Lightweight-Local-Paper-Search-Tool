import os
import sys
import re
from openai import OpenAI

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def read_api_config():
    txt_path = os.path.join(get_base_dir(), "api.txt")
    if not os.path.exists(txt_path):
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("API_KEY=\nBASE_URL=https://api.deepseek.com\nMODEL=deepseek-chat\n")
        raise FileNotFoundError("未找到 api.txt，已自动生成模板，请先填入 API_KEY！")

    config = {}
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip()

    if not config.get("API_KEY"):
        raise ValueError("api.txt 中的 API_KEY 为空！")
    return config

def local_coarse_rank(query, papers_data, top_k=5):
    """【零 Tokens 消耗】本地通过关键词 + 字符相关度快速初选 Top-5"""
    # 提取英文/中文字词
    keywords = [k.lower() for k in re.findall(r'[\w]+', query) if len(k) > 1]
    scores = {}

    for name in papers_data.keys():
        score = 0
        name_lower = name.lower()
        # 命中查询关键词加分（文件名命中权重极高）
        for kw in keywords:
            if kw in name_lower:
                score += 10
        scores[name] = score

    # 按分值从大到小排序
    ranked_titles = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    return ranked_titles[:top_k]

def ask_agent(query, papers_data):
    """最终优化：本地粗排 + 纯净精排（只发起 1 次极低成本的 API 请求）"""
    cfg = read_api_config()
    client = OpenAI(
        api_key=cfg["API_KEY"],
        base_url=cfg.get("BASE_URL", "https://api.deepseek.com")
    )
    model = cfg.get("MODEL", "deepseek-chat")

    # 1. 本地零成本筛选出 5 篇候选
    top5_titles = local_coarse_rank(query, papers_data, top_k=5)

    # 2. 组装极致压缩后的上下文
    top5_context = ""
    for idx, title in enumerate(top5_titles, 1):
        abstract = papers_data.get(title, "无摘要信息")
        top5_context += f"[{idx}] 《{title}》\n摘要精要: {abstract}\n\n"

    prompt = f"""学术检索任务。用户需求: "{query}"

候选文献精要列表：
{top5_context}

请严格按格式输出（言简意赅，不要废话）：
1. 【核心推荐 Top-2】：列出最符合的两篇，每篇用50字以内说明理由。
2. 【综合排序 1~5】：从高到低排列上述5篇文献的文件名。
"""

    # 3. 单次极小调用，设置 max_tokens 彻底锁死输出成本
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个追求极致精准、用词凝练的学术检索助理。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=400  # 锁死输出长度
    )

    return response.choices[0].message.content
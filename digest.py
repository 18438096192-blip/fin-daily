# -*- coding: utf-8 -*-
"""AI 汇总：调用 DeepSeek API 生成"公司金融视角"日报。

未配置 DEEPSEEK_API_KEY 时自动退回关键词规则版（便于先跑通流程）。
"""
import json
import os
import urllib.request

# ===== 可配置：兼容学校网关 / 官方 API / 任何 OpenAI 兼容端点 =====
# LLM_BASE_URL 例：https://api.deepseek.com  或  https://你的学校网关/v1
# LLM_MODEL    例：deepseek-chat / deepseek-v3 / gpt-4o-mini ...
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


def _settings():
    base = os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL).strip()
    max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "1600") or 1600)
    key = (os.environ.get("LLM_API_KEY")
           or os.environ.get("DEEPSEEK_API_KEY")
           or os.environ.get("DEEPSEEK_SCHOOL_KEY")
           or "").strip()
    return base, model, max_tokens, key

SYSTEM_PROMPT = """你是《公司金融》课程的财经编辑。请把用户提供的当日财经快讯，整理成一份给金融专硕研究生看的日报：

1. 分四个栏目：【宏观与政策】【融资·IPO·并购】【市场与行情】【监管与行业动态】；其中公司金融主线（融资、IPO、并购、回购、分红、公司治理）优先收录。
2. 每条不超过 40 字，条目前标注重要度（★~★★★）；琐碎快讯直接舍弃，全篇控制在 12~18 条。
3. 结尾加一段"💡 编辑点评"：不超过 3 句话，概括当日对公司融资环境/A股的含义。
4. 直接输出 Markdown 正文（不要重复总标题），不要任何开场白或解释。"""

_RULES = [
    ("融资·IPO·并购", ["IPO", "上市", "融资", "并购", "收购", "重组", "增发", "定增",
                     "回购", "分红", "借壳", "私有化", "退市", "股东", "董事", "市值", "估值", "合并"]),
    ("宏观与政策", ["央行", "美联储", "加息", "降息", "利率", "CPI", "GDP", "政治局",
                   "国常会", "发改委", "财政部", "证监会", "关税", "政策", "座谈会", "规划", "选举"]),
    ("市场与行情", ["指数", "A股", "美股", "港股", "涨", "跌", "原油", "黄金", "美元",
                   "汇率", "持仓", "成交", "牛市", "熊市", "多头", "空头"]),
    ("监管与行业动态", ["监管", "罚", "立案", "调查", "处罚", "新规", "反垄断",
                      "行业", "芯片", "新能源", "固态电池", "AI", "数据中心"]),
]
_STAR_WORDS = ["突发", "首次", "史上", "重大", "暴增", "大跌", "大涨", "历史", "最大", "突然"]


def make_digest(items):
    """返回 (markdown正文, 模式)。模式: deepseek / demo / fallback。"""
    lines = []
    for i, it in enumerate(items, 1):
        t = it["time"].strftime("%H:%M") if it["time"] else "--:--"
        lines.append("%d. [%s][%s] %s" % (i, t, it["source"], it["text"]))
    user_content = "以下是近24~36小时的财经快讯，请生成今日日报：\n" + "\n".join(lines)

    base, model, max_tokens, api_key = _settings()
    if not api_key:
        return _rule_based_digest(items), "demo"
    try:
        return _call_llm(api_key, base, model, max_tokens, user_content), "llm"
    except Exception as e:
        body = _rule_based_digest(items)
        return body + "\n\n> ⚠️ AI 摘要调用失败（%s），本期为规则版兜底。" % e, "fallback"


def _call_llm(api_key, base, model, max_tokens, user_content):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
            "User-Agent": "fin-daily/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"].strip()
    if not content:
        raise RuntimeError("模型返回空内容 finish_reason=%s" % (
            data["choices"][0].get("finish_reason")))
    return content


def _rule_based_digest(items):
    groups = {name: [] for name, _ in _RULES}
    others = []
    for it in items:
        text = it["text"]
        target = None
        for name, kws in _RULES:
            if any(k in text for k in kws):
                target = name
                break
        star = "★★★" if any(k in text for k in _STAR_WORDS) else "★"
        line = "%s %s" % (star, text[:42])
        (groups[target] if target else others).append(line)
    parts = []
    for name, _ in _RULES:
        if groups[name]:
            parts.append("## 【%s】" % name)
            parts.extend("- " + l for l in groups[name][:6])
            parts.append("")
    if others:
        parts.append("## 【要闻速览】")
        parts.extend("- " + l for l in others[:4])
        parts.append("")
    parts.append("> ⚙️ 演示模式：未配置 DEEPSEEK_API_KEY，本期由关键词规则生成；配置后将由大模型生成。")
    return "\n".join(parts)

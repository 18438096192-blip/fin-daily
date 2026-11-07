# -*- coding: utf-8 -*-
"""AI 汇总：调用大模型生成"硬科技投资视角"的财经日报。

关注主线：芯片/半导体、光通信、存储、AI/算力、先进封装；
同时覆盖重大宏观事件（如美国中期选举、美联储、出口管制）并分析其对产业链的影响。

配置（环境变量）：
    LLM_API_KEY     密钥（也兼容 DEEPSEEK_API_KEY / DEEPSEEK_SCHOOL_KEY）
    LLM_BASE_URL    默认 https://dashscope.aliyuncs.com/compatible-mode/v1
    LLM_MODEL       默认 qwen3.7-max
    LLM_MAX_TOKENS  默认 2200
"""
import json
import os
import urllib.request

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.7-max"

SYSTEM_PROMPT = """你是一位专注硬科技赛道的卖方研究员，服务对象是金融专硕学生与产业投资人。请把用户给的当日财经快讯，写成一份"有观点、有影响分析"的日报。

【用户重点关注方向，优先级从高到低】
1. 芯片 / 半导体（设计、制造、设备、材料、EDA、国产替代、出口管制、晶圆厂扩产）
2. 光通信（光模块、CPO/硅光、800G/1.6T、光芯片、AI数据中心互联）
3. 存储（HBM、DRAM、NAND、存储涨价、原厂减产/扩产、模组厂）
4. AI / 算力（大模型、GPU/ASIC、数据中心、推理需求、AI应用与资本开支）
5. 先进封装（CoWoS、2.5D/3D、Chiplet、TSV、面板级封装、封测厂扩产）
6. 重大宏观与政策（美国中期选举及两党政策取向、美联储利率、中美关税与出口管制、国内产业政策、重要会议）——这类新闻必须单独列出，并明确分析"对上述科技板块的影响方向"

【输出格式（严格遵守，直接输出 Markdown，不要开场白）】
## 🎯 今日核心（3 条）
1. **一句话标题** ——一句话说明为什么重要
2. ...
3. ...

## 🔬 产业链动态
### 芯片 / 半导体
- ★★★ **标题**：事件要点。**影响**：一句话分析（利好/利空谁、传导路径）
（该子板块无新闻则整节省略，不要编造）
### 光通信
### 存储
### AI / 算力
### 先进封装

## 🌍 宏观与政策
- ★★★ **标题**：要点。**影响**：对芯片/AI板块的方向性判断（利多/利空、影响哪条链）

## ⚠️ 风险提示
- 1~3 条，结合当日新闻点出需要警惕的变量

## 💡 研究员观点
3~4 句话，串联当日主线，给出对后续 1~2 周产业链与股价催化剂的判断。

【硬性要求】
- 每条须"新闻事实 + 影响分析"，不能只复述新闻标题。
- 重要度标记 ★~★★★，只标在每条前面。
- 全文控制在 20~28 条信息，务必精炼；宁可少而深，不要多而浅。
- 严禁编造快讯中没有的具体数字、公司或事件；没有相关新闻的子板块直接省略。
- 使用简体中文，专业但不啰嗦。"""

# 规则版兜底用：板块关键词
SECTORS = [
    ("芯片 / 半导体", ["芯片", "半导体", "晶圆", "光刻", "EDA", "台积电", "中芯", "华虹",
                   "设备", "材料", "国产替代", "制程", "晶体管", "IGBT", "第三代半导体"]),
    ("光通信", ["光模块", "光通信", "CPO", "硅光", "800G", "1.6T", "光芯片", "光纤",
             "光缆", "互联", "数据中心互联", "中际旭创", "新易盛", "天孚"]),
    ("存储", ["存储", "HBM", "DRAM", "NAND", "闪存", "内存", "美光", "三星电子",
            "SK海力士", "长江存储", "长鑫", "涨价", "颗粒"]),
    ("AI / 算力", ["AI", "人工智能", "大模型", "算力", "GPU", "英伟达", "AMD", "推理",
                "训练", "智算", "数据中心", "服务器", "液冷", "OpenAI", "Anthropic"]),
    ("先进封装", ["封装", "CoWoS", "Chiplet", "2.5D", "3D封装", "TSV", "封测",
              "面板级", "先进制程", "长电", "通富", "华天"]),
    ("宏观与政策", ["美联储", "加息", "降息", "中期选举", "民主党", "共和党", "特朗普",
                "关税", "出口管制", "制裁", "国常会", "政治局", "发改委", "工信部",
                "商务部", "财政", "通胀", "CPI", "GDP", "利率", "汇率"]),
]
_STAR_WORDS = ["突发", "首次", "史上", "重大", "暴增", "大跌", "大涨", "历史", "最大",
               "禁止", "管制", "制裁", "涨价", "减产", "扩产", "投资", "收购"]


def _settings():
    base = os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL).strip()
    max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2200") or 2200)
    key = (os.environ.get("LLM_API_KEY")
           or os.environ.get("DEEPSEEK_API_KEY")
           or os.environ.get("DEEPSEEK_SCHOOL_KEY")
           or "").strip()
    return base, model, max_tokens, key


def make_digest(items):
    """返回 (markdown正文, 模式)。模式: llm / demo / fallback。"""
    lines = []
    for i, it in enumerate(items, 1):
        t = it["time"].strftime("%m-%d %H:%M") if it["time"] else "--"
        lines.append("%d. [%s][%s] %s" % (i, t, it["source"], it["text"]))
    user_content = ("以下是最近 24~36 小时的财经快讯。请按研究方向筛选并写成日报：\n"
                    + "\n".join(lines))

    base, model, max_tokens, api_key = _settings()
    if not api_key:
        return _rule_based_digest(items), "demo"
    try:
        return _call_llm(api_key, base, model, max_tokens, user_content), "llm"
    except Exception as e:
        body = _rule_based_digest(items)
        return body + "\n\n> ⚠️ 大模型调用失败（%s），本期为规则版兜底。" % e, "fallback"


def _call_llm(api_key, base, model, max_tokens, user_content):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.6,
        "max_tokens": max_tokens,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
            "User-Agent": "fin-daily/2.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    choice = data["choices"][0]
    content = (choice.get("message") or {}).get("content") or ""
    content = content.strip()
    if not content:
        raise RuntimeError("模型返回空内容 finish_reason=%s" % choice.get("finish_reason"))
    return content


def _rule_based_digest(items):
    """无 Key / 调用失败时的兜底：按板块关键词归类。"""
    groups = {name: [] for name, _ in SECTORS}
    others = []
    for it in items:
        text = it["text"]
        target = None
        for name, kws in SECTORS:
            if any(k in text for k in kws):
                target = name
                break
        star = "★★★" if any(k in text for k in _STAR_WORDS) else "★"
        line = "%s %s" % (star, text[:46])
        (groups[target] if target else others).append(line)
    parts = []
    for name, _ in SECTORS:
        if groups[name]:
            parts.append("### 【%s】" % name)
            parts.extend("- " + l for l in groups[name][:6])
            parts.append("")
    if others:
        parts.append("### 【其他要闻】")
        parts.extend("- " + l for l in others[:5])
        parts.append("")
    parts.append("> ⚙️ 演示模式：未调用大模型（未配置 Key 或调用失败），以上为关键词规则归类。")
    return "\n".join(parts)

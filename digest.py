# -*- coding: utf-8 -*-
"""AI 汇总：把当日财经快讯整理成"有观点、有影响分析"的日报。

关注方向、日报标题、条数等全部来自 config.json，用户无需改代码。

环境变量：
    LLM_API_KEY     大模型密钥（必填，缺失时自动降级为规则版）
    LLM_BASE_URL    默认 https://dashscope.aliyuncs.com/compatible-mode/v1
    LLM_MODEL       默认 qwen3.7-max
    LLM_MAX_TOKENS  默认 2200
"""
import json
import os
import urllib.request

import config as cfgmod

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.7-max"

PROMPT_TEMPLATE = """你是一位专注{topics_short}赛道的卖方研究员，服务对象是关注产业与投资机会的读者。请把用户给的当日财经快讯，写成一份"有观点、有影响分析"的日报。

【读者重点关注方向，优先级从高到低】
{topics_list}

【重大宏观与政策】
政治、利率、关税、出口管制、产业政策等重大事件必须单独成栏，并明确分析"对上述方向的传导影响"（利多/利空、影响哪条链、路径是什么）。
{extra}

【输出格式（严格遵守，直接输出 Markdown，不要开场白）】
## 🎯 今日核心（3 条）
1. **一句话标题** —— 一句话说明为什么重要
2. ...
3. ...

## 🔬 产业链动态
### {first_topic}
- ★★★ **标题**：事件要点。**影响**：一句话分析（利好/利空谁、传导路径）
（某个子板块当天没有新闻就整节省略，严禁编造）
### 其他方向同理

## 🌍 宏观与政策
- ★★★ **标题**：要点。**影响**：对上述方向的方向性判断

## ⚠️ 风险提示
- 1~3 条，结合当日新闻点出需要警惕的变量

## 💡 研究员观点
3~4 句话，串联当日主线，给出对后续 1~2 周催化剂与股价/基本面的判断。

【硬性要求】
- 每条必须"新闻事实 + 影响分析"，不能只复述标题。
- 重要度标记 ★~★★★，只标在每条开头。
- 全文 {max_items} 条信息，宁可少而深，不要多而浅。
- 严禁编造快讯中没有的具体数字、公司或事件。
- 使用简体中文，专业但不啰嗦。"""


def build_prompt(cfg):
    topics = cfg.get("topics") or []
    topics_list = "\n".join("%d. %s" % (i + 1, t) for i, t in enumerate(topics)) or "1. 财经综合"
    extra = cfg.get("extra_instructions") or ""
    if extra:
        extra = "\n【额外要求】\n" + extra
    return PROMPT_TEMPLATE.format(
        topics_short="、".join(topics[:3]) or "财经",
        topics_list=topics_list,
        first_topic=topics[0] if topics else "要闻",
        extra=extra,
        max_items=cfg.get("max_digest_items", "20~28"),
    )


def _settings():
    base = os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL).strip()
    max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "2200") or 2200)
    key = (os.environ.get("LLM_API_KEY")
           or os.environ.get("DEEPSEEK_API_KEY")
           or os.environ.get("DEEPSEEK_SCHOOL_KEY")
           or "").strip()
    return base, model, max_tokens, key


def make_digest(items, cfg=None):
    """返回 (markdown正文, 模式)。模式: llm / fallback / demo。"""
    cfg = cfg or cfgmod.load()
    lines = []
    for i, it in enumerate(items, 1):
        t = it["time"].strftime("%m-%d %H:%M") if it["time"] else "--"
        lines.append("%d. [%s][%s] %s" % (i, t, it["source"], it["text"]))
    user_content = ("以下是最近 24~36 小时的财经快讯。请筛选出与关注方向相关的部分，写成日报：\n"
                    + "\n".join(lines))

    base, model, max_tokens, api_key = _settings()
    if not api_key:
        return _rule_based_digest(items, cfg), "demo"
    try:
        return _call_llm(api_key, base, model, max_tokens, build_prompt(cfg), user_content), "llm"
    except Exception as e:
        body = _rule_based_digest(items, cfg)
        return body + "\n\n> ⚠️ 大模型调用失败（%s），本期为规则版兜底。" % e, "fallback"


def _call_llm(api_key, base, model, max_tokens, system_prompt, user_content):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
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


_MACRO_KWS = ["美联储", "加息", "降息", "选举", "关税", "出口管制", "制裁", "国常会",
              "政治局", "发改委", "工信部", "商务部", "财政", "通胀", "CPI", "GDP"]
_STAR_WORDS = ["突发", "首次", "史上", "重大", "暴增", "大跌", "大涨", "历史", "最大",
               "禁止", "管制", "制裁", "涨价", "减产", "扩产", "收购"]


def _rule_based_digest(items, cfg=None):
    """无 API Key / 调用失败时的兜底：按关注方向关键词归类。"""
    cfg = cfg or cfgmod.load()
    topics = cfg.get("topics") or []
    groups = {t: [] for t in topics}
    groups["宏观与政策"] = []
    others = []
    for it in items:
        text = it["text"]
        target = None
        for t in topics:
            # 用方向名里的词做匹配（"芯片 / 半导体" → 芯片, 半导体）
            words = [w.strip() for w in t.replace("/", " ").split() if len(w.strip()) >= 2]
            if any(w in text for w in words):
                target = t
                break
        if target is None and any(k in text for k in _MACRO_KWS):
            target = "宏观与政策"
        star = "★★★" if any(k in text for k in _STAR_WORDS) else "★"
        line = "%s %s" % (star, text[:46])
        if target:
            groups[target].append(line)
        else:
            others.append(line)
    parts = []
    for t in topics + ["宏观与政策"]:
        if groups.get(t):
            parts.append("### 【%s】" % t)
            parts.extend("- " + l for l in groups[t][:6])
            parts.append("")
    if others:
        parts.append("### 【其他要闻】")
        parts.extend("- " + l for l in others[:5])
        parts.append("")
    parts.append("> ⚙️ 演示模式：未配置大模型 Key，以上为关键词规则归类。配置后由 AI 生成完整分析。")
    return "\n".join(parts)

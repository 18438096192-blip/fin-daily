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

PROMPT_TEMPLATE = """你是一位很会讲财经的朋友，不是券商研究员。读者是普通上班族/学生，没学过金融，早上只有 5 分钟，只想知道两件事：**昨天发生了什么**、**这跟我有什么关系**。

【写作风格 —— 这是最重要的部分】
1. 用大白话，像微信里跟朋友聊天那样讲。**禁用**"估值""传导""边际""出清""beta""beta 修复""戴维斯双击"这类词；万一必须提到某个专业词，立刻在括号里用一句话解释清楚。
2. 每一条只讲两件事：
   - ① 发生了什么（一句话说清，不堆数字、不堆机构名）
   - ② 这意味着什么（对行业、对普通人、对投资者意味着什么，说人话）
3. 全程 5 分钟能读完：总共 8~12 条，正文控制在 800~1200 字。
4. 宁可少讲几条讲透，也不要堆一堆看不懂的。

【读者关心的方向】
{topics_list}

【重大事件】
政治、利率、关税、科技政策这类大事要单独说，并且直接讲明白"这对哪些行业、哪些人是好消息还是坏消息"，不要绕弯子、不要端着。
{extra}

【输出格式（严格遵守，直接输出 Markdown，不要开场白）】
## 🌅 一句话看完
用 1~2 句话说清昨天最重要的事。

## 🔥 最该知道的三件事
1. **大白话标题**：发生了什么。👉 **放到你身上**：意味着什么
2. ...
3. ...

## 📌 还值得看一眼
- **标题**：发生了什么。👉 意味着什么
- （从这里开始 5~8 条，按关注方向挑，无关的直接不要）

## 🍵 说句人话
用 3 句话收尾：昨天的主线是什么、接下来一两周要留意什么、对普通人有什么提醒。

【硬性要求】
- **所有事实必须来自下面提供的快讯清单**。清单里没出现的公司、人物、数字、事件，一律不许写。
- 特别禁止"凭印象补充"：比如写某个大佬的持仓、某个产品的具体价格、某个机构的预测——**除非清单里明确写了**。
- 想不起来出处的句子，直接删掉，宁可不写。
- 不要堆 ★★★ 这种符号；只有特别重要的 1~2 条，前面加一个 ⚠️ 就够。
- 读起来要像人说话，不要像研报。写完后自己检查一遍：一个没学过金融的人能不能一遍看懂？
- 全文 {max_items} 条。"""


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
        draft = _call_llm(api_key, base, model, max_tokens, build_prompt(cfg), user_content)
        if cfg.get("fact_check", True):
            draft = _audit(api_key, base, model, max_tokens, draft, user_content)
        return draft, "llm"
    except Exception as e:
        body = _rule_based_digest(items, cfg)
        return body + "\n\n> ⚠️ 大模型调用失败（%s），本期为规则版兜底。" % e, "fallback"


AUDIT_PROMPT = """你是严格的事实核查员。用户会给你两份材料：
【A】原始的财经快讯清单
【B】根据清单写成的日报草稿

请逐条核对 B 中的每一个具体事实（公司名、人名、数字、事件、价格、预测）：
- 如果 A 中**没有**依据，就删掉这句话，或改写成不带具体数字的笼统说法；
- 如果 A 中有但写错了，按 A 改正；
- 保留原有的 Markdown 结构、栏目和口语化风格，**不要添加任何新的内容**；
- 直接输出修正后的完整日报，不要解释、不要加"核查说明"。

原则：宁可少写一条，也不能留下没有出处的具体事实。"""


def _audit(api_key, base, model, max_tokens, draft, user_content):
    """第二道关卡：核对草稿中的事实是否都能在原始快讯中找到依据。"""
    try:
        audit_user = "【A】原始快讯清单：\n" + user_content + "\n\n【B】日报草稿：\n" + draft
        fixed = _call_llm(api_key, base, model, max_tokens, AUDIT_PROMPT, audit_user)
        # 如果核查结果异常短，说明模型跑偏了，保留原稿更安全
        if len(fixed) < len(draft) * 0.5:
            print("[核查] 返回内容过短，保留原稿")
            return draft
        print("[核查] 事实核对完成，已剔除无出处内容")
        return fixed
    except Exception as e:
        print("[核查] 跳过（%s），使用原稿" % e)
        return draft


def _call_llm(api_key, base, model, max_tokens, system_prompt, user_content):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.35,
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

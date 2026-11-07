# -*- coding: utf-8 -*-
"""免费财经新闻源抓取（全部为公开接口，仅用标准库）。

4 个新闻源，任何一个失败都会被 collect_news 捕获并跳过，不影响整体。
"""
import json
import re
import urllib.request
from datetime import datetime, timedelta, timezone

BJT = timezone(timedelta(hours=8))  # 北京时间（无夏令时，固定 UTC+8）
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126 Safari/537.36"}

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _clean(text):
    text = _TAG.sub("", str(text or ""))
    return _WS.sub(" ", text.replace("&nbsp;", " ")).strip()


def _parse_time(v):
    """把各种时间格式统一成北京时间 datetime，失败返回 None。"""
    v = str(v or "").strip()
    if not v:
        return None
    if re.fullmatch(r"\d{9,13}", v):
        n = int(v)
        if n > 10 ** 12:
            n = n / 1000.0
        try:
            return datetime.fromtimestamp(n, BJT)
        except (OverflowError, OSError, ValueError):
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(v, fmt).replace(tzinfo=BJT)
        except ValueError:
            pass
    try:
        return datetime.strptime(v, "%m-%d %H:%M").replace(
            year=datetime.now(BJT).year, tzinfo=BJT)
    except ValueError:
        return None


def _get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


def _get_text(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def fetch_sina_724(limit=50):
    """新浪财经 7×24 快讯。"""
    url = ("https://zhibo.sina.com.cn/api/zhibo/feed?"
           "page=1&page_size=%d&zhibo_id=152&tag_id=0&dire=f&dpc=1" % limit)
    items = _get_json(url)["result"]["data"]["feed"]["list"]
    out = []
    for it in items:
        text = _clean(it.get("rich_text"))
        if not text:
            continue
        out.append({"source": "新浪7×24", "time": _parse_time(it.get("create_time")), "text": text})
    return out


def fetch_sina_roll(limit=30):
    """新浪财经·滚动新闻（媒体要闻标题）。"""
    url = ("https://feed.mix.sina.com.cn/api/roll/get?"
           "pageid=153&lid=2516&k=&num=%d&page=1" % limit)
    items = _get_json(url)["result"]["data"]
    out = []
    for it in items:
        text = _clean(it.get("title"))
        if not text:
            continue
        out.append({"source": "新浪滚动", "time": _parse_time(it.get("ctime")), "text": text})
    return out


def fetch_eastmoney(limit=50):
    """东方财富·全球财经快讯。"""
    url = ("https://np-listapi.eastmoney.com/comm/web/getFastNewsList?"
           "client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=%d&req_trace=1" % limit)
    items = _get_json(url)["data"]["fastNewsList"]
    out = []
    for it in items:
        text = _clean(it.get("title") or it.get("summary"))
        if not text:
            continue
        out.append({"source": "东方财富", "time": _parse_time(it.get("showTime")), "text": text})
    return out


def fetch_jin10(limit=50):
    """金十数据快讯（免费公开 JS 接口）。"""
    raw = _get_text("https://www.jin10.com/flash_newest.js")
    arr = json.loads(raw.split("=", 1)[1].strip().rstrip(";"))
    out = []
    for it in arr[:limit]:
        content = _clean((it.get("data") or {}).get("content"))
        content = re.sub(r"^金十数据\d+月\d+日讯[，,]?\s*", "", content)
        if not content:
            continue
        out.append({"source": "金十", "time": _parse_time(it.get("time")), "text": content})
    return out


def collect_news(hours=36):
    """抓取全部新闻源 -> 去重 -> 只保留近 hours 小时（时间缺失的保留）。"""
    raw, errors = [], []
    for fn in (fetch_sina_724, fetch_sina_roll, fetch_eastmoney, fetch_jin10):
        try:
            raw.extend(fn())
        except Exception as e:  # 单源失败不影响整体
            errors.append("%s(%s)" % (fn.__name__, e))
    seen, uniq = set(), []
    for it in raw:
        key = re.sub(r"[【】\s]", "", it["text"])[:14]
        if key and key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    horizon = datetime.now(BJT) - timedelta(hours=hours)
    keep = [it for it in uniq if it["time"] is None or it["time"] >= horizon]
    keep.sort(key=lambda it: it["time"] or datetime.now(BJT), reverse=True)
    return keep, errors

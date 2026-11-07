# -*- coding: utf-8 -*-
"""推送通道。目前支持：
    1) Server酱·Turbo  -> 个人微信      https://sct.ftqq.com
    2) 企业微信群机器人 -> 企业微信群    （可选，配 WEBHOOK_URL 即启用）

环境变量：
    SERVERCHAN_SENDKEY   Server酱 SendKey
    WEBHOOK_URL          企业微信群机器人 webhook 地址（可选）
"""
import json
import os
import urllib.parse
import urllib.request


def push_all(title, markdown):
    """按已配置的通道依次推送，返回成功的通道列表。"""
    sent = []
    if push_serverchan(title, markdown):
        sent.append("serverchan")
    if push_webhook(title, markdown):
        sent.append("webhook")
    if not sent:
        print("[推送] 未配置任何推送通道，跳过（干跑）。标题:", title)
    return sent


def push_serverchan(title, markdown, key=None):
    key = key or os.environ.get("SERVERCHAN_SENDKEY", "").strip()
    if not key:
        return False
    data = urllib.parse.urlencode({"title": title, "desp": markdown}).encode("utf-8")
    req = urllib.request.Request(
        "https://sctapi.ftqq.com/%s.send" % key,
        data=data,
        headers={"User-Agent": "fin-daily/2.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") == 0:
        print("[推送] Server酱 → 微信 已发送 ✓")
        return True
    raise RuntimeError("Server酱返回错误: %s" % result)


def push_webhook(title, markdown, url=None):
    """企业微信群机器人（Markdown 消息）。"""
    url = url or os.environ.get("WEBHOOK_URL", "").strip()
    if not url:
        return False
    payload = {"msgtype": "markdown", "markdown": {"content": "## %s\n%s" % (title, markdown)}}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "fin-daily/2.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("errcode") == 0:
        print("[推送] 企业微信机器人 已发送 ✓")
        return True
    raise RuntimeError("企业微信返回错误: %s" % result)

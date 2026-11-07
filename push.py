# -*- coding: utf-8 -*-
"""Server酱·Turbo：把 Markdown 日报推送到个人微信。https://sct.ftqq.com

先在官网微信扫码登录拿到 SendKey，并按提示关注"Server酱"服务号完成绑定。
"""
import json
import os
import urllib.parse
import urllib.request


def push_serverchan(title, markdown, key=None):
    key = key or os.environ.get("SERVERCHAN_SENDKEY", "").strip()
    if not key:
        print("[推送] 未配置 SERVERCHAN_SENDKEY，跳过推送（干跑）。标题:", title)
        return False
    data = urllib.parse.urlencode({"title": title, "desp": markdown}).encode("utf-8")
    req = urllib.request.Request(
        "https://sctapi.ftqq.com/%s.send" % key,
        data=data,
        headers={"User-Agent": "fin-daily/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if result.get("code") == 0:
        print("[推送] 已发送到微信 ✓")
        return True
    raise RuntimeError("Server酱返回错误: %s" % result)

# -*- coding: utf-8 -*-
"""统一读取 config.json（用户可自由修改，无需懂代码）。"""
import json
import os

DEFAULTS = {
    "title": "每日财经速览",
    "topics": ["芯片 / 半导体", "光通信", "存储", "AI / 算力", "先进封装"],
    "extra_instructions": "",
    "max_input_items": 120,
    "hours_window": 36,
    "max_digest_items": "8~12",
    "push_wechat": True,
    "fact_check": True,
}


def load(path=None):
    path = path or os.environ.get("FIN_CONFIG", "config.json")
    cfg = dict(DEFAULTS)
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                user = json.load(f)
            if isinstance(user, dict):
                cfg.update({k: v for k, v in user.items() if v not in (None, "")})
        except Exception as e:
            print("[config] 读取 %s 失败，使用默认配置：%s" % (path, e))
    return cfg

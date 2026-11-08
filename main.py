# -*- coding: utf-8 -*-
"""AI 财经日报：抓取免费财经快讯 -> 大模型汇总 -> 推送到微信。

用法：
    python main.py

配置优先级：环境变量 > .env 文件 > config.json > 内置默认值
"""
import os
import sys
from datetime import datetime

import config as cfgmod
import digest
import news
import push


def load_dotenv(path=".env"):
    """极简 .env 加载器（KEY=VALUE），避免引入第三方依赖。"""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"'))


def main():
    load_dotenv()
    cfg = cfgmod.load()
    now = datetime.now(news.BJT)
    date_str = "%s 周%s" % (now.strftime("%Y-%m-%d"), "一二三四五六日"[now.weekday()])
    title = cfg.get("title") or "每日财经速览"

    # 幂等守卫：定时任务可能被触发多次（补偿延迟），当天已经出过报就不再重复推送
    path = os.path.join("reports", now.strftime("%Y-%m-%d") + ".md")
    if os.environ.get("GITHUB_EVENT_NAME") == "schedule" and os.path.exists(path):
        print("今日日报已存在（%s），跳过本次，避免重复推送" % path)
        return

    print("[1/3] 抓取新闻 ...")
    items, errors = news.collect_news(hours=int(cfg.get("hours_window", 36)))
    if errors:
        print("      以下新闻源失败（不影响整体）:", "; ".join(errors))
    print("      去重后共 %d 条" % len(items))
    if not items:
        print("!! 未抓到任何新闻，退出")
        sys.exit(1)
    items = items[:int(cfg.get("max_input_items", 120))]

    print("[2/3] 生成日报 ...")
    body, mode = digest.make_digest(items, cfg)
    report = "\n".join([
        "# 📊 " + title + " · " + date_str,
        "",
        body,
        "",
        "---",
        "*AI 自动汇总 · 关注方向：" + "、".join(cfg.get("topics") or []) + " · 数据源：新浪财经 / 东方财富 / 金十*",
        "",
    ])
    os.makedirs("reports", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print("      已保存 %s（摘要模式: %s）" % (path, mode))

    print("[3/3] 推送 ...")
    if os.environ.get("FIN_NO_PUSH") == "1":
        print("      已设置 FIN_NO_PUSH=1，跳过推送（仅存档）")
    elif not cfg.get("push_wechat", True):
        print("      config.json 中 push_wechat=false，跳过微信推送（仅存档）")
    else:
        push.push_all(title + " " + date_str, report)
    print("完成 ✓  存档: " + path)


if __name__ == "__main__":
    main()

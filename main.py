# -*- coding: utf-8 -*-
"""AI 财经日报：抓取免费财经快讯 -> DeepSeek 汇总 -> 推送到个人微信。

用法：
    python main.py        # 正常运行（本地读 .env，云端读环境变量）

密钥存放（二选一）：
    本地  : 同目录 .env 文件（参考 .env.example，勿提交到 git）
    云端  : GitHub 仓库 Settings -> Secrets -> Actions 里的同名变量
"""
import os
import sys
from datetime import datetime

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
    today = datetime.now(news.BJT)
    today_str = "%s 周%s" % (today.strftime("%Y-%m-%d"), "一二三四五六日"[today.weekday()])

    print("[1/3] 抓取新闻 ...")
    items, errors = news.collect_news()
    if errors:
        print("      以下新闻源失败（不影响整体）:", "; ".join(errors))
    print("      去重后共 %d 条" % len(items))
    if not items:
        print("!! 未抓到任何新闻，退出")
        sys.exit(1)
    items = items[:80]  # 控制 AI 输入长度

    print("[2/3] 生成日报 ...")
    body, mode = digest.make_digest(items)
    report = "\n".join([
        "# 📊 每日财经速览 · " + today_str,
        "",
        body,
        "",
        "---",
        "*AI 自动汇总并推送 · 数据源：新浪财经7×24 / 东方财富快讯 / 金十数据 / 新浪滚动*",
        "",
    ])
    os.makedirs("reports", exist_ok=True)
    path = os.path.join("reports", today.strftime("%Y-%m-%d") + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print("      已保存 %s（摘要模式: %s）" % (path, mode))

    print("[3/3] 推送到微信 ...")
    push.push_serverchan("财经速览 " + today_str, report)
    print("完成 ✓")


if __name__ == "__main__":
    main()

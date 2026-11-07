# -*- coding: utf-8 -*-
"""快速自检：两个 Key 是否配置正确。用法：python test_keys.py"""
import digest
import push


def main():
    items = [{"source": "自检", "time": None,
              "text": "样例快讯：测试公司宣布完成新一轮测试融资，用于验证 DeepSeek 通道。"}]
    print("== DeepSeek 通道 ==")
    body, mode = digest.make_digest(items)
    print("模式:", mode)
    print(body[:200])
    print("\n== Server酱 通道 ==")
    push.push_serverchan("fin-daily 自检", "配置自检：微信收到这条说明推送通道 OK ✓\n\n" + body[:300])


if __name__ == "__main__":
    main()

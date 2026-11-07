# 📊 fin-daily · AI 财经日报推送

> 每天早上 08:00，自动抓取财经快讯 → 大模型写成"带影响分析"的日报 → 推送到你的微信。
> **零服务器、零成本、Fork 即用。**

[![Daily Digest](https://github.com/lizhihe-x/fin-daily/actions/workflows/daily.yml/badge.svg)](https://github.com/lizhihe-x/fin-daily/actions/workflows/daily.yml)
[![CI](https://github.com/lizhihe-x/fin-daily/actions/workflows/ci.yml/badge.svg)](https://github.com/lizhihe-x/fin-daily/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

---

## ✨ 它解决了什么问题

市面上的财经 App 给你的是**信息流**：两百条新闻堆在那里，你还得自己判断哪条跟自己的赛道有关、影响是什么。

fin-daily 给你的是**观点**：

- 🎯 **只讲你关心的赛道**（默认芯片/光通信/存储/AI/先进封装，可自由修改）
- 🧠 **每条都带"影响分析"**，不是复述标题
- 🌍 **重大宏观单独成栏**，并判断对产业链的传导方向
- 📱 **每天定时推送到微信**，电脑关机也照发
- 🗂️ **自动存档**到 `reports/`，随时回看

## 📸 效果预览

```markdown
## 🎯 今日核心（3 条）
1. **美中期选举民主党赢得两院** —— 国会分裂或放缓极端科技制裁推进节奏，利好科技板块情绪修复。
2. **苹果披露人形机器人"大脑"HALO进展** —— 具身智能从仿真走向真实验证，算力与机器人产业链迎催化。

## 🔬 产业链动态
### 存储
- ★★ **美光暗盘股价突破700美元**：日内涨1.9%。**影响**：反映资金对存储周期复苏与HBM产能溢价的持续看好，利好国内存储模组厂估值修复。

## 🌍 宏观与政策
- ★★★ **美中期选举民主党赢得国会两院**：特朗普政府成"跛脚鸭"。**影响**：国会分裂将增加极端对华科技管制法案的立法难度，短期科技制裁预期边际缓和。
```

完整示例见 [docs/sample-report.md](docs/sample-report.md)。

---

## 🏗️ 工作原理

```
GitHub Actions 定时器（每天 08:00）
        │
        ▼
抓取 6 个免费财经源（新浪7×24 / 新浪滚动 / 新浪科技 / 东财快讯 / 东财科技 / 金十）
        │  去重 · 时间窗过滤 · 单源失败自动跳过
        ▼
大模型按 config.json 的关注方向，生成"事实 + 影响分析"日报
        │  （无 Key 时自动降级为关键词规则版，不会失败静默）
        ▼
Server酱 / 企业微信机器人 → 你的手机
        │
        ▼
自动提交到 reports/ 存档（可回溯、可做周报）
```

**只用 Python 标准库**，无需 `pip install` 任何依赖。

---

## 🚀 三步用起来（约 10 分钟）

### 第 1 步：Fork 这个仓库

点右上角 **Fork** → 得到你自己的副本。

> 想改关注方向？Fork 后直接编辑 `config.json`（见下方"配置"）。

### 第 2 步：填两个 Key

进入你自己的仓库 → **Settings → Secrets and variables → Actions**：

| Secret 名称 | 从哪里获取 |
|---|---|
| `LLM_API_KEY` | 阿里云百炼 / DeepSeek / 智谱 等任一 OpenAI 兼容服务的 API Key |
| `SERVERCHAN_SENDKEY` | [sct.ftqq.com](https://sct.ftqq.com) 微信扫码登录后获取（记得关注"Server酱"服务号并绑定） |

（可选）在 **Variables** 标签页添加：

| Variable | 默认值 | 说明 |
|---|---|---|
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 模型服务地址 |
| `LLM_MODEL` | `qwen3.7-max` | 模型名 |

### 第 3 步：启用并测试

进入 **Actions** 标签页 → 左侧选 `daily-fin-digest` → **Enable workflow** → 点 **Run workflow**。

一两分钟后微信应收到日报。之后每天北京时间 08:00 自动执行。

---

## ⚙️ 配置（不改代码，只改 config.json）

```json
{
  "title": "每日财经速览",
  "topics": ["芯片 / 半导体", "光通信", "存储", "AI / 算力", "先进封装"],
  "extra_instructions": "",
  "max_input_items": 120,
  "hours_window": 36,
  "max_digest_items": "20~28"
}
```

| 字段 | 作用 | 举例 |
|---|---|---|
| `title` | 日报标题 | `"我的科技早报"` |
| `topics` | **你最关心的方向**，日报按这些分类 | `["新能源", "光伏", "储能"]` |
| `extra_instructions` | 额外要求，会拼进提示词 | `"每条控制在30字内，多关注A股"` |
| `max_input_items` | 送给模型的新闻条数上限 | `80` |
| `hours_window` | 只取最近多少小时的新闻 | `24` |
| `max_digest_items` | 日报条数范围 | `"12~15"` |

> 💡 改完 `config.json` 提交即可，下次运行自动生效。想立刻看效果就手动 Run workflow。

**不想用这个赛道？** 直接把 `topics` 换成你关心的任何领域——消费、医药、地产、宏观利率都可以，提示词会自动适配。

---

## 🔧 进阶玩法

| 想做什么 | 怎么做 |
|---|---|
| 改推送时间 | 编辑 `.github/workflows/daily.yml` 的 `cron`（**UTC 时间**，北京时间 = UTC+8） |
| 换模型 | 改 Variable `LLM_MODEL`（如 `deepseek-v4-pro`、`glm-5.3`、`kimi-k3`） |
| 加新闻源 | 在 `news.py` 里照葫芦画瓢加一个 `fetch_xxx()`，再加进 `collect_news` 的列表 |
| 推送到企业微信群 | 配 `WEBHOOK_URL`（群机器人 webhook），支持 Markdown |
| 本地跑 | `cp .env.example .env` 填入 Key，然后 `python main.py` |

---

## 📁 项目结构

```
main.py                     # 主流程：抓取 → 汇总 → 推送 → 存档
config.json                 # ⭐ 用户配置（关注方向、标题、条数）
config.py                   # 配置加载
news.py                     # 6 个免费新闻源（容错、去重、时间窗）
digest.py                   # 提示词构建 + 大模型调用 + 规则版降级
push.py                     # Server酱 / 企业微信 webhook
test_keys.py                # 密钥自检
.github/workflows/daily.yml # 每日定时任务
.github/workflows/ci.yml    # 提交时自动校验
reports/                    # 每日日报存档（自动提交）
docs/sample-report.md       # 效果样例
```

---

## ❓ FAQ

**Q：一定要用阿里云吗？**
不。任何 OpenAI 兼容接口都行——DeepSeek 官方、智谱、Kimi、本地 Ollama（`http://localhost:11434/v1`）都可以，改 `LLM_BASE_URL` 和 `LLM_MODEL` 即可。

**Q：没有 API Key 能跑吗？**
能跑，但输出的是关键词分类版（无 AI 分析）。配置 Key 后才有完整效果。

**Q：每天跑一次要花多少钱？**
GitHub Actions 公共仓库免费；大模型每次约 1 万 token，按各家价格通常几分钱。

**Q：数据可靠吗？**
全部来自公开接口，报告底部标注来源。程序对每个源做了容错，单源失效不影响出报。

**Q：会编造新闻吗？**
提示词里明确禁止编造快讯中没有的数字与公司；日报原文存档可核对。但 LLM 仍可能误判重要性，**请勿作为投资依据**。

---

## ⚠️ 免责声明

本项目仅用于**个人学习与技术研究**。所有新闻内容版权归原媒体所有；生成的日报**不构成任何投资建议**。请遵守目标网站的使用条款，控制请求频率。

## 📄 License

[MIT](LICENSE) © lizhihe-x

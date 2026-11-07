# 📊 AI 财经日报 · fin-daily

> 每天早上 **08:00**，自动抓取免费财经快讯 → DeepSeek 生成"公司金融视角"日报 → 推送到**个人微信**。
> 《公司金融》课程作业项目：零服务器、零费用、纯 Python 标准库。

## 一、它做了什么

```
GitHub Actions 定时触发（每天 08:00）
        │
        ▼
抓取免费新闻源：新浪财经7×24 / 东方财富快讯 / 金十数据 / 新浪滚动（news.py）
        │
        ▼
DeepSeek API 按课程定制提示词生成日报：四栏分类 + 重要度 + 编辑点评（digest.py）
        │
        ▼
Server酱 推送到你的个人微信（push.py），同时在 reports/ 存档一份 Markdown
```

## 二、效果预览

见 sample_report.md（真实数据生成的样例）。微信里将以消息卡片形式收到同样内容。

## 三、一次性准备：注册 3 个免费账号（约 15 分钟）

| 要注册什么 | 网址 | 你要拿到 | 备注 |
|---|---|---|---|
| GitHub | github.com | 一个空仓库 | 公共仓库 Actions 免费用 |
| DeepSeek 开放平台 | platform.deepseek.com | API Key | 先充值 ¥10（约够用数月，以官网价目为准）；在"API keys"页创建 |
| Server酱 | sct.ftqq.com | SendKey | 微信扫码登录；**务必按提示关注"Server酱"服务号并绑定微信**，否则收不到 |

## 四、部署 5 步

1. 把本项目全部文件上传到 GitHub 仓库（网页拖拽上传即可，注意包含隐藏的 .github 文件夹）
2. 仓库 Settings → Secrets and variables → Actions → New repository secret，添加两条：DEEPSEEK_SCHOOL_KEY（或 DEEPSEEK_API_KEY）和 SERVERCHAN_SENDKEY
   - 若使用学校/第三方 OpenAI 兼容网关：再到 Settings → Secrets and variables → **Variables** 添加 LLM_BASE_URL（如 https://网关地址/v1）和 LLM_MODEL（如 deepseek-v3）
3. 打开 Actions 标签页 → 左侧选中 daily-fin-digest → Enable workflow
4. 点击 Run workflow 手动跑一次，一两分钟后微信应收到日报（没收到就点进该次运行看日志排错；也可先在本机跑 python test_keys.py 自检）
5. 之后每天北京时间 08:00 自动执行

## 五、本地运行（可选）

```
copy .env.example .env    # Windows；填入两个 Key（本地专用，勿提交）
python main.py
```

## 六、想改点什么

- 改推送时间：编辑 .github/workflows/daily.yml 的 cron（UTC 时间，北京时间 = UTC + 8）
- 改栏目 / 语气 / 条数：编辑 digest.py 里的 SYSTEM_PROMPT
- 增删新闻源：编辑 news.py（每个源一个函数，单源失败自动跳过）
- 换推送通道（如企业微信群机器人 webhook）：改 push.py

## 七、这个项目里 AI 的角色（答辩要点）

1. **AI 写代码**：整条流水线由 AI 规划并编写
2. **AI 当编辑**：每天把上百条快讯压缩成 12~18 条分栏日报并写点评
3. 非 AI 的只有"闹钟"（cron）和"邮差"（HTTP 推送）

## 八、文件结构

```
main.py                     # 主流程：抓取 → 汇总 → 推送
news.py                     # 4 个免费新闻源抓取（容错、去重、限时段）
digest.py                   # AI 汇总（DeepSeek API，无 Key 时规则版兜底）
push.py                     # Server酱 微信推送
test_keys.py                # 两个 Key 的快速自检脚本
.env.example                # 本地密钥模板
requirements.txt            # 声明：无第三方依赖
.github/workflows/daily.yml # GitHub Actions 每日定时
reports/                    # 本地运行时的日报存档（不入库）
sample_report.md            # 效果样例
```

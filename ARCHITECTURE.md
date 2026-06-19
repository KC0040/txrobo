# TXROBO AI Agent — 完整架構說明
*2026-05-02 | 技術決策文件*

---

## 整體架構圖

```
你（或排程觸發）
      │
      ▼
agent_runner.py  ←──── 讀 PM_AGENT.md + KNOWLEDGE.md + AGENT.md
  (Claude Opus)
  Tool Use Brain
      │
      ├─ 本地檔案 ──────────────────────────────────────────────────
      │   read_file / write_file → *.html, data/*.json
      │   add_blog_post          → data/blog_posts.json
      │   get_leads              → data/comments.json
      │
      ├─ HTTP 直抓（keenon.com, 行業新聞）────────────────────────
      │   fetch_url              → 任意網頁文字內容
      │   list_keenon_articles   → keenon.com/en/news 列表
      │   localize_article       → 抓文章 + Claude 改寫 + 發布
      │
      ├─ 官方 API ─────────────────────────────────────────────────
      │   post_facebook          → Facebook Graph API
      │   get/reply_facebook_comment → Facebook Graph API
      │   send_telegram          → Telegram Bot API
      │
      ├─ Playwright 瀏覽器（需要 Instagram 等無 API 的平台）──────
      │   browser(navigate)      → 前往 URL
      │   browser(screenshot)    → 截圖 → data/screenshot.jpg
      │   browser(click/type)    → 操作頁面元素
      │   browser(content)       → 讀取頁面文字
      │
      └─ ADB 手機控制（手機 app，最靈活）───────────────────────
          adb(screenshot)        → 截圖 → data/phone_screenshot.png
          adb(tap/swipe/type)    → 操作手機螢幕
          adb(launch)            → 開啟 App

網站前端（訪客看的）
      │
      ▼
server.py (Flask port 5000) ─ 需要一直執行
  /api/chat           → Claude Alex 人設客服
  /api/blog           → 讀 blog_posts.json
  /api/blog/generate  → AI 生成文章
  /api/comment        → 收詢問 → Telegram 通知
```

---

## 開源瀏覽器自動化方案比較

### 可讓 AI 直接操作的開源瀏覽器工具

| 工具 | 底層 | AI 整合 | 穩定度 | 適合場景 |
|------|------|---------|--------|---------|
| **Playwright** | Chromium/Firefox/WebKit | 手動整合 | ⭐⭐⭐⭐⭐ | 所有場景首選 |
| **browser-use** | Playwright | 直接支援 Claude/GPT | ⭐⭐⭐⭐ | 快速上手 AI agent |
| **Skyvern** | Playwright | 自帶 AI 視覺 | ⭐⭐⭐⭐ | 複雜表單/流程 |
| **Puppeteer** | Chromium only | 手動整合 | ⭐⭐⭐⭐ | Node.js 環境 |
| **Selenium** | 所有瀏覽器 | 手動整合 | ⭐⭐⭐ | 舊專案相容 |
| **Open Interpreter** | 電腦控制 | 直接支援 | ⭐⭐⭐ | 更廣的電腦操作 |

### 本架構的選擇：Playwright（已整合到 agent_runner.py）

```bash
# 安裝
pip install playwright
playwright install chromium   # 下載 Chromium（~130MB）
```

**優點**：
- Microsoft 官方維護，最穩定
- 支援 headless 或有頭（可以看到瀏覽器動作）
- 自動等待元素（不需要 sleep）
- 截圖 → Claude 看圖 → 決定下一步（視覺 loop）

---

## 三種自動化方案決策樹

```
你需要操作什麼？
      │
      ├─ Facebook 頁面貼文/留言 ──→ Facebook Graph API（最快最穩）
      │
      ├─ keenon.com 抓文章 ───────→ HTTP requests（2秒完成）
      │
      ├─ Instagram 貼文 ─────────→ ADB（手機）或 Playwright（網頁版）
      │                              推薦 ADB，更穩定不易封號
      │
      ├─ YouTube 留言/管理 ───────→ YouTube Data API（官方）
      │
      ├─ 任意網站（有帳號登入）──→ Playwright（browser工具）
      │
      └─ 任意手機 App ────────────→ ADB（adb工具）
```

---

## KEENON 文章 Pipeline

### 流程

```
1. list_keenon_articles()
   └─ 列出最新 10 篇文章 + URL

2. localize_article(url, mode='rewrite', publish=False)
   └─ 抓原文 → Claude 改寫（TXROBO 視角 + Texas 在地化）
   └─ 回傳草稿 JSON 供審閱

3. 確認 OK → localize_article(url, publish=True)
   └─ 直接發布到 blog_posts.json
   └─ 前端 blog.html 立即顯示
```

### Agent 指令範例
```bash
python agent_runner.py "去 keenon.com 找最新文章，改寫成 TXROBO 版本給我看"
python agent_runner.py "把 keenon.com 最新的那篇新聞改寫並直接發布"
python agent_runner.py "自己寫一篇 Dallas 餐廳節省人力的 blog 文章並發布"
```

---

## Playwright 瀏覽器使用流程（Instagram 範例）

### Agent 的 Vision Loop

```
1. browser(navigate, url='https://www.instagram.com')
2. browser(screenshot)  → 存成 data/screenshot.jpg
3. Claude 看截圖 → 找到登入按鈕座標
4. browser(click, selector='input[name=username]')
5. browser(type, selector='input[name=username]', text='txrobot')
6. browser(type, selector='input[name=password]', text='...')
7. browser(click, selector='button[type=submit]')
8. browser(screenshot) → 確認登入成功
9. ... 繼續操作發文
```

### Agent 指令
```bash
python agent_runner.py "開啟 Instagram 瀏覽器，登入 @txrobot，發一篇 T10 的貼文"
```

---

## ADB 手機操作流程（Instagram App 範例）

### 設定步驟
```
1. 手機 → 設定 → 開發者選項 → 開啟 USB 偵錯
2. 用 USB 連接電腦
3. 手機上接受「允許 USB 偵錯」
4. 確認連線：adb devices（應該顯示手機序號）
5. 下載 Android Platform Tools：
   https://developer.android.com/tools/releases/platform-tools
```

### Agent 的 ADB Vision Loop

```
1. adb(screenshot) → 存成 data/phone_screenshot.png
2. Claude 看截圖分析目前畫面
3. adb(launch, package='com.instagram.android')
4. adb(screenshot) → 確認 Instagram 已開啟
5. adb(tap, x=540, y=1200) → 點擊「+」新增貼文
6. adb(screenshot) → 看目前狀態
7. ... Claude 根據截圖決定每一步
```

### Agent 指令
```bash
python agent_runner.py "用手機 ADB 開啟 Instagram，發一則 T9 的限時動態"
```

### 常用 App Package Name
```
Instagram:   com.instagram.android
Facebook:    com.facebook.katana
Facebook Page: com.facebook.pages.app
YouTube:     com.google.android.youtube
TikTok:      com.zhiliaoapp.musically
```

---

## 安裝清單

### 基本（必裝）
```bash
pip install anthropic requests beautifulsoup4
```

### Playwright 瀏覽器（選裝）
```bash
pip install playwright
playwright install chromium
```

### ADB 手機控制（選裝）
```
下載 Android Platform Tools：
https://developer.android.com/tools/releases/platform-tools

解壓到 C:\platform-tools\
把 C:\platform-tools\ 加入 PATH 環境變數
確認：adb devices
```

### browser-use（選裝，如果想用更高階 AI 瀏覽器）
```bash
pip install browser-use
playwright install chromium
```

---

## 環境變數（.env）

```env
# 必填
ANTHROPIC_API_KEY=sk-ant-...

# Facebook Graph API（貼文/留言管理）
FACEBOOK_PAGE_TOKEN=EAAxxxxx
FACEBOOK_PAGE_ID=61576172333620

# Telegram（Lead 通知）
TELEGRAM_BOT_TOKEN=7xxxxx:AAxxxx
TELEGRAM_CHANNEL_ID=-1001003596501916

# Instagram 帳號（給 Playwright/ADB 用，不是 API）
INSTAGRAM_USERNAME=txrobot
INSTAGRAM_PASSWORD=（建議用 App 密碼，非主密碼）
```

---

## 執行方式

```bash
# 每日例行（建議排程）
python agent_runner.py 每日

# KEENON 文章抓取改寫
python agent_runner.py "去 keenon.com 找最新文章，改寫一篇發布"

# 自己寫 blog
python agent_runner.py "寫一篇 Houston 飯店機器人的 SEO 文章並發布"

# Facebook 管理
python agent_runner.py "發一則 T10 iF Award 的 Facebook 貼文"
python agent_runner.py "讀取並回覆 Facebook 最新留言"

# 瀏覽器操作
python agent_runner.py "用瀏覽器到 Instagram 發一則貼文"

# ADB 手機操作
python agent_runner.py "用手機 ADB 截圖看目前狀態"
```

### Windows 工作排程器（每日 9:00 自動執行）
```
程式：C:\Users\kaize\anaconda3\python.exe
引數：C:\Claude\txrobo-website\agent_runner.py 每日
```

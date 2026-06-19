#!/usr/bin/env python3
"""
TXROBO PM Agent Runner
使用 Claude API + Tool Use 驅動的全能本地 PM Agent

功能：
  - 讀寫網站檔案（blog、leads）
  - 瀏覽任意網頁（keenon.com 新聞、行業動態）
  - 發布 Facebook 貼文、回覆留言
  - 發 Telegram 通知
  - 以 Alex 人設回覆客戶詢問

用法：
  python agent_runner.py                           # 互動模式
  python agent_runner.py 每日例行檢查
  python agent_runner.py "寫一篇 Dallas 餐廳 blog"
  python agent_runner.py "發 T10 iF Award FB 貼文"
  python agent_runner.py "檢查並回覆 Facebook 留言"
"""

import os, sys, json, datetime, re
from pathlib import Path

# ── 自動安裝依賴 ──────────────────────────────────────────────────
def _ensure(pkgs):
    for pkg in pkgs:
        mod = pkg.split('[')[0].replace('-', '_')
        try:
            __import__(mod)
        except ImportError:
            print(f"  安裝 {pkg}...")
            os.system(f"{sys.executable} -m pip install {pkg} --quiet")

_ensure(['anthropic', 'requests', 'beautifulsoup4'])

# Playwright（可選，瀏覽器自動化）
try:
    from playwright.sync_api import sync_playwright, Playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

# ADB（可選，手機控制）
import subprocess, shutil
ADB_PATH = shutil.which('adb') or r'C:\platform-tools\adb.exe'
ADB_OK   = Path(ADB_PATH).exists() if ADB_PATH else False

import anthropic
import requests
from bs4 import BeautifulSoup

# ── 路徑設定 ──────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent          # txrobo-website/
DATA_DIR     = BASE_DIR / 'data'
BLOG_FILE    = DATA_DIR / 'blog_posts.json'
COMMENT_FILE = DATA_DIR / 'comments.json'

DATA_DIR.mkdir(exist_ok=True)

# ── 讀取環境變數 ──────────────────────────────────────────────────
for env_path in [BASE_DIR.parent / '.env', BASE_DIR / '.env']:
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    os.environ.setdefault(k.strip(), v.strip())

ANTHROPIC_KEY     = os.environ.get('ANTHROPIC_API_KEY', '')
TELEGRAM_TOKEN    = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL  = os.environ.get('TELEGRAM_CHANNEL_ID', '')
FB_PAGE_TOKEN     = os.environ.get('FACEBOOK_PAGE_TOKEN', '')
FB_PAGE_ID        = os.environ.get('FACEBOOK_PAGE_ID', '')

if not ANTHROPIC_KEY:
    print("❌ 缺少 ANTHROPIC_API_KEY，請設定 .env")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ═══════════════════════════════════════════════════════════════════
# 工具實作
# ═══════════════════════════════════════════════════════════════════

def tool_fetch_url(url: str, max_chars: int = 10000) -> str:
    """抓取網頁文字內容（不需要 browser，直接 HTTP）"""
    try:
        r = requests.get(url, timeout=20, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text[:max_chars]
    except Exception as e:
        return f"ERROR fetching {url}: {e}"


def tool_read_file(path: str) -> str:
    """讀取本地檔案"""
    try:
        p = Path(path) if Path(path).is_absolute() else BASE_DIR / path
        if not p.exists():
            return f"File not found: {p}"
        return p.read_text(encoding='utf-8')
    except Exception as e:
        return f"ERROR: {e}"


def tool_write_file(path: str, content: str) -> str:
    """寫入本地檔案（HTML 頁面更新用）"""
    try:
        p = Path(path) if Path(path).is_absolute() else BASE_DIR / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        return f"Written {len(content)} chars → {p.name}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_get_leads(status_filter: str = 'pending') -> str:
    """取得未處理的 leads"""
    try:
        if not COMMENT_FILE.exists():
            return "No comments file yet."
        data = json.loads(COMMENT_FILE.read_text(encoding='utf-8'))
        if status_filter == 'pending':
            items = [c for c in data if c.get('category') == 'LEAD'
                     and c.get('status') != 'followed_up']
        else:
            items = data
        if not items:
            return "No pending leads."
        return json.dumps(items, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"ERROR: {e}"


def tool_add_blog_post(post_json: str) -> str:
    """發布新 blog 文章到 data/blog_posts.json"""
    try:
        post = json.loads(post_json)
        required = ['slug', 'title', 'excerpt', 'content', 'tags', 'date']
        missing = [f for f in required if f not in post]
        if missing:
            return f"Missing required fields: {missing}"

        posts = []
        if BLOG_FILE.exists():
            posts = json.loads(BLOG_FILE.read_text(encoding='utf-8'))

        if any(p['slug'] == post['slug'] for p in posts):
            return f"Slug '{post['slug']}' already exists. Choose another slug."

        post.setdefault('author', 'TXROBO Team')
        post.setdefault('readTime', f"{max(3, len(post['content']) // 1500)} min read")
        post.setdefault('featured', False)
        posts.insert(0, post)
        BLOG_FILE.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding='utf-8')
        return f"✅ Published: '{post['title']}' (slug: {post['slug']})"
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_mark_lead_handled(lead_id: str, note: str) -> str:
    """標記 lead 已跟進"""
    try:
        if not COMMENT_FILE.exists():
            return "No comments file."
        data = json.loads(COMMENT_FILE.read_text(encoding='utf-8'))
        for item in data:
            if item.get('id') == lead_id:
                item['status'] = 'followed_up'
                item['follow_up_note'] = note
                item['follow_up_date'] = datetime.datetime.now().isoformat()
                COMMENT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                return f"Lead {lead_id} marked as followed up."
        return f"Lead ID '{lead_id}' not found."
    except Exception as e:
        return f"ERROR: {e}"


def tool_post_facebook(message: str, link: str = '') -> str:
    """發 Facebook 貼文"""
    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        return "⚠️ Facebook not configured. Set FACEBOOK_PAGE_TOKEN + FACEBOOK_PAGE_ID in .env"
    try:
        payload = {'message': message, 'access_token': FB_PAGE_TOKEN}
        if link:
            payload['link'] = link
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed",
            data=payload, timeout=20
        )
        result = r.json()
        if 'id' in result:
            return f"✅ Posted to Facebook! Post ID: {result['id']}"
        return f"Facebook Error: {result}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_get_facebook_comments(post_id: str = '') -> str:
    """讀取 Facebook 頁面留言"""
    if not FB_PAGE_TOKEN or not FB_PAGE_ID:
        return "⚠️ Facebook not configured."
    try:
        if not post_id:
            # 取最新一篇貼文
            r = requests.get(
                f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed",
                params={'access_token': FB_PAGE_TOKEN, 'limit': 3},
                timeout=15
            )
            posts = r.json().get('data', [])
            if not posts:
                return "No posts found on Facebook page."
            post_id = posts[0]['id']

        r = requests.get(
            f"https://graph.facebook.com/v19.0/{post_id}/comments",
            params={
                'access_token': FB_PAGE_TOKEN,
                'fields': 'id,from,message,created_time,can_reply_privately',
                'limit': 25
            }, timeout=15
        )
        data = r.json()
        comments = data.get('data', [])
        if not comments:
            return f"No comments on post {post_id}."
        return json.dumps(comments, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"ERROR: {e}"


def tool_reply_facebook_comment(comment_id: str, message: str) -> str:
    """回覆 Facebook 留言"""
    if not FB_PAGE_TOKEN:
        return "⚠️ Facebook not configured."
    try:
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{comment_id}/replies",
            data={'message': message, 'access_token': FB_PAGE_TOKEN},
            timeout=15
        )
        result = r.json()
        if 'id' in result:
            return f"✅ Replied to comment {comment_id}"
        return f"Facebook Error: {result}"
    except Exception as e:
        return f"ERROR: {e}"


def tool_send_telegram(message: str) -> str:
    """發 Telegram 通知"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHANNEL:
        return "⚠️ Telegram not configured."
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={'chat_id': TELEGRAM_CHANNEL, 'text': message, 'parse_mode': 'HTML'},
            timeout=10
        )
        result = r.json()
        if result.get('ok'):
            return "✅ Telegram notification sent."
        return f"Telegram Error: {result}"
    except Exception as e:
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════════
# KEENON 文章 Pipeline
# ═══════════════════════════════════════════════════════════════════

KEENON_NEWS_URL = 'https://www.keenon.com/en/news/'

def tool_list_keenon_articles(max_items: int = 10) -> str:
    """列出 keenon.com 最新新聞文章"""
    try:
        r = requests.get(KEENON_NEWS_URL, timeout=20,
                         headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = []
        # keenon.com 的新聞列表結構（抓所有含日期/標題的連結）
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if '/en/news/' in href and len(text) > 20:
                full_url = href if href.startswith('http') else f"https://www.keenon.com{href}"
                if full_url != KEENON_NEWS_URL and full_url not in [x['url'] for x in articles]:
                    articles.append({'title': text[:120], 'url': full_url})
            if len(articles) >= max_items:
                break
        if not articles:
            return "找不到文章，試著用 fetch_url 直接抓 keenon.com/en/news/"
        return json.dumps(articles, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"ERROR: {e}"


def tool_localize_article(article_url: str, mode: str = 'rewrite', publish: bool = False) -> str:
    """
    抓取 KEENON 文章並改寫成 TXROBO 版本。
    mode: 'rewrite'（完全改寫為 TXROBO 在地化版本）| 'summarize'（只摘要）
    publish: True = 直接發布到 blog_posts.json
    """
    try:
        # 抓原文
        r = requests.get(article_url, timeout=20,
                         headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        original = soup.get_text(separator='\n', strip=True)[:6000]

        # 用 Claude 改寫
        prompt = f"""你是 TXROBO 的內容編輯。以下是 KEENON 官網的一篇文章。

原文（KEENON 官方）：
{original}

任務：{'完全改寫' if mode == 'rewrite' else '摘要'} 成一篇適合發布在 txrobo.com 的 blog 文章。

要求：
- 角度從 TXROBO（德州授權經銷商）出發，不是 KEENON 全球視角
- 加入德州/美國西南市場的關聯（Dallas, Houston, Texas, Oklahoma 等）
- 只提 T10, T9, S100 這三款產品
- 標題含城市/州名，50-60 chars
- 600-900 字
- 結尾 CTA：Book your 6-day free trial at txrobo.com/contact
- 回傳純 JSON 格式（不要 markdown code block）：
{{
  "slug": "kebab-case-title",
  "title": "文章標題",
  "excerpt": "150-160字摘要",
  "content": "<p>HTML 格式內文</p><h2>...</h2>",
  "tags": ["Texas", "tag2"],
  "date": "{datetime.date.today().isoformat()}",
  "source_url": "{article_url}"
}}"""

        response = client.messages.create(
            model='claude-opus-4-7',
            max_tokens=3000,
            messages=[{'role': 'user', 'content': prompt}]
        )
        raw = response.content[0].text.strip()

        # 解析 JSON
        # 移除可能的 markdown fences
        raw = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
        raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE)
        post = json.loads(raw)

        if publish:
            result = tool_add_blog_post(json.dumps(post, ensure_ascii=False))
            return f"{result}\n\n原文來源: {article_url}"
        else:
            return json.dumps(post, indent=2, ensure_ascii=False)

    except json.JSONDecodeError as e:
        return f"JSON 解析失敗: {e}\n原始回覆: {raw[:500]}"
    except Exception as e:
        return f"ERROR: {e}"


# ═══════════════════════════════════════════════════════════════════
# Playwright 瀏覽器工具（需要 pip install playwright + playwright install chromium）
# ═══════════════════════════════════════════════════════════════════

_pw_instance = None   # Playwright context 全域保留
_pw_browser  = None
_pw_page     = None

def _get_page():
    """取得或建立 Playwright 頁面"""
    global _pw_instance, _pw_browser, _pw_page
    if _pw_page is None:
        if not PLAYWRIGHT_OK:
            raise RuntimeError("Playwright 未安裝。執行：pip install playwright && playwright install chromium")
        _pw_instance = sync_playwright().start()
        _pw_browser  = _pw_instance.chromium.launch(headless=False)  # headless=False 可以看到瀏覽器
        _pw_page     = _pw_browser.new_page()
    return _pw_page


def tool_browser(action: str, url: str = '', selector: str = '',
                 text: str = '', x: int = 0, y: int = 0,
                 wait_ms: int = 1000) -> str:
    """
    Playwright 瀏覽器控制（所有動作都在同一個瀏覽器視窗）
    action:
      navigate   — 前往 URL
      screenshot — 截圖（回傳 base64 PNG）
      click      — 點擊 selector 或 (x,y) 座標
      type       — 在 selector 輸入文字
      content    — 取得目前頁面文字內容
      wait       — 等待 wait_ms 毫秒
      scroll     — 往下捲動
      press      — 按鍵（text = 'Enter', 'Tab', 'Escape' 等）
    """
    import base64, io
    try:
        page = _get_page()
        if action == 'navigate':
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(wait_ms)
            return f"Navigated to {page.url}"
        elif action == 'screenshot':
            buf = page.screenshot(type='jpeg', quality=60)
            b64 = base64.b64encode(buf).decode()
            # 存到檔案方便查看
            ss_path = BASE_DIR / 'data' / 'screenshot.jpg'
            ss_path.write_bytes(buf)
            return f"Screenshot saved → data/screenshot.jpg (base64 len={len(b64)})"
        elif action == 'click':
            if selector:
                page.click(selector, timeout=10000)
            else:
                page.mouse.click(x, y)
            page.wait_for_timeout(wait_ms)
            return f"Clicked {'selector: '+selector if selector else f'({x},{y})'}"
        elif action == 'type':
            if selector:
                page.fill(selector, text)
            else:
                page.keyboard.type(text)
            page.wait_for_timeout(wait_ms)
            return f"Typed: {text[:50]}"
        elif action == 'content':
            content = page.inner_text('body')
            return re.sub(r'\n{3,}', '\n\n', content)[:8000]
        elif action == 'wait':
            page.wait_for_timeout(wait_ms)
            return f"Waited {wait_ms}ms"
        elif action == 'scroll':
            page.keyboard.press('End')
            page.wait_for_timeout(wait_ms)
            return "Scrolled to bottom"
        elif action == 'press':
            page.keyboard.press(text)
            page.wait_for_timeout(wait_ms)
            return f"Pressed {text}"
        else:
            return f"Unknown action: {action}. Use: navigate/screenshot/click/type/content/wait/scroll/press"
    except Exception as e:
        return f"Browser ERROR: {e}"


# ═══════════════════════════════════════════════════════════════════
# ADB 手機工具（需要 Android 手機 + USB + ADB 驅動）
# ═══════════════════════════════════════════════════════════════════

def _adb(args: list, timeout: int = 15) -> str:
    """執行 adb 命令"""
    try:
        result = subprocess.run(
            [ADB_PATH] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return (result.stdout + result.stderr).strip()
    except FileNotFoundError:
        return "ADB 未找到。安裝 Android Platform Tools 並設定 PATH"
    except subprocess.TimeoutExpired:
        return f"ADB timeout ({timeout}s)"
    except Exception as e:
        return f"ADB ERROR: {e}"


def tool_adb(action: str, x: int = 0, y: int = 0, x2: int = 0, y2: int = 0,
             text: str = '', package: str = '', duration_ms: int = 100) -> str:
    """
    ADB 手機控制（Android 手機透過 USB）
    action:
      devices    — 列出連線裝置
      screenshot — 手機截圖（存到 data/phone_screenshot.png）
      tap        — 點擊 (x,y)
      swipe      — 從 (x,y) 滑到 (x2,y2)
      type       — 輸入文字（需先點擊輸入框）
      keyevent   — 按鍵（text = KEYCODE，如 KEYCODE_ENTER, KEYCODE_BACK）
      launch     — 開啟 App（package = app package name）
      home       — 回主畫面
      back       — 返回
    """
    import base64
    if not ADB_OK:
        return f"ADB 未安裝或未找到 ({ADB_PATH})。下載 Android Platform Tools。"

    if action == 'devices':
        return _adb(['devices'])

    elif action == 'screenshot':
        _adb(['shell', 'screencap', '-p', '/sdcard/ss.png'])
        ss_path = BASE_DIR / 'data' / 'phone_screenshot.png'
        _adb(['pull', '/sdcard/ss.png', str(ss_path)])
        if ss_path.exists():
            return f"Phone screenshot saved → data/phone_screenshot.png ({ss_path.stat().st_size} bytes)"
        return "Screenshot failed"

    elif action == 'tap':
        return _adb(['shell', 'input', 'tap', str(x), str(y)])

    elif action == 'swipe':
        return _adb(['shell', 'input', 'swipe',
                     str(x), str(y), str(x2), str(y2), str(duration_ms)])

    elif action == 'type':
        # ADB input text 不支援特殊字符，用 broadcast 方式
        safe = text.replace(' ', '%s').replace("'", "\\'")
        return _adb(['shell', 'input', 'text', safe])

    elif action == 'keyevent':
        return _adb(['shell', 'input', 'keyevent', text])

    elif action == 'launch':
        if '/' not in package:
            return _adb(['shell', 'monkey', '-p', package, '-c',
                         'android.intent.category.LAUNCHER', '1'])
        return _adb(['shell', 'am', 'start', '-n', package])

    elif action == 'home':
        return _adb(['shell', 'input', 'keyevent', 'KEYCODE_HOME'])

    elif action == 'back':
        return _adb(['shell', 'input', 'keyevent', 'KEYCODE_BACK'])

    else:
        return f"Unknown ADB action: {action}"


# ═══════════════════════════════════════════════════════════════════
# Claude Tool Schema
# ═══════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "fetch_url",
        "description": "Fetch and read the text content of any webpage. Use for: browsing keenon.com/en/news for new articles, checking industry news, researching blog topics. Returns cleaned text content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to fetch (e.g. https://www.keenon.com/en/news/)"},
                "max_chars": {"type": "integer", "description": "Max characters to return (default 10000)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a local file from the txrobo-website directory. Use for reading blog_posts.json, comments.json, HTML pages, or any website file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from txrobo-website/ (e.g. 'data/blog_posts.json', 'index.html', 'KNOWLEDGE.md')"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a local file. Use for updating HTML pages (index.html, products.html etc). For blog posts use add_blog_post instead.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from txrobo-website/"},
                "content": {"type": "string", "description": "Full file content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "get_leads",
        "description": "Get leads and inquiries submitted through the website chat or contact form.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {"type": "string", "enum": ["pending", "all"], "description": "Filter: 'pending' (default) = unhandled leads, 'all' = everything"}
            }
        }
    },
    {
        "name": "add_blog_post",
        "description": "Publish a new blog post to the website. It will immediately appear on the blog page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_json": {
                    "type": "string",
                    "description": "JSON string. Required fields: slug (kebab-case), title (50-60 chars with city name), excerpt (150-160 chars), content (HTML with <p><h2><ul> tags), tags (array of strings), date (YYYY-MM-DD). Optional: author, readTime, featured (bool)"
                }
            },
            "required": ["post_json"]
        }
    },
    {
        "name": "mark_lead_handled",
        "description": "Mark a lead as followed up after the human sales team has contacted them.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string", "description": "Lead UUID from comments.json"},
                "note": {"type": "string", "description": "Follow-up note (e.g. 'Called May 2, scheduled trial for May 6')"}
            },
            "required": ["lead_id", "note"]
        }
    },
    {
        "name": "post_facebook",
        "description": "Post to the TXROBO Facebook page. Use line breaks (\\n) in the message. Include relevant hashtags at the end.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Full post content with hashtags"},
                "link": {"type": "string", "description": "Optional URL to attach (e.g. blog post URL)"}
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_facebook_comments",
        "description": "Get comments from the TXROBO Facebook page posts. Returns comment IDs, text, and author info.",
        "input_schema": {
            "type": "object",
            "properties": {
                "post_id": {"type": "string", "description": "Specific post ID (optional — omit to get comments from the most recent post)"}
            }
        }
    },
    {
        "name": "reply_facebook_comment",
        "description": "Reply to a comment on Facebook as the TXROBO page. Use the Alex persona — warm, professional, guide toward 6-day free trial.",
        "input_schema": {
            "type": "object",
            "properties": {
                "comment_id": {"type": "string", "description": "Facebook comment ID"},
                "message": {"type": "string", "description": "Reply text (conversational, ≤3 sentences, Alex persona)"}
            },
            "required": ["comment_id", "message"]
        }
    },
    {
        "name": "send_telegram",
        "description": "Send a notification to the TXROBO Telegram channel. Use for: HIGH urgency leads, daily reports, important updates requiring human attention.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message text. Supports HTML: <b>bold</b>, <i>italic</i>, <a href='url'>link</a>"}
            },
            "required": ["message"]
        }
    },
    # ── KEENON Pipeline ──────────────────────────────────────────────
    {
        "name": "list_keenon_articles",
        "description": "List the latest articles from keenon.com/en/news/. Returns titles and URLs. Use this first to find articles worth localizing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_items": {"type": "integer", "description": "Max articles to return (default 10)"}
            }
        }
    },
    {
        "name": "localize_article",
        "description": "Fetch a KEENON article URL, rewrite it as a TXROBO-branded blog post targeting Texas/Southwest market, and optionally publish it directly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "article_url": {"type": "string", "description": "Full URL of the KEENON article to localize"},
                "mode": {"type": "string", "enum": ["rewrite", "summarize"], "description": "'rewrite' = full localized blog post (default), 'summarize' = short summary only"},
                "publish": {"type": "boolean", "description": "If true, immediately publish to blog_posts.json (default false — review first)"}
            },
            "required": ["article_url"]
        }
    },
    # ── Playwright 瀏覽器 ─────────────────────────────────────────────
    {
        "name": "browser",
        "description": "Control a real browser (Playwright/Chromium). Use for: Instagram posting, sites without APIs, social media that blocks API. Requires: pip install playwright && playwright install chromium",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["navigate", "screenshot", "click", "type", "content", "wait", "scroll", "press"],
                    "description": "navigate=go to URL | screenshot=capture page | click=click element/coords | type=fill input | content=get page text | wait=pause | scroll=scroll down | press=keyboard key"
                },
                "url":       {"type": "string",  "description": "URL for navigate action"},
                "selector":  {"type": "string",  "description": "CSS selector for click/type (e.g. 'input[name=email]', 'button.submit')"},
                "text":      {"type": "string",  "description": "Text to type, or key name for press (Enter/Tab/Escape/ArrowDown)"},
                "x":         {"type": "integer", "description": "X coordinate for click (if no selector)"},
                "y":         {"type": "integer", "description": "Y coordinate for click (if no selector)"},
                "wait_ms":   {"type": "integer", "description": "Milliseconds to wait after action (default 1000)"}
            },
            "required": ["action"]
        }
    },
    # ── ADB 手機控制 ──────────────────────────────────────────────────
    {
        "name": "adb",
        "description": "Control an Android phone via USB (ADB). Use for: posting to Instagram app, any mobile-only social media, apps without PC version. Phone must be connected via USB with USB debugging enabled.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["devices", "screenshot", "tap", "swipe", "type", "keyevent", "launch", "home", "back"],
                    "description": "devices=list connected phones | screenshot=capture phone screen (saved to data/phone_screenshot.png) | tap=touch at (x,y) | swipe=drag from (x,y) to (x2,y2) | type=input text | keyevent=press key | launch=open app | home=home button | back=back button"
                },
                "x":          {"type": "integer", "description": "X coordinate (tap/swipe start)"},
                "y":          {"type": "integer", "description": "Y coordinate (tap/swipe start)"},
                "x2":         {"type": "integer", "description": "X end coordinate (swipe)"},
                "y2":         {"type": "integer", "description": "Y end coordinate (swipe)"},
                "text":       {"type": "string",  "description": "Text to type, or keycode (KEYCODE_ENTER, KEYCODE_BACK, KEYCODE_HOME)"},
                "package":    {"type": "string",  "description": "App package name for launch (e.g. 'com.instagram.android', 'com.facebook.katana')"},
                "duration_ms":{"type": "integer", "description": "Swipe duration in ms (default 100, use 300+ for slow scroll)"}
            },
            "required": ["action"]
        }
    }
]

# ═══════════════════════════════════════════════════════════════════
# Tool Executor
# ═══════════════════════════════════════════════════════════════════

TOOL_MAP = {
    'fetch_url':               lambda i: tool_fetch_url(i['url'], i.get('max_chars', 10000)),
    'read_file':               lambda i: tool_read_file(i['path']),
    'write_file':              lambda i: tool_write_file(i['path'], i['content']),
    'get_leads':               lambda i: tool_get_leads(i.get('status_filter', 'pending')),
    'add_blog_post':           lambda i: tool_add_blog_post(i['post_json']),
    'mark_lead_handled':       lambda i: tool_mark_lead_handled(i['lead_id'], i['note']),
    'post_facebook':           lambda i: tool_post_facebook(i['message'], i.get('link', '')),
    'get_facebook_comments':   lambda i: tool_get_facebook_comments(i.get('post_id', '')),
    'reply_facebook_comment':  lambda i: tool_reply_facebook_comment(i['comment_id'], i['message']),
    'send_telegram':           lambda i: tool_send_telegram(i['message']),
    # KEENON pipeline
    'list_keenon_articles':    lambda i: tool_list_keenon_articles(i.get('max_items', 10)),
    'localize_article':        lambda i: tool_localize_article(
                                   i['article_url'], i.get('mode', 'rewrite'), i.get('publish', False)),
    # 瀏覽器
    'browser':                 lambda i: tool_browser(
                                   i['action'], i.get('url',''), i.get('selector',''),
                                   i.get('text',''), i.get('x',0), i.get('y',0), i.get('wait_ms',1000)),
    # ADB
    'adb':                     lambda i: tool_adb(
                                   i['action'], i.get('x',0), i.get('y',0),
                                   i.get('x2',0), i.get('y2',0), i.get('text',''),
                                   i.get('package',''), i.get('duration_ms',100)),
}

def execute_tool(name: str, inputs: dict) -> str:
    fn = TOOL_MAP.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    try:
        return fn(inputs)
    except Exception as e:
        return f"Tool error ({name}): {e}"

# ═══════════════════════════════════════════════════════════════════
# System Prompt（讀 PM_AGENT.md + KNOWLEDGE.md）
# ═══════════════════════════════════════════════════════════════════

def load_system() -> str:
    parts = []
    for fname in ['PM_AGENT.md', 'KNOWLEDGE.md', 'AGENT.md']:
        fpath = BASE_DIR / fname
        if fpath.exists():
            parts.append(f"# {fname}\n\n{fpath.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(parts)

# ═══════════════════════════════════════════════════════════════════
# Agent 執行迴圈
# ═══════════════════════════════════════════════════════════════════

def run_agent(task: str, verbose: bool = True):
    system = load_system()
    messages = [{"role": "user", "content": task}]

    if verbose:
        print(f"\n{'='*60}")
        print(f"🤖 TXROBO PM Agent")
        print(f"任務: {task[:100]}")
        print(f"{'='*60}\n")

    iteration = 0
    max_iterations = 20  # 防止無限迴圈

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages
        )

        # 顯示 Agent 文字輸出
        for block in response.content:
            if hasattr(block, 'text') and block.text.strip():
                print(f"\nAlex: {block.text}")

        # 結束條件
        if response.stop_reason == 'end_turn':
            break

        # 處理工具呼叫
        if response.stop_reason == 'tool_use':
            tool_results = []
            for block in response.content:
                if block.type == 'tool_use':
                    input_preview = json.dumps(block.input, ensure_ascii=False)[:100]
                    if verbose:
                        print(f"\n  🔧 {block.name}({input_preview}...)")

                    result = execute_tool(block.name, block.input)

                    if verbose:
                        result_preview = str(result)[:150].replace('\n', ' ')
                        print(f"  ↳ {result_preview}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    if verbose:
        print(f"\n{'='*60}")
        print(f"✅ Agent 完成（{iteration} 輪）")
        print(f"{'='*60}\n")

# ═══════════════════════════════════════════════════════════════════
# 預設任務
# ═══════════════════════════════════════════════════════════════════

DAILY_TASK = f"""
今日（{datetime.date.today()}）例行任務，請依序執行：

1. 讀取 data/comments.json，整理今日新的 LEAD，分 HIGH/MEDIUM/LOW 優先序
2. 瀏覽 https://www.keenon.com/en/news/ 看有無最近一週的新消息
3. 根據情報，判斷是否有值得寫的 blog 文章主題（如有，直接寫並發布）
4. 讀取 Facebook 最新貼文的留言，回覆尚未回覆的留言（Alex 人設）
5. 如果有 HIGH urgency lead，發 Telegram 通知
6. 最後給出今日摘要 + 下週建議行動
"""

TASK_SHORTCUTS = {
    'daily':  DAILY_TASK,
    '每日':   DAILY_TASK,
    '例行':   DAILY_TASK,
}

# ═══════════════════════════════════════════════════════════════════
# 主程式
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if len(sys.argv) > 1:
        task = ' '.join(sys.argv[1:])
        task = TASK_SHORTCUTS.get(task, task)
    else:
        print("\nTXROBO PM Agent — 指令範例:")
        print("  python agent_runner.py 每日                            # 每日例行")
        print("  python agent_runner.py 寫一篇 Dallas 餐廳機器人的文章")
        print("  python agent_runner.py 發一則 T10 iF Award 的 Facebook 貼文")
        print("  python agent_runner.py 檢查並回覆 Facebook 留言")
        print("  python agent_runner.py 整理今日 leads 報告")
        print("  python agent_runner.py 瀏覽 keenon.com 找最新新聞\n")
        task = input("請輸入任務 (Enter = 每日例行): ").strip()
        if not task:
            task = DAILY_TASK

    run_agent(task)

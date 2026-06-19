"""
TXROBO 網站後端伺服器
功能：
  1. 靜態 HTML 頁面服務
  2. /api/chat          — AI 客服聊天（Claude API）
  3. /api/blog          — GET Blog 文章列表 / 單篇
  4. /api/blog/generate — POST AI Agent 自動生成 SEO Blog 文章
  5. /api/comment       — GET/POST 留言系統
  6. /api/notify        — Hermes：重要留言 → Telegram 頻道通知

啟動方式：
    C:\\Users\\kaize\\anaconda3\\python.exe server.py

開啟瀏覽器前往：http://localhost:5000
"""

import os
import sys
import json
import uuid
import datetime
import threading
from pathlib import Path

# ── 載入 .env ──────────────────────────────────────────────────
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# ── 自動安裝依賴 ───────────────────────────────────────────────
def _ensure(pkgs):
    for pkg in pkgs:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            os.system(f"{sys.executable} -m pip install {pkg} --quiet")

_ensure(["flask", "flask-cors", "anthropic", "requests"])

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic
import requests

# ── 設定 ───────────────────────────────────────────────────────
WEBSITE_DIR  = Path(__file__).parent
DATA_DIR     = WEBSITE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

BLOG_FILE    = DATA_DIR / "blog_posts.json"
COMMENT_FILE = DATA_DIR / "comments.json"

API_KEY            = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# 設定為你的私人頻道 ID（格式：@channelname 或 -100xxxxxxxxxx）
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

# ── 服務範圍（GEO SEO）──────────────────────────────────────────
SERVICE_AREAS = {
    "Texas":      ["Dallas", "Houston", "Austin", "San Antonio", "Fort Worth", "El Paso"],
    "Oklahoma":   ["Oklahoma City", "Tulsa", "Norman"],
    "Louisiana":  ["New Orleans", "Baton Rouge", "Shreveport"],
    "New Mexico": ["Albuquerque", "Santa Fe", "Las Cruces"],
    "Arkansas":   ["Little Rock", "Fayetteville", "Fort Smith"],
    "Mississippi":["Jackson", "Biloxi", "Gulfport"],
    "Colorado":   ["Denver", "Colorado Springs", "Boulder"],
    "Kansas":     ["Wichita", "Kansas City", "Overland Park"],
}

# ── AI 系統提示詞 ───────────────────────────────────────────────
CHAT_SYSTEM = """You are Alex, a customer advisor at TXROBO — the authorized KEENON Robotics distributor for Texas and the Southwest United States.

PERSONALITY:
- Warm, professional, and genuinely helpful — like a knowledgeable local business rep based in Dallas, Texas.
- You speak naturally and conversationally, NOT like a chatbot. Use a friendly tone with hints of Southern hospitality.
- You are enthusiastic about robots but never pushy. For Dallas-area customers, guide toward the 6-day FREE trial. For other regions, guide toward calling 214-454-9356.
- If asked if you are an AI or robot: "Ha, good one! I'm Alex, your TXROBO advisor — here to help you find the right fit for your business."
- Keep responses concise (under 120 words) unless explaining something complex.
- Match the user's language — respond in English or 中文 based on what they write.

COMPANY:
- TXROBO | Phone: 214-454-9356 | Email: info@txrobo.com | Website: txrobo.com
- Authorized KEENON Robotics distributor — 35,000+ robots deployed, 60+ countries, Marriott/Hilton partner
- Service areas: Texas (Dallas, Houston, Austin, San Antonio, Fort Worth), Oklahoma, Louisiana, New Mexico, Arkansas
- Expanding: Colorado, Kansas, Mississippi

PRODUCTS (ONLY mention these three):
1. **T10** ⭐ PRIMARY — 2025 iF Design Award | 40kg payload | 23.8" HD advertising screen | 24h battery | LIDAR
   Best for: restaurants, hotels, corporate offices | UNIQUE: earns ad revenue while delivering
2. **T9** ⭐ PRIMARY — Flagship delivery | 30kg | 4 trays | silent LIDAR | multi-floor support
   Best for: restaurants, hotels, hospitals, offices | Trusted by global hospitality chains
3. **S100** — Autonomous UV + spray disinfection | scheduled cycles | no staff needed during operation
   Recommend only when customer asks about disinfection/healthcare

KEY VALUE PROPOSITIONS:
- 6-day FREE trial — available within 100 miles of Dallas, TX (DFW metro) only
- Outside Dallas 100-mile radius: robots available but call 214-454-9356 for deployment options
- $300+ per week typical savings per robot
- Deploy in 1–3 business days, no IT changes needed
- Monthly rental plans, no large upfront cost
- Maintenance & repairs INCLUDED, local same-day support

CONVERSATION GOALS (in order):
1. Understand their business type and pain point
2. Match them to the right robot (T9/T10 for most, S100 for healthcare)
3. Get them excited about the free trial
4. Collect: name, business name, city, phone/email → tell them "our Texas team will reach out within 1 business day"

PRICING: Never quote specific numbers. Say: "We work on a monthly rental model — most clients find it pays for itself in the first month. Want me to have someone reach out with an exact quote for your setup?"

DO NOT: Mention BellaBot, KettyBot, W3, or any product not in this list. Never say you are an AI or language model. Never guarantee specific ROI amounts."""

BLOG_SYSTEM = """You are TXROBO's content strategist and SEO writer. Write blog posts targeting businesses in Texas, Oklahoma, Louisiana, New Mexico, Arkansas, and neighboring states that face labor shortages.

TXROBO sells KEENON Robotics service robots (T10, T9, S100) to restaurants, hotels, hospitals, offices, and retail.

WRITING RULES:
- Target primary keyword in H1 and first paragraph
- Include location-specific references (city/state names)
- Include statistics on labor costs, ROI, or robot efficiency
- Mention 6-day free trial and 214-454-9356 as CTA
- Tone: confident, practical, business-focused (not hype)
- Length: 600–900 words
- Structure: H2 subheadings, bullet points where appropriate
- End with: call to action for free trial"""

COMMENT_CLASSIFIER_SYSTEM = """You analyze visitor comments/inquiries on TXROBO's robotics website.

Classify each comment into ONE category:
- LEAD: Person expresses interest in buying, renting, or trying the robots
- QUESTION: General question, needs informational answer
- COMPLAINT: Problem, issue, or negative feedback
- SPAM: Irrelevant, promotional, or gibberish
- MEDIA: Press/journalist/blogger inquiry

Also rate urgency: HIGH / MEDIUM / LOW

Respond in JSON:
{
  "category": "LEAD|QUESTION|COMPLAINT|SPAM|MEDIA",
  "urgency": "HIGH|MEDIUM|LOW",
  "summary": "One-sentence summary of the comment",
  "should_notify_owner": true|false,
  "suggested_reply": "A helpful, concise reply (2–4 sentences) in the same language as the comment"
}

Notify owner (should_notify_owner: true) for: LEAD (always), COMPLAINT (HIGH/MEDIUM), MEDIA (always)."""

# ── 資料層 helpers ──────────────────────────────────────────────
def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Telegram 頻道通知 ───────────────────────────────────────────
def send_telegram_alert(message: str):
    """發送訊息到 Telegram 私人頻道（不顯示 BOT 標籤）"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print(f"[Telegram] 未設定，跳過通知。訊息：{message[:80]}...")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[Telegram] 通知失敗: {e}")
        return False

def format_hermes_alert(comment_data: dict, analysis: dict) -> str:
    """格式化 Hermes 通知訊息"""
    cat_emoji = {
        "LEAD": "🔥", "COMPLAINT": "⚠️", "MEDIA": "📰",
        "QUESTION": "💬", "SPAM": "🗑️"
    }
    urgency_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

    cat = analysis.get("category", "QUESTION")
    urgency = analysis.get("urgency", "LOW")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"{cat_emoji.get(cat,'📌')} <b>TXROBO ALERT — {cat}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{urgency_emoji.get(urgency,'⚪')} Urgency: <b>{urgency}</b>\n"
        f"🕐 {now}\n\n"
        f"📝 <b>Comment:</b>\n{comment_data.get('content','')[:300]}\n\n"
        f"👤 From: {comment_data.get('author_name','Anonymous')}\n"
        f"🌐 Post: {comment_data.get('post_slug','homepage')}\n\n"
        f"💡 <b>AI Summary:</b> {analysis.get('summary','')}\n\n"
        f"📞 Call: 214-454-9356\n"
        f"📧 Email: info@txrobo.com"
    )

# ── Claude helpers ──────────────────────────────────────────────
def claude_chat(user_message: str) -> str:
    if not API_KEY:
        return "Chat not configured. Call **214-454-9356** or email **info@txrobo.com**."
    client = anthropic.Anthropic(api_key=API_KEY)
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=350,
        system=CHAT_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )
    return r.content[0].text

def claude_generate_blog(topic: str, target_state: str = "Texas") -> dict:
    if not API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=API_KEY)

    prompt = (
        f"Write a blog post for TXROBO targeting businesses in {target_state}.\n"
        f"Topic: {topic}\n\n"
        f"Return ONLY valid JSON with these fields:\n"
        f'{{"title": "...", "slug": "...", "excerpt": "...", '
        f'"content": "...(HTML with <h2>,<p>,<ul>,<li>)", '
        f'"tags": ["tag1","tag2"], "target_state": "{target_state}"}}'
    )
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        system=BLOG_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = r.content[0].text.strip()
    # 移除可能的 ```json 標記
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def claude_classify_comment(content: str) -> dict:
    if not API_KEY:
        return {
            "category": "QUESTION", "urgency": "LOW",
            "summary": content[:80],
            "should_notify_owner": False,
            "suggested_reply": "Thank you for your message! Please contact us at 214-454-9356 or info@txrobo.com."
        }
    client = anthropic.Anthropic(api_key=API_KEY)
    r = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        system=COMMENT_CLASSIFIER_SYSTEM,
        messages=[{"role": "user", "content": f"Comment:\n{content}"}],
    )
    raw = r.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ── Flask App ───────────────────────────────────────────────────
app = Flask(__name__, static_folder=str(WEBSITE_DIR))
CORS(app)

# ── Static file serving ─────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(WEBSITE_DIR, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    # 避免 API 路由被攔截
    if filename.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(WEBSITE_DIR, filename)

# ══════════════════════════════════════════════════════════════
# API: CHAT
# ══════════════════════════════════════════════════════════════
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing message"}), 400
    msg = str(data["message"]).strip()[:1000]
    try:
        reply = claude_chat(msg)
        return jsonify({"reply": reply})
    except anthropic.AuthenticationError:
        return jsonify({"reply": "Chat temporarily unavailable. Call **214-454-9356** or email **info@txrobo.com**."}), 200
    except Exception as e:
        return jsonify({"reply": "Connection issue. Call **214-454-9356** for immediate help."}), 200

# ══════════════════════════════════════════════════════════════
# API: BLOG
# ══════════════════════════════════════════════════════════════
@app.route("/api/blog", methods=["GET"])
def api_blog_list():
    """回傳 Blog 文章列表（摘要，不含完整內容）"""
    posts = _load_json(BLOG_FILE, [])
    # 最新優先，回傳摘要
    summary = [
        {k: p[k] for k in ("id","title","slug","excerpt","tags","target_state","published_at","author")}
        for p in reversed(posts) if p.get("published", True)
    ]
    return jsonify({"posts": summary, "total": len(summary)})

@app.route("/api/blog/<slug>", methods=["GET"])
def api_blog_post(slug):
    """回傳單篇 Blog 文章（含完整 HTML 內容）"""
    posts = _load_json(BLOG_FILE, [])
    post = next((p for p in posts if p["slug"] == slug), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post)

@app.route("/api/blog/generate", methods=["POST"])
def api_blog_generate():
    """AI Agent 生成新 Blog 文章並儲存"""
    data = request.get_json() or {}
    topic = data.get("topic", "How service robots help businesses save on labor costs")
    target_state = data.get("target_state", "Texas")
    author = data.get("author", "TXROBO AI")

    if not API_KEY:
        return jsonify({"error": "ANTHROPIC_API_KEY not configured"}), 503

    try:
        post_data = claude_generate_blog(topic, target_state)
    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500

    posts = _load_json(BLOG_FILE, [])
    new_post = {
        "id": str(uuid.uuid4())[:8],
        "title": post_data.get("title", topic),
        "slug": post_data.get("slug", topic.lower().replace(" ", "-")[:60]),
        "excerpt": post_data.get("excerpt", ""),
        "content": post_data.get("content", ""),
        "tags": post_data.get("tags", [target_state, "service robots"]),
        "target_state": target_state,
        "author": author,
        "published": True,
        "published_at": datetime.datetime.utcnow().isoformat() + "Z",
        "ai_generated": True,
        "seo": {
            "meta_description": post_data.get("excerpt", "")[:160],
            "keywords": [target_state, "service robots", "KEENON", "TXROBO"] + post_data.get("tags", []),
        }
    }
    posts.append(new_post)
    _save_json(BLOG_FILE, posts)

    # 非同步通知（新文章發佈）
    def notify():
        send_telegram_alert(
            f"📝 <b>新 Blog 文章已發佈</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"標題：{new_post['title']}\n"
            f"目標州：{target_state}\n"
            f"作者：{author}\n"
            f"連結：https://www.txrobo.com/blog/{new_post['slug']}"
        )
    threading.Thread(target=notify, daemon=True).start()

    return jsonify({"success": True, "post": new_post}), 201

# ══════════════════════════════════════════════════════════════
# API: COMMENTS
# ══════════════════════════════════════════════════════════════
@app.route("/api/comment/<post_slug>", methods=["GET"])
def api_comments_get(post_slug):
    """取得指定文章的留言（含 AI 回覆）"""
    comments = _load_json(COMMENT_FILE, [])
    post_comments = [c for c in comments if c.get("post_slug") == post_slug and not c.get("hidden")]
    return jsonify({"comments": post_comments, "total": len(post_comments)})

@app.route("/api/comment", methods=["POST"])
def api_comment_post():
    """提交新留言 → AI 分類 → 自動回覆 → 重要留言 Hermes 通知"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    required = ("post_slug", "author_name", "content")
    if not all(data.get(k) for k in required):
        return jsonify({"error": f"Required: {required}"}), 400

    content   = str(data["content"]).strip()[:2000]
    post_slug = str(data["post_slug"]).strip()[:100]
    author    = str(data["author_name"]).strip()[:80]
    author_email = str(data.get("author_email", "")).strip()[:120]

    # ── AI 分類 ──
    try:
        analysis = claude_classify_comment(content)
    except Exception:
        analysis = {
            "category": "QUESTION", "urgency": "LOW",
            "summary": content[:80], "should_notify_owner": False,
            "suggested_reply": "Thank you for your message! Contact us at 214-454-9356 or info@txrobo.com."
        }

    comment_id = str(uuid.uuid4())[:12]
    now = datetime.datetime.utcnow().isoformat() + "Z"

    comment_record = {
        "id": comment_id,
        "post_slug": post_slug,
        "author_name": author,
        "author_email": author_email,
        "content": content,
        "submitted_at": now,
        "hidden": analysis["category"] == "SPAM",
        "ai_category": analysis["category"],
        "ai_urgency": analysis["urgency"],
        "ai_summary": analysis.get("summary", ""),
        "ai_reply": analysis.get("suggested_reply", ""),
        "ai_replied_at": now,
        "notified_owner": False,
    }

    # ── 儲存 ──
    comments = _load_json(COMMENT_FILE, [])
    comments.append(comment_record)
    _save_json(COMMENT_FILE, comments)

    # ── Hermes 通知（非同步）──
    def notify_and_update():
        if analysis.get("should_notify_owner") and analysis["category"] != "SPAM":
            alert_msg = format_hermes_alert(
                {"content": content, "author_name": author, "post_slug": post_slug},
                analysis
            )
            sent = send_telegram_alert(alert_msg)
            # 更新通知狀態
            cs = _load_json(COMMENT_FILE, [])
            for c in cs:
                if c["id"] == comment_id:
                    c["notified_owner"] = sent
            _save_json(COMMENT_FILE, cs)

    threading.Thread(target=notify_and_update, daemon=True).start()

    return jsonify({
        "success": True,
        "comment_id": comment_id,
        "ai_reply": analysis.get("suggested_reply", ""),
        "category": analysis["category"],
    }), 201

# ══════════════════════════════════════════════════════════════
# API: ADMIN (簡單保護，未來可加 JWT)
# ══════════════════════════════════════════════════════════════
@app.route("/api/admin/stats", methods=["GET"])
def api_admin_stats():
    """管理員統計：文章數、留言數、分類分佈"""
    posts    = _load_json(BLOG_FILE, [])
    comments = _load_json(COMMENT_FILE, [])

    cat_counts = {}
    for c in comments:
        cat = c.get("ai_category", "UNKNOWN")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    return jsonify({
        "blog_posts": len(posts),
        "total_comments": len(comments),
        "comment_categories": cat_counts,
        "leads": cat_counts.get("LEAD", 0),
        "pending_review": sum(1 for c in comments if c.get("ai_urgency") == "HIGH"),
    })

@app.route("/api/admin/comments", methods=["GET"])
def api_admin_comments():
    """管理員：所有留言（含隱藏的 SPAM）"""
    comments = _load_json(COMMENT_FILE, [])
    return jsonify({"comments": list(reversed(comments))})

# ══════════════════════════════════════════════════════════════
# 啟動
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  TXROBO 智慧網站後端")
    print("=" * 55)
    print(f"  網站目錄   : {WEBSITE_DIR}")
    print(f"  資料目錄   : {DATA_DIR}")
    print(f"  Claude API : {'✓ 已設定' if API_KEY else '✗ 未設定 (使用備援回答)'}")
    print(f"  Telegram   : {'✓ 已設定' if TELEGRAM_BOT_TOKEN else '✗ 未設定 (Hermes 停用)'}")
    print(f"  頻道 ID    : {TELEGRAM_CHANNEL_ID or '未設定'}")
    print()
    print("  API 端點：")
    print("    POST /api/chat           — AI 客服聊天")
    print("    GET  /api/blog           — Blog 列表")
    print("    GET  /api/blog/<slug>    — 單篇文章")
    print("    POST /api/blog/generate  — AI 生成文章")
    print("    GET  /api/comment/<slug> — 取得留言")
    print("    POST /api/comment        — 提交留言")
    print("    GET  /api/admin/stats    — 管理統計")
    print()
    print("  開啟瀏覽器：http://localhost:5000")
    print("  Ctrl+C 停止")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False)

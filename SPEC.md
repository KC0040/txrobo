# TXROBO Website — Design & SEO Specification
*Last updated: 2026-05-01 | Reference this before writing any page*

---

## Company Info
- **Name**: TXROBO
- **Role**: Authorized KEENON Robotics Distributor — Texas & Southwest USA
- **Phone**: 214-454-9356
- **Email**: info@txrobo.com
- **Website**: txrobo.com
- **Social**: YouTube @TXROBOT | Facebook: /profile.php?id=61576172333620
- **HQ**: Texas (Est. 2024)

## Products (KEENON Robotics)
| Model | Type | Payload | Key Feature | Award |
|-------|------|---------|-------------|-------|
| T10 | Delivery + Ads | 40kg | 23.8" HD Ad Screen, 4 trays | 2025 iF Design Award |
| T9 | Delivery | 30kg | 4 trays, silent LIDAR, multi-floor | — |
| S100 | Disinfection | — | UV + spray dual-mode, autonomous | — |

All robots: 24h battery, LIDAR navigation, 1-3 day deployment, no IT changes needed.

## Service Areas
| State | Status | Key Cities |
|-------|--------|-----------|
| Texas | PRIMARY | Dallas, Houston, Austin, San Antonio, Fort Worth, El Paso |
| Oklahoma | Active | Oklahoma City, Tulsa, Norman |
| Louisiana | Active | New Orleans, Baton Rouge, Shreveport |
| New Mexico | Active | Albuquerque, Santa Fe, Las Cruces |
| Arkansas | Active | Little Rock, Fayetteville, Fort Smith |
| Mississippi | Expanding | Jackson, Biloxi, Gulfport |
| Colorado | Expanding | Denver, Colorado Springs, Boulder |
| Kansas | Expanding | Wichita, Kansas City, Overland Park |

## Key Value Propositions
- 6-day FREE trial — **within 100 miles of Dallas, TX only**
- Outside Dallas area: call 214-454-9356 for deployment options
- $300+ weekly savings per robot
- Deploy in 1–3 business days
- Monthly rental plans (no large upfront)
- Maintenance & repairs INCLUDED
- Local support teams — same-day on-site

---

## Design System

### Colors
```
bg:          #0d131f  ← page background (deep navy)
bg-low:      #080e1a  ← footer / dark sections
surf:        #161c28  ← cards, sections
surf-mid:    #1a202c  ← hover states
surf-high:   #242a37  ← elevated elements
surf-top:    #2f3542  ← glassmorphism
primary:     #b2c5ff  ← ice blue (headlines accent, labels)
primary-btn: #2b6cee  ← button blue
on-surf:     #dde2f4  ← main text
on-surf-2:   #c3c6d7  ← secondary text
on-surf-3:   #8c90a0  ← dimmed text
border:      #424654  ← borders
green:       #4ade80  ← online indicator
amber:       #fbbf24  ← award badge
teal:        #34d399  ← healthcare / check icons
```

### Typography
- **Display/Headlines**: Space Grotesk (wt 800-900, letter-spacing: -0.03em)
- **Body/UI**: Inter (wt 300-600)
- **Mono Labels**: DM Mono (wt 300-500, letter-spacing: 0.1em, UPPERCASE)

### Buttons
```css
.btn-machined  /* gradient: #b2c5ff → #2b6cee, color: #001848 */
.btn-ghost     /* glass: rgba(178,197,255,0.07), border rgba(178,197,255,0.15) */
```

### Key Rules
- NO 1px border lines between sections — use bg color shifts
- Sections alternate: #0d131f ↔ #161c28
- Cards use #161c28 on #0d131f bg, or #1a202c on #161c28 bg
- Glassmorphism: rgba(47,53,66,0.35) + backdrop-blur(14px)
- External CSS: `assets/css/txrobo.css`
- External JS fallback: `assets/js/chat.js`

### Shared Fonts (in every <head>)
```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800;900&family=DM+Mono:wght@300;400;500&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,300,0,0&display=swap" rel="stylesheet"/>
```

### Tailwind Config (in every page)
```js
tailwind.config = { darkMode:'class', theme:{ extend:{ colors:{
  'bg':'#0d131f','bg-low':'#080e1a','surf':'#161c28','surf-mid':'#1a202c',
  'surf-high':'#242a37','surf-top':'#2f3542','primary':'#b2c5ff',
  'primary-btn':'#2b6cee','on-surf':'#dde2f4','on-surf-2':'#c3c6d7',
  'on-surf-3':'#8c90a0','border':'#424654'
}, fontFamily:{ display:['Space Grotesk'], mono:['DM Mono'], body:['Inter'] } }}}
```

---

## SEO / GEO Requirements (every page)

### Required Meta Tags
```html
<meta name="geo.region" content="US-TX"/>
<meta name="geo.placename" content="Dallas, Texas"/>
<meta name="geo.position" content="32.7767;-96.7970"/>
<meta name="ICBM" content="32.7767, -96.7970"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="TXROBO"/>
<meta name="twitter:card" content="summary_large_image"/>
```

### Structured Data — Organization (every page)
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://www.txrobo.com/#org",
  "name": "TXROBO",
  "url": "https://www.txrobo.com",
  "telephone": "+1-214-454-9356",
  "email": "info@txrobo.com",
  "areaServed": ["Texas","Oklahoma","Louisiana","New Mexico","Arkansas","Colorado","Kansas","Mississippi"],
  "description": "Authorized KEENON Robotics distributor serving Texas and surrounding states with autonomous service robots.",
  "sameAs": ["https://www.youtube.com/@TXROBOT","https://www.facebook.com/profile.php?id=61576172333620"]
}
```

### Structured Data — LocalBusiness (every page)
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "TXROBO",
  "telephone": "+1-214-454-9356",
  "email": "info@txrobo.com",
  "address": {"@type":"PostalAddress","addressRegion":"TX","addressCountry":"US"},
  "areaServed": ["Dallas","Houston","Austin","San Antonio","Oklahoma City","New Orleans","Albuquerque","Little Rock"]
}
```

### Keyword Strategy
- Primary: `service robots Texas`, `delivery robot Dallas`, `KEENON T10 T9 S100`
- Secondary: `restaurant robot Houston`, `hotel delivery robot Texas`, `disinfection robot`, `autonomous robot Southwest USA`
- Long-tail: `6-day free robot trial Texas`, `robot rental Texas no contract`, `labor shortage solution restaurant Texas`
- GEO modifiers: Add city/state names to every page (Dallas, Houston, Austin, San Antonio, Oklahoma City, New Orleans, Albuquerque)

### Image Alt Text Pattern
- Robot images: `KEENON [MODEL] [TYPE] robot for [INDUSTRY] in Texas`
- Logo: `TXROBO — Authorized KEENON Robotics Distributor Texas`

---

## Page Structure Template

```
<html lang="en" class="dark">
<head>
  [meta charset, viewport]
  [title — include location keyword]
  [meta description — 150-160 chars with location]
  [canonical]
  [geo meta tags]
  [og: tags]
  [structured data JSON-LD]
  [font links]
  [link rel=stylesheet txrobo.css]
  [tailwind CDN + config]
  [page-specific <style>]
</head>
<body>
<div id="page-wrapper">
  [#navbar — same across all pages]
  [page hero — #080e1a + dot-grid]
  [sections — alternating #0d131f / #161c28]
  [cta-sec]
  [footer — same across all pages]
</div>
[ai-overlay + ai-panel]
[#ai-fab]
[<script src="assets/js/chat.js">]
[<script> toggleAI / sendMessage / scrollMsgs / renderMd / appendMsg / showTyping / removeTyping / sendQuickMsg ]
</body>
</html>
```

---

## Images (Cloudinary CDN)
- TXROBO Logo: `https://res.cloudinary.com/dchlhfrdi/image/upload/txrobo/TXROBO-LOGO.webp`
- T10: `https://res.cloudinary.com/dchlhfrdi/image/upload/txrobo/T10.webp`
- T9: `https://res.cloudinary.com/dchlhfrdi/image/upload/txrobo/T9.webp`
- S100 fallback: `https://www.keenon.com/Uploads/image/20230829/1693299814196427.webp`

## KEENON News Sources (for blog content)
- Official: https://www.keenon.com/en/news/
- Product pages: https://www.keenon.com/en/products/
- iF Award reference: T10 won 2025 iF Design Award
- Key stats: 35,000+ robots deployed, 60+ countries, Marriott/Hilton partner

---

## Backend API (server.py on port 5000)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/chat | POST | AI chatbot (Claude Haiku) |
| /api/blog | GET | Blog post list |
| /api/blog/:slug | GET | Single post |
| /api/blog/generate | POST | AI generate new post |
| /api/comment | POST | Submit + classify comment |
| /api/comment/:slug | GET | Get comments for post |
| /api/admin/stats | GET | Admin statistics |

All fetch calls use: `signal: AbortSignal.timeout(12000)` + getFallbackAnswer() on error.

---

## Page Inventory
| File | Status | Active Nav | SEO Complete |
|------|--------|-----------|--------------|
| index.html | ✅ Complete | Home | ✅ Full (geo + OG + FAQPage schema) |
| products.html | ✅ Complete | Products | ✅ Full (geo + OG + Product schema) |
| solutions.html | ✅ Complete | Solutions | ✅ Full (geo + OG) |
| contact.html | ✅ Complete | Contact | ✅ Full (geo + OG + ContactPage schema) |
| services.html | ✅ Complete | — | ⚠️ Missing geo + OG |
| about.html | ✅ Complete | About | ✅ Full (geo + OG) |
| blog.html | ✅ Complete | Blog | ⚠️ Missing geo + OG |

---

## AI Agent File Package
*給 AI Agent 的完整打包文件 — 直接交付給自動化工具*

| File | Purpose |
|------|---------|
| `AGENT.md` | Agent 角色設定、System Prompt、對話腳本、Blog Agent 指令、API 整合指南 |
| `KNOWLEDGE.md` | 產品知識庫、FAQ、異議處理、Blog 寫作指南 |
| `SPEC.md`（本文件） | 設計規範、SEO 要求、頁面結構模板 |
| `server.py` | 後端 API（/api/chat 使用 Alex 人設 system prompt）|

### 快速連結方式
- **Chat Agent**: POST /api/chat → server.py Alex 人設已內建
- **Blog Agent**: POST /api/blog/generate → server.py Blog system prompt 已內建
- **Lead 收集**: POST /api/comment → 觸發 Telegram Hermes 通知
- **外部 AI 工具**: 直接使用 AGENT.md 第二節「System Prompt」內容

### 產品主推順序
1. **T9** — 主推（餐廳、飯店、辦公室）
2. **T10** — 主推（帶廣告螢幕，高附加值）
3. **S100** — 詢問才推（醫療、消毒需求）

/**
 * TXRobo 展示級動畫 — 機器人主題
 *  1. Hero 粒子電路網絡（canvas，滑鼠互動）
 *  2. 標題文字解碼效果（robotic decode）
 *  3. 卡片 3D 傾斜（滑鼠視差）
 *  4. CTA 磁吸按鈕
 *  5. 頂部捲動進度條（品牌漸層）
 * 純前端無依賴。尊重 prefers-reduced-motion。
 */
(function () {
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ───────────────────────────────────────────
     5. 捲動進度條（動效最小，reduced 也保留）
  ─────────────────────────────────────────── */
  var bar = document.createElement("div");
  bar.id = "tx-progress";
  document.body.appendChild(bar);
  window.addEventListener("scroll", function () {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = "scaleX(" + (h > 0 ? window.scrollY / h : 0) + ")";
  }, { passive: true });

  if (reduced) return;

  /* ───────────────────────────────────────────
     1. Hero 粒子電路網絡
  ─────────────────────────────────────────── */
  var hero = document.querySelector(".hero");
  if (hero) {
    var canvas = document.createElement("canvas");
    canvas.id = "tx-net";
    hero.insertBefore(canvas, hero.firstChild);
    var ctx = canvas.getContext("2d");
    var W, H, nodes = [], mouse = { x: -9999, y: -9999 };
    var COUNT = Math.min(70, Math.floor(window.innerWidth / 20));
    var LINK = 130;

    function resize() {
      W = canvas.width = hero.offsetWidth;
      H = canvas.height = hero.offsetHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    for (var i = 0; i < COUNT; i++) {
      nodes.push({
        x: Math.random() * W,
        y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 1.6 + 0.8,
      });
    }

    hero.addEventListener("mousemove", function (e) {
      var rect = hero.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    });
    hero.addEventListener("mouseleave", function () { mouse.x = mouse.y = -9999; });

    function tick() {
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < nodes.length; i++) {
        var n = nodes[i];
        n.x += n.vx; n.y += n.vy;
        if (n.x < 0 || n.x > W) n.vx *= -1;
        if (n.y < 0 || n.y > H) n.vy *= -1;

        // 滑鼠輕微吸引
        var dxm = mouse.x - n.x, dym = mouse.y - n.y;
        var dm = Math.sqrt(dxm * dxm + dym * dym);
        if (dm < 180 && dm > 0.01) {
          n.x += dxm / dm * 0.35;
          n.y += dym / dm * 0.35;
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(178,197,255,0.55)";
        ctx.fill();

        for (var j = i + 1; j < nodes.length; j++) {
          var m = nodes[j];
          var dx = n.x - m.x, dy = n.y - m.y;
          var d = Math.sqrt(dx * dx + dy * dy);
          if (d < LINK) {
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(m.x, m.y);
            ctx.strokeStyle = "rgba(43,108,238," + (0.28 * (1 - d / LINK)) + ")";
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(tick);
    }
    tick(); // 首幀同步繪製，之後由 rAF 接手
  }

  /* ───────────────────────────────────────────
     2. 文字解碼效果（hero 標題第一行 + 各頁 h1）
  ─────────────────────────────────────────── */
  var GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ01<>/_#%";
  function decode(el) {
    var finalText = el.textContent;
    var frame = 0, totalFrames = finalText.length * 3 + 12;
    function step() {
      frame++;
      var done = Math.floor((frame / totalFrames) * finalText.length);
      var out = "";
      for (var i = 0; i < finalText.length; i++) {
        if (i < done || finalText[i] === " ") out += finalText[i];
        else out += GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
      }
      el.textContent = out;
      if (frame < totalFrames) requestAnimationFrame(step);
      else el.textContent = finalText;
    }
    requestAnimationFrame(step);
  }
  // hero 標題的純文字節點（AUTOMATING）— 不動 location-cycler
  var headline = document.querySelector(".hero-headline");
  if (headline && headline.childNodes[0] && headline.childNodes[0].nodeType === 3) {
    var span = document.createElement("span");
    span.textContent = headline.childNodes[0].textContent.trim();
    headline.replaceChild(span, headline.childNodes[0]);
    decode(span);
  } else {
    var h1 = document.querySelector("h1");
    if (h1 && h1.children.length === 0) decode(h1);
  }

  /* ───────────────────────────────────────────
     3. 卡片 3D 傾斜
  ─────────────────────────────────────────── */
  document.querySelectorAll(".state-card, .sol-card, .p-card, .blog-card").forEach(function (card) {
    card.classList.add("tx-tilt");
    card.addEventListener("mousemove", function (e) {
      var r = card.getBoundingClientRect();
      var px = (e.clientX - r.left) / r.width - 0.5;
      var py = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform =
        "perspective(800px) rotateY(" + px * 7 + "deg) rotateX(" + -py * 7 + "deg) translateY(-4px)";
    });
    card.addEventListener("mouseleave", function () {
      card.style.transform = "";
    });
  });

  /* ───────────────────────────────────────────
     4. CTA 磁吸按鈕
  ─────────────────────────────────────────── */
  document.querySelectorAll('a[class*="btn"], button[class*="btn"]').forEach(function (btn) {
    btn.addEventListener("mousemove", function (e) {
      var r = btn.getBoundingClientRect();
      var x = (e.clientX - r.left - r.width / 2) * 0.25;
      var y = (e.clientY - r.top - r.height / 2) * 0.35;
      btn.style.transform = "translate(" + x + "px," + y + "px)";
    });
    btn.addEventListener("mouseleave", function () {
      btn.style.transform = "";
    });
  });
})();

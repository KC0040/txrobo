/**
 * TXRobo 版面動效強化 — IntersectionObserver 捲動進場 + 微互動
 * 純前端，無依賴。所有頁面 </body> 前引入：
 *   <link rel="stylesheet" href="/assets/css/enhance.css">
 *   <script src="/assets/js/enhance.js" defer></script>
 */
(function () {
  // 尊重減少動態偏好
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  // ── 1. 自動標記要進場的元素 ──
  var selectors = [
    "main h2", "section h2",
    ".state-card", ".sol-card", ".p-card", ".blog-card",
    ".why-grid > *", "section .grid > *",
  ];
  var targets = [];
  selectors.forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (el) {
      if (!el.hasAttribute("data-no-reveal") && targets.indexOf(el) === -1) targets.push(el);
    });
  });

  // 同一容器內的兄弟元素做 stagger 延遲
  var siblingIndex = new Map();
  targets.forEach(function (el) {
    var parent = el.parentElement;
    var idx = siblingIndex.get(parent) || 0;
    siblingIndex.set(parent, idx + 1);
    el.style.transitionDelay = Math.min(idx * 70, 420) + "ms";
    el.classList.add("tx-reveal");
  });

  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("tx-in");
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );
  targets.forEach(function (el) { io.observe(el); });

  // 後備機制：IO 延遲或失效時，用位置檢查補觸發（load + scroll）
  function bcrCheck() {
    var vh = window.innerHeight;
    targets.forEach(function (el) {
      if (el.classList.contains("tx-in")) return;
      var r = el.getBoundingClientRect();
      if (r.top < vh * 0.92 && r.bottom > 0) {
        el.classList.add("tx-in");
        io.unobserve(el);
      }
    });
  }
  var bcrTick = false;
  window.addEventListener("scroll", function () {
    if (bcrTick) return;
    bcrTick = true;
    setTimeout(function () { bcrCheck(); bcrTick = false; }, 80);
  }, { passive: true });
  bcrCheck();

  // ── 2. 數字滾動：data-counter="120" ──
  var cio = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        cio.unobserve(e.target);
        var el = e.target;
        var end = parseFloat(el.getAttribute("data-counter")) || 0;
        var suffix = el.getAttribute("data-counter-suffix") || "";
        var t0 = null;
        function step(t) {
          if (!t0) t0 = t;
          var p = Math.min((t - t0) / 1400, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(end * eased) + suffix;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    },
    { threshold: 0.5 }
  );
  document.querySelectorAll("[data-counter]").forEach(function (el) { cio.observe(el); });

  // ── 3. 導覽列捲動加深背景 ──
  var nav = document.querySelector("nav, header nav, header");
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("tx-nav-scrolled", window.scrollY > 24);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }
})();

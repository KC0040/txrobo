/**
 * TXROBO JSON 驅動多語言引擎
 * 新增語言 = 在 /lang/ 放一個新 JSON + 在 LANGS 加一行
 */
(function () {
  var LANGS = [
    { code: "en", label: "EN" },
    { code: "es", label: "ES" },
  ];
  var DEFAULT = "en";

  function currentLang() {
    var q = new URLSearchParams(location.search).get("lang");
    if (q && LANGS.some(function (l) { return l.code === q; })) {
      localStorage.setItem("txrobo_lang", q);
      return q;
    }
    return localStorage.getItem("txrobo_lang") || DEFAULT;
  }

  function apply(lang) {
    document.documentElement.lang = lang;
    if (lang === DEFAULT) return;
    fetch("/lang/" + lang + ".json")
      .then(function (r) { return r.json(); })
      .then(function (dict) {
        document.querySelectorAll("[data-i18n]").forEach(function (el) {
          var key = el.getAttribute("data-i18n");
          if (dict[key] !== undefined) el.innerHTML = dict[key];
        });
      })
      .catch(function () {});
  }

  function buildSwitcher(lang) {
    var css =
      "#tx-lang{position:fixed;bottom:24px;left:24px;z-index:9998;display:flex;gap:2px;" +
      "border:1px solid rgba(66,70,84,0.5);background:#080e1a;border-radius:2px;overflow:hidden}" +
      "#tx-lang button{background:none;border:none;color:#8c90a0;font:700 11px/1 'Space Grotesk',sans-serif;" +
      "letter-spacing:.08em;padding:9px 14px;cursor:pointer;transition:background .2s,color .2s}" +
      "#tx-lang button.on{background:#2b6cee;color:#fdfbff}";
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var bar = document.createElement("div");
    bar.id = "tx-lang";
    LANGS.forEach(function (l) {
      var b = document.createElement("button");
      b.textContent = l.label;
      if (l.code === lang) b.className = "on";
      b.addEventListener("click", function () {
        localStorage.setItem("txrobo_lang", l.code);
        location.search = "?lang=" + l.code;
      });
      bar.appendChild(b);
    });
    document.body.appendChild(bar);
  }

  var lang = currentLang();
  apply(lang);
  document.addEventListener("DOMContentLoaded", function () {
    buildSwitcher(lang);
  });
})();

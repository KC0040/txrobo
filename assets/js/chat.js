/**
 * TXRobo AI Chat Widget + tawk.to 升級整合
 * 多語言：EN / ES / ZH（自動偵測 + 手動切換）
 *
 * 使用方式（每個頁面 </body> 前）：
 *   <script src="/assets/js/chat.js" defer></script>
 *   <!-- tawk.to embed code 接在後面 -->
 */
(function () {

  var ENDPOINT  = 'https://new2-chatbotservice.pkxdtf.easypanel.host/chat';
  var SITE      = 'txrobo';
  var history   = [];
  var escalated = false;

  // ── 多語言字串 ──
  var LANG = {
    en: {
      welcome:    'Hi! I\'m Alex, your TXROBO assistant. Ask me about our T10, T9, or S100 robots — or request a free demo.',
      placeholder:'Ask about robots, pricing, deployment…',
      send:       'SEND',
      specialist: 'Connect to Live Specialist',
      connecting: 'Connecting…',
      subtitle:   'AI · Robot specialist available',
      error:      'Connection issue — email info@txrobo.com.',
    },
    es: {
      welcome:    '¡Hola! Soy Alex, tu asistente TXROBO. Pregúntame sobre los robots T10, T9 o S100.',
      placeholder:'Pregunta sobre robots, precios, implementación…',
      send:       'ENVIAR',
      specialist: 'Conectar con Especialista',
      connecting: 'Conectando…',
      subtitle:   'IA · Especialista disponible',
      error:      'Error de conexión — email info@txrobo.com.',
    },
    zh: {
      welcome:    '您好！我是 Alex，您的 TXROBO 助理。有關 T10、T9 或 S100 機器人的問題請告訴我。',
      placeholder:'詢問機器人、價格、部署方式…',
      send:       '發送',
      specialist: '連接真人客服',
      connecting: '連接中…',
      subtitle:   'AI · 真人客服待機中',
      error:      '連線問題 — 請 email info@txrobo.com',
    }
  };

  function detectLang() {
    var p = (document.documentElement.lang || '').toLowerCase().substring(0, 2);
    if (LANG[p]) return p;
    var n = (navigator.language || 'en').toLowerCase().substring(0, 2);
    return LANG[n] ? n : 'en';
  }

  var lang = detectLang();
  var t    = LANG[lang];

  // ── 樣式 ──
  var css =
    '#txw-btn{position:fixed;bottom:24px;right:24px;z-index:9000;width:58px;height:58px;border:none;cursor:pointer;' +
    'background:#2b6cee;color:#fff;display:flex;align-items:center;justify-content:center;' +
    'border-radius:0.125rem;box-shadow:0 4px 28px rgba(43,108,238,.45);transition:transform .2s,box-shadow .2s}' +
    '#txw-btn:hover{transform:scale(1.06);box-shadow:0 8px 36px rgba(43,108,238,.6)}' +
    '#txw-panel{position:fixed;bottom:96px;right:24px;z-index:9000;width:370px;max-width:calc(100vw - 32px);height:520px;' +
    'background:#0d131f;border:1px solid rgba(66,70,84,.5);border-radius:0.25rem;' +
    'display:none;flex-direction:column;overflow:hidden;font-family:Inter,system-ui,sans-serif;box-shadow:0 16px 56px rgba(0,0,0,.6)}' +
    '#txw-panel.open{display:flex}' +
    '#txw-head{background:#080e1a;border-bottom:1px solid rgba(66,70,84,.4);padding:14px 18px;display:flex;align-items:center;justify-content:space-between}' +
    '#txw-head .hinfo{display:flex;align-items:center;gap:10px}' +
    '#txw-head .dot{width:7px;height:7px;border-radius:50%;background:#2ed573;flex-shrink:0}' +
    '#txw-head b{color:#dde2f4;font-size:12px;font-family:"Space Grotesk",sans-serif;font-weight:700;letter-spacing:.12em;text-transform:uppercase;display:block}' +
    '#txw-head .sub{color:#8c90a0;font-size:10px;letter-spacing:.06em}' +
    '#txw-close{background:none;border:none;color:#8c90a0;cursor:pointer;font-size:17px;line-height:1;padding:2px 4px;transition:color .15s}' +
    '#txw-close:hover{color:#dde2f4}' +
    '#txw-lang{display:flex;gap:4px;padding:8px 14px;border-bottom:1px solid rgba(66,70,84,.3)}' +
    '.txw-lb{padding:3px 9px;font-size:10px;font-family:"Space Grotesk",sans-serif;font-weight:700;letter-spacing:.1em;text-transform:uppercase;' +
    'background:none;border:1px solid rgba(66,70,84,.4);color:#8c90a0;cursor:pointer;border-radius:0.125rem;transition:all .15s}' +
    '.txw-lb.active,.txw-lb:hover{background:#2b6cee;color:#fff;border-color:#2b6cee}' +
    '#txw-msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:9px;scroll-behavior:smooth}' +
    '#txw-msgs::-webkit-scrollbar{width:3px}#txw-msgs::-webkit-scrollbar-thumb{background:#2b6cee}' +
    '.txw-m{max-width:86%;padding:9px 13px;font-size:13px;line-height:1.55;border-radius:0.125rem}' +
    '.txw-m.user{align-self:flex-end;background:#2b6cee;color:#fdfbff}' +
    '.txw-m.bot{align-self:flex-start;background:#161c28;color:#c3c6d7;border:1px solid rgba(66,70,84,.35)}' +
    '.bot-lbl{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#8c90a0;margin-bottom:4px;font-family:"Space Grotesk",sans-serif}' +
    '.txw-m p{margin:0;white-space:pre-wrap}' +
    '.td{width:5px;height:5px;border-radius:50%;background:#8c90a0;display:inline-block;animation:txwb .9s infinite}' +
    '.td:nth-child(2){animation-delay:.15s}.td:nth-child(3){animation-delay:.3s}' +
    '@keyframes txwb{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-5px)}}' +
    '#txw-esc{display:block;width:calc(100% - 28px);margin:0 14px 10px;padding:9px;' +
    'background:rgba(43,108,238,.1);color:#b2c5ff;border:1px solid rgba(43,108,238,.3);' +
    'border-radius:0.125rem;cursor:pointer;font-size:.67rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;transition:background .2s}' +
    '#txw-esc:hover{background:rgba(43,108,238,.22)}#txw-esc:disabled{opacity:.5;cursor:default}' +
    '#txw-in{border-top:1px solid rgba(66,70,84,.35);padding:10px;display:flex;gap:8px}' +
    '#txw-in input{flex:1;background:#161c28;border:1px solid rgba(66,70,84,.4);color:#dde2f4;font-size:13px;padding:9px 12px;border-radius:0.125rem;outline:none}' +
    '#txw-in input:focus{border-color:#2b6cee}' +
    '#txw-in button{background:#2b6cee;border:none;color:#fff;font-size:10px;font-weight:700;letter-spacing:.1em;padding:0 14px;cursor:pointer;border-radius:0.125rem;font-family:"Space Grotesk",sans-serif}' +
    '@media(max-width:480px){#txw-panel{width:calc(100vw - 24px);right:12px;height:70vh;bottom:88px}}';

  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  // ── DOM ──
  var btn = document.createElement('button');
  btn.id = 'txw-btn'; btn.setAttribute('aria-label', 'Chat with TXROBO');
  btn.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>';

  var panel = document.createElement('div'); panel.id = 'txw-panel';
  panel.innerHTML =
    '<div id="txw-head"><div class="hinfo"><span class="dot"></span><div><b>TXROBO</b><span class="sub" id="txw-sub">' + t.subtitle + '</span></div></div><button id="txw-close">✕</button></div>' +
    '<div id="txw-lang">' +
      '<button class="txw-lb' + (lang==='en'?' active':'') + '" data-l="en">EN</button>' +
      '<button class="txw-lb' + (lang==='es'?' active':'') + '" data-l="es">ES</button>' +
      '<button class="txw-lb' + (lang==='zh'?' active':'') + '" data-l="zh">中文</button>' +
    '</div>' +
    '<div id="txw-msgs"></div>' +
    '<div id="txw-in"><input type="text" id="txw-input" placeholder="' + t.placeholder + '" /><button id="txw-send">' + t.send + '</button></div>';

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  var msgs  = document.getElementById('txw-msgs');
  var input = document.getElementById('txw-input');
  var send  = document.getElementById('txw-send');

  // 語言切換
  panel.querySelectorAll('.txw-lb').forEach(function(b){
    b.addEventListener('click', function(){
      lang = b.dataset.l; t = LANG[lang];
      panel.querySelectorAll('.txw-lb').forEach(function(x){x.classList.remove('active');});
      b.classList.add('active');
      input.placeholder = t.placeholder; send.textContent = t.send;
      document.getElementById('txw-sub').textContent = t.subtitle;
      var eb = document.getElementById('txw-esc');
      if (eb && !eb.disabled) eb.textContent = t.specialist;
    });
  });

  document.getElementById('txw-close').addEventListener('click', function(){ panel.classList.remove('open'); });

  // 訊息渲染
  function add(role, text) {
    var d = document.createElement('div'); d.className = 'txw-m ' + (role==='user'?'user':'bot');
    if (role==='bot') { var l=document.createElement('div'); l.className='bot-lbl'; l.textContent='TXROBO AI'; d.appendChild(l); }
    var p = document.createElement('p'); p.textContent = text; d.appendChild(p);
    msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d;
  }
  function showTyping(){
    var d=document.createElement('div'); d.className='txw-m bot'; d.id='txw-tp';
    d.innerHTML='<div class="bot-lbl">TXROBO AI</div><span class="td"></span><span class="td"></span><span class="td"></span>';
    msgs.appendChild(d); msgs.scrollTop=msgs.scrollHeight;
  }
  function removeTyping(){ var d=document.getElementById('txw-tp'); if(d) d.remove(); }

  // tawk.to 升級按鈕
  function showEsc() {
    if (document.getElementById('txw-esc')) return;
    var eb = document.createElement('button'); eb.id='txw-esc';
    eb.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:5px"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' + t.specialist;
    panel.insertBefore(eb, document.getElementById('txw-in'));
    eb.addEventListener('click', function(){
      if (escalated) return; escalated=true; eb.textContent=t.connecting; eb.disabled=true; tawkHandoff();
    });
  }

  // tawk.to 轉接
  function tawkHandoff() {
    var tr = history.slice(-6).map(function(m){
      return '['+(m.role==='user'?'Customer':'AI')+']: '+(m.text||'').substring(0,200);
    }).join('\n');
    var summary = '=== TXROBO AI Handoff ===\nLang: '+lang.toUpperCase()+'\n---\n'+tr+'\n=== Continue here ===';
    try { sessionStorage.setItem('tawk_ai_transcript', summary); } catch(e){}

    function go() {
      if (window.Tawk_API) {
        if (window.Tawk_API.setAttributes) window.Tawk_API.setAttributes({'ai-site':'txrobo','lang':lang,'handoff':'true'},function(){});
        window.Tawk_API.maximize();
      } else {
        window.open('mailto:info@txrobo.com?subject=Chat%20Inquiry&body='+encodeURIComponent(summary));
      }
    }
    if (window.Tawk_API && window.Tawk_API.maximize) { go(); }
    else {
      var tm = setInterval(function(){ if(window.Tawk_API&&window.Tawk_API.maximize){clearInterval(tm);go();} },400);
      setTimeout(function(){clearInterval(tm);go();},5000);
    }
  }

  add('bot', t.welcome);

  btn.addEventListener('click', function(){ panel.classList.toggle('open'); if(panel.classList.contains('open')) input.focus(); });

  var busy = false;
  function submit() {
    var text = input.value.trim(); if (!text || busy) return;
    input.value = ''; add('user', text); history.push({role:'user',text:text}); busy=true; showTyping();
    fetch(ENDPOINT, { method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message:text, site:SITE, lang:lang, history:history.slice(-12)})
    })
    .then(function(r){return r.json();})
    .then(function(data){
      removeTyping();
      var reply = data.reply || data.error || 'Sorry, please try again.';
      add('bot', reply); history.push({role:'assistant',text:reply});
      var low = reply.toLowerCase();
      if (low.includes('specialist')||low.includes('connect')||low.includes('unable')||
          low.includes('follow up')||low.includes('email')||history.length>8) {
        setTimeout(showEsc, 400);
      }
    })
    .catch(function(){ removeTyping(); add('bot', t.error); showEsc(); })
    .finally(function(){busy=false;});
  }

  send.addEventListener('click', submit);
  input.addEventListener('keydown', function(e){ if(e.key==='Enter') submit(); });

})();

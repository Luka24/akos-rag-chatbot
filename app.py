"""
AKOS Asistent – UI strežnik (FastAPI + vdelana HTML/JS stran)
==============================================================
Celoten UI je vdelana HTML stran, ki jo FastAPI strežemo na /
JS koda kliče mock RAG API na http://localhost:8000/api/chat

Zagon:
    uvicorn app:app --reload --port 7860
    → odpre se http://localhost:7860
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="sl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AKOS Asistent – RAG Demo</title>
<style>
  /* ── Reset & Base ──────────────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --blue-dark:  #003B8E;
    --blue-main:  #0055CC;
    --blue-light: #E8F0FE;
    --blue-mid:   #b3c9f0;
    --green:      #28a745;
    --grey-bg:    #f4f6f9;
    --grey-card:  #ffffff;
    --grey-text:  #444;
    --grey-light: #888;
    --border:     #e2e8f0;
    --shadow:     0 2px 8px rgba(0,60,150,0.10);
    --radius:     12px;
  }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: var(--grey-bg);
    color: var(--grey-text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── Glava ─────────────────────────────────────────── */
  header {
    background: linear-gradient(135deg, var(--blue-dark) 0%, var(--blue-main) 100%);
    color: white;
    padding: 20px 32px;
    display: flex;
    align-items: center;
    gap: 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15);
  }
  header .logo {
    width: 52px; height: 52px;
    background: white;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem; font-weight: 900; color: var(--blue-main);
    flex-shrink: 0;
  }
  header h1 { font-size: 1.45rem; font-weight: 700; letter-spacing: -0.3px; }
  header p  { font-size: 0.85rem; opacity: 0.82; margin-top: 2px; }
  .status-dot {
    margin-left: auto;
    display: flex; align-items: center; gap: 7px;
    font-size: 0.82rem; opacity: 0.9;
  }
  .dot {
    width: 9px; height: 9px; border-radius: 50%;
    background: #4ade80;
    box-shadow: 0 0 6px #4ade80;
    animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }

  /* ── Layout ────────────────────────────────────────── */
  .layout {
    display: flex;
    flex: 1;
    gap: 0;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 24px 20px;
    gap: 20px;
  }
  .chat-col { flex: 3; display: flex; flex-direction: column; gap: 14px; }
  .side-col  { flex: 2; display: flex; flex-direction: column; gap: 14px; min-width: 300px; }

  /* ── Panel ─────────────────────────────────────────── */
  .panel {
    background: var(--grey-card);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    overflow: hidden;
  }
  .panel-header {
    background: var(--blue-light);
    padding: 11px 18px;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--blue-dark);
    letter-spacing: 0.4px;
    text-transform: uppercase;
    border-bottom: 1px solid var(--blue-mid);
    display: flex; align-items: center; gap: 7px;
  }

  /* ── Chat ──────────────────────────────────────────── */
  #messages {
    padding: 18px;
    height: 440px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
    scroll-behavior: smooth;
  }
  .msg { display: flex; gap: 10px; align-items: flex-start; }
  .msg.user { flex-direction: row-reverse; }

  .avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0; font-weight: 700;
  }
  .msg.bot  .avatar { background: var(--blue-main); color: white; }
  .msg.user .avatar { background: #475569; color: white; }

  .bubble {
    max-width: 82%;
    padding: 12px 16px;
    border-radius: 14px;
    font-size: 0.93rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg.bot  .bubble {
    background: white;
    border: 1px solid var(--border);
    border-top-left-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .msg.user .bubble {
    background: var(--blue-main);
    color: white;
    border-top-right-radius: 4px;
  }

  /* ── Markdown v bubble-ih ──────────────────────────── */
  .bubble strong { font-weight: 700; }
  .bubble em     { font-style: italic; }
  .bubble code   { background:#f1f5f9; padding:1px 5px; border-radius:4px; font-family:monospace; font-size:0.88em; color:var(--blue-dark); }
  .bubble ul, .bubble ol { margin: 6px 0 6px 22px; }
  .bubble li { margin: 3px 0; }
  .bubble hr { border:none; border-top:1px solid var(--border); margin:10px 0; }
  .bubble table { border-collapse:collapse; width:100%; font-size:0.87em; margin:8px 0; }
  .bubble th { background:var(--blue-light); color:var(--blue-dark); padding:5px 9px; text-align:left; }
  .bubble td { padding:5px 9px; border-bottom:1px solid var(--border); }

  /* ── Typing indicator ──────────────────────────────── */
  .typing .bubble { background: var(--blue-light); border: 1px dashed var(--blue-mid); }
  .typing-dots span {
    display: inline-block; width:7px; height:7px; border-radius:50%;
    background: var(--blue-main); margin: 0 2px;
    animation: bounce 1.2s infinite;
  }
  .typing-dots span:nth-child(2) { animation-delay:.2s; }
  .typing-dots span:nth-child(3) { animation-delay:.4s; }
  @keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-7px)} }

  /* ── Input bar ─────────────────────────────────────── */
  .input-bar {
    display: flex;
    gap: 8px;
    padding: 14px 16px;
    border-top: 1px solid var(--border);
    background: #fafbff;
  }
  #q {
    flex: 1;
    border: 2px solid var(--blue-mid);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.95rem;
    font-family: inherit;
    resize: none;
    outline: none;
    transition: border-color .2s;
    min-height: 44px;
    max-height: 120px;
  }
  #q:focus { border-color: var(--blue-main); box-shadow: 0 0 0 3px rgba(0,85,204,0.12); }
  .btn {
    padding: 0 18px;
    border: none;
    border-radius: 8px;
    font-size: 0.93rem;
    font-weight: 600;
    cursor: pointer;
    transition: background .2s, opacity .2s;
    white-space: nowrap;
  }
  #send { background: var(--blue-main); color: white; }
  #send:hover { background: var(--blue-dark); }
  #send:disabled { opacity: 0.5; cursor: not-allowed; }
  #clr  { background: #f1f5f9; color: #555; border: 1px solid var(--border); }
  #clr:hover { background: #e2e8f0; }

  /* ── Primeri vprašanj ──────────────────────────────── */
  .examples { padding: 12px 16px; display: flex; flex-wrap: wrap; gap: 7px; border-top: 1px solid var(--border); }
  .ex-chip {
    background: var(--blue-light);
    color: var(--blue-dark);
    border: 1px solid var(--blue-mid);
    border-radius: 20px;
    padding: 5px 13px;
    font-size: 0.82rem;
    cursor: pointer;
    transition: background .15s;
    font-family: inherit;
  }
  .ex-chip:hover { background: #d0dcf7; }

  /* ── Stranski panel: Viri ──────────────────────────── */
  #sources-body { padding: 14px; min-height: 100px; }
  .source-card {
    border: 1px solid #dce8ff;
    border-radius: 9px;
    padding: 12px 14px;
    margin-bottom: 10px;
    background: #f8f9ff;
    font-size: 0.875rem;
    line-height: 1.55;
  }
  .source-card:last-child { margin-bottom: 0; }
  .source-num {
    display: inline-block;
    background: var(--blue-main);
    color: white;
    border-radius: 50%;
    width: 22px; height: 22px;
    text-align: center; line-height: 22px;
    font-size: 0.78rem; font-weight: 700;
    margin-right: 7px; flex-shrink: 0;
  }
  .source-title { font-weight: 700; color: var(--blue-dark); margin-bottom: 4px; display:flex; align-items:center; }
  .source-url   { color: var(--blue-main); text-decoration: none; font-size: 0.82rem; word-break:break-all; }
  .source-url:hover { text-decoration: underline; }
  .source-docid { font-size: 0.78rem; color: var(--grey-light); margin-top: 2px; font-family:monospace; }
  .source-excerpt { margin-top: 7px; color: #555; font-style: italic; font-size:0.84rem; border-top:1px solid #e0e8ff; padding-top:6px; }
  .no-sources { color: var(--grey-light); font-size: 0.88rem; padding: 6px 0; }

  /* ── Metapodatki ───────────────────────────────────── */
  #meta-body { padding: 12px 16px; font-size: 0.85rem; }
  .meta-row  { display:flex; gap:8px; margin-bottom:6px; align-items:center; }
  .meta-label{ font-weight:600; color:var(--blue-dark); min-width:80px; }
  .conf-bar  { font-family:monospace; letter-spacing:1px; color:var(--grey-text); }
  .conf-hi   { color: var(--green); }
  .conf-mid  { color: #f59e0b; }
  .conf-lo   { color: #ef4444; }

  /* ── Info panel ────────────────────────────────────── */
  #info-body { padding: 14px 18px; font-size: 0.86rem; line-height:1.65; }
  #info-body table { border-collapse:collapse; width:100%; margin:8px 0; }
  #info-body th { background:var(--blue-light); color:var(--blue-dark); padding:5px 9px; text-align:left; font-size:0.83rem; }
  #info-body td { padding:5px 9px; border-bottom:1px solid var(--border); font-size:0.83rem; }
  #info-body code { background:#f1f5f9; padding:1px 5px; border-radius:4px; font-family:monospace; color:var(--blue-dark); }

  /* ── Scrollbar ─────────────────────────────────────── */
  #messages::-webkit-scrollbar { width:5px; }
  #messages::-webkit-scrollbar-track { background:transparent; }
  #messages::-webkit-scrollbar-thumb { background:var(--blue-mid); border-radius:10px; }
</style>
</head>
<body>

<!-- ── Glava ──────────────────────────────────────────── -->
<header>
  <div class="logo">A</div>
  <div>
    <h1>AKOS Asistent</h1>
    <p>Agencija za komunikacijska omrežja in storitve RS &nbsp;·&nbsp; RAG Demo Prototip</p>
  </div>
  <div class="status-dot">
    <div class="dot" id="api-dot"></div>
    <span id="api-status">API aktiven</span>
  </div>
</header>

<!-- ── Glavna vsebina ─────────────────────────────────── -->
<div class="layout">

  <!-- Leva kolona: chat -->
  <div class="chat-col">
    <div class="panel">
      <div class="panel-header">💬 Pogovor z AKOS Asistentom</div>

      <div id="messages">
        <!-- Uvodni pozdrav -->
        <div class="msg bot" id="welcome-msg">
          <div class="avatar">A</div>
          <div class="bubble" id="welcome-bubble"></div>
        </div>
      </div>

      <!-- Primeri vprašanj -->
      <div class="examples">
        <button class="ex-chip" onclick="setQ(this)">Dodelitev frekvenc za 5G</button>
        <button class="ex-chip" onclick="setQ(this)">Pritožba zoper operaterja</button>
        <button class="ex-chip" onclick="setQ(this)">Kaj ureja ZEKom-2?</button>
        <button class="ex-chip" onclick="setQ(this)">Prenos mobilne številke</button>
        <button class="ex-chip" onclick="setQ(this)">Universalna storitev in internet</button>
      </div>

      <!-- Vnosni pas -->
      <div class="input-bar">
        <textarea id="q" rows="1"
          placeholder="Vnesite vprašanje o telekomunikacijski zakonodaji..."></textarea>
        <button class="btn" id="send" onclick="sendMsg()">Pošlji ↵</button>
        <button class="btn" id="clr"  onclick="clearChat()">Počisti</button>
      </div>
    </div>
  </div>

  <!-- Desna kolona: viri + meta + info -->
  <div class="side-col">

    <!-- Viri -->
    <div class="panel">
      <div class="panel-header">📄 Viri (RAG dokumenti)</div>
      <div id="sources-body">
        <p class="no-sources">Viri se prikažejo tukaj po prvem odgovoru.</p>
      </div>
    </div>

    <!-- Metapodatki -->
    <div class="panel">
      <div class="panel-header">📊 Metapodatki odgovora</div>
      <div id="meta-body">
        <p class="no-sources">Čakam na odgovor...</p>
      </div>
    </div>

    <!-- O sistemu -->
    <div class="panel">
      <div class="panel-header">ℹ️ O sistemu</div>
      <div id="info-body">
        <table>
          <tr><th>Tema</th><th>Ključne besede</th></tr>
          <tr><td>Radijske frekvence &amp; 5G</td><td>spekter, MHz, GHz</td></tr>
          <tr><td>Pritožbe zoper operaterje</td><td>reklamacija, pogodba</td></tr>
          <tr><td>ZEKom-2 in zakonodaja</td><td>zakon, direktiva</td></tr>
          <tr><td>Prenosljivost številk</td><td>SIM, menjava</td></tr>
          <tr><td>Universalna storitev</td><td>internet, pokritost</td></tr>
        </table>
        <p style="margin-top:10px">
          API: <code>http://localhost:8000</code><br>
          Docs: <a href="http://localhost:8000/docs" target="_blank"
                   style="color:var(--blue-main)">localhost:8000/docs</a>
        </p>
      </div>
    </div>

  </div>
</div>

<script>
// ── Konfiguracija ───────────────────────────────────────
const API = 'http://localhost:8000/api/chat';
const STREAM_DELAY = 25; // ms med besedami

// ── Pozdravno sporočilo (typewriter) ────────────────────
const WELCOME = `Pozdravljeni! Sem AKOS Asistent.

Odgovarjam na vprašanja s področja telekomunikacij in elektronskih komunikacij. Moji odgovori temeljijo na uradnih dokumentih, splošnih aktih in odločbah AKOS.

**Vnesite vprašanje** spodaj ali kliknite enega od primerov.`;

typewrite(document.getElementById('welcome-bubble'), WELCOME, 18);

// ── Pomožne funkcije ────────────────────────────────────

/** Preprost Markdown → HTML pretvornik */
function md(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
    .replace(/^---+$/gm, '<hr>')
    .replace(/^\| (.+) \|$/gm, (_, row) => {
      const cells = row.split(' | ');
      if (cells.every(c => /^-+$/.test(c.trim()))) return '';
      const tag = cells[0].match(/^-/) ? 'td' : 'td';
      return '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
    })
    .replace(/(<tr>.*<\/tr>\n?)+/gs, m => `<table>${m}</table>`)
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

/** Typewriter efekt */
function typewrite(el, text, delay) {
  el.innerHTML = '';
  let i = 0;
  function step() {
    if (i < text.length) {
      el.innerHTML = md(text.slice(0, ++i));
      setTimeout(step, delay);
    }
  }
  step();
}

/** Dodaj sporočilo v chat */
function addMsg(role, content) {
  const box = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  const av = role === 'bot' ? 'A' : '👤';
  div.innerHTML = `
    <div class="avatar">${av}</div>
    <div class="bubble">${role === 'bot' ? md(content) : escHtml(content)}</div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div.querySelector('.bubble');
}

function escHtml(t) {
  return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

/** Typing indicator */
function addTyping() {
  const box = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'msg bot typing';
  div.id = 'typing-indicator';
  div.innerHTML = `
    <div class="avatar">A</div>
    <div class="bubble">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
      <small style="color:var(--grey-light);font-size:0.78rem"> Iščem v bazi znanja...</small>
    </div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}
function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

/** Simulacija token-by-token streaminga */
async function streamText(bubble, text) {
  const words = text.split(' ');
  let built = '';
  for (let i = 0; i < words.length; i++) {
    built += words[i] + (i < words.length - 1 ? ' ' : '');
    bubble.innerHTML = md(built) + '<span style="color:var(--blue-main)">▌</span>';
    document.getElementById('messages').scrollTop = 9999;
    await new Promise(r => setTimeout(r, STREAM_DELAY));
  }
  bubble.innerHTML = md(text);
}

/** Prikaz virov v stranskem panelu */
function showSources(sources) {
  const el = document.getElementById('sources-body');
  if (!sources || !sources.length) {
    el.innerHTML = '<p class="no-sources">Ni virov za ta odgovor.</p>';
    return;
  }
  el.innerHTML = sources.map((s, i) => `
    <div class="source-card">
      <div class="source-title">
        <span class="source-num">${i+1}</span>${escHtml(s.title)}
      </div>
      <a class="source-url" href="${s.url}" target="_blank">🔗 ${s.url}</a>
      <div class="source-docid">ID: ${s.doc_id}</div>
      <div class="source-excerpt">${escHtml(s.excerpt)}</div>
    </div>`).join('');
}

/** Prikaz metapodatkov */
function showMeta(topic, confidence) {
  const filled = Math.round(confidence * 10);
  const bar = '█'.repeat(filled) + '░'.repeat(10 - filled);
  const cls = confidence >= 0.8 ? 'conf-hi' : confidence >= 0.5 ? 'conf-mid' : 'conf-lo';
  const pct = Math.round(confidence * 100) + '%';
  document.getElementById('meta-body').innerHTML = `
    <div class="meta-row">
      <span class="meta-label">Tema:</span>
      <span>${escHtml(topic)}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">Zaupanje:</span>
      <span class="conf-bar ${cls}">${bar} ${pct}</span>
    </div>`;
}

// ── Gumbi in vnosno polje ───────────────────────────────

function setQ(btn) {
  document.getElementById('q').value = btn.textContent;
  document.getElementById('q').focus();
}

function clearChat() {
  const box = document.getElementById('messages');
  box.innerHTML = `
    <div class="msg bot">
      <div class="avatar">A</div>
      <div class="bubble">Pogovor počiščen. Postavite novo vprašanje.</div>
    </div>`;
  document.getElementById('sources-body').innerHTML = '<p class="no-sources">Viri se prikažejo tukaj po prvem odgovoru.</p>';
  document.getElementById('meta-body').innerHTML = '<p class="no-sources">Čakam na odgovor...</p>';
}

// Enter pošlje (Shift+Enter = nova vrstica)
document.getElementById('q').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
});

// ── Glavna funkcija pošiljanja ──────────────────────────
async function sendMsg() {
  const input = document.getElementById('q');
  const question = input.value.trim();
  if (!question) return;

  input.value = '';
  document.getElementById('send').disabled = true;

  // Prikaz uporabnikovega sporočila
  addMsg('user', question);

  // Typing indicator
  addTyping();

  let data;
  try {
    const res = await fetch(API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    removeTyping();
    addMsg('bot',
      `**Napaka:** Ne morem se povezati z API strežnikom.\n\n` +
      `Preverite, ali je zagnan:\n` +
      `\`uvicorn api:app --port 8000\`\n\n` +
      `Napaka: ${err.message}`
    );
    document.getElementById('send').disabled = false;
    return;
  }

  removeTyping();

  // Strean odgovora
  const bubble = addMsg('bot', '');
  const answerWithMeta =
    data.answer +
    `\n\n---\n**Tema:** ${data.topic}  ·  **Zaupanje:** ${Math.round(data.confidence_score*100)}%`;

  await streamText(bubble, answerWithMeta);

  // Posodobitev stranskega panela
  showSources(data.sources);
  showMeta(data.topic, data.confidence_score);

  document.getElementById('send').disabled = false;
  document.getElementById('q').focus();
}

// ── Preverjanje API statusa ─────────────────────────────
async function checkApi() {
  const dot  = document.getElementById('api-dot');
  const span = document.getElementById('api-status');
  try {
    const r = await fetch('http://localhost:8000/health');
    if (r.ok) {
      dot.style.background  = '#4ade80';
      dot.style.boxShadow   = '0 0 6px #4ade80';
      span.textContent      = 'API aktiven';
    } else { throw new Error(); }
  } catch {
    dot.style.background  = '#ef4444';
    dot.style.boxShadow   = '0 0 6px #ef4444';
    span.textContent      = 'API nedosegljiv';
  }
}
checkApi();
setInterval(checkApi, 10000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return HTMLResponse(content=HTML_PAGE)

"""
AKOS Asistent – Chainlit UI
============================
Zagon:
    uvicorn api:app --port 8000          (mock RAG API)
    chainlit run chainlit_app.py --port 8080

Brez prijave – vsi obiskovalci so samodejno prijavljeni kot gost.
Zgodovina pogovorov se shranjuje v akos_history.db.
"""

from __future__ import annotations

import asyncio
import base64
import sqlite3

import httpx
import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

# ---------------------------------------------------------------------------
# Konfiguracija
# ---------------------------------------------------------------------------

API_URL = "http://localhost:8000/api/chat"
STREAM_DELAY = 0.018
ASSISTANT_NAME = "AKOS Asistent"
_DB_PATH = "akos_history.db"

# ---------------------------------------------------------------------------
# Inicializacija SQLite baze (se izvede enkrat ob zagonu)
# ---------------------------------------------------------------------------

def _init_db() -> None:
    """Ustvari tabele za Chainlit data layer. Varno za večkratni zagon (IF NOT EXISTS)."""
    conn = sqlite3.connect(_DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            "id"          TEXT PRIMARY KEY,
            "identifier"  TEXT NOT NULL UNIQUE,
            "metadata"    TEXT NOT NULL DEFAULT '{}',
            "createdAt"   TEXT
        );

        CREATE TABLE IF NOT EXISTS threads (
            "id"              TEXT PRIMARY KEY,
            "createdAt"       TEXT,
            "name"            TEXT,
            "userId"          TEXT,
            "userIdentifier"  TEXT,
            "tags"            TEXT,
            "metadata"        TEXT,
            FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS steps (
            "id"            TEXT PRIMARY KEY,
            "name"          TEXT NOT NULL,
            "type"          TEXT NOT NULL,
            "threadId"      TEXT NOT NULL,
            "parentId"      TEXT,
            "streaming"     INTEGER,
            "waitForAnswer" INTEGER,
            "isError"       INTEGER,
            "metadata"      TEXT,
            "tags"          TEXT,
            "input"         TEXT,
            "output"        TEXT,
            "createdAt"     TEXT,
            "start"         TEXT,
            "end"           TEXT,
            "generation"    TEXT,
            "showInput"     TEXT,
            "language"      TEXT,
            "indent"        INTEGER,
            FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS elements (
            "id"           TEXT PRIMARY KEY,
            "threadId"     TEXT,
            "type"         TEXT,
            "chainlitKey"  TEXT,
            "url"          TEXT,
            "objectKey"    TEXT,
            "name"         TEXT NOT NULL,
            "display"      TEXT,
            "size"         TEXT,
            "language"     TEXT,
            "page"         INTEGER,
            "forId"        TEXT,
            "mime"         TEXT,
            "props"        TEXT
        );

        CREATE TABLE IF NOT EXISTS feedbacks (
            "id"      TEXT PRIMARY KEY,
            "forId"   TEXT NOT NULL,
            "value"   INTEGER NOT NULL,
            "comment" TEXT
        );
    """)
    conn.commit()
    conn.close()


_init_db()

# ---------------------------------------------------------------------------
# Data layer – persistentna zgodovina pogovorov (SQLite)
# ---------------------------------------------------------------------------

cl_data._data_layer = SQLAlchemyDataLayer(
    conninfo=f"sqlite+aiosqlite:///{_DB_PATH}",
    show_logger=False,
)

# ---------------------------------------------------------------------------
# Avtentikacija – samodejno (brez prijave), vsi kot "gost"
# Header auth se pokliče pri vsakem obisku; vrne User brez forme.
# ---------------------------------------------------------------------------

@cl.header_auth_callback
def header_auth_callback(headers: dict) -> cl.User | None:
    return cl.User(identifier="gost", metadata={"role": "guest"})


# ---------------------------------------------------------------------------
# Ikone za starter kartice (base64 SVG data URI)
# ---------------------------------------------------------------------------

def _svg_to_data_uri(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


_ICON_ANTENNA = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 16 0"/><path d="M7.5 12a4.5 4.5 0 0 1 9 0"/><circle cx="12" cy="12" r="1.6" fill="#0055CC" stroke="none"/><path d="M12 14v8"/><path d="M9 22h6"/></svg>"""
_ICON_COMPLAINT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="15" r="1" fill="#0055CC" stroke="none"/></svg>"""
_ICON_LAW = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M5 7h14"/><path d="M4 13l2-6 2 6"/><path d="M16 13l2-6 2 6"/><path d="M3 13a3 3 0 0 0 6 0"/><path d="M15 13a3 3 0 0 0 6 0"/><path d="M8 21h8"/></svg>"""
_ICON_PHONE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2" width="12" height="20" rx="2.5"/><line x1="10" y1="18.5" x2="14" y2="18.5"/><line x1="9" y1="5.5" x2="15" y2="5.5" opacity="0.4"/></svg>"""
_ICON_WIFI = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 8.5a16 16 0 0 1 21 0"/><path d="M5 12a11 11 0 0 1 14 0"/><path d="M8.5 15.5a6 6 0 0 1 7 0"/><circle cx="12" cy="20" r="1.4" fill="#0055CC" stroke="none"/></svg>"""

ICON_ANTENNA  = _svg_to_data_uri(_ICON_ANTENNA)
ICON_COMPLAINT = _svg_to_data_uri(_ICON_COMPLAINT)
ICON_LAW      = _svg_to_data_uri(_ICON_LAW)
ICON_PHONE    = _svg_to_data_uri(_ICON_PHONE)
ICON_WIFI     = _svg_to_data_uri(_ICON_WIFI)


# ---------------------------------------------------------------------------
# Starter prompts
# ---------------------------------------------------------------------------

@cl.set_starters
async def starters():
    return [
        cl.Starter(
            label="Dodelitev 5G frekvenc",
            message="Kako poteka postopek dodelitve radijskih frekvenc za omrežja 5G?",
            icon=ICON_ANTENNA,
        ),
        cl.Starter(
            label="Pritožba zoper operaterja",
            message="Kako vložim pritožbo zoper mobilnega operaterja in v kakšnem roku mora odgovoriti?",
            icon=ICON_COMPLAINT,
        ),
        cl.Starter(
            label="ZEKom-2 – pregled",
            message="Katera so ključna področja, ki jih ureja ZEKom-2?",
            icon=ICON_LAW,
        ),
        cl.Starter(
            label="Prenos telefonske številke",
            message="V kolikšnem času mora operater prenesti mobilno telefonsko številko?",
            icon=ICON_PHONE,
        ),
        cl.Starter(
            label="Univerzalna storitev",
            message="Do kakšne hitrosti interneta sem upravičen v okviru univerzalne storitve?",
            icon=ICON_WIFI,
        ),
    ]


# ---------------------------------------------------------------------------
# Pretvori interna imena v slovenska
# ---------------------------------------------------------------------------

@cl.author_rename
def rename(orig_author: str) -> str:
    mapping = {
        "Assistant": ASSISTANT_NAME,
        "Tool": "Iskanje po bazi znanja",
        "Chatbot": ASSISTANT_NAME,
    }
    return mapping.get(orig_author, orig_author)


# ---------------------------------------------------------------------------
# Inicializacija seje – pogovorna zgodovina za multi-turn kontekst
# ---------------------------------------------------------------------------

@cl.on_chat_start
async def on_start():
    cl.user_session.set("history", [])


# ---------------------------------------------------------------------------
# Pomožne funkcije
# ---------------------------------------------------------------------------

def confidence_badge(conf: float) -> str:
    pct = round(conf * 100)
    filled = round(conf * 10)
    bar = "█" * filled + "░" * (10 - filled)
    if conf >= 0.8:
        emoji, label = "🟢", "visoko"
    elif conf >= 0.5:
        emoji, label = "🟡", "srednje"
    else:
        emoji, label = "🔴", "nizko"
    return f"{emoji} **{label}** `{bar}` {pct}%"


def source_element_name(idx: int) -> str:
    return f"Vir {idx}"


def format_source_content(idx: int, src: dict) -> str:
    return (
        f"# 📄 Vir {idx}\n\n"
        f"## {src['title']}\n\n"
        f"**ID dokumenta:** `{src['doc_id']}`\n\n"
        f"**Povezava do izvirnika:**  \n"
        f"[{src['url']}]({src['url']})\n\n"
        f"---\n\n"
        f"### Izsek iz dokumenta\n\n"
        f"> {src['excerpt']}\n\n"
        f"---\n\n"
        f"*Vir je pridobljen iz indeksa AKOS dokumentov v okviru RAG procesa.*"
    )


def sources_summary_md(sources: list[dict]) -> str:
    if not sources:
        return ""
    lines = ["\n\n---\n\n**📄 Uporabljeni viri:**\n"]
    for i, s in enumerate(sources, 1):
        name = source_element_name(i)
        lines.append(f"- {name} — **{s['title']}** · `{s['doc_id']}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Klic RAG API
# ---------------------------------------------------------------------------

async def call_rag_api(question: str, history: list) -> dict | None:
    """Pokliče RAG API. History je poslan za multi-turn kontekst (ko bo pravi backend)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                API_URL,
                json={"question": question, "history": history},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectError:
        await cl.Message(
            author=ASSISTANT_NAME,
            content=(
                "### ⚠️ API strežnik ni dosegljiv\n\n"
                "RAG backend ne odgovarja. Preverite, ali je zagnan:\n\n"
                "```bash\n"
                "uvicorn api:app --port 8000\n"
                "```"
            ),
        ).send()
        return None
    except Exception as exc:
        await cl.Message(
            author=ASSISTANT_NAME,
            content=f"### ⚠️ Napaka pri obdelavi vprašanja\n\n`{exc}`",
        ).send()
        return None


# ---------------------------------------------------------------------------
# Glavna logika – ob vsakem sporočilu
# ---------------------------------------------------------------------------

@cl.on_message
async def reply(message: cl.Message):
    history: list = cl.user_session.get("history") or []

    # 1) Vizualni RAG korak
    async with cl.Step(name="Iščem v bazi dokumentov AKOS", type="tool") as step:
        step.input = message.content
        data = await call_rag_api(message.content, history)
        if data is None:
            return
        step.output = (
            f"Najdena tema: **{data['topic']}**  \n"
            f"Število virov: **{len(data['sources'])}**  \n"
            f"Zaupanje: **{round(data['confidence_score'] * 100)}%**"
        )

    answer: str = data["answer"]
    sources: list = data["sources"]
    conf: float = data["confidence_score"]
    topic: str = data["topic"]

    # 2) Viri kot stranski elementi
    side_elements = [
        cl.Text(
            name=source_element_name(i),
            content=format_source_content(i, s),
            display="side",
        )
        for i, s in enumerate(sources, 1)
    ]

    # 3) Gumbi za povratno informacijo (kopiranje je vgrajeno v Chainlit)
    actions = [
        cl.Action(
            name="helpful",
            payload={"value": "yes"},
            label="👍 Koristno",
            tooltip="Odgovor je bil koristen",
        ),
        cl.Action(
            name="not_helpful",
            payload={"value": "no"},
            label="👎 Ni koristno",
            tooltip="Odgovor ni bil koristen",
        ),
    ]

    # 4) Sestavi besedilo odgovora
    header_md = (
        f"<span class='akos-badge akos-badge-topic'>📂 {topic}</span> "
        f"&nbsp; {confidence_badge(conf)}\n\n"
    )
    full_text = header_md + answer + sources_summary_md(sources)

    # 5) Streaming word-by-word
    msg = cl.Message(author=ASSISTANT_NAME, content="")
    await msg.send()

    words = full_text.split(" ")
    for i, word in enumerate(words):
        await msg.stream_token(word + (" " if i < len(words) - 1 else ""))
        if i % 4 == 0:
            await asyncio.sleep(STREAM_DELAY)

    msg.elements = side_elements
    msg.actions = actions
    await msg.update()

    # 6) Posodobi pogovorno zgodovino za multi-turn kontekst
    history.append({"role": "user", "content": message.content})
    history.append({"role": "assistant", "content": answer})
    cl.user_session.set("history", history)


# ---------------------------------------------------------------------------
# Povratna informacija
# ---------------------------------------------------------------------------

@cl.action_callback("helpful")
async def on_helpful(action: cl.Action):
    await cl.Message(
        author=ASSISTANT_NAME,
        content="✅ Hvala za povratno informacijo – odgovor je označen kot **koristen**.",
    ).send()


@cl.action_callback("not_helpful")
async def on_not_helpful(action: cl.Action):
    await cl.Message(
        author=ASSISTANT_NAME,
        content=(
            "📝 Hvala za povratno informacijo. Če želite, opišite, kaj je manjkalo, "
            "in vprašanje bom poskusil obravnavati drugače."
        ),
    ).send()

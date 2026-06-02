"""
AKOS Asistent – Chainlit UI
============================
Zagon:
    uvicorn api:app --port 8000          (mock RAG API)
    chainlit run chainlit_app.py --port 8080

Cilj te datoteke je *demo UI*: lep, tekoč, AKOS-brandiran pogovor.
Resnični RAG backend bo zamenjal mock API – tukaj poliramo izgled.
"""

from __future__ import annotations

import asyncio
import base64
import httpx
import chainlit as cl

# ---------------------------------------------------------------------------
# Konfiguracija
# ---------------------------------------------------------------------------

API_URL = "http://localhost:8000/api/chat"
STREAM_DELAY = 0.018  # sekunde med besedami – dovolj počasi za bralni efekt
ASSISTANT_NAME = "AKOS Asistent"


# ---------------------------------------------------------------------------
# Ikone za starter kartice
# ---------------------------------------------------------------------------
# Chainlit izriše icon kot <img src="..."> v okencu 20×20.  Da se izognemo
# kakršnimkoli težavam s strežniškim MIME tipom za /public/, ikone vstavimo
# kot base64 data URI – brskalnik jih nariše neposredno.
#
# Vse ikone uporabljajo AKOS modro (#0055CC).

def _svg_to_data_uri(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


_ICON_ANTENNA = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 0 1 16 0"/><path d="M7.5 12a4.5 4.5 0 0 1 9 0"/><circle cx="12" cy="12" r="1.6" fill="#0055CC" stroke="none"/><path d="M12 14v8"/><path d="M9 22h6"/></svg>"""

_ICON_COMPLAINT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="15" r="1" fill="#0055CC" stroke="none"/></svg>"""

_ICON_LAW = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18"/><path d="M5 7h14"/><path d="M4 13l2-6 2 6"/><path d="M16 13l2-6 2 6"/><path d="M3 13a3 3 0 0 0 6 0"/><path d="M15 13a3 3 0 0 0 6 0"/><path d="M8 21h8"/></svg>"""

_ICON_PHONE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2" width="12" height="20" rx="2.5"/><line x1="10" y1="18.5" x2="14" y2="18.5"/><line x1="9" y1="5.5" x2="15" y2="5.5" opacity="0.4"/></svg>"""

_ICON_WIFI = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#0055CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 8.5a16 16 0 0 1 21 0"/><path d="M5 12a11 11 0 0 1 14 0"/><path d="M8.5 15.5a6 6 0 0 1 7 0"/><circle cx="12" cy="20" r="1.4" fill="#0055CC" stroke="none"/></svg>"""

ICON_ANTENNA = _svg_to_data_uri(_ICON_ANTENNA)
ICON_COMPLAINT = _svg_to_data_uri(_ICON_COMPLAINT)
ICON_LAW = _svg_to_data_uri(_ICON_LAW)
ICON_PHONE = _svg_to_data_uri(_ICON_PHONE)
ICON_WIFI = _svg_to_data_uri(_ICON_WIFI)


# ---------------------------------------------------------------------------
# Starter prompts – kartice, ki se prikažejo na uvodnem zaslonu
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
# Pretvori interna imena ("Assistant", "Tool") v slovenska, prijazna imena
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
# Pomožne funkcije za predstavitev metapodatkov
# ---------------------------------------------------------------------------

def confidence_badge(conf: float) -> str:
    """Vrne markdown z barvno značko za stopnjo zaupanja."""
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
    """Kratko, predvidljivo ime elementa – mora se *dobesedno* pojaviti v
    besedilu sporočila, da Chainlit prikaže klikljiv žeton za stranski panel."""
    return f"Vir {idx}"


def format_source_content(idx: int, src: dict) -> str:
    """Markdown za vsebino vira v stranskem panelu (odpre se ob kliku)."""
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
    """Povzetek virov pod odgovorom – vsak `Vir N` se pojavi v besedilu kot
    klikljiv žeton, ker se Chainlit elementi z display='side' aktivirajo
    šele, ko se ime elementa dobesedno pojavi v sporočilu."""
    if not sources:
        return ""
    lines = ["\n\n---\n\n**📄 Uporabljeni viri:**\n"]
    for i, s in enumerate(sources, 1):
        name = source_element_name(i)
        # Ime "Vir N" mora ostati golo (brez markdown, brez oklepajev),
        # da ga Chainlit pretvori v klikljiv side-panel sprožilec.
        lines.append(f"- {name} — **{s['title']}** · `{s['doc_id']}`")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Klic mock API
# ---------------------------------------------------------------------------

async def call_rag_api(question: str) -> dict | None:
    """Pokliče RAG API. Vrne dict ali None ob napaki (napako sporoči uporabniku)."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(API_URL, json={"question": question})
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
# Glavna logika – ob vsakem sporočilu uporabnika
# ---------------------------------------------------------------------------

@cl.on_message
async def reply(message: cl.Message):
    # 1) Vizualno predstavi "iskanje" kot Step, da uporabnik vidi RAG proces
    async with cl.Step(name="Iščem v bazi dokumentov AKOS", type="tool") as step:
        step.input = message.content
        data = await call_rag_api(message.content)
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

    # 2) Pripravi vire kot stranske (side) elemente.
    #    Pomembno: ime elementa MORA biti dobesedno prisotno v besedilu sporočila –
    #    šele takrat Chainlit izriše klikljiv žeton, ki odpre stranski panel.
    side_elements: list[cl.Text] = []
    for i, s in enumerate(sources, 1):
        side_elements.append(
            cl.Text(
                name=source_element_name(i),
                content=format_source_content(i, s),
                display="side",
            )
        )

    # 3) Akcijski gumbi pod odgovorom
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
        cl.Action(
            name="copy_answer",
            payload={"text": answer},
            label="📋 Kopiraj odgovor",
            tooltip="Kopiraj besedilo v odložišče",
        ),
        cl.Action(
            name="show_sources",
            payload={"count": len(sources)},
            label=f"📄 Viri ({len(sources)})",
            tooltip="Odpri stransko ploščo z viri",
        ),
    ]

    # 4) Sestavi celotno besedilo – glavni odgovor + metapodatkovni footer + povzetek virov
    header_md = (
        f"<span class='akos-badge akos-badge-topic'>📂 {topic}</span> "
        f"&nbsp; {confidence_badge(conf)}\n\n"
    )
    full_text = header_md + answer + sources_summary_md(sources)

    # 5) Streamaj besedo-po-besedo (občutek tipkanja); ko končamo, dodamo elemente + akcije
    msg = cl.Message(author=ASSISTANT_NAME, content="")
    await msg.send()

    words = full_text.split(" ")
    for i, word in enumerate(words):
        await msg.stream_token(word + (" " if i < len(words) - 1 else ""))
        # Hitrejši streaming na zelo dolgih odgovorih
        if i % 4 == 0:
            await asyncio.sleep(STREAM_DELAY)

    msg.elements = side_elements
    msg.actions = actions
    await msg.update()


# ---------------------------------------------------------------------------
# Akcijski gumbi – odziv
# ---------------------------------------------------------------------------

@cl.action_callback("helpful")
async def on_helpful(action: cl.Action):
    await cl.Message(
        author=ASSISTANT_NAME,
        content="✅ Hvala za povratno informacijo – odgovor je shranjen kot **koristen**.",
    ).send()


@cl.action_callback("not_helpful")
async def on_not_helpful(action: cl.Action):
    await cl.Message(
        author=ASSISTANT_NAME,
        content=(
            "📝 Hvala za povratno informacijo. Če želite, opišite, kaj je manjkalo, "
            "in vprašanje bom poskusil ponovno z drugim pristopom."
        ),
    ).send()


@cl.action_callback("copy_answer")
async def on_copy(action: cl.Action):
    # Chainlit nima JS clipboard API, zato odgovor prikažemo v kodi za hitro označitev
    text = action.payload.get("text", "")
    await cl.Message(
        author=ASSISTANT_NAME,
        content=(
            "📋 Besedilo za kopiranje (Cmd/Ctrl+C):\n\n"
            f"```text\n{text}\n```"
        ),
    ).send()


@cl.action_callback("show_sources")
async def on_show_sources(action: cl.Action):
    count = action.payload.get("count", 0)
    await cl.Message(
        author=ASSISTANT_NAME,
        content=(
            f"📄 V tem odgovoru je uporabljenih **{count} virov**. "
            "Kliknite na ime vira pod odgovorom – odprla se bo stranska plošča "
            "s celotnim izsekom in povezavo do izvirnega dokumenta."
        ),
    ).send()

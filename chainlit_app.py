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
import httpx
import chainlit as cl

# ---------------------------------------------------------------------------
# Konfiguracija
# ---------------------------------------------------------------------------

API_URL = "http://localhost:8000/api/chat"
STREAM_DELAY = 0.018  # sekunde med besedami – dovolj počasi za bralni efekt
ASSISTANT_NAME = "AKOS Asistent"


# ---------------------------------------------------------------------------
# Starter prompts – kartice, ki se prikažejo na uvodnem zaslonu
# ---------------------------------------------------------------------------

@cl.set_starters
async def starters():
    return [
        cl.Starter(
            label="Dodelitev 5G frekvenc",
            message="Kako poteka postopek dodelitve radijskih frekvenc za omrežja 5G?",
            icon="/public/icons/antenna.svg",
        ),
        cl.Starter(
            label="Pritožba zoper operaterja",
            message="Kako vložim pritožbo zoper mobilnega operaterja in v kakšnem roku mora odgovoriti?",
            icon="/public/icons/complaint.svg",
        ),
        cl.Starter(
            label="ZEKom-2 – pregled",
            message="Katera so ključna področja, ki jih ureja ZEKom-2?",
            icon="/public/icons/law.svg",
        ),
        cl.Starter(
            label="Prenos telefonske številke",
            message="V kolikšnem času mora operater prenesti mobilno telefonsko številko?",
            icon="/public/icons/phone.svg",
        ),
        cl.Starter(
            label="Univerzalna storitev",
            message="Do kakšne hitrosti interneta sem upravičen v okviru univerzalne storitve?",
            icon="/public/icons/wifi.svg",
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


def format_source_content(idx: int, src: dict) -> str:
    """Markdown za posamezen vir v stranskem panelu."""
    return (
        f"# Vir {idx}\n\n"
        f"## {src['title']}\n\n"
        f"**ID dokumenta:** `{src['doc_id']}`\n\n"
        f"**Povezava:**  \n"
        f"<{src['url']}>\n\n"
        f"---\n\n"
        f"### Izsek iz dokumenta\n\n"
        f"> {src['excerpt']}\n\n"
        f"---\n\n"
        f"*Vir je pridobljen iz indeksa AKOS dokumentov v okviru RAG procesa.*"
    )


def sources_summary_md(sources: list[dict]) -> str:
    """Kratek povzetek virov pod odgovorom – kliknete na vir za podrobnosti."""
    if not sources:
        return ""
    lines = ["\n\n**📄 Uporabljeni viri:**\n"]
    for i, s in enumerate(sources, 1):
        lines.append(f"{i}. **{s['title']}**  \n   `{s['doc_id']}` · [odpri dokument]({s['url']})")
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

    # 2) Pripravi viri kot stranski (side) elementi – kliknete na ime in se odpre panel
    side_elements: list[cl.Text] = []
    for i, s in enumerate(sources, 1):
        side_elements.append(
            cl.Text(
                name=f"Vir {i}: {s['title'][:60]}",
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

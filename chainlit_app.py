"""
AKOS Asistent – Chainlit UI
============================
Zagon:
    chainlit run chainlit_app.py --port 8080
    (API mora teči na localhost:8000)
"""

import asyncio
import httpx
import chainlit as cl

API_URL = "http://localhost:8000/api/chat"
STREAM_DELAY = 0.030  # sekunde med besedami


# ---------------------------------------------------------------------------
# Ob zagonu pogovora
# ---------------------------------------------------------------------------

@cl.on_chat_start
async def start():
    await cl.Message(
        author="AKOS Asistent",
        content=(
            "## Pozdravljeni v AKOS Asistentu\n\n"
            "Sem pomočnik Agencije za komunikacijska omrežja in storitve RS. "
            "Odgovarjam na podlagi uradnih dokumentov, splošnih aktov in ZEKom-2.\n\n"
            "**Kar znam:**\n"
            "- Dodelitev radijskih frekvenc in 5G postopki\n"
            "- Pritožbe zoper telekomunikacijske operaterje\n"
            "- ZEKom-2 in splošni akti AKOS\n"
            "- Prenosljivost telefonskih številk\n"
            "- Universalna storitev in dostop do interneta\n\n"
            "**Primer:** *Kako vložim pritožbo zoper mobilnega operaterja?*"
        ),
    ).send()


# ---------------------------------------------------------------------------
# Ob vsaki sporočilu
# ---------------------------------------------------------------------------

@cl.on_message
async def reply(message: cl.Message):
    # Pokliče API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(API_URL, json={"question": message.content})
            resp.raise_for_status()
            data = resp.json()
    except httpx.ConnectError:
        await cl.Message(
            author="AKOS Asistent",
            content=(
                "**Napaka:** API strežnik ni dosegljiv.\n\n"
                "Preverite: `uvicorn api:app --port 8000`"
            ),
        ).send()
        return
    except Exception as exc:
        await cl.Message(author="AKOS Asistent", content=f"**Napaka:** {exc}").send()
        return

    answer: str   = data["answer"]
    sources: list = data["sources"]
    conf: float   = data["confidence_score"]
    topic: str    = data["topic"]

    # Confidence bar
    bar = "█" * round(conf * 10) + "░" * (10 - round(conf * 10))
    label = "visoko" if conf >= 0.8 else "srednje" if conf >= 0.5 else "nizko"

    # Celotno besedilo z metapodatki
    full_text = (
        answer
        + f"\n\n---\n**Tema:** {topic}  \n"
        + f"**Zaupanje:** `{bar}` {conf:.0%} ({label})"
    )

    # Streaming simulacija beseda po besedo
    msg = cl.Message(author="AKOS Asistent", content="")
    await msg.send()

    words = full_text.split(" ")
    for i, word in enumerate(words):
        await msg.stream_token(word + (" " if i < len(words) - 1 else ""))
        await asyncio.sleep(STREAM_DELAY)

    # Viri kot Chainlit Text elementi
    if sources:
        elements = []
        for i, s in enumerate(sources, 1):
            elements.append(
                cl.Text(
                    name=f"Vir {i} – {s['title'][:50]}",
                    content=(
                        f"### {s['title']}\n\n"
                        f"**Povezava:** {s['url']}\n\n"
                        f"**ID dokumenta:** `{s['doc_id']}`\n\n"
                        f"---\n\n> {s['excerpt']}"
                    ),
                    display="inline",
                )
            )
        msg.elements = elements

    await msg.update()

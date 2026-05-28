"""
AKOS RAG Mock API  –  FastAPI backend
======================================
Simulira RAG (Retrieval-Augmented Generation) sistem nad dokumenti AKOS.
Brez zunanjih API ključev, brez prijave.

Zagon:
    uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Aplikacija
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AKOS RAG Mock API",
    description="Simulirani RAG sistem nad dokumenti Agencije za komunikacijska omrežja in storitve",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Podatkovni modeli
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class Source(BaseModel):
    title: str
    url: str
    doc_id: str
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence_score: float
    topic: str


# ---------------------------------------------------------------------------
# Mock baza znanja – simulira indeksirane dokumente AKOS
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE: list[dict] = [
    # -----------------------------------------------------------------------
    # TEMA 1: 5G radijske frekvence in spekter
    # -----------------------------------------------------------------------
    {
        "topic": "5G radijske frekvence",
        "keywords": [
            "5g", "frekvenc", "radij", "spekter", "mhz", "ghz",
            "700", "3.6", "26", "oddajnik", "pas", "dovoljenje",
        ],
        "answer": (
            "AKOS je v skladu z ZEKom-2 (Ur. l. RS, št. 130/22) in Uredbo EU 2021/696 "
            "izvedla postopek javnega razpisa za dodelitev radijskih frekvenc za omrežja 5G.\n\n"
            "**Dodeljeni frekvenčni pasovi:**\n"
            "- **700 MHz** (694–790 MHz) – pokritost ruralnih območij in stavb\n"
            "- **3,6 GHz** (3400–3800 MHz) – kapacitetna mestna omrežja\n"
            "- **26 GHz** (24,25–27,5 GHz) – milimetrski val za zelo gosto pokritost\n\n"
            "**Pogoji za dodelitev radijskega dovoljenja:**\n"
            "1. Zagotovitev pokritosti najmanj 95 % prebivalstva do konca leta 2027\n"
            "2. Letna taksa za uporabo spektra (v skladu s Tarifo AKOS, Ur. l. RS, št. 42/23)\n"
            "3. Izpolnjevanje tehničnih pogojev iz Sklepa Komisije 2020/1426/EU\n"
            "4. Predložitev poslovnega načrta z mejniki uvajanja omrežja\n"
            "5. Obveza gradnje lastne infrastrukture ali souporabe z drugim imetnikom\n\n"
            "**Postopek vložitve vloge:**\n"
            "Vlogo za radijsko dovoljenje se vloži na obrazcu **AKOS-RD-01** v elektronski "
            "obliki prek portala eAKOS ali po pošti. Odločba se izda v roku 30 dni od prejema "
            "popolne vloge."
        ),
        "sources": [
            {
                "title": "Javni razpis za dodelitev radijskih frekvenc 5G",
                "url": "https://www.akos-rs.si/radijske-frekvence/5g-razpis",
                "doc_id": "AKOS-RF-2023-0042",
                "excerpt": (
                    "AKOS objavlja javni razpis za dodelitev radijskih frekvenc v pasovih "
                    "700 MHz, 3,6 GHz in 26 GHz za zagotovitev storitev 5G na ozemlju RS."
                ),
            },
            {
                "title": "ZEKom-2 – Zakon o elektronskih komunikacijah (Ur. l. RS, 130/22)",
                "url": "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2022-01-3901",
                "doc_id": "UL-RS-2022-3901",
                "excerpt": (
                    "Zakon ureja področje elektronskih komunikacij, vključno z upravljanjem "
                    "radijskega spektra, postopkom dodeljevanja frekvenc in pogoji za operaterje."
                ),
            },
            {
                "title": "Splošni akt o pogojih za dodelitev in uporabo radijskih frekvenc (SA-RF-2023)",
                "url": "https://www.akos-rs.si/splosni-akti/SA-RF-2023",
                "doc_id": "AKOS-SA-RF-2023",
                "excerpt": (
                    "Splošni akt podrobneje določa tehnične in administrativne pogoje za "
                    "dodelitev radijskih frekvenc ter obveznosti imetnikov radijskih dovoljenj."
                ),
            },
        ],
        "confidence": 0.93,
    },

    # -----------------------------------------------------------------------
    # TEMA 2: Pritožbe zoper telekomunikacijske operaterje
    # -----------------------------------------------------------------------
    {
        "topic": "Pritožbe zoper operaterje",
        "keywords": [
            "pritožb", "operater", "reklamacij", "pogodba", "prekinitev",
            "račun", "storitev", "telekom", "a1", "telemach", "t-2",
            "kabel", "spor", "reševanje", "potrošnik",
        ],
        "answer": (
            "Postopek vlaganja pritožbe zoper telekomunikacijskega operaterja poteka v **dveh fazah** "
            "in temelji na ZEKom-2 (207.–215. člen).\n\n"
            "**1. faza – Obvezna pritožba pri operaterju:**\n"
            "Pred obrnitvijo na AKOS morate pritožbo najprej nasloviti neposredno na operaterja "
            "(pisno, e-pošta ali prek portala operaterja). Operater mora odgovoriti:\n"
            "- Potrošniki: v roku **15 delovnih dni**\n"
            "- Poslovni naročniki: v roku **30 dni**\n\n"
            "**2. faza – Izvensodni postopek pri AKOS:**\n"
            "Če ste z odgovorom nezadovoljni ali odgovora niste prejeli, vložite vlogo pri AKOS:\n"
            "- **eAKOS portal** (priporočeno) – najhitrejša pot\n"
            "- **Po pošti:** AKOS, Stegne 7, 1000 Ljubljana\n"
            "- **Osebno:** pon.–pet., 9:00–13:00\n\n"
            "AKOS izvede postopek v roku **60 dni** od prejema popolne vloge. Postopek je brezplačen.\n\n"
            "**Najpogostejši razlogi pritožb:**\n"
            "- Napake na računih ali neupravičeno zaračunane storitve\n"
            "- Enostranska sprememba pogodbenih pogojev brez obvestila\n"
            "- Kakovost storitev pod pogodbenimi parametri (hitrost interneta, izpadi)\n"
            "- Stroški predčasne prekinitve pogodbe in vezavni roki"
        ),
        "sources": [
            {
                "title": "Postopek pritožbe – AKOS navodila za potrošnike",
                "url": "https://www.akos-rs.si/za-uporabnike/pritozbe",
                "doc_id": "AKOS-UPR-PRIT-2024",
                "excerpt": (
                    "Korak-za-korakom opis postopka vlaganja pritožbe zoper elektronskega "
                    "komunikacijskega operaterja, roki in obrazci za potrošnike in poslovne stranke."
                ),
            },
            {
                "title": "ZEKom-2, 207.–215. člen – Reševanje sporov",
                "url": "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2022-01-3901#cl-207",
                "doc_id": "UL-RS-2022-3901-207",
                "excerpt": (
                    "ZEKom-2 v 207. do 215. členu določa postopek izvensodnega reševanja sporov "
                    "med operaterji in uporabniki ter pristojnost AKOS."
                ),
            },
            {
                "title": "Obrazec za pritožbo AKOS-P-01",
                "url": "https://www.akos-rs.si/obrazci/AKOS-P-01.pdf",
                "doc_id": "AKOS-P-01",
                "excerpt": (
                    "Standardiziran obrazec za vložitev pritožbe zoper telekomunikacijskega "
                    "operaterja pri Agenciji AKOS – obvezni priponki: kopija pogodbe in korespondenco."
                ),
            },
        ],
        "confidence": 0.89,
    },

    # -----------------------------------------------------------------------
    # TEMA 3: ZEKom-2 in splošni akti AKOS
    # -----------------------------------------------------------------------
    {
        "topic": "ZEKom-2 in zakonodaja",
        "keywords": [
            "zekom", "zakon", "elektronsk", "komunik", "splošni akt",
            "predpis", "uredba", "direktiva", "eu", "zakonodaj", "člen",
            "dostop", "infrastruktur", "smp", "trg",
        ],
        "answer": (
            "**ZEKom-2** (Zakon o elektronskih komunikacijah, Ur. l. RS, št. 130/22) je stopil "
            "v veljavo januarja 2023 in prenaša Direktivo EU 2018/1972 (Evropski zakonik o "
            "elektronskih komunikacijah – EECC) v slovensko pravo.\n\n"
            "**Ključna področja ureditve:**\n\n"
            "| Področje | Vsebina ZEKom-2 |\n"
            "|---|---|\n"
            "| Dostop do omrežja | Obveze operaterjev s tržno močjo (SMP), 58.–87. člen |\n"
            "| Radijski spekter | Dodelitev, pogoji, nadzor, 140.–180. člen |\n"
            "| Varstvo potrošnikov | Pogodbe, transparentnost, pritožbe, 190.–220. člen |\n"
            "| Infrastruktura | Skupna gradnja, dostop do stavb, 30.–57. člen |\n"
            "| Varnost omrežja | Obveznosti glede kibernetske varnosti, 221.–240. člen |\n\n"
            "**Veljavni splošni akti AKOS** (podzakonski akti):\n"
            "- **SA-KS-2023** – Kakovost storitev in merjenje hitrosti interneta\n"
            "- **SA-PN-2023** – Prenosljivost telefonskih številk\n"
            "- **SA-RF-2023** – Radijske frekvence in pogoji dodelitve\n"
            "- **SA-DI-2022** – Dostop do telekomunikacijske infrastrukture\n"
            "- **SA-US-2023** – Universalna storitev\n\n"
            "Vse splošne akte sprejme **Svet AKOS** po postopku javnega posvetovanja."
        ),
        "sources": [
            {
                "title": "ZEKom-2 – Uradni list RS, št. 130/22",
                "url": "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2022-01-3901",
                "doc_id": "UL-RS-2022-3901",
                "excerpt": (
                    "Besedilo Zakona o elektronskih komunikacijah (ZEKom-2), ki ureja celotno "
                    "področje elektronskih komunikacij v RS od januarja 2023 dalje."
                ),
            },
            {
                "title": "Register splošnih aktov AKOS – 2024",
                "url": "https://www.akos-rs.si/splosni-akti",
                "doc_id": "AKOS-SA-REG-2024",
                "excerpt": (
                    "Uradni register vseh veljavnih splošnih aktov, ki jih je sprejel Svet AKOS "
                    "na podlagi ZEKom-2, vključno z besedili in obrazložitvami."
                ),
            },
            {
                "title": "Direktiva EU 2018/1972 – Evropski zakonik o elektronskih komunikacijah",
                "url": "https://eur-lex.europa.eu/legal-content/SL/TXT/?uri=CELEX:32018L1972",
                "doc_id": "EU-DIR-2018-1972",
                "excerpt": (
                    "Direktiva EP in Sveta EU, ki jo ZEKom-2 prenaša v slovensko zakonodajo – "
                    "temelj regulacije elektronskih komunikacij v vseh državah članicah EU."
                ),
            },
        ],
        "confidence": 0.87,
    },

    # -----------------------------------------------------------------------
    # TEMA 4: Prenosljivost telefonskih številk
    # -----------------------------------------------------------------------
    {
        "topic": "Prenosljivost telefonskih številk",
        "keywords": [
            "prenosljivost", "prenosljiv", "prenos", "številk", "menjava",
            "mno", "mvno", "sim", "mobiln", "fiksn", "geografsk",
        ],
        "answer": (
            "**Prenosljivost telefonskih številk** (Number Portability) omogoča ohranitev "
            "telefonske številke pri menjavi operaterja in jo ureja ZEKom-2 (88.–95. člen) "
            "ter SA-PN-2023.\n\n"
            "**Prenos mobilne številke – postopek:**\n"
            "1. Pri izbranem novem operaterju podpišete novo pogodbo in vložite zahtevo za prenos\n"
            "2. Novi operater (prejemnik) posreduje zahtevo matičnemu operaterju (donorju)\n"
            "3. Prenos se izvede v roku **1 delovnega dne** (potrošniki in mikropodjetja)\n"
            "4. Prekinitev storitve med prenosom ne sme trajati več kot **1 uro**\n\n"
            "**Prenos fiksne številke:**\n"
            "- Rok: do **10 delovnih dni**\n"
            "- Možen je sočasen prenos ob zamenjavi tehnologije (npr. PSTN → VoIP)\n\n"
            "**Stroški:** Operater **ne sme zaračunati** pristojbine za prenos številke.\n\n"
            "**Zakoniti razlogi za zavrnitev prenosa:**\n"
            "- Neporavnane obveznosti pri matičnem operaterju (le za poslovne naročnike)\n"
            "- Vložena zahteva nima ustreznega pooblastila (za poslovne naročnike)\n\n"
            "**Pritožba:** V primeru nezakonitega zavračanja ali prekoračitve roka se obrnite "
            "na AKOS z obrazcem AKOS-P-01."
        ),
        "sources": [
            {
                "title": "Splošni akt o prenosljivosti številk SA-PN-2023",
                "url": "https://www.akos-rs.si/splosni-akti/SA-PN-2023",
                "doc_id": "AKOS-SA-PN-2023",
                "excerpt": (
                    "Splošni akt ureja postopek, roke in pogoje za prenosljivost geografskih, "
                    "negeografskih in mobilnih telefonskih številk med operaterji."
                ),
            },
            {
                "title": "ZEKom-2, 88.–95. člen – Prenosljivost številk",
                "url": "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2022-01-3901#cl-88",
                "doc_id": "UL-RS-2022-3901-88",
                "excerpt": (
                    "ZEKom-2 v 88. do 95. členu določa pravico naročnikov do prenosljivosti "
                    "telefonskih številk in obveznosti operaterjev pri izvedbi prenosa."
                ),
            },
            {
                "title": "Vodič za potrošnike: Menjava operaterja z ohranitivijo številke",
                "url": "https://www.akos-rs.si/za-uporabnike/menjava-operaterja",
                "doc_id": "AKOS-VPC-MEN-2024",
                "excerpt": (
                    "Praktičen korak-za-korakom vodič AKOS za menjavo mobilnega ali fiksnega "
                    "operaterja z ohranitivijo obstoječe telefonske številke."
                ),
            },
        ],
        "confidence": 0.91,
    },

    # -----------------------------------------------------------------------
    # TEMA 5: Universalna storitev in dostop do interneta
    # -----------------------------------------------------------------------
    {
        "topic": "Universalna storitev",
        "keywords": [
            "univerz", "dostop", "internet", "širokopas", "pasovn",
            "hitrost", "mbps", "pokritost", "rural", "bela", "siva",
            "lisa", "subvencij", "cef", "eksrp",
        ],
        "answer": (
            "**Universalna storitev** v elektronskih komunikacijah zagotavlja minimalni nabor "
            "storitev vsem končnim uporabnikom po dostopni ceni, ne glede na geografsko lego.\n\n"
            "**Vsebina universalne storitve (ZEKom-2, 115.–130. člen):**\n"
            "- Dostop do interneta s funkcionalnimi hitrostmi (min. **10 Mbit/s** download)\n"
            "- Glasovne komunikacijske storitve in klic v sili (112, 113)\n"
            "- Dostopne rešitve za osebe s posebnimi potrebami\n"
            "- Zagotovitev dostopa na zahtevo za gospodinjstva brez obstoječega priključka\n\n"
            "**Izvajalci universalne storitve:**\n"
            "AKOS z odločbo določi izvajalce za posamezna geografska območja na podlagi "
            "analize trga. Stroški se krijejo iz Sklada za universalno storitev.\n\n"
            "**Bele in sive lise pokritosti:**\n"
            "AKOS vodi geografske evidence pokritosti z NGA (Next Generation Access) omrežji "
            "in koordinira z Ministrstvom za digitalno preobrazbo pri dodeljevanju sredstev EU "
            "(CEF Digital, EKSRP) za gradnjo infrastrukture v nerentabilnih območjih.\n\n"
            "**Merjenje kakovosti internetne povezave:**\n"
            "Vsak naročnik ima pravico do garantirane hitrosti po pogodbi. Odmike merite z "
            "uradnim orodjem **Merjenje interneta AKOS** (mrljenje.akos-rs.si)."
        ),
        "sources": [
            {
                "title": "Universalna storitev – AKOS",
                "url": "https://www.akos-rs.si/elektronske-komunikacije/univerzalna-storitev",
                "doc_id": "AKOS-US-2024",
                "excerpt": (
                    "Opis obveznosti universalne storitve, seznam izvajalcev, postopek merjenja "
                    "kakovosti internetnih priključkov in evidence pokritosti."
                ),
            },
            {
                "title": "ZEKom-2, 115.–130. člen – Universalna storitev",
                "url": "https://www.uradni-list.si/glasilo-uradni-list-rs/vsebina/2022-01-3901#cl-115",
                "doc_id": "UL-RS-2022-3901-115",
                "excerpt": (
                    "ZEKom-2 določa vsebino universalne storitve, obveznosti izvajalcev, "
                    "mehanizem financiranja in nadzorno vlogo AKOS."
                ),
            },
            {
                "title": "Orodje za merjenje hitrosti interneta – AKOS",
                "url": "https://meritev.akos-rs.si",
                "doc_id": "AKOS-MI-TOOL-2024",
                "excerpt": (
                    "Uradno akreditirano orodje AKOS za merjenje dejanske hitrosti internetne "
                    "povezave in primerjavo z garantiranimi parametri iz pogodbe z operaterjem."
                ),
            },
        ],
        "confidence": 0.85,
    },
]

# Rezervni odgovor, ko noben vnos ne ustreza poizvedbi
DEFAULT_ENTRY = {
    "topic": "Splošno",
    "answer": (
        "Hvala za vaše vprašanje. Na podlagi indeksiranih dokumentov AKOS nisem našel "
        "natančnega odgovora na vašo poizvedbo.\n\n"
        "**Predlagam naslednje:**\n"
        "- Obiščite uradno spletno stran: [www.akos-rs.si](https://www.akos-rs.si)\n"
        "- Info center: **01 583 63 00** (pon.–pet., 9:00–13:00)\n"
        "- E-pošta: info@akos-rs.si\n\n"
        "**Teme, ki jih obvladujem:**\n"
        "radijske frekvence in 5G, pritožbe zoper operaterje, ZEKom-2 in splošni akti, "
        "prenosljivost telefonskih številk, universalna storitev in dostop do interneta."
    ),
    "sources": [
        {
            "title": "AKOS – Uradna spletna stran",
            "url": "https://www.akos-rs.si",
            "doc_id": "AKOS-HOME-2024",
            "excerpt": (
                "Uradna spletna stran Agencije za komunikacijska omrežja in storitve "
                "Republike Slovenije z vsemi dokumenti, akti in obrazci."
            ),
        }
    ],
    "confidence": 0.30,
}

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Sprejme vprašanje, poišče najboljši ujemajoč dokument in vrne strukturiran odgovor."""
    question_lower = request.question.lower()

    best_entry = None
    best_score = 0

    for entry in KNOWLEDGE_BASE:
        score = sum(1 for kw in entry["keywords"] if kw in question_lower)
        if score > best_score:
            best_score = score
            best_entry = entry

    result = best_entry if (best_entry is not None and best_score > 0) else DEFAULT_ENTRY

    return ChatResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
        confidence_score=result["confidence"],
        topic=result["topic"],
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "AKOS RAG Mock API", "version": "1.0.0"}

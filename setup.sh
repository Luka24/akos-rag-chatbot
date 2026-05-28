#!/bin/bash
# AKOS RAG Chatbot – namestitev in popravki
# Zaženi enkrat po kloniranju: bash setup.sh

set -e

echo ">>> Nameščam odvisnosti..."
pip install -r requirements.txt

echo ">>> Iščem nameščene pakete..."
SITE=$(python3 -c "import site; print(site.getsitepackages()[0])")
echo "    site-packages: $SITE"

# ── Popravek 1: chainlit/step.py – ContextVar brez defaulta ──────────────
STEP="$SITE/chainlit/step.py"
if [ -f "$STEP" ]; then
  sed -i.bak \
    's/local_steps\.get() or \[\]/local_steps.get([]) or []/g' \
    "$STEP"
  sed -i.bak \
    's/= local_steps\.get()$/= local_steps.get(None)/g' \
    "$STEP"
  echo "    [OK] chainlit/step.py popravljen"
else
  echo "    [!!] chainlit/step.py ni najden – preskoči"
fi

# ── Popravek 2: engineio/payload.py – max_decode_packets premajhen ────────
PAYLOAD="$SITE/engineio/payload.py"
if [ -f "$PAYLOAD" ]; then
  sed -i.bak \
    's/max_decode_packets = 16/max_decode_packets = 512/' \
    "$PAYLOAD"
  echo "    [OK] engineio/payload.py popravljen"
else
  echo "    [!!] engineio/payload.py ni najden – preskoči"
fi

# ── Popravek 3: engineio/async_socket.py – strict UTF-8 decode ───────────
ASOCK="$SITE/engineio/async_socket.py"
if [ -f "$ASOCK" ]; then
  sed -i.bak \
    "s/.decode('utf-8')/.decode('utf-8', errors='replace')/" \
    "$ASOCK"
  echo "    [OK] engineio/async_socket.py popravljen"
else
  echo "    [!!] engineio/async_socket.py ni najden – preskoči"
fi

echo ""
echo "============================================"
echo " Namestitev končana. Zagon:"
echo ""
echo "  Terminal 1:  uvicorn api:app --port 8000"
echo "  Terminal 2:  uvicorn app:app --port 7860"
echo "  Terminal 3:  chainlit run chainlit_app.py --port 8080"
echo ""
echo "  HTML UI:     http://localhost:7860"
echo "  Chainlit UI: http://localhost:8080"
echo "  API docs:    http://localhost:8000/docs"
echo "============================================"

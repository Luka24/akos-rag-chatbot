#!/bin/bash
# AKOS RAG Chatbot – namestitev in popravki
# Zaženi enkrat po kloniranju: bash setup.sh
set -e

echo ">>> Nameščam odvisnosti..."
pip install -r requirements.txt

# Najdi pravo lokacijo site-packages prek samega paketa (deluje vsepovsod)
echo ">>> Iščem lokacijo nameščenih paketov..."
SITE=$(python3 -c "
import chainlit, os, sys
# Chainlit ob uvozu izpiše konfig sporočila na stdout – jih preusmerimo
path = os.path.dirname(os.path.dirname(chainlit.__file__))
print(path)
" 2>/dev/null)
echo "    site-packages: $SITE"

patch_file() {
  local FILE="$1"
  local PATTERN="$2"
  local REPLACEMENT="$3"
  local DESC="$4"

  if [ ! -f "$FILE" ]; then
    echo "    [!!] $DESC – datoteka ne obstaja, preskoči"
    return
  fi
  if grep -q "$REPLACEMENT" "$FILE" 2>/dev/null; then
    echo "    [==] $DESC – že popravljen, preskoči"
    return
  fi
  sed -i.bak "s/$PATTERN/$REPLACEMENT/g" "$FILE"
  echo "    [OK] $DESC"
}

# ── Popravek 1a: chainlit/step.py – local_steps.get() or [] ──────────────
patch_file \
  "$SITE/chainlit/step.py" \
  "local_steps\\.get() or \\[\\]" \
  "local_steps.get([]) or []" \
  "chainlit/step.py (ContextVar default za liste)"

# ── Popravek 1b: chainlit/step.py – = local_steps.get() ──────────────────
# Posebej za vrstice kjer rezultat shranimo v spremenljivko
python3 - "$SITE/chainlit/step.py" <<'PYEOF'
import sys, re
path = sys.argv[1]
try:
    txt = open(path).read()
    if 'local_steps.get(None)' in txt:
        print("    [==] chainlit/step.py (ContextVar default za None) – že popravljen, preskoči")
    else:
        patched = re.sub(r'= local_steps\.get\(\)(\s*$)', r'= local_steps.get(None)\1', txt, flags=re.MULTILINE)
        open(path, 'w').write(patched)
        print("    [OK] chainlit/step.py (ContextVar default za None)")
except Exception as e:
    print(f"    [!!] chainlit/step.py – napaka: {e}")
PYEOF

# ── Popravek 2: engineio/payload.py – max_decode_packets ─────────────────
patch_file \
  "$SITE/engineio/payload.py" \
  "max_decode_packets = 16" \
  "max_decode_packets = 512" \
  "engineio/payload.py (max_decode_packets)"

# ── Popravek 3: engineio/async_socket.py – UTF-8 strict decode ───────────
patch_file \
  "$SITE/engineio/async_socket.py" \
  ".decode('utf-8')" \
  ".decode('utf-8', errors='replace')" \
  "engineio/async_socket.py (UTF-8 decode)"

echo ""
echo "============================================"
echo " Namestitev končana. Zagon v 3 terminalih:"
echo ""
echo "  Terminal 1:  uvicorn api:app --port 8000"
echo "  Terminal 2:  uvicorn app:app --port 7860"
echo "  Terminal 3:  chainlit run chainlit_app.py --port 8080"
echo ""
echo "  HTML UI:     http://localhost:7860"
echo "  Chainlit UI: http://localhost:8080"
echo "  API docs:    http://localhost:8000/docs"
echo "============================================"

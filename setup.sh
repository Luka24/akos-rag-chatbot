#!/bin/bash
# AKOS Asistent – namestitev (macOS / Linux)
# Zaženi enkrat po kloniranju: bash setup.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ">>> Nameščam odvisnosti iz requirements.txt..."
pip3 install -r "$ROOT/requirements.txt"

# Ustvari .env če še ne obstaja
ENV_FILE="$ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo ">>> Generiram CHAINLIT_AUTH_SECRET..."
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "CHAINLIT_AUTH_SECRET=$SECRET" > "$ENV_FILE"
    echo "    .env ustvarjen."
else
    echo "    .env že obstaja, preskočim."
fi

# Najdi site-packages
echo ">>> Iščem lokacijo nameščenih paketov..."
SITE=$(pip3 show chainlit 2>/dev/null | grep "^Location:" | cut -d' ' -f2)
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
  if grep -qF "$REPLACEMENT" "$FILE" 2>/dev/null; then
    echo "    [==] $DESC – že popravljen, preskoči"
    return
  fi
  sed -i.bak "s/$PATTERN/$REPLACEMENT/g" "$FILE"
  echo "    [OK] $DESC"
}

echo ">>> Preverjam in popravljam chainlit/engineio..."

patch_file \
  "$SITE/chainlit/step.py" \
  "local_steps\\.get() or \\[\\]" \
  "local_steps.get([]) or []" \
  "chainlit/step.py (ContextVar default za liste)"

python3 - "$SITE/chainlit/step.py" <<'PYEOF'
import sys, re
path = sys.argv[1]
try:
    txt = open(path).read()
    if 'local_steps.get(None)' in txt:
        print("    [==] chainlit/step.py (ContextVar None) – že popravljen, preskoči")
    else:
        patched = re.sub(r'= local_steps\.get\(\)(\s*$)', r'= local_steps.get(None)\1', txt, flags=re.MULTILINE)
        open(path, 'w').write(patched)
        print("    [OK] chainlit/step.py (ContextVar None)")
except Exception as e:
    print(f"    [!!] chainlit/step.py – napaka: {e}")
PYEOF

patch_file \
  "$SITE/engineio/payload.py" \
  "max_decode_packets = 16" \
  "max_decode_packets = 512" \
  "engineio/payload.py (max_decode_packets)"

patch_file \
  "$SITE/engineio/async_socket.py" \
  ".decode('utf-8')" \
  ".decode('utf-8', errors='replace')" \
  "engineio/async_socket.py (UTF-8 decode)"

echo ""
echo "============================================"
echo " Namestitev končana!"
echo ""
echo " Zagon v dveh terminalih:"
echo "   Terminal 1: python3 -m uvicorn api:app --port 8000"
echo "   Terminal 2: python3 -m chainlit run chainlit_app.py --port 8081"
echo ""
echo "   Aplikacija: http://localhost:8081"
echo "   API docs:   http://localhost:8000/docs"
echo "============================================"

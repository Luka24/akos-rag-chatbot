# AKOS RAG Chatbot - namestitev in popravki (Windows / PowerShell)
# Zazeni enkrat po kloniranju iz korenske mape projekta:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
#
# Predpostavke:
#   - Python 3.9+ je v PATH (preveri z: python --version)
#   - pip je dostopen kot "pip" ali "python -m pip"

$ErrorActionPreference = "Stop"

function Invoke-Pip {
    # Klice pip s podanimi argumenti. Uporabi "pip" ce je v PATH,
    # sicer pade nazaj na "python -m pip". Splatting prek @Args je varen
    # za en ali vec argumentov (za razliko od rocnega rezanja arrayja).
    param([Parameter(ValueFromRemainingArguments=$true)]$Args)
    if (Get-Command pip -ErrorAction SilentlyContinue) {
        & pip @Args
    } else {
        & python -m pip @Args
    }
}

Write-Host ">>> Namescam odvisnosti..." -ForegroundColor Cyan
Invoke-Pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install ni uspel" }

Write-Host ">>> Iscem lokacijo namescenih paketov..." -ForegroundColor Cyan
$showOutput = Invoke-Pip show chainlit
$locationLine = $showOutput | Where-Object { $_ -like "Location:*" } | Select-Object -First 1
if (-not $locationLine) { throw "Ne najdem chainlit paketa (pip show chainlit)" }
$Site = ($locationLine -replace "^Location:\s*", "").Trim()
Write-Host "    site-packages: $Site"

# Python skripta, ki opravi vse patche v eni potezi.
# Idempotentna: ce je popravek ze izveden, ga preskoci.
$patchScript = @'
import os, re, sys, io

site = sys.argv[1]

def edit(path, transforms, desc):
    if not os.path.isfile(path):
        print(f"    [!!] {desc} - datoteka ne obstaja, preskoci")
        return
    with io.open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    new = txt
    any_change = False
    for sentinel, fn in transforms:
        if sentinel in new:
            # ze popravljen
            continue
        new2 = fn(new)
        if new2 != new:
            new = new2
            any_change = True
    if any_change:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        print(f"    [OK] {desc}")
    else:
        print(f"    [==] {desc} - ze popravljen, preskoci")

# 1) chainlit/step.py: oba popravka za ContextVar default
step_py = os.path.join(site, "chainlit", "step.py")
edit(step_py, [
    # sentinel = string, ki je prisoten SAMO po patchu
    ("local_steps.get([]) or []",
        lambda s: s.replace("local_steps.get() or []", "local_steps.get([]) or []")),
    ("local_steps.get(None)",
        lambda s: re.sub(r"= local_steps\.get\(\)(\s*$)",
                          r"= local_steps.get(None)\1", s, flags=re.MULTILINE)),
], "chainlit/step.py (ContextVar default)")

# 2) engineio/payload.py: max_decode_packets
payload_py = os.path.join(site, "engineio", "payload.py")
edit(payload_py, [
    ("max_decode_packets = 512",
        lambda s: s.replace("max_decode_packets = 16",
                            "max_decode_packets = 512")),
], "engineio/payload.py (max_decode_packets)")

# 3) engineio/async_socket.py: UTF-8 strict decode
async_socket_py = os.path.join(site, "engineio", "async_socket.py")
edit(async_socket_py, [
    (".decode('utf-8', errors='replace')",
        lambda s: s.replace(".decode('utf-8')",
                            ".decode('utf-8', errors='replace')")),
], "engineio/async_socket.py (UTF-8 decode)")
'@

$tmpPy = Join-Path $env:TEMP "akos_patch.py"
Set-Content -Path $tmpPy -Value $patchScript -Encoding UTF8
python $tmpPy $Site
if ($LASTEXITCODE -ne 0) { throw "Patch skripta ni uspela" }
Remove-Item $tmpPy -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Namestitev koncana. Zagon v 3 terminalih:" -ForegroundColor Green
Write-Host ""
Write-Host "  Terminal 1:  uvicorn api:app --port 8000"
Write-Host "  Terminal 2:  uvicorn app:app --port 7860"
Write-Host "  Terminal 3:  chainlit run chainlit_app.py --port 8080"
Write-Host ""
Write-Host "  HTML UI:     http://localhost:7860"
Write-Host "  Chainlit UI: http://localhost:8080"
Write-Host "  API docs:    http://localhost:8000/docs"
Write-Host "============================================" -ForegroundColor Green

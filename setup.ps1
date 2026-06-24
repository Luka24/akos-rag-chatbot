# AKOS Asistent – namestitev (Windows / PowerShell)
# Zazeni enkrat po kloniranju:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
#
# Predpostavke:
#   - Python 3.9+ je v PATH (preveri: python --version)
#   - pip je dostopen

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition

function Invoke-Pip {
    param([Parameter(ValueFromRemainingArguments=$true)]$Args)
    if (Get-Command pip -ErrorAction SilentlyContinue) {
        & pip @Args
    } else {
        & python -m pip @Args
    }
}

# 1) Namesti odvisnosti
Write-Host ">>> Nameščam odvisnosti iz requirements.txt..." -ForegroundColor Cyan
Invoke-Pip install -r "$Root\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw "pip install ni uspel" }

# 2) Ustvari .env če še ne obstaja
$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envFile)) {
    Write-Host ">>> Generiram CHAINLIT_AUTH_SECRET..." -ForegroundColor Cyan
    $secret = & python -c "import secrets; print(secrets.token_hex(32))"
    Set-Content -Path $envFile -Value "CHAINLIT_AUTH_SECRET=$secret" -Encoding UTF8
    Write-Host "    .env ustvarjen." -ForegroundColor Green
} else {
    Write-Host "    .env že obstaja, preskočim." -ForegroundColor Yellow
}

# 3) Popravki chainlit/engineio (idempotentni)
Write-Host ">>> Preverjam in popravljam chainlit/engineio..." -ForegroundColor Cyan

$showOutput = Invoke-Pip show chainlit
$locationLine = $showOutput | Where-Object { $_ -like "Location:*" } | Select-Object -First 1
if (-not $locationLine) { throw "Ne najdem chainlit paketa (pip show chainlit)" }
$Site = ($locationLine -replace "^Location:\s*", "").Trim()
Write-Host "    site-packages: $Site"

$patchScript = @'
import os, re, sys, io

site = sys.argv[1]

def edit(path, transforms, desc):
    if not os.path.isfile(path):
        print(f"    [!!] {desc} - datoteka ne obstaja, preskoči")
        return
    with io.open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    new = txt
    any_change = False
    for sentinel, fn in transforms:
        if sentinel in new:
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
        print(f"    [==] {desc} - že popravljen, preskoči")

step_py = os.path.join(site, "chainlit", "step.py")
edit(step_py, [
    ("local_steps.get([]) or []",
        lambda s: s.replace("local_steps.get() or []", "local_steps.get([]) or []")),
    ("local_steps.get(None)",
        lambda s: re.sub(r"= local_steps\.get\(\)(\s*$)",
                          r"= local_steps.get(None)\1", s, flags=re.MULTILINE)),
], "chainlit/step.py (ContextVar default)")

payload_py = os.path.join(site, "engineio", "payload.py")
edit(payload_py, [
    ("max_decode_packets = 512",
        lambda s: s.replace("max_decode_packets = 16", "max_decode_packets = 512")),
], "engineio/payload.py (max_decode_packets)")

async_socket_py = os.path.join(site, "engineio", "async_socket.py")
edit(async_socket_py, [
    (".decode('utf-8', errors='replace')",
        lambda s: s.replace(".decode('utf-8')", ".decode('utf-8', errors='replace')")),
], "engineio/async_socket.py (UTF-8 decode)")
'@

$tmpPy = Join-Path $env:TEMP "akos_patch.py"
Set-Content -Path $tmpPy -Value $patchScript -Encoding UTF8
python $tmpPy $Site
if ($LASTEXITCODE -ne 0) { throw "Patch skripta ni uspela" }
Remove-Item $tmpPy -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Namestitev končana!" -ForegroundColor Green
Write-Host ""
Write-Host " Zagon: dvojni klik na run.bat"
Write-Host ""
Write-Host "   ali ročno v dveh terminalih:"
Write-Host "   Terminal 1: python -m uvicorn api:app --port 8000"
Write-Host "   Terminal 2: python -m chainlit run chainlit_app.py --port 8081"
Write-Host ""
Write-Host "   Aplikacija: http://localhost:8081"
Write-Host "   API docs:   http://localhost:8000/docs"
Write-Host "============================================" -ForegroundColor Green

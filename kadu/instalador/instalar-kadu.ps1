# ============================================================
#  Instalador do Kadu (Jarvis v2.8.0 modificado)
#  - Baixa o codigo-fonte do Jarvis v2.8.0
#  - Aplica os arquivos do Kadu (pasta "arquivos" ao lado deste script)
#  - Instala o Python 3.12 e as dependencias com o uv (nao precisa de nada instalado antes)
#  - Ajusta a configuracao: nome Kadu, variacoes do nome, Gemini (reaproveita sua chave)
#  - Cria o atalho "Kadu" na Area de Trabalho
#
#  Como rodar (PowerShell, dentro desta pasta):
#    powershell -ExecutionPolicy Bypass -File .\instalar-kadu.ps1
# ============================================================

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Info($m) { Write-Host "[kadu]  $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "[ ok ]  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[aviso] $m" -ForegroundColor Yellow }

$Setup     = Split-Path -Parent $MyInvocation.MyCommand.Path      # ...\GIT\kadu-setup
$Base      = Join-Path (Split-Path -Parent $Setup) 'kadu'          # ...\GIT\kadu
$App       = Join-Path $Base 'app'
$Tools     = Join-Path $Base 'ferramentas'
$CfgDir    = Join-Path $HOME '.config\jarvis'
$CfgFile   = Join-Path $CfgDir 'config.json'
$GeminiUrl = 'https://generativelanguage.googleapis.com/v1beta/openai'
$Versao    = 'v2.8.0'

if (-not (Test-Path (Join-Path $Setup 'arquivos\src\desktop_app\kadu_widget.py'))) {
    throw 'Nao achei a pasta "arquivos" ao lado deste script. Rode o instalador de dentro da pasta kadu-setup.'
}

# ---------- 0. Jarvis antigo aberto? ----------
$antigo = Get-Process -Name 'Jarvis' -ErrorAction SilentlyContinue
if ($antigo) {
    Warn 'O Jarvis antigo esta aberto. Os dois disputariam o microfone.'
    $r = Read-Host 'Posso fechar o Jarvis antigo agora? (S/N)'
    if ($r -match '^[sS]') { $antigo | Stop-Process -Force; Start-Sleep 2; Ok 'Jarvis antigo fechado.' }
    else { throw 'Feche o Jarvis (icone perto do relogio > Sair) e rode o instalador de novo.' }
}

# ---------- 0b. Kadu aberto? (o Python dele trava a pasta) ----------
$kaduAberto = Get-Process -Name 'python', 'pythonw' -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and $_.Path.StartsWith($Base, [System.StringComparison]::OrdinalIgnoreCase) }
if ($kaduAberto) {
    Info 'Fechando o Kadu que esta aberto para poder atualizar...'
    $kaduAberto | Stop-Process -Force
    Start-Sleep 3
    Ok 'Kadu fechado.'
}

New-Item $Base, $Tools -ItemType Directory -Force | Out-Null

# ---------- 1. Codigo-fonte do Jarvis ----------
Info "Baixando o codigo-fonte do Jarvis $Versao..."
$zip = Join-Path $env:TEMP "jarvis-$Versao.zip"
Invoke-WebRequest "https://github.com/isair/jarvis/archive/refs/tags/$Versao.zip" -OutFile $zip -Headers @{ 'User-Agent' = 'kadu-setup' }
$tmp = Join-Path $env:TEMP 'kadu-src'
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Expand-Archive $zip -DestinationPath $tmp -Force
Remove-Item $zip -Force
$src = Get-ChildItem $tmp -Directory | Select-Object -First 1
$venvAntigo = Join-Path $App '.venv'
$guardaVenv = Join-Path $Base '.venv-guardado'
if (Test-Path $venvAntigo) {                     # reinstalacao: mantem o Python ja baixado
    if (Test-Path $guardaVenv) { Remove-Item $guardaVenv -Recurse -Force }
    Move-Item $venvAntigo $guardaVenv
}
if (-not (Test-Path $guardaVenv)) { $guardaVenv = $null }   # sobra de uma tentativa anterior tambem e reaproveitada
if (Test-Path $App) { Remove-Item $App -Recurse -Force }
Move-Item $src.FullName $App
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
if ($guardaVenv) { Move-Item $guardaVenv $venvAntigo }
Ok "Codigo em $App"

# ---------- 2. Arquivos do Kadu ----------
Info 'Aplicando os arquivos do Kadu...'
$origem = Join-Path $Setup 'arquivos'
Get-ChildItem $origem -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($origem.Length + 1)
    $dest = Join-Path $App $rel
    New-Item (Split-Path $dest) -ItemType Directory -Force | Out-Null
    Copy-Item $_.FullName $dest -Force
    Write-Host "         $rel"
}
Copy-Item (Join-Path $Setup 'requisitos-windows.txt') (Join-Path $App 'requisitos-windows.txt') -Force
Ok 'Kadu aplicado.'

# ---------- 3. uv (instala o Python sozinho) ----------
$uv = Join-Path $Tools 'uv.exe'
if (-not (Test-Path $uv)) {
    Info 'Baixando o uv (gerenciador de Python)...'
    $uvZip = Join-Path $env:TEMP 'uv.zip'
    Invoke-WebRequest 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile $uvZip -Headers @{ 'User-Agent' = 'kadu-setup' }
    Expand-Archive $uvZip -DestinationPath $Tools -Force
    Remove-Item $uvZip -Force
}
Ok "uv pronto: $(& $uv --version)"

# ---------- 4. Python 3.12 + dependencias ----------
$py = Join-Path $App '.venv\Scripts\python.exe'
$pyw = Join-Path $App '.venv\Scripts\pythonw.exe'   # sem console: nenhum evento de console derruba o Kadu
if (-not (Test-Path $py)) {
    Info 'Criando o ambiente Python 3.12 (baixa o Python na primeira vez)...'
    & $uv venv --python 3.12 (Join-Path $App '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o ambiente Python.' }
}
Info 'Instalando as dependencias (primeira vez: uns 800 MB, pode levar de 5 a 15 minutos)...'
& $uv pip install --python $py -r (Join-Path $App 'requisitos-windows.txt')
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar as dependencias. Me mande um print desta tela.' }
Ok 'Dependencias instaladas.'

# ---------- 5. Configuracao ----------
New-Item $CfgDir -ItemType Directory -Force | Out-Null
$cfg = $null
if (Test-Path $CfgFile) {
    Copy-Item $CfgFile ("$CfgFile.bak-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    $cfg = Get-Content $CfgFile -Raw | ConvertFrom-Json
}
if ($null -eq $cfg) { $cfg = New-Object PSObject }
function Set-Cfg($nome, $valor) { $cfg | Add-Member -NotePropertyName $nome -NotePropertyValue $valor -Force }

if (-not $cfg.llm_api_key) {
    Write-Host 'Cole sua API Key do Google AI Studio e aperte Enter (nada aparece enquanto digita):' -ForegroundColor White
    $sec = Read-Host -AsSecureString
    $key = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)).Trim()
    if (-not $key) { throw 'Nenhuma chave informada.' }
    Set-Cfg 'llm_provider' 'openai_compatible'
    Set-Cfg 'llm_base_url' $GeminiUrl
    Set-Cfg 'llm_api_key' $key
    Set-Cfg 'embedding_provider' 'openai_compatible'
    Set-Cfg 'embedding_model' 'gemini-embedding-001'
    if (-not $cfg.llm_chat_model) { Set-Cfg 'llm_chat_model' 'gemini-3.6-flash' }
    if (-not $cfg.fast_model)     { Set-Cfg 'fast_model' 'gemini-3.5-flash-lite' }
} else {
    Ok 'Reaproveitando a chave e os modelos do Gemini que ja estavam configurados.'
}
Set-Cfg 'wake_word' 'kadu'
Set-Cfg 'wake_aliases' @('cadu', 'kadú', 'cadú', 'kado', 'cado', 'kaduu', 'cadum', 'kadum', 'catu', 'kahdu')
if (-not $cfg.whisper_model)  { Set-Cfg 'whisper_model' 'small' }
# Espera so 1,8 s de silencio depois da frase (o padrao de 4,5 s deixava a resposta lenta)
if (-not $cfg.voice_collect_seconds -or [double]$cfg.voice_collect_seconds -gt 2) { Set-Cfg 'voice_collect_seconds' 1.8 }
# Ajuste de velocidade (aplicado uma vez so; depois voce pode voltar para 'small' no config.json se preferir)
if (-not $cfg.kadu_ajuste_velocidade) {
    Set-Cfg 'whisper_model' 'base'
    Set-Cfg 'endpoint_silence_ms' 650
    Set-Cfg 'kadu_ajuste_velocidade' 1
    Ok 'Reconhecimento de voz ajustado para o modelo base (mais rapido).'
}
# Menos chamadas ao Gemini por pergunta = resposta mais rapida e menos erro 429 (limite do plano gratis).
# O planejador e o roteador de ferramentas por IA ajudam modelos pequenos; o Gemini nao precisa deles.
if (-not $cfg.kadu_ajuste_chamadas) {
    Set-Cfg 'planner_enabled' $false
    Set-Cfg 'tool_selection_strategy' 'keyword'
    Set-Cfg 'kadu_ajuste_chamadas' 1
    Ok 'Menos chamadas ao Gemini por pergunta (mais rapido, menos limite estourado).'
}
if (-not $cfg.whisper_device) { Set-Cfg 'whisper_device' 'cpu' }
if (-not $cfg.tts_piper_model_path) { Set-Cfg 'tts_piper_model_path' (Join-Path $HOME '.local\share\jarvis\models\piper\pt_BR-faber-medium.onnx') }
[IO.File]::WriteAllText($CfgFile, ($cfg | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding($false)))
Ok "Configuracao atualizada em $CfgFile"

# ---------- 6. Atalhos ----------
$vbs = Join-Path $Base 'Kadu.vbs'
$conteudoVbs = @"
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = "$App"
sh.Environment("Process")("PYTHONPATH") = "$App\src"
sh.Environment("Process")("PYTHONIOENCODING") = "utf-8"
sh.Environment("Process")("FOR_DISABLE_CONSOLE_CTRL_HANDLER") = "1"
sh.Run """$pyw"" -m desktop_app", 0, False
"@
[IO.File]::WriteAllText($vbs, $conteudoVbs, [Text.Encoding]::Default)

$cmd = Join-Path $Base 'Kadu (com log).cmd'
$conteudoCmd = @"
@echo off
cd /d "$App"
set "PYTHONPATH=$App\src"
set "PYTHONIOENCODING=utf-8"
set "FOR_DISABLE_CONSOLE_CTRL_HANDLER=1"
"$py" -m desktop_app
pause
"@
[IO.File]::WriteAllText($cmd, $conteudoCmd, [Text.Encoding]::Default)

try {
    $icone = Join-Path $App 'src\desktop_app\desktop_assets\icon_idle.ico'
    $ws = New-Object -ComObject WScript.Shell
    $lnk = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Kadu.lnk'))
    $lnk.TargetPath = "$env:WINDIR\System32\wscript.exe"
    $lnk.Arguments = "`"$vbs`""
    $lnk.WorkingDirectory = $App
    if (Test-Path $icone) { $lnk.IconLocation = $icone }
    $lnk.Save()
    Ok 'Atalho "Kadu" criado na Area de Trabalho.'
} catch { Warn "Nao consegui criar o atalho. Abra pelo arquivo $vbs" }

Write-Host ''
Ok 'Kadu instalado!'
Write-Host '  - Use o atalho "Kadu". Nao abra o Jarvis antigo junto (os dois usam o microfone).'
Write-Host '  - Chame falando: "Kadu, que horas sao?"'
Write-Host '  - Clique direito no Kadu: modo de conversa, tamanho, animacao, esconder.'
Write-Host "  - Se algo der errado, abra '$cmd' para ver o log e me mande um print."
Write-Host ''
$abrir = Read-Host 'Abrir o Kadu agora? (S/N)'
if ($abrir -match '^[sS]') { Start-Process "$env:WINDIR\System32\wscript.exe" -ArgumentList "`"$vbs`"" }

# Installe les dépendances et lance le suivi au démarrage de Windows.
# Utilisation : clic droit > "Exécuter avec PowerShell"
#   ou : powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

$python = (Get-Command py -ErrorAction SilentlyContinue).Source
if (-not $python) { $python = (Get-Command python -ErrorAction Stop).Source }

Write-Host "Création de l'environnement Python..."
& $python -m venv "$dir\.venv"
& "$dir\.venv\Scripts\python.exe" -m pip install --upgrade pip -q
& "$dir\.venv\Scripts\python.exe" -m pip install -r "$dir\requirements.txt" -q

if (-not (Test-Path "$dir\config.json")) {
    Copy-Item "$dir\config.example.json" "$dir\config.json"
    Write-Host "config.json créé : remplissez-le puis relancez install.ps1." -ForegroundColor Yellow
    notepad "$dir\config.json"
    exit
}

$startup = [Environment]::GetFolderPath("Startup")
$lnk = Join-Path $startup "Prog FFLogs.lnk"
$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnk)
$sc.TargetPath = "$dir\.venv\Scripts\pythonw.exe"
$sc.Arguments = "`"$dir\prog_tracker.py`""
$sc.WorkingDirectory = $dir
$sc.Description = "Suivi de progression FFLogs"
$sc.Save()
Write-Host "Raccourci de démarrage créé : $lnk" -ForegroundColor Green

Start-Process "$dir\.venv\Scripts\pythonw.exe" -ArgumentList "`"$dir\prog_tracker.py`"" -WorkingDirectory $dir
Write-Host "Suivi lancé (icône orange dans la barre des tâches)."

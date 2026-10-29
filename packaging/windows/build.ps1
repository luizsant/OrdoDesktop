# Gera dist\OrdoDesktop\ (PyInstaller) e o instalador dist\OrdoDesktop-<versão>-setup.exe (Inno Setup).
# Uso:  powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1 -Version 2.0.0
param([string]$Version = "0.0.0")
$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root
python packaging\windows\make_ico.py
pyinstaller --noconfirm --clean --windowed --name OrdoDesktop `
  --icon packaging\windows\ordo.ico `
  --add-data "ordo-desktop.svg;." `
  --paths . `
  packaging\windows\launcher.py
$env:ORDO_VERSION = $Version
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) { $iscc = "ISCC.exe" }
& $iscc packaging\windows\ordo.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup falhou" }
Get-ChildItem dist\*.exe

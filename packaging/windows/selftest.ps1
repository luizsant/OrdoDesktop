# Teste do Ordo numa máquina Windows de verdade (GitHub Actions): instala, abre, fotografa e desinstala.
# Resultados em selftest\ (capturas de tela, diagnóstico JSON e log).
$ErrorActionPreference = "Continue"
$out = New-Item -ItemType Directory -Force selftest
function Log($m) { $line = "$(Get-Date -Format HH:mm:ss) $m"; Write-Host $line; Add-Content "$out\log.txt" $line }
function Shot($file) {
  Add-Type -AssemblyName System.Windows.Forms, System.Drawing
  $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
  $bmp.Save($file); $g.Dispose(); $bmp.Dispose()
}

# 1. Área de trabalho de exemplo (arquivos fictícios)
$desk = [Environment]::GetFolderPath("Desktop")
Log "Área de Trabalho: $desk"
"Projetos", "Faturas 2026", "Clientes" | ForEach-Object { New-Item -ItemType Directory -Force "$desk\$_" | Out-Null }
"Contrato de prestação.pdf", "Relatório anual.pdf", "Proposta comercial.docx", "Anotações.txt",
  "Orçamento 2026.xlsx", "Vendas por mês.csv", "Apresentação Q4.pptx", "backup-fotos.zip" |
  ForEach-Object { Set-Content "$desk\$_" "exemplo" }
$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut("$desk\Bloco de Notas.lnk"); $lnk.TargetPath = "$env:WINDIR\System32\notepad.exe"; $lnk.Save()
Log "Itens criados: $((Get-ChildItem $desk -Force).Count)"

# 2. Instalação silenciosa
$setup = Get-ChildItem dist\OrdoDesktop-*-setup.exe | Select-Object -First 1
Log "Instalando $($setup.Name)"
Start-Process $setup.FullName -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=$out\install.log" -Wait
$exe = "$env:LOCALAPPDATA\Programs\OrdoDesktop\OrdoDesktop.exe"
Log "Instalado: $(Test-Path $exe)"

# 3. Um programa comum aberto: as caixas devem ficar atrás dele
Start-Process notepad.exe
Start-Sleep 2

# 4. Abre o Ordo com autoteste (ele mesmo fotografa a tela aos 25 s e fecha)
$env:ORDO_SELFTEST = "$((Resolve-Path $out).Path)\ordo-self.png;25"
$p = Start-Process $exe -PassThru
Start-Sleep 15
Shot "$out\tela-com-notepad.png"
Log "Captura externa feita (Ordo rodando há 15 s)"
# Win+D ("Mostrar área de trabalho"): as caixas devem continuar visíveis
$shell = New-Object -ComObject Shell.Application
$shell.MinimizeAll()
Start-Sleep 3
Shot "$out\tela-mostrar-area-de-trabalho.png"
Log "Captura após minimizar tudo"
$p.WaitForExit(30000) | Out-Null
Log "Ordo fechou sozinho após o autoteste: $($p.HasExited)"
$env:ORDO_SELFTEST = ""
$run = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue).OrdoDesktop
Log "Iniciar com o Windows (registro): $run"

# 5. Fechamento seguro pelo --quit
$p2 = Start-Process $exe -PassThru
Start-Sleep 8
Start-Process $exe -ArgumentList "--quit" -Wait
Start-Sleep 2
Log "--quit fechou a instância: $($p2.HasExited)"

# 6. Desinstalação silenciosa
$p3 = Start-Process $exe -PassThru
Start-Sleep 8
$unins = "$env:LOCALAPPDATA\Programs\OrdoDesktop\unins000.exe"
Start-Process $unins -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES" -Wait
# o desinstalador do Inno continua num processo temporário depois que este retorna
for ($i = 0; $i -lt 30 -and (Test-Path $exe); $i++) { Start-Sleep 1 }
Log "Desinstalador fechou o Ordo: $($p3.HasExited)"
Log "Arquivos removidos: $(-not (Test-Path $exe))"
$run = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -ErrorAction SilentlyContinue).OrdoDesktop
Log "Registro de início removido: $(-not $run)"
Copy-Item "$env:APPDATA\OrdoDesktop\config.json" "$out\config.json" -ErrorAction SilentlyContinue
Copy-Item "$env:APPDATA\OrdoDesktop\ordo-error.log" "$out\ordo-error.log" -ErrorAction SilentlyContinue

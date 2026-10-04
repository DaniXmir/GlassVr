#to build use:
#powershell -ExecutionPolicy Bypass -File .\build.ps1

$ErrorActionPreference = "Stop"
$name = "GlassVR"
$out  = "dist\$name"

pyinstaller --noconfirm --clean --windowed --name $name `
  --icon "assets/;Prism.ico" `
  --collect-all sdl3 --collect-all openvr --collect-all mediapipe --collect-all cv2 `
  --hidden-import settings --hidden-import globals --hidden-import elements `
  --hidden-import controller_handler --hidden-import steamvr --hidden-import udp_relay `
  --hidden-import playspace --hidden-import mirroring --hidden-import mode_manager `
  --hidden-import mode_registry --hidden-import sdl_display --hidden-import sender `
  --hidden-import win32file --hidden-import win32pipe --hidden-import pywintypes `
  --hidden-import win32gui --hidden-import win32ui --hidden-import win32con --hidden-import win32api `
  --hidden-import flask --hidden-import screeninfo --hidden-import psutil --hidden-import pygame `
  main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

if (Test-Path "$out\plugins") { Remove-Item -Recurse -Force "$out\plugins" }
robocopy plugins "$out\plugins" /E /XD __pycache__ libs /NFL /NDL /NJH /NJS | Out-Null

$pyiDir = Split-Path (Get-Command pyinstaller).Source -Parent
$python = Join-Path (Split-Path $pyiDir -Parent) "python.exe"
if (-not (Test-Path $python)) { $python = Join-Path $pyiDir "python.exe" }
Write-Host "Using Python: $python"

Get-ChildItem "$out\plugins" -Recurse -Filter requirements.txt | ForEach-Object {
    $file = $_
    try {
        $manifest = Get-Content $file.FullName -Raw | ConvertFrom-Json
    } catch {
        throw "Invalid JSON in $($file.FullName): $_"
    }

    $packages = @($manifest.pip)
    if ($packages.Count -eq 0) { return }

    $libs = Join-Path $file.DirectoryName "libs"
    Write-Host "Installing libs for $($file.DirectoryName): $($packages -join ', ')"
    & $python -m pip install @packages --target $libs --no-deps --upgrade
    if ($LASTEXITCODE -ne 0) { throw "pip failed for $($file.FullName)" }
}

if (Test-Path assets) { Copy-Item -Recurse -Force assets "$out\assets" }

Write-Host "Done: $out\$name.exe"
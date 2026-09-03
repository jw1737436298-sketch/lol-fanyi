@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0lol_translator_overlay.ps1"
if errorlevel 1 (
  echo.
  echo Failed to start LOL Translator.
  pause
)

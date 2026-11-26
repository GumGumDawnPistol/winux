@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0test-qemu.ps1" -ForceTCG
if errorlevel 1 pause

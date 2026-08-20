@echo off
REM Double-click or run from cmd after starting XAMPP MySQL
cd /d "%~dp0.."
powershell -ExecutionPolicy Bypass -File "scripts\start_jofa.ps1" %*

@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PATH=C:\Users\zahih\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin;%PATH%"

REM Windows Task Scheduler catches up multiple missed triggers at once when the
REM laptop wakes from sleep - without a lock, several AETHER runs can launch in
REM the same second and collide (Ollama port, temp files, etc). mkdir is atomic
REM across processes on Windows, so it doubles as a cross-process lock.
set "LOCKDIR=%~dp0.aether_lock"
set /a WAITED=0
:waitloop
mkdir "%LOCKDIR%" 2>nul
if errorlevel 1 (
    if !WAITED! GEQ 1500 (
        echo %date% %time% - gave up waiting for lock after 25 minutes >> "%~dp0auto_publish_task.log"
        exit /b 1
    )
    timeout /t 30 /nobreak >nul
    set /a WAITED+=30
    goto waitloop
)

REM make sure the local Ollama server is up (harmless if already running)
tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe" >nul
if errorlevel 1 (
    start "" /min "C:\Users\zahih\AppData\Local\Programs\Ollama\ollama.exe" serve
    timeout /t 8 /nobreak >nul
)

"%~dp0venv\Scripts\python.exe" "%~dp0auto_publish.py" >> "%~dp0auto_publish_task.log" 2>&1

rmdir "%LOCKDIR%"

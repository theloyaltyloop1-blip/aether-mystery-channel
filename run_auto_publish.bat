@echo off
setlocal
cd /d "%~dp0"

set "PATH=C:\Users\zahih\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin;%PATH%"

REM make sure the local Ollama server is up (harmless if already running)
tasklist /FI "IMAGENAME eq ollama.exe" | find /I "ollama.exe" >nul
if errorlevel 1 (
    start "" /min "C:\Users\zahih\AppData\Local\Programs\Ollama\ollama.exe" serve
    timeout /t 8 /nobreak >nul
)

"%~dp0venv\Scripts\python.exe" "%~dp0auto_publish.py" >> "%~dp0auto_publish_task.log" 2>&1

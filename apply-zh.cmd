@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title SoundShredder zh-CN patch

set "SELF=%~dp0"
set "PY="
set "HOME_DIR="

rem --- 1. read the storage folder that SoundShredder remembers ---
if exist "%LOCALAPPDATA%\SoundShredder\desktop-storage.json" (
  for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try{(Get-Content -LiteralPath '%LOCALAPPDATA%\SoundShredder\desktop-storage.json' -Raw | ConvertFrom-Json).home}catch{''}"`) do set "HOME_DIR=%%H"
)

rem --- 2. prefer the Python that ships with SoundShredder ---
if defined HOME_DIR (
  if exist "!HOME_DIR!\runtimes\py313-cuda\python.exe" set "PY=!HOME_DIR!\runtimes\py313-cuda\python.exe"
  if not defined PY if exist "!HOME_DIR!\app\resources\backend\python\python.exe" set "PY=!HOME_DIR!\app\resources\backend\python\python.exe"
)
if not defined PY if exist "%LOCALAPPDATA%\Programs\SoundShredder\resources\backend\python\python.exe" set "PY=%LOCALAPPDATA%\Programs\SoundShredder\resources\backend\python\python.exe"

rem --- 3. last resort: system Python ---
if not defined PY (
  where python >nul 2>nul
  if not errorlevel 1 set "PY=python"
)

if not defined PY (
  echo.
  echo   Python could not be found automatically.
  echo   If you have Python installed, run this instead:
  echo       python apply_zh.py
  echo   Or point it at the install folder:
  echo       python apply_zh.py --app "D:\SoundShredder"
  echo.
  pause
  exit /b 1
)

echo.
"%PY%" -B "%SELF%apply_zh.py" %*
set "CODE=%ERRORLEVEL%"
echo.
if "%CODE%"=="0" echo   Done. Restart SoundShredder to see the Chinese interface.
if "%~1"=="" pause
exit /b %CODE%

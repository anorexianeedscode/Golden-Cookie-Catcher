@echo off
chcp 65001 >nul
setlocal
python -m pip install --upgrade --quiet pyinstaller pillow
python -m pip install --quiet -r requirements.txt
python tools\prepare_assets.py

if not exist icon.ico (
  echo ! icon.ico не создан — положи assets\icon_src.png
  pause & exit /b 1
)
if not exist assets\golden_cookie.png (
  echo ! спрайт не создан
  pause & exit /b 1
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm build.spec
echo.
echo Готово: dist\GoldenCookieCatcher.exe
pause
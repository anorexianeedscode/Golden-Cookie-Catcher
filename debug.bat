@echo off
chcp 65001 >nul
python -c "import app; print('module ok'); app.main(); print('main returned')"
echo.
echo exit=%ERRORLEVEL%
pause
@echo off
title Building Sort.exe...

echo Cleaning old builds...
rmdir /s /q build >nul 2>&1
rmdir /s /q dist >nul 2>&1

echo.
echo Installing dependencies...
pip install --quiet pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --icon=sort.ico --add-data "sort.ico;." Sort.py

echo.
echo Build complete!
echo Output file: dist\Sort.exe

pause

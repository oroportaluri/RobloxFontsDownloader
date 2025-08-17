@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --onefile --windowed --name RobloxFontsDownloader --add-data "config.json;." main.py

echo.
echo Build complete! Check the dist folder for RobloxFontsDownloader.exe
pause

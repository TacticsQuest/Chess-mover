@echo off
cd /d "%~dp0"
echo.
echo ============================================================
echo   CHESS MOVER MACHINE - 7" TOUCHSCREEN MODE v1.3.0
echo ============================================================
echo   Window Size: 1024x600 (simulates 7" touchscreen)
echo   Features:
echo   - Maximized board (728x728 - edge to edge)
echo   - Compact piece palette (272 width, 38px buttons)
echo   - Profile selector in right panel
echo   - No title text, theme toggle, or AI Training tab
echo   - Logs button in toolbar
echo ============================================================
echo.
python launch_compact.py
echo.
pause

@echo off
echo ===================================================
echo     Compiling IDEO to Standalone Executable (.exe)
echo ===================================================

cd /d "C:\Users\atiff\CoDev\WORKSPACE\ideo"

"C:\Users\atiff\AppData\Local\Programs\Python\Python314\python.exe" -m PyInstaller ^
    --noconsole ^
    --onefile ^
    --name="IDEO" ^
    --icon="assets\icon_dark.ico" ^
    --add-data="assets;assets" ^
    --hidden-import="customtkinter" ^
    --hidden-import="pystray" ^
    --hidden-import="PIL" ^
    --hidden-import="astral" ^
    --hidden-import="apscheduler" ^
    --hidden-import="sqlalchemy" ^
    main.py

echo.
echo Build completed! Executable is located in C:\Users\atiff\CoDev\WORKSPACE\ideo\dist\IDEO.exe
pause

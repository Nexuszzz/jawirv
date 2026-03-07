@echo off
REM JAWIR OS - KiCad Schematic Generator
REM =====================================
REM Usage: jawir-kicad "deskripsi rangkaian"
REM        jawir-kicad -i  (interactive mode)

cd /d D:\jawirv2\jawirv2\backend
call venv\Scripts\activate.bat
cd tools\kicad

if "%~1"=="" (
    python kicad_cli.py -i
) else (
    python kicad_cli.py %*
)

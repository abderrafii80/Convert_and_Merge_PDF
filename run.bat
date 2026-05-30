@echo off
cd /d "%~dp0"
pyw -3 "%~dp0main.py"
if errorlevel 1 pythonw "%~dp0main.py"
exit
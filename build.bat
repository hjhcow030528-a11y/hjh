@echo off
REM Build a standalone Windows executable for defect_detect.py
REM Produces: dist\defect_detect.exe (single file, no console-less so stdout is visible)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --name defect_detect ^
    --hidden-import tkinter ^
    --collect-submodules cv2 ^
    defect_detect.py

echo.
echo ===============================================
echo  Build finished.  Executable:  dist\defect_detect.exe
echo ===============================================

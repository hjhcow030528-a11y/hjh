@echo off
REM Build a standalone Windows executable for defect_detect.py and
REM copy it to the current user's Documents folder.

setlocal

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

if not exist "dist\defect_detect.exe" (
    echo.
    echo [ERROR] Build failed: dist\defect_detect.exe not found.
    exit /b 1
)

REM Resolve Documents folder (handles OneDrive redirection via USERPROFILE)
set "DOCS=%USERPROFILE%\Documents"
if not exist "%DOCS%" mkdir "%DOCS%"

copy /Y "dist\defect_detect.exe" "%DOCS%\defect_detect.exe" >nul

echo.
echo ===============================================
echo  Build finished.
echo  Executable copied to: %DOCS%\defect_detect.exe
echo ===============================================

endlocal

@echo off
REM Build a standalone Windows executable for parquet_to_csv.py and
REM copy it to the current user's Documents folder.

setlocal

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller ^
    --noconfirm ^
    --onefile ^
    --name parquet_to_csv ^
    --hidden-import tkinter ^
    --collect-submodules pyarrow ^
    --collect-submodules pandas ^
    parquet_to_csv.py

if not exist "dist\parquet_to_csv.exe" (
    echo.
    echo [ERROR] Build failed: dist\parquet_to_csv.exe not found.
    exit /b 1
)

REM Resolve Documents folder (handles OneDrive redirection via USERPROFILE)
set "DOCS=%USERPROFILE%\Documents"
if not exist "%DOCS%" mkdir "%DOCS%"

copy /Y "dist\parquet_to_csv.exe" "%DOCS%\parquet_to_csv.exe" >nul

echo.
echo ===============================================
echo  Build finished.
echo  Executable copied to: %DOCS%\parquet_to_csv.exe
echo ===============================================

endlocal

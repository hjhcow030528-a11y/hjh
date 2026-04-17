#!/usr/bin/env bash
# Build a standalone executable for defect_detect.py on Linux / macOS.
# Produces: dist/defect_detect

set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

pyinstaller \
    --noconfirm \
    --onefile \
    --name defect_detect \
    --hidden-import tkinter \
    --collect-submodules cv2 \
    defect_detect.py

echo
echo "==============================================="
echo " Build finished.  Executable: dist/defect_detect"
echo "==============================================="

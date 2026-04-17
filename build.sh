#!/usr/bin/env bash
# Build a standalone executable for defect_detect.py on Linux / macOS
# and copy it to the current user's Documents folder.

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

if [[ ! -f "dist/defect_detect" ]]; then
    echo "[ERROR] Build failed: dist/defect_detect not found." >&2
    exit 1
fi

DOCS="${HOME}/Documents"
mkdir -p "${DOCS}"
cp -f "dist/defect_detect" "${DOCS}/defect_detect"
chmod +x "${DOCS}/defect_detect"

echo
echo "==============================================="
echo " Build finished."
echo " Executable copied to: ${DOCS}/defect_detect"
echo "==============================================="

#!/usr/bin/env bash
# Build a standalone executable for parquet_to_csv.py on Linux / macOS
# and copy it to the current user's Documents folder.

set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

pyinstaller \
    --noconfirm \
    --onefile \
    --name parquet_to_csv \
    --hidden-import tkinter \
    --collect-submodules pyarrow \
    --collect-submodules pandas \
    parquet_to_csv.py

if [[ ! -f "dist/parquet_to_csv" ]]; then
    echo "[ERROR] Build failed: dist/parquet_to_csv not found." >&2
    exit 1
fi

DOCS="${HOME}/Documents"
mkdir -p "${DOCS}"
cp -f "dist/parquet_to_csv" "${DOCS}/parquet_to_csv"
chmod +x "${DOCS}/parquet_to_csv"

echo
echo "==============================================="
echo " Build finished."
echo " Executable copied to: ${DOCS}/parquet_to_csv"
echo "==============================================="

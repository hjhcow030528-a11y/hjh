#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parquet to CSV batch converter (single-file executable).

Workflow:
  1) Pick the source folder (searched recursively) and the output folder.
  2) Every *.parquet file found under the source folder is read and
     written out as a UTF-8 CSV file in the output folder, preserving the
     relative sub-directory layout so filenames never collide.

Run:
    python parquet_to_csv.py
"""

import os
import sys
import traceback
from pathlib import Path

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox


PARQUET_EXT = ".parquet"


def pick_folder(title: str) -> str:
    return filedialog.askdirectory(title=title)


def find_parquet_files(folder: Path):
    return sorted(
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() == PARQUET_EXT
    )


def csv_stem_from(src: Path) -> str:
    """Derive the CSV filename stem from a parquet filename.

    Rule: take the substring after the last '_' in the original stem. If
    the stem contains no '_' (or the tail would be empty), use the full
    stem unchanged.

    Examples:
        'data_20240101_part1.parquet' -> 'part1'
        'report_final.parquet'        -> 'final'
        'plain.parquet'               -> 'plain'
    """
    stem = src.stem
    _, sep, tail = stem.rpartition("_")
    return tail if sep and tail else stem


def convert_one(src: Path, src_root: Path, dst_root: Path) -> Path:
    """Read a parquet file and write it as CSV under dst_root.

    The relative directory structure under src_root is mirrored under
    dst_root, and the CSV filename is derived via `csv_stem_from`.
    """
    rel = src.relative_to(src_root)
    out_path = dst_root / rel.with_name(csv_stem_from(src) + ".csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(src)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path


def main():
    root = tk.Tk()
    root.withdraw()

    src_dir = pick_folder("Select source folder (will be searched recursively for *.parquet)")
    if not src_dir:
        print("No source folder selected. Exiting.")
        return

    dst_dir = pick_folder("Select output folder for CSV files")
    if not dst_dir:
        print("No output folder selected. Exiting.")
        return

    src_root = Path(src_dir).resolve()
    dst_root = Path(dst_dir).resolve()

    if dst_root == src_root or src_root in dst_root.parents:
        messagebox.showwarning(
            "Folder choice",
            "Output folder is the same as or inside the source folder.\n"
            "CSV files will still be written, but be careful not to re-run "
            "against the same tree repeatedly.")

    dst_root.mkdir(parents=True, exist_ok=True)

    files = find_parquet_files(src_root)
    if not files:
        messagebox.showerror("Error", f"No *.parquet files found under:\n{src_root}")
        return

    print(f"\nSource : {src_root}")
    print(f"Output : {dst_root}")
    print(f"Found  : {len(files)} parquet file(s)\n")

    ok = 0
    failed = []
    for i, src in enumerate(files, 1):
        rel = src.relative_to(src_root)
        try:
            out_path = convert_one(src, src_root, dst_root)
            ok += 1
            print(f"  [{i}/{len(files)}] OK    {rel}  ->  {out_path.relative_to(dst_root)}")
        except Exception as e:
            failed.append((rel, str(e)))
            print(f"  [{i}/{len(files)}] FAIL  {rel}  ({e})")
            traceback.print_exc()

    summary = (
        f"Converted: {ok} / {len(files)}\n"
        f"Failed   : {len(failed)}\n\n"
        f"Source : {src_root}\n"
        f"Output : {dst_root}"
    )
    print("\n" + summary)

    if failed:
        details = "\n".join(f"- {p}: {msg}" for p, msg in failed[:20])
        more = "" if len(failed) <= 20 else f"\n... and {len(failed) - 20} more"
        messagebox.showwarning("Finished with errors", summary + "\n\n" + details + more)
    else:
        messagebox.showinfo("Finished", summary)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        try:
            tk.Tk().withdraw()
            messagebox.showerror("Unexpected error", f"{type(e).__name__}: {e}")
        except Exception:
            pass
        sys.exit(1)

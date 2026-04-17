#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defect detection program (single-file executable).

Workflow:
  1) Pick the input image folder and the output (result) folder.
  2) Load the first image, draw an ROI with the mouse, press ENTER/SPACE to
     confirm, or press ESC / click Cancel to re-select the ROI.
  3) Process every image in the input folder with the same ROI, detect
     defects inside the ROI, and list up the defect sizes (pixel area).
     Per-image visualizations and a summary CSV are written to the output
     folder.

Run:
    python defect_detect.py
"""

import csv
import os
from pathlib import Path

import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox


IMAGE_EXTS = {".bmp", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
MIN_DEFECT_AREA = 20  # px, noise floor for a defect blob


# ---------- folder / file utilities ----------

def pick_folder(title: str) -> str:
    return filedialog.askdirectory(title=title)


def list_images(folder: str):
    return sorted(
        p for p in Path(folder).iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


# ---------- ROI selection ----------

def select_roi(image):
    """Interactive ROI selection with confirm / cancel-retry loop.

    Returns (x, y, w, h) on confirm, or None if the user aborts.
    """
    win = "Draw ROI  |  ENTER/SPACE = confirm,  ESC = cancel"
    while True:
        roi = cv2.selectROI(win, image, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow(win)
        cv2.waitKey(1)
        x, y, w, h = map(int, roi)

        if w == 0 or h == 0:
            if messagebox.askretrycancel(
                    "ROI",
                    "ROI was not drawn.\nRetry to draw again, or Cancel to abort."):
                continue
            return None

        if messagebox.askokcancel(
                "Confirm ROI",
                f"Use this ROI?\n\nx={x}, y={y}, w={w}, h={h}\n\n"
                f"OK = confirm,   Cancel = draw again"):
            return x, y, w, h
        # otherwise loop and re-draw


# ---------- defect detection ----------

def detect_defects(roi_bgr):
    """Detect defects inside an ROI crop.

    Strategy: Otsu-threshold the part, take the largest connected component,
    and treat the concavities (convex hull minus the part) as candidate
    defects. Small noise blobs are discarded.

    Returns (defects, vis) where `defects` is a list of dicts with keys
    `area`, `bbox`, `width`, `height`, and `vis` is an annotated BGR image.
    """
    if roi_bgr.ndim == 3:
        gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
        vis = roi_bgr.copy()
    else:
        gray = roi_bgr.copy()
        vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, binary = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    num, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num <= 1:
        return [], vis

    areas = stats[1:, cv2.CC_STAT_AREA]
    main_label = 1 + int(np.argmax(areas))
    mask = (labels == main_label).astype(np.uint8) * 255

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return [], vis
    cnt = max(contours, key=cv2.contourArea)

    filled = np.zeros_like(mask)
    cv2.drawContours(filled, [cnt], -1, 255, thickness=cv2.FILLED)

    hull = cv2.convexHull(cnt)
    hull_mask = np.zeros_like(mask)
    cv2.drawContours(hull_mask, [hull], -1, 255, thickness=cv2.FILLED)

    defect_mask = cv2.subtract(hull_mask, filled)
    kernel = np.ones((3, 3), np.uint8)
    defect_mask = cv2.morphologyEx(defect_mask, cv2.MORPH_OPEN, kernel)

    defect_contours, _ = cv2.findContours(
        defect_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    defects = []
    for dc in defect_contours:
        area = float(cv2.contourArea(dc))
        if area < MIN_DEFECT_AREA:
            continue
        x, y, w, h = cv2.boundingRect(dc)
        defects.append({
            "area": area,
            "bbox": (int(x), int(y), int(w), int(h)),
            "width": int(w),
            "height": int(h),
        })
        cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(vis, f"{int(area)}px", (x, max(0, y - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1,
                    cv2.LINE_AA)

    return defects, vis


# ---------- main ----------

def main():
    root = tk.Tk()
    root.withdraw()

    input_dir = pick_folder("Select folder containing input images")
    if not input_dir:
        print("No input folder selected. Exiting.")
        return

    output_dir = pick_folder("Select folder for results (images + CSV)")
    if not output_dir:
        print("No output folder selected. Exiting.")
        return
    os.makedirs(output_dir, exist_ok=True)

    images = list_images(input_dir)
    if not images:
        messagebox.showerror("Error", f"No images found in:\n{input_dir}")
        return

    first = cv2.imread(str(images[0]))
    if first is None:
        messagebox.showerror("Error", f"Cannot read first image:\n{images[0]}")
        return

    roi = select_roi(first)
    if roi is None:
        print("ROI selection aborted.")
        return
    rx, ry, rw, rh = roi

    csv_path = os.path.join(output_dir, "defects.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename", "result", "defect_count",
            "total_area_px", "max_area_px",
            "defect_sizes_px (area;w;h)",
        ])

        print(f"\nROI: x={rx} y={ry} w={rw} h={rh}")
        print(f"Processing {len(images)} image(s)...\n")

        for img_path in images:
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"  [skip] cannot read {img_path.name}")
                continue

            H, W = img.shape[:2]
            x2 = min(rx + rw, W)
            y2 = min(ry + rh, H)
            if rx >= W or ry >= H or x2 <= rx or y2 <= ry:
                print(f"  [skip] ROI out of bounds for {img_path.name}")
                continue

            roi_img = img[ry:y2, rx:x2]
            defects, vis = detect_defects(roi_img)

            out_vis = img.copy()
            out_vis[ry:y2, rx:x2] = vis
            cv2.rectangle(out_vis, (rx, ry), (x2, y2), (0, 255, 0), 2)

            status = "DEFECT" if defects else "OK"
            label = f"{status}  n={len(defects)}"
            color = (0, 0, 255) if defects else (0, 200, 0)
            cv2.putText(out_vis, label, (rx, max(20, ry - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)

            out_path = os.path.join(output_dir, f"{img_path.stem}_result.png")
            cv2.imwrite(out_path, out_vis)

            sizes = [(round(d["area"], 1), d["width"], d["height"]) for d in defects]
            total = sum(d["area"] for d in defects)
            max_a = max((d["area"] for d in defects), default=0.0)

            writer.writerow([
                img_path.name, status, len(defects),
                round(total, 1), round(max_a, 1),
                ";".join(f"{a}:{w}x{h}" for a, w, h in sizes),
            ])

            print(f"  {img_path.name:<40s} {status:<7s} "
                  f"count={len(defects):<3d} total={total:>7.1f}px  "
                  f"sizes={sizes}")

    print(f"\nDone.\n  CSV:    {csv_path}\n  Images: {output_dir}")
    messagebox.showinfo(
        "Finished",
        f"Processed {len(images)} image(s).\n\n"
        f"CSV:    {csv_path}\nImages: {output_dir}")


if __name__ == "__main__":
    main()

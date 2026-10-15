#!/usr/bin/env python3
"""
Prepare the avatar photo (assets/avatar-dog.jpg) for clean, high-contrast ASCII conversion:
  1. Remove background with rembg (+ GrabCut foreground isolation of puppy & keyboard)
  2. OpenCV CLAHE contrast boost to bring out facial features, eyes, and keyboard details
  3. Dark-line and feature enhancement (difference of Gaussians) so contours remain sharp
  4. Composite on pure white background
  5. Tight crop and export as grayscale PNG

Usage:
    python scripts/prep_photo.py [input.jpg] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
import rembg

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "assets", "avatar-dog.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")


def prep(input_path, output_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    img_bgr = cv2.imread(input_path)
    if img_bgr is None:
        raise ValueError(f"Could not read image: {input_path}")

    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 1. GrabCut to isolate the puppy and keyboard from the circular graphic background
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    
    # Bounding box around dog and keyboard (approx center region)
    rect = (int(w * 0.20), int(h * 0.20), int(w * 0.60), int(h * 0.68))
    cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
    gc_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype(np.uint8)

    # rembg background refinement
    try:
        # Use u2net or u2netp if available
        session = rembg.new_session("u2net")
        raw_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        rembg_cut = rembg.remove(raw_pil, session=session)
        rembg_alpha = np.array(rembg_cut.split()[-1])
        alpha = cv2.bitwise_and(rembg_alpha, gc_mask)
    except Exception as e:
        print(f"rembg notice: {e}, falling back to GrabCut mask", file=sys.stderr)
        alpha = gc_mask

    # Feather mask slightly for clean antialiasing
    alpha_smooth = cv2.GaussianBlur(alpha, (3, 3), 0).astype(np.float32) / 255.0

    # 2. OpenCV CLAHE contrast boost
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    cl = clahe.apply(gray)

    # 3. Enhance contours and dark lines (Difference of Gaussians)
    fine = cv2.GaussianBlur(cl, (0, 0), 1.0).astype(np.float32)
    coarse = cv2.GaussianBlur(cl, (0, 0), 4.0).astype(np.float32)
    edges = np.clip(coarse - fine, 0, 255)
    enhanced = np.clip(cl.astype(np.float32) - 0.5 * edges, 0, 255)

    # 4. Composite onto pure white background (255)
    comp = (enhanced * alpha_smooth + 255.0 * (1.0 - alpha_smooth)).astype(np.uint8)

    # 5. Crop tightly around the subject with slight margin
    ys, xs = np.where(alpha > 20)
    if len(ys) > 0 and len(xs) > 0:
        pad = 16
        ymin, ymax = max(0, ys.min() - pad), min(h, ys.max() + pad)
        xmin, xmax = max(0, xs.min() - pad), min(w, xs.max() + pad)
        cropped = comp[ymin:ymax, xmin:xmax]
    else:
        cropped = comp

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cv2.imwrite(output_path, cropped)
    print(f"prepped image saved to {output_path} ({cropped.shape[1]}x{cropped.shape[0]})")


if __name__ == "__main__":
    prep(INP, OUT)

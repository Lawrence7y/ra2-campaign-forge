import os
import glob
from PIL import Image
import numpy as np

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
png_files = sorted(glob.glob(os.path.join(BASE_DIR, "*", "measure_w*_end_x.png")))

# Let's inspect regions:
# TITLE: (600, 0, 800, 60)
# TIMER: (400, 100, 700, 160)
# PANEL: (85, 108, 630, 275)

print("Inspecting pixel characteristics for all 25 images...")
for idx, p in enumerate(png_files):
    rel = os.path.relpath(p, BASE_DIR)
    im = Image.open(p).convert("RGB")
    arr = np.array(im)
    
    # 1. Title region (approx x: 600-790, y: 10-50)
    title_crop = arr[10:50, 600:790]
    # In skirmish score screen, title is bright yellow/gold or white text on dark blue background
    # 2. Panel region (approx x: 85-630, y: 108-275)
    panel_crop = arr[108:275, 85:630]
    r, g, b = panel_crop[:, :, 0], panel_crop[:, :, 1], panel_crop[:, :, 2]
    # Blue-purple mask: b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150
    bp_mask = (b > r + 18) & (b > g + 10) & (b >= 40) & (b <= 190) & (r < 150)
    bp_ratio = np.mean(bp_mask)
    
    # 3. Overall brightness / darkness
    mean_rgb = np.mean(arr, axis=(0, 1))
    
    print(f"[{idx:02d}] {rel:35s} | shape={arr.shape} | mean_rgb=({mean_rgb[0]:.1f},{mean_rgb[1]:.1f},{mean_rgb[2]:.1f}) | panel_bp_ratio={bp_ratio:.4f}")

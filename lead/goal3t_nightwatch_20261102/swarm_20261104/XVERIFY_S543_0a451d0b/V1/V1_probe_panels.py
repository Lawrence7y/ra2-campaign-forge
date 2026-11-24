import os
import glob
from PIL import Image, ImageDraw

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"

png_files = sorted(glob.glob(os.path.join(BASE_DIR, "*", "measure_w*_end_x.png")))

# Let's crop the whole score panel: x: 80 to 640, y: 100 to 280
# Size is 560 x 180
# Let's also crop l3_20261023r in detail
panel_crops = []
labels = []

for idx, p in enumerate(png_files):
    rel = os.path.relpath(p, BASE_DIR)
    trip = rel.replace("\\", "/")
    im = Image.open(p).convert("RGB")
    panel = im.crop((80, 100, 640, 280))
    panel_crops.append(panel)
    labels.append(f"[{idx:02d}] {trip}")

# Let's save l3_20261023r panel specifically
l3_idx = 24
l3_panel = panel_crops[l3_idx]
l3_panel.save(os.path.join(OUT_DIR, "V1_panel_l3_detail.png"))

# Let's save a representative early trip panel (e.g. T34 w1)
t34_panel = panel_crops[2]
t34_panel.save(os.path.join(OUT_DIR, "V1_panel_t34_detail.png"))

# Let's save a montage of panels for all 20 score-screen images
# We know 5 are non-scorescreen: [1], [13], [14], [20], [23]
score_indices = [i for i in range(25) if i not in (1, 13, 14, 20, 23)]
print(f"Total score-screen candidates: {len(score_indices)}")

# Make a montage of the score tables: 10 rows x 2 cols or 20 rows
# 20 rows of 560x180 is 3600px, let's do 5 rows x 4 cols
cols = 2
rows = 10
grid_w = cols * 570
grid_h = rows * 190
montage = Image.new("RGB", (grid_w, grid_h), (20, 20, 20))
draw = ImageDraw.Draw(montage)

for slot, idx in enumerate(score_indices):
    c = slot % cols
    r = slot // cols
    x = c * 570 + 5
    y = r * 190 + 5
    montage.paste(panel_crops[idx], (x, y))
    draw.text((x + 5, y + 5), labels[idx], fill=(255, 255, 0))

montage.save(os.path.join(OUT_DIR, "V1_score_panels_montage.png"))
print("Saved V1_score_panels_montage.png")

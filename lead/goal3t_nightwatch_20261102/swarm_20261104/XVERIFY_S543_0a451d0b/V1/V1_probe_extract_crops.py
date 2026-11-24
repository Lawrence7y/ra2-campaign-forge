import os
import glob
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"

png_files = sorted(glob.glob(os.path.join(BASE_DIR, "*", "measure_w*_end_x.png")))

# Let's inspect where title, header, and timer are.
# In 800x600 RA2 resolution:
# Let's create a montage for:
# 1. Timer box (approx 440, 120, 600, 145)
# 2. Title box (approx 620, 10, 790, 45)
# 3. Header box (approx 90, 115, 620, 140)
# 4. Score table body (approx 90, 140, 620, 220)

# Let's make small montages
timer_crops = []
title_crops = []
full_thumbs = []

labels = []

for idx, p in enumerate(png_files):
    rel = os.path.relpath(p, BASE_DIR)
    trip = rel.replace("\\", "/")
    im = Image.open(p).convert("RGB")
    
    # timer crop (x: 430 to 620, y: 115 to 150)
    timer_im = im.crop((430, 115, 620, 150))
    # title crop (x: 620 to 790, y: 10 to 45)
    title_im = im.crop((620, 10, 790, 45))
    # thumb
    thumb = im.resize((200, 150), Image.Resampling.LANCZOS)
    
    timer_crops.append(timer_im)
    title_crops.append(title_im)
    full_thumbs.append(thumb)
    labels.append(f"[{idx:02d}] {trip}")

# Assemble Timer Grid: 25 rows
# Each row: label (draw text) + timer crop (scale 2x)
row_h = 40
grid_w = 600
grid_h = row_h * len(png_files)
timer_grid = Image.new("RGB", (grid_w, grid_h), (30, 30, 30))
draw = ImageDraw.Draw(timer_grid)

for idx in range(len(png_files)):
    y = idx * row_h
    draw.text((10, y + 12), labels[idx], fill=(220, 220, 220))
    # Paste timer crop
    tc = timer_crops[idx]
    timer_grid.paste(tc, (320, y + 2))

timer_grid.save(os.path.join(OUT_DIR, "V1_timers_grid.png"))
print("Saved V1_timers_grid.png")

# Assemble Title Grid
title_grid = Image.new("RGB", (grid_w, grid_h), (30, 30, 30))
draw = ImageDraw.Draw(title_grid)
for idx in range(len(png_files)):
    y = idx * row_h
    draw.text((10, y + 12), labels[idx], fill=(220, 220, 220))
    title_grid.paste(title_crops[idx], (320, y + 2))

title_grid.save(os.path.join(OUT_DIR, "V1_titles_grid.png"))
print("Saved V1_titles_grid.png")

# Assemble Thumbnails Grid: 5 columns x 5 rows
thumb_grid = Image.new("RGB", (5 * 200, 5 * 170), (20, 20, 20))
draw = ImageDraw.Draw(thumb_grid)
for idx in range(len(png_files)):
    col = idx % 5
    row = idx // 5
    x = col * 200
    y = row * 170
    thumb_grid.paste(full_thumbs[idx], (x, y))
    short_lbl = labels[idx].replace("archive_", "").replace("lead/qc161_u0400_trip/", "")
    draw.text((x + 5, y + 152), short_lbl, fill=(255, 255, 100))

thumb_grid.save(os.path.join(OUT_DIR, "V1_thumbnails_grid.png"))
print("Saved V1_thumbnails_grid.png")

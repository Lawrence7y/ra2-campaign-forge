import os
from PIL import Image

OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"
p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_20261023r\measure_w2_end_x.png"

im = Image.open(p).convert("RGB")
# Crop l3 table area: x: 90 to 600, y: 110 to 260
# Score table rows:
# Header: y=130 to 155
# Row 1 (blue): y=155 to 195
# Row 2 (red): y=195 to 240
# Columns:
# Name: x=90..230
# Kills: x=240..330
# Losses: x=340..430
# Built: x=440..510
# Score: x=510..600

crop = im.crop((90, 110, 600, 260))
# Scale 4x nearest neighbor to see pixels exactly
crop_4x = crop.resize((crop.width * 4, crop.height * 4), Image.Resampling.NEAREST)
crop_4x.save(os.path.join(OUT_DIR, "V1_l3_table_zoom4x.png"))
print("Saved V1_l3_table_zoom4x.png")

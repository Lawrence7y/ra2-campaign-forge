"""Tight, high-zoom crops of the HH:MM:SS digits only (x 486-532) for the trips whose displayed
time is load-bearing in §543's table, so each value can be read independently of §543's transcription."""
import os
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"

CASES = [("archive_T38/measure_w2_end_x.png", 940), ("archive_T40/measure_w1_end_x.png", 908),
         ("archive_T49_u0800/measure_w1_end_x.png", 448), ("measure_w1_end_x.png", 373),
         ("archive_T45/measure_w1_end_x.png", 845), ("archive_T36/measure_w1_end_x.png", 310)]

for i, (rel, f0) in enumerate(CASES):
    im = Image.open(os.path.join(R, rel.replace("/", os.sep))).convert("RGB")
    crop = im.crop((484, 122, 534, 141))
    big = crop.resize((crop.width * 18, crop.height * 18), Image.LANCZOS)
    p = os.path.join(OUT, f"digits_{i}.png")
    big.save(p)
    print(f"[DG] {i} {rel} f0={f0} -> {p} {big.size}   implied fps if you read S seconds: f0/S")

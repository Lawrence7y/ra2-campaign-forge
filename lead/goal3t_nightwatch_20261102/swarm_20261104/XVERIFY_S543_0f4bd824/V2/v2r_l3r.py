"""Zoom the 损失数 column of l3_20261023r/measure_w2_end_x.png, and locate the score table inside
l3_20261023r/frame_target_01.png (in case §543's numbers came from that second image)."""
import os
import numpy as np
from PIL import Image, ImageDraw

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"

q = os.path.join(R, "l3_20261023r", "measure_w2_end_x.png")
im = Image.open(q).convert("RGB")
arr = np.asarray(im).astype(np.int16)
yellow = (arr[:, :, 0] > 150) & (arr[:, :, 1] > 120) & (arr[:, :, 2] < 110)
rows = np.where(yellow[100:300].sum(axis=1) > 40)[0] + 100
print("[L1] yellow header rows:", rows[:3], rows[-3:])
# header row of column titles: find the band containing 玩家/摧毁数/损失数/建造数/分数
for y0 in range(140, 200, 2):
    band = yellow[y0:y0 + 12].sum(axis=0)
    xs = np.where(band > 0)[0]
    if len(xs) > 40:
        groups = []
        s = xs[0]
        p = xs[0]
        for x in xs[1:]:
            if x - p > 6:
                groups.append((int(s), int(p)))
                s = x
            p = x
        groups.append((int(s), int(p)))
        if len(groups) >= 4:
            print(f"[L2] y={y0} column-title groups: {groups}")
        break

# crop the two data rows, one strip per column, at 14x
dr = ImageDraw.Draw(im)
strips = [(95, 150), (245, 290), (295, 340), (345, 390), (400, 460), (460, 540)]
rows_band = [(185, 225), (222, 272)]
canvas = Image.new("RGB", (1400, 4 * 140), (10, 10, 14))
c = ImageDraw.Draw(canvas)
lbl = 0
for (y0, y1) in rows_band:
    crop = im.crop((90, y0, 545, y1))
    big = crop.resize((crop.width * 3, (y1 - y0) * 3), Image.LANCZOS)
    canvas.paste(big, (0, lbl * 140))
    c.text((1006, lbl * 140 + 4), f"l3r measure_w2_end_x.png  y{y0}-{y1}", fill=(255, 255, 0))
    lbl += 1
canvas.save(os.path.join(OUT, "l3r_rowstrip.png"))
print("[L3] wrote l3r_rowstrip.png", canvas.size)

q2 = os.path.join(R, "l3_20261023r", "frame_target_01.png")
im2 = Image.open(q2).convert("RGB")
print("[L4] frame_target_01 size:", im2.size, os.path.getsize(q2))
a2 = np.asarray(im2).astype(np.int16)
y2 = (a2[:, :, 0] > 150) & (a2[:, :, 1] > 120) & (a2[:, :, 2] < 110)
print("     yellow px:", int(y2.sum()), " row hits:", int((y2.sum(axis=1) > 30).sum()))
small = im2.resize((im2.width // max(1, im2.width // 1000), im2.height // max(1, im2.width // 1000)))
small.save(os.path.join(OUT, "l3r_frame_target_01_small.png"))
print("     wrote l3r_frame_target_01_small.png", small.size)

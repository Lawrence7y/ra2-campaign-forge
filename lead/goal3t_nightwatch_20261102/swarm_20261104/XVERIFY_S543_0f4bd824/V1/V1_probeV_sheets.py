"""V1 probe V: contact sheets.
 (a) all 27 window-end shots downscaled into one grid (visual pass over the whole set),
 (b) the 时间 field of each shot, 8x zoomed, stacked with an index label drawn as text
     is NOT possible without a font, so instead stack them in a fixed order and print the
     order in the console so the sheet can be read positionally.
"""
import os, glob
from PIL import Image, ImageDraw

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
V1 = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"

shots = sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png")) + sorted(glob.glob(ROOT + "/measure_w*_end_x.png"))
shots = [p for p in shots if os.path.isfile(p)]
print("order for contact sheet A (row-major, 6 per row):")
for i, p in enumerate(shots):
    print("  %2d %s" % (i, p[len(ROOT) + 1:].replace("\\", "/")))

TH = 6
sheet = Image.new("RGB", (800, 600 * 0 + 150 * ((len(shots) + TH - 1) // TH) + 20), (30, 30, 30))
d = ImageDraw.Draw(sheet)
for i, p in enumerate(shots):
    im = Image.open(p).convert("RGB").resize((148, 111), Image.LANCZOS)
    x, y = (i % TH) * 150 + 1, (i // TH) * 150 + 1
    sheet.paste(im, (x, y))
    d.text((x + 2, y + 113), "%d" % i, fill=(255, 255, 0))
sheet.save(V1 + "/V1_sheetA_all27.png")
print("saved V1_sheetA_all27.png", sheet.size)

# timer strip, 8x, 4 per row
strips = []
for p in shots:
    im = Image.open(p).convert("RGB").crop((450, 118, 535, 142)).resize((85 * 8, 24 * 8), Image.NEAREST)
    strips.append(im)
H = 24 * 8
sh2 = Image.new("RGB", (85 * 8 * 2, ((len(strips) + 1) // 2) * (H + 18)), (20, 20, 20))
d2 = ImageDraw.Draw(sh2)
for i, s in enumerate(strips):
    x, y = (i % 2) * (85 * 8), (i // 2) * (H + 18)
    sh2.paste(s, (x, y))
    d2.text((x + 3, y + H + 2), "%d" % i, fill=(255, 255, 0))
sh2.save(V1 + "/V1_sheetB_timers.png")
print("saved V1_sheetB_timers.png", sh2.size)

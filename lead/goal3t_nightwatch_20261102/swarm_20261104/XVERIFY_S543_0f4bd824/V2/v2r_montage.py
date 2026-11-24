"""Montage of the timer field of every table-bearing screenshot, 9x zoom, labelled with the
window's own f0, for one independent visual read. Also crops the full score table of two
trips so the player rows can be read.

Run: python -I -X utf8 v2r_montage.py
"""
import os, glob, json
from PIL import Image, ImageDraw, ImageFont

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 22)
except Exception:
    FONT = ImageFont.load_default()

pngs = sorted(glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))) + sorted(glob.glob(os.path.join(R, "measure_w*_end_*.png")))


def meta(q):
    rel = os.path.relpath(q, R).replace("\\", "/")
    dr = "." if "/" not in rel else rel.split("/")[0]
    w = int(rel.split("measure_w")[1][0])
    jr = os.path.join(R, "measure_w%d.json" % w) if dr == "." else os.path.join(R, dr, "measure_w%d.json" % w)
    d = json.load(open(jr, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    f0 = fe[0][0] if fe else None
    df = (fe[-1][0] - fe[0][0]) if fe else None
    kind = "NO_EDGES" if not fe else ("ADV" if df > 0 else ("LOAD" if f0 == 0 else ("FRZ" if df == 0 else "BACK")))
    return rel, f0, kind, dr


Z = 9
X0, X1, Y0, Y1 = 450, 532, 121, 141
items = []
for q in pngs:
    rel, f0, kind, dr = meta(q)
    im = Image.open(q).convert("RGB")
    crop = im.crop((X0, Y0, X1, Y1))
    items.append((rel, f0, kind, crop))

W = (X1 - X0) * Z
H = (Y1 - Y0) * Z + 26
sheet = Image.new("RGB", (W + 340, H * len(items)), (15, 15, 20))
dr2 = ImageDraw.Draw(sheet)
for i, (rel, f0, kind, crop) in enumerate(items):
    y = i * H
    dr2.text((6, y + 4), f"#{i} {rel}  f0={f0} [{kind}]", fill=(255, 255, 0), font=FONT)
    sheet.paste(crop.resize(((X1 - X0) * Z, (Y1 - Y0) * Z), Image.NEAREST), (340, y))
sheet.save(os.path.join(OUT, "timer_montage.png"))
print("[MM] wrote", os.path.join(OUT, "timer_montage.png"), sheet.size, "rows", len(items))

# split into two halves so the read is legible
half = len(items) // 2 + 1
for tag, sl in (("A", items[:half]), ("B", items[half:])):
    sh = Image.new("RGB", (W + 340, H * len(sl)), (15, 15, 20))
    d3 = ImageDraw.Draw(sh)
    for i, (rel, f0, kind, crop) in enumerate(sl):
        y = i * H
        d3.text((6, y + 4), f"[{tag}{i}] {rel} f0={f0} {kind}", fill=(255, 255, 0), font=FONT)
        sh.paste(crop.resize(((X1 - X0) * Z, (Y1 - Y0) * Z), Image.NEAREST), (340, y))
    p = os.path.join(OUT, f"timer_montage_{tag}.png")
    sh.save(p)
    print(f"[MM] wrote {p} {sh.size} rows {len(sl)}")

for rel, box, name in [("l3_20261023r/measure_w2_end_x.png", (90, 105, 545, 280), "table_l3r.png"),
                       ("archive_T33/measure_w1_end_x.png", (90, 105, 545, 280), "table_T33.png")]:
    im = Image.open(os.path.join(R, rel.replace("/", os.sep))).convert("RGB").crop(box)
    im = im.resize((im.width * 3, im.height * 3), Image.LANCZOS)
    im.save(os.path.join(OUT, name))
    print("[MM] wrote", name, im.size)

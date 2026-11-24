"""Read the on-screen timer digits WITHOUT OCR: cluster the exact pixel bitmap of each of the
6 HH:MM:SS glyph slots over all 27 screenshots, render every distinct glyph once (zoomed,
labelled) into one sheet for a single visual read, then print the per-image slot-id string.

Run: python -I -X utf8 v2r_glyph.py
"""
import os, glob, json, hashlib
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)

Y0, Y1 = 124, 138
SLOTS = [("H1", 488, 492), ("H2", 494, 498), ("M1", 503, 507), ("M2", 509, 513),
         ("S1", 518, 522), ("S2", 524, 528)]
COLONS = [(485, 486), (500, 501), (515, 516)]

pngs = sorted(glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))) + \
       sorted(glob.glob(os.path.join(R, "measure_w*_end_*.png")))


def meta_for(q):
    rel = os.path.relpath(q, R).replace("\\", "/")
    dr = "." if "/" not in rel else rel.split("/")[0]
    w = int(rel.split("measure_w")[1][0])
    jr = os.path.join(R, "measure_w%d.json" % w) if dr == "." else os.path.join(R, dr, "measure_w%d.json" % w)
    d = json.load(open(jr, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    f0 = fe[0][0] if fe else None
    df = (fe[-1][0] - fe[0][0]) if fe else None
    kind = "NO_EDGES" if not fe else ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK")))
    return rel, dict(dir=dr, w=w, f0=f0, df=df, kind=kind, units0=(d.get("gate") or {}).get("units0"))


data = {}
for q in pngs:
    rel, m = meta_for(q)
    arr = np.asarray(Image.open(q).convert("RGB")).astype(np.int16)
    rr, gg, bb = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    ym = (rr > 150) & (gg > 120) & (bb < 110)
    data[rel] = dict(meta=m, ym=ym, arr=arr, path=q)


def slot_hash(rel, nm, x0, x1):
    sub = data[rel]["ym"][Y0:Y1 + 1, x0:x1 + 1].astype(np.uint8)
    return hashlib.sha256(np.packbits(sub).tobytes()).hexdigest()[:8]


tables = []
print("[G1] presence test: do all 6 digit slots and all 3 colons carry yellow glyphs?")
for rel in sorted(data):
    ok_s = all(data[rel]["ym"][Y0:Y1 + 1, a:b + 1].sum() > 0 for _, a, b in SLOTS)
    ok_c = all(data[rel]["ym"][Y0:Y1 + 1, a:b + 1].sum() > 0 for a, b in COLONS)
    if ok_s and ok_c:
        tables.append(rel)
    print(f"    {rel:46s} {data[rel]['meta']['kind']:5s} f0={data[rel]['meta']['f0']} slots={ok_s} colons={ok_c} TABLE={ok_s and ok_c}")
print(f"    => images whose timer field is fully present: {len(tables)} / {len(data)}")
print("    => images WITHOUT it:", [r for r in sorted(data) if r not in tables])

glyphs = {}
for nm, x0, x1 in SLOTS:
    cls = defaultdict(list)
    for rel in tables:
        cls[slot_hash(rel, nm, x0, x1)].append(rel)
    glyphs[nm] = cls
    print(f"[G2] slot {nm}: {len(cls)} distinct bitmaps")

label_of = {}
for nm, x0, x1 in SLOTS:
    order = sorted(glyphs[nm], key=lambda h: min(data[r]["meta"]["f0"] for r in glyphs[nm][h]))
    for i, h in enumerate(order):
        label_of[(nm, h)] = i

Z, GW, GH = 16, 5, 15
total = sum(len(c) for c in glyphs.values())
sheet = Image.new("RGB", (520 + (GW + 4) * Z, 30 * total + 10), (18, 18, 24))
dr = ImageDraw.Draw(sheet)
yc = 4
for nm, x0, x1 in SLOTS:
    for h, lst in sorted(glyphs[nm].items(), key=lambda kv: min(data[r]["meta"]["f0"] for r in kv[1])):
        sub = (data[lst[0]]["ym"][Y0:Y1 + 1, x0:x1 + 1].astype(np.uint8)) * 255
        gi = Image.fromarray(sub, "L").resize((GW * Z, GH * Z), Image.NEAREST)
        sheet.paste(gi, (4, yc))
        f0s = sorted({data[r]["meta"]["f0"] for r in lst})
        dr.text((8 + GW * Z, yc + 2), f"slot {nm}  DIGIT-ID={label_of[(nm, h)]}  appears n={len(lst)}  f0={f0s[:8]}", fill=(255, 255, 0))
        dr.text((8 + GW * Z, yc + 18), f"example={lst[0]}", fill=(170, 215, 255))
        yc += GH * Z + 28
sheet.save(os.path.join(OUT, "glyph_sheet.png"))
print("[G3] wrote glyph_sheet.png", sheet.size, "distinct glyph rows:", total)

print("\n[G4] per-image timer field as slot DIGIT-IDs (id order H1 H2 M1 M2 S1 S2)")
for rel in tables:
    ids = [label_of[(nm, slot_hash(rel, nm, a, b))] for nm, a, b in SLOTS]
    print(f"    {rel:46s} f0={data[rel]['meta']['f0']:6d} ids={' '.join(str(i) for i in ids)}")

print("\n[G5] whole timer cluster (x454-528) exact-RGB classes: which screenshots show the SAME field")
box = defaultdict(list)
for rel in sorted(data):
    b = data[rel]["arr"][Y0:Y1 + 1, 454:529]
    box[hashlib.sha256(b.tobytes()).hexdigest()[:8]].append((rel, data[rel]["meta"]["f0"], data[rel]["meta"]["kind"]))
for h, lst in sorted(box.items(), key=lambda kv: -len(kv[1])):
    print(f"    class {h}: n={len(lst)} f0={sorted({x[1] for x in lst})}")
    for rel, f, k in lst:
        print("        ", rel, k, "f0=", f)

for rel in ["l3_20261023r/measure_w2_end_x.png", "archive_T33/measure_w1_end_x.png", "measure_w1_end_x.png"]:
    if rel in data:
        arr = data[rel]["arr"].astype(np.uint8)
        im = Image.fromarray(arr[108:272, 90:545]).resize((int(455 * 2.6), int(164 * 2.6)), Image.NEAREST)
        out = os.path.join(OUT, "table_" + rel.replace("/", "_").replace(".png", "") + ".png")
        im.save(out)
        print("[G6] wrote crop", out, im.size)

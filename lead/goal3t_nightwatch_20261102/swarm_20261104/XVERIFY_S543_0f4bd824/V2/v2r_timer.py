"""Extract the on-screen timer digits from every score-screen screenshot WITHOUT OCR:
  * locate the yellow '时间' cluster;
  * split the HH:MM:SS into fixed glyph slots;
  * cluster each slot's exact pixel bitmap across all images;
  * emit one zoomed montage per slot so each distinct glyph is read once by eye,
  * and diff w1 vs w2 inside the timer box (tests S543 evidence-2 'maxdiff=0').

Run: python -I -X utf8 v2r_timer.py
"""
import os, glob, json, hashlib
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)

# fixed geometry, measured in v2r_yellow.py from archive_T33/measure_w1_end_x.png
Y0, Y1 = 124, 138
SLOTS = [("H1", 488, 492), ("H2", 494, 498), ("M1", 503, 507), ("M2", 509, 513),
         ("S1", 518, 522), ("S2", 524, 528)]
LABEL = (454, 486)      # the '时间' + first colon
TIMER = (488, 528)


def mask_yellow(arr):
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    return (r > 150) & (g > 120) & (b < 110)


def load(rel):
    im = Image.open(os.path.join(R, rel.replace("/", os.sep))).convert("L")
    rgb = np.asarray(Image.open(os.path.join(R, rel.replace("/", os.sep))).convert("RGB")).astype(np.int16)
    return rgb, mask_yellow(rgb)


pngs = sorted(glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))) + sorted(glob.glob(os.path.join(R, "measure_w*_end_*.png")))
info = {}
for q in pngs:
    rel = os.path.relpath(q, R).replace("\\", "/")
    dr = "." if "/" not in rel else rel.split("/")[0]
    w = int(rel.split("measure_w")[1][0])
    jr = os.path.join(R, *(("measure_w%d.json" % w).split("/"))) if dr == "." else os.path.join(R, dr, "measure_w%d.json" % w)
    d = json.load(open(jr, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    f0 = fe[0][0] if fe else None
    df = (fe[-1][0] - fe[0][0]) if fe else None
    kind = "NO_EDGES" if not fe else ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK")))
    info[rel] = dict(dir=dr, w=w, f0=f0, df=df, kind=kind,
                     fps=(d.get("stats") or {}).get("fps_avg"), units0=(d.get("gate") or {}).get("units0"))

print("[M1] per-image presence of the yellow 时间 cluster + slot bitmaps")
classes = defaultdict(list)
rows = []
for rel in sorted(info):
    rgb, ym = load(rel)
    hdr = ym[Y0:Y1 + 1, :]
    cols = hdr.sum(axis=0)
    xs = np.where(cols > 0)[0]
    has = len(xs) > 0
    if has:
        c0, c1 = int(xs.min()), int(xs.max())
    else:
        c0 = c1 = -1
    slots = {}
    if has and abs(c1 - TIMER[1]) <= 4 and abs(c0 - LABEL[0]) <= 8:
        for nm, x0, x1 in SLOTS:
            sub = hdr[:, x0:x1 + 1]
            slots[nm] = hashlib.sha256(np.packbits(sub.astype(np.uint8)).tobytes()).hexdigest()[:10]
    box = rgb[Y0:Y1 + 1, TIMER[0]:TIMER[1] + 1]
    tb = hashlib.sha256(box.tobytes()).hexdigest()[:10]
    rows.append((rel, info[rel], has, (c0, c1), slots, tb))
    classes["__timerbox__" ].append((rel, tb))

print("\n     %-46s %-6s %-6s %-5s %-9s %s" % ("image", "class", "f0", "timer?", "cluster", "slot hashes(H1H2:M1M2:S1S2)"))
for rel, meta, has, clu, slots, tb in rows:
    s = "-".join(slots.get(n, "?")[:4] for n, _, _ in SLOTS) if slots else "NO-TABLE"
    print("     %-46s %-6s %-6s %-5s %-9s %s  tb=%s" % (rel, meta["kind"], meta["f0"], has, str(clu), s, tb))

print("\n[M2] distinct timer-box bitmaps (exact match => same displayed string)")
byt = defaultdict(list)
for rel, meta, has, clu, slots, tb in rows:
    if slots:
        byt[tb].append((rel, meta["f0"], slots))
for tb, lst in sorted(byt.items(), key=lambda kv: -len(kv[1])):
    f0s = sorted({x[1] for x in lst})
    print(f"    box {tb}: n={len(lst)} f0={f0s} slots={lst[0][2]}")
    for rel, f, sl in lst:
        print("        ", rel, "f0=", f)

print("\n[M3] per-slot glyph classes (each unique bitmap is one digit glyph)")
Z = 12
for idx, (nm, x0, x1) in enumerate(SLOTS):
    g = defaultdict(list)
    for rel, meta, has, clu, slots, tb in rows:
        if slots:
            rgb, ym = load(rel)
            sub = ym[Y0:Y1 + 1, x0:x1 + 1]
            g[hashlib.sha256(np.packbits(sub.astype(np.uint8)).tobytes()).hexdigest()[:8]].append((rel, sub))
    print(f"    slot {nm} (x{x0}-{x1}): {len(g)} distinct glyphs over {sum(len(v) for v in g.values())} images")
    montage = Image.new("L", (14 * Z * max(1, len(g)), 15 * Z + 22 * len(g)), 30)
    dr = ImageDraw.Draw(montage)
    ycur = 0
    for gh, lst in sorted(g.items(), key=lambda kv: -len(kv[1])):
        sub = lst[0][1].astype(np.uint8) * 255
        gi = Image.fromarray(sub).resize(((x1 - x0 + 1) * Z, 15 * Z), Image.NEAREST)
        montage.paste(gi, (0, ycur))
        dr.text((2, ycur + 15 * Z + 2), f"{nm} glyph {gh} n={len(lst)} first={lst[0][0]}", fill=255)
        ycur += 15 * Z + 20
    montage.save(os.path.join(OUT, f"slot_{nm}.png"))
    for gh, lst in sorted(g.items(), key=lambda kv: -len(kv[1])):
        print(f"        glyph {gh} n={len(lst)} example={lst[0][0]} f0={info[lst[0][0]]['f0']}")

print("\n[M4] w1 vs w2 inside the timer box, per trip (S543 evidence-2 'maxdiff=0')")
for dr_ in sorted({v["dir"] for v in info.values()}):
    if dr_ == ".":
        continue
    a = f"{dr_}/measure_w1_end_x.png"
    b = f"{dr_}/measure_w2_end_x.png"
    if a in info and b in info:
        ra, _ = load(a); rb, _ = load(b)
        d = np.abs(ra - rb)
        full = d.max()
        tim = d[Y0:Y1 + 1, LABEL[0]:TIMER[1] + 1].max()
        sec = d[Y0:Y1 + 1, 518:529].max()
        print(f"    {dr_:22s} whole-img maxdiff={full:4d}  timer-cluster maxdiff={tim:4d}  seconds-digits maxdiff={sec:4d}")

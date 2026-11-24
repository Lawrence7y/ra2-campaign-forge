"""Split the score table of a screenshot into per-cell crops and render every distinct digit
bitmap once, so the transcribed numbers can be checked without trusting an eyeballed summary.

Run: python -I -X utf8 v2r_cells.py [rel_png ...]
"""
import os, sys, hashlib
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 18)
except Exception:
    FONT = ImageFont.load_default()

TABLE = (90, 108, 545, 275)     # x0,y0,x1,y1 : the score panel, located by the diff bbox in v2r_croploc.py
rels = sys.argv[1:] or ["l3_20261023r/measure_w2_end_x.png", "archive_T33/measure_w1_end_x.png"]

for rel in rels:
    im = Image.open(os.path.join(R, rel.replace("/", os.sep))).convert("RGB")
    arr = np.asarray(im).astype(np.int16)
    x0, y0, x1, y1 = TABLE
    sub = arr[y0:y1, x0:x1]
    mx = sub.max(axis=2)
    bright = mx > 150
    yellow = (sub[:, :, 0] > 150) & (sub[:, :, 1] > 120) & (sub[:, :, 2] < 110)
    textish = bright & ~yellow          # data rows are green/blue/red, headers are yellow
    print("=" * 78)
    print("[CELLS]", rel)
    rowproj = textish.sum(axis=1)
    bands, inb = [], False
    for i, v in enumerate(rowproj):
        if v > 2 and not inb:
            inb, r0 = True, i
        elif v <= 2 and inb:
            inb = False
            if i - r0 >= 6:
                bands.append((r0, i - 1))
    if inb:
        bands.append((r0, len(rowproj) - 1))
    print("    data row bands (y in image coords):", [(b[0] + y0, b[1] + y0) for b in bands])

    cells = []
    for ri, (r0, r1) in enumerate(bands):
        band = textish[r0:r1 + 1]
        colproj = band.sum(axis=0)
        cs, inc = [], False
        for i, v in enumerate(colproj):
            if v > 0 and not inc:
                inc, c0 = True, i
            elif v == 0 and inc:
                inc = False
                cs.append((c0, i - 1))
        if inc:
            cs.append((c0, len(colproj) - 1))
        # merge clusters closer than 3 px (a number's digits), keep wide gaps as cell breaks
        merged = []
        for (a, b) in cs:
            if merged and a - merged[-1][1] <= 3:
                merged[-1] = (merged[-1][0], b)
            else:
                merged.append([a, b])
        for ci, (a, b) in enumerate(merged):
            if b - a >= 3:
                cells.append((ri, ci, a + x0, b + x0, r0 + y0, r1 + y0))
    print("    cells found:", len(cells))
    for (ri, ci, cx0, cx1, cy0, cy1) in cells:
        print(f"      row{ri} cell{ci} x {cx0}-{cx1} (w={cx1-cx0+1}) y {cy0}-{cy1} (h={cy1-cy0+1})")

    # digit-level: split each cell into glyphs and cluster exact bitmaps over colour-agnostic mask
    glyphs = defaultdict(list)
    for (ri, ci, cx0, cx1, cy0, cy1) in cells:
        csub = textish[cy0 - y0:cy1 - y0 + 1, cx0 - x0:cx1 - x0 + 1]
        cp = csub.sum(axis=0)
        gs, ginc = [], False
        for i, v in enumerate(cp):
            if v > 0 and not ginc:
                ginc, g0 = True, i
            elif v == 0 and ginc:
                ginc = False
                gs.append((g0, i - 1))
        if ginc:
            gs.append((g0, len(cp) - 1))
        for gi, (a, b) in enumerate(gs):
            gm = csub[:, a:b + 1]
            key = hashlib.sha256(np.packbits(gm.astype(np.uint8)).tobytes()).hexdigest()[:8]
            glyphs[key].append((ri, ci, gi, gm))

    print(f"    distinct digit bitmaps: {len(glyphs)}")
    # sheet: every distinct digit, 18x, with the ids; plus per-cell digit-id strings
    order = sorted(glyphs.items(), key=lambda kv: (len(kv[1]), kv[0]), reverse=True)
    ids = {kv[0]: i for i, kv in enumerate(order)}
    sheet = Image.new("RGB", (200 + 22 * 18, 40 * len(order)), (15, 15, 20))
    d = ImageDraw.Draw(sheet)
    for i, (key, lst) in enumerate(order):
        gm = lst[0][3].astype(np.uint8) * 255
        gi = Image.fromarray(gm, "L").resize(((gm.shape[1]) * 18, gm.shape[0] * 18), Image.NEAREST)
        sheet.paste(gi, (4, i * 40))
        where = ", ".join(f"r{r}c{c}g{g}" for (r, c, g, _) in lst[:10])
        d.text((10 + 22 * 18, i * 40 + 2), f"DIGIT {i}  n={len(lst)}  sha={key}", fill=(255, 255, 0), font=FONT)
        d.text((10 + 22 * 18, i * 40 + 20), f"at: {where}", fill=(170, 215, 255), font=FONT)
    tag = rel.replace("/", "_").replace(".png", "")
    sheet.save(os.path.join(OUT, f"cells_digits_{tag}.png"))
    print("    wrote", os.path.join(OUT, f"cells_digits_{tag}.png"), sheet.size)

    bycell = defaultdict(list)
    for key, lst in glyphs.items():
        for (ri, ci, gi, gm) in lst:
            bycell[(ri, ci)].append((gi, ids[key]))
    print("    per-cell digit-ID strings (read DIGIT n from the sheet):")
    for (ri, ci) in sorted(bycell):
        s = "".join(str(i) for (_, i) in sorted(bycell[(ri, ci)]))
        print(f"      row{ri} cell{ci}: ids[{s}]  glyphs={sorted(bycell[(ri, ci)])}")

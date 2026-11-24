"""Read-only probe #3b (mine). Fixed, simple method: in rows 120..142, cols>470, a 'digit'
column-run is any run with >=15 yellow px (colons are 4 or 8 px, label fragments are >470? no,
label ends at 484 -> excluded by taking only runs whose ink >=15 and width <=7). Print bitmap.
Then cluster bitmaps across images (sha) so the same glyph is read once and applied everywhere."""
import os, hashlib
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
R0, R1 = 120, 142
THRESH = [dict(name="y200/110", lo=200, hi=110), dict(name="y150/130", lo=150, hi=130), dict(name="y230/70", lo=230, hi=70)]

def paths():
    out = []
    for f in sorted(os.listdir(ROOT)):
        if f.startswith("measure_w") and f.endswith("_end_x.png"):
            out.append(f)
    for d in sorted(os.listdir(ROOT)):
        dd = os.path.join(ROOT, d)
        if os.path.isdir(dd):
            for f in sorted(os.listdir(dd)):
                if f.startswith("measure_w") and f.endswith("_end_x.png"):
                    out.append(os.path.join(d, f))
    return out

def band_mask(a, lo, hi):
    # "yellow": both R and G high, B clearly lower than them
    return (a[..., 0] > lo) & (a[..., 1] > lo) & (a[..., 2] < hi) & ((a[..., 0] - a[..., 2]) > 60)

def runs_of(cols_bool):
    runs, x = [], 0
    while x < len(cols_bool):
        if cols_bool[x]:
            y = x
            while y + 1 < len(cols_bool) and cols_bool[y + 1]:
                y += 1
            runs.append((x, y))
            x = y + 1
        else:
            x += 1
    return runs

per_thresh = {t["name"]: {} for t in THRESH}
for rel in paths():
    a = np.asarray(Image.open(os.path.join(ROOT, rel.replace("/", os.sep))).convert("RGB"), dtype=np.int16)
    for t in THRESH:
        m = band_mask(a, t["lo"], t["hi"])[R0:R1 + 1, 470:]
        rr = [r for r in runs_of(m.any(0)) if int(m[:, r[0]:r[1] + 1].sum()) >= 15 and (r[1] - r[0]) <= 7]
        cells = []
        for (c0, c1) in rr:
            sub = m[:, c0:c1 + 1]
            rows = np.where(sub.any(1))[0]
            sub = sub[rows.min():rows.max() + 1]
            txt = "/".join("".join("#" if v else "." for v in row) for row in sub)
            cells.append((470 + c0, 470 + c1, hashlib.sha256(txt.encode()).hexdigest()[:10], txt))
        per_thresh[t["name"]][rel] = cells
        if t is THRESH[0]:
            print(f"### {rel}  ndig={len(cells)}")
            for (c0, c1, sh, txt) in cells:
                print(f"  cols{c0}-{c1} sha{sh}")
                for line in txt.split("/"):
                    print("    " + line)

print("\n==== cross-threshold agreement (same image, same cell count, same sha sequence) ====")
base = per_thresh[THRESH[0]["name"]]
for rel in base:
    seqs = [tuple(c[2] for c in per_thresh[t["name"]][rel]) for t in THRESH]
    agree = len(set(seqs)) == 1
    print(f"{rel:46s} ndig={[len(per_thresh[t['name']][rel]) for t in THRESH]} agree={agree} seq={seqs[0]}")

print("\n==== glyph clusters across ALL images (thresh y200/110) ====")
group = {}
for rel, cells in base.items():
    for i, (c0, c1, sh, txt) in enumerate(cells):
        group.setdefault(sh, [0, txt, []])
        group[sh][0] += 1
        group[sh][2].append(f"{rel}#{i}")
for sh, (n, txt, where) in sorted(group.items(), key=lambda kv: -kv[1][0]):
    print(f"sha{sh} n={n}  w={txt.count('.') and len(txt.split('/')[0])}  h={len(txt.split('/'))}")
    for line in txt.split("/"):
        print("      " + line)
    print("      seen in:", ", ".join(where[:12]) + ("..." if len(where) > 12 else ""))

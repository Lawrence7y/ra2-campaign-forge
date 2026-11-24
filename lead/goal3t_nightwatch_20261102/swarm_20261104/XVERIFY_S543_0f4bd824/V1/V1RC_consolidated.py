"""Read-only consolidated recheck (my own numbers, nothing copied from V1's scripts).

Glyph map is MY OWN reading of the 9 shapes printed by V1RC_cells2_out.txt:
  67fd1346e7=0  8a16be9c89=1  6a788ed98c=2  a268f45208=3  ae603b1c0d=8
  84dee0c2e7=5  be2cf68e01=9  6737b710be=4  4034a7fba6=6
"""
import os, json, glob, hashlib, time
import numpy as np
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
MAP = {"67fd1346e7": "0", "8a16be9c89": "1", "6a788ed98c": "2", "a268f45208": "3",
       "ae603b1c0d": "8", "84dee0c2e7": "5", "be2cf68e01": "9", "6737b710be": "4",
       "4034a7fba6": "6"}
R0, R1 = 120, 142

def pngs():
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "measure_w*_end_x.png"))):
        out.append(os.path.basename(f))
    for d in sorted(os.listdir(ROOT)):
        for f in sorted(glob.glob(os.path.join(ROOT, d, "measure_w*_end_x.png"))):
            out.append(os.path.relpath(f, ROOT).replace("\\", "/"))
    return out

def runs_of(cb):
    r, x = [], 0
    while x < len(cb):
        if cb[x]:
            y = x
            while y + 1 < len(cb) and cb[y + 1]:
                y += 1
            r.append((x, y)); x = y + 1
        else:
            x += 1
    return r

arr, info = {}, {}
for rel in pngs():
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    im = Image.open(p).convert("RGB")
    a = np.asarray(im, dtype=np.int16)
    arr[rel] = a
    st = os.stat(p)
    h = hashlib.sha256(a.tobytes()).hexdigest()
    fh = hashlib.sha256(open(p, "rb").read()).hexdigest()
    m = (a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] < 110) & ((a[..., 0] - a[..., 2]) > 60)
    band = m[R0:R1 + 1, 470:]
    cells = []
    for (c0, c1) in runs_of(band.any(0)):
        sub = band[:, c0:c1 + 1]
        ink = int(sub.sum())
        if ink < 15 or (c1 - c0) > 7:
            continue
        rows = np.where(sub.any(1))[0]
        txt = "/".join("".join("#" if v else "." for v in r) for r in sub[rows.min():rows.max() + 1])
        cells.append(hashlib.sha256(txt.encode()).hexdigest()[:10])
    title = int(m[9:24, 400:800].sum())          # my own: yellow ink in the title band, right half
    hdr = int(m[160:175, 99:529].sum())          # my own: header row band
    info[rel] = dict(pixsha=h[:16], filesha=fh[:16], mtime=st.st_mtime, size=st.st_size,
                     title=title, hdr=hdr, cells=cells,
                     read=("".join(MAP[c] for c in cells) if len(cells) == 6 and all(c in MAP for c in cells) else None))
    # json side
    jp = p.replace("_end_x.png", ".json")
    if not os.path.exists(jp):
        jp = os.path.join(ROOT, rel.replace("_end_x.png", ".json").replace("_end_x", ""))
    d = None
    jrel = rel.replace("_end_x.png", ".json")
    jpath = os.path.join(ROOT, jrel.replace("/", os.sep))
    if os.path.exists(jpath):
        d = json.load(open(jpath, encoding="utf-8"))
    fe = d.get("frame_edges") if d else None
    f0 = fe[0][0] if fe else None
    f1 = fe[-1][0] if fe else None
    wend = (d["t_abs0"] + d["span_s"]) if d else None
    info[rel].update(json_ok=bool(d), f0=f0, f1=f1, nedges=len(fe) if fe else None,
                     df=(f1 - f0) if fe else None, trip=(d or {}).get("trip_id"),
                     win=(d or {}).get("window"), wend=wend,
                     dmt=(st.st_mtime - wend) if wend else None)

print("rel | trip | win | titleInk | hdrInk | ncells | READ | f0 | f1 | n_edges | df | mtime | dmt | pixsha | filesha")
for rel in pngs():
    i = info[rel]
    print(f"{rel:44s} {str(i['trip']):18s} w{i['win']} title={i['title']:4d} hdr={i['hdr']:4d} "
          f"n={len(i['cells'])} READ={i['read']} f0={i['f0']} f1={i['f1']} ne={i['nedges']} df={i['df']} "
          f"mtime={i['mtime']:.1f} dmt={None if i['dmt'] is None else round(i['dmt'],1)} "
          f"pix={i['pixsha']} file={i['filesha']}")

print("\n--- seconds -> implied rate (my own reading) ---")
for rel in pngs():
    i = info[rel]
    r = i["read"]
    if not r or i["f1"] is None:
        continue
    hh, mm, ss = int(r[0:2]), int(r[2:4]), int(r[4:6])
    secs = hh * 3600 + mm * 60 + ss
    print(f"{rel:44s} {r} secs={secs:4d} f1={i['f1']:5d} f1/secs={i['f1']/secs if secs else float('nan'):.2f} "
          f"in29.9_31.4={29.9 <= (i['f1']/secs if secs else 0) <= 31.4} | /31.2 gives {i['f1']/31.2:.2f}s")

print("\n--- duplicate groups (pixel sha / file sha) ---")
g = {}
for rel in pngs():
    g.setdefault(info[rel]["pixsha"], []).append(rel)
for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    if len(v) > 1:
        print(f"PIXSHA {k} n={len(v)} mtimes={[round(info[x]['mtime'],1) for x in v]} -> {v}")
    else:
        print(f"pixsha {k} n=1 {v[0]} mtime={info[v[0]]['mtime']:.1f}")
print("distinct pixel shas:", len(g), "of", len(pngs()))

print("\n--- w1 vs w2 pixel diffs (time field cols 470-560 rows 118-145) and other regions ---")
REGIONS = {"TIMER": (118, 145, 450, 560), "MONITOR": (47, 100, 665, 765),
           "TITLEBAR": (5, 30, 660, 760), "HDR": (158, 176, 95, 530),
           "TABLE": (190, 300, 95, 560), "LEFTEDGE": (0, 600, 0, 96), "FULL": (0, 600, 0, 800)}
pairs = {}
for rel in pngs():
    d_, f_ = (os.path.dirname(rel), os.path.basename(rel))
    if f_.startswith("measure_w"):
        w = f_.split("_")[1]
        pairs.setdefault(d_, {})[w] = rel
for d_, dd in pairs.items():
    if "w1" in dd and "w2" in dd:
        a1, a2 = arr[dd["w1"]], arr[dd["w2"]]
        line = f"{(d_ or '<root>'):22s}"
        for name, (r0, r1, c0, c1) in REGIONS.items():
            diff = np.abs(a1[r0:r1, c0:c1] - a2[r0:r1, c0:c1]).max(2)
            line += f" {name}:max={int(diff.max())},npix={int((diff>0).sum())}"
        print(line)

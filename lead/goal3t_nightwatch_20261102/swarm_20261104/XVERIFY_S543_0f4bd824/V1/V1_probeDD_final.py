"""V1 probe DD: final structural table over all 27 window-end shots.
Columns: plate ink (title LCD), header-row ink (游戏/时间 line), column-header ink (5 CJK),
time-field cell count, decoded time, trip_id from the json, game/fg window title + focus_ok +
current_frame from qc151_fields.json.  All pixel-derived; no OCR.
"""
import os, glob, json
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
R0, R1, C0, C1 = 120, 142, 480, 545

GL = {
    "0": ".###. ##.## ##.## ##.## ##.## ##.## ##.## ##.## .###.".split(),
    "1": "..## .### #### #.## ..## ..## ..## ..## ..##".split(),
    "2": ".###. ##.## ...## ...## ..##. .###. ###.. ##... #####".split(),
    "3": ".###. ##.## ...## ...## ..##. ...## ...## ##.## .###.".split(),
    "4": "..##. ..##. .###. .###. #.##. #.##. ##### ..##. ..##.".split(),
    "5": ".#### .##.. ##... ####. #..## ...## ...## ##.## .###.".split(),
    "6": ".###. ##.## ##... ####. ##.## ##.## ##.## ##.## .###.".split(),
    "7": "##### ...## ..##. ..#.. .##.. .##.. .##.. .##.. .##..".split(),
    "8": ".###. ##.## ##.## ##.## .###. ##.## ##.## ##.## .###.".split(),
    "9": ".###. ##.## ##.## ##.## ##.## .#### ...## ##.#. .###.".split(),
}


def psig(pat):
    h, w = len(pat), max(len(p) for p in pat)
    c = np.array([[(ch == "#") for ch in p.ljust(w)] for p in pat])
    o = np.zeros((8, 10), dtype=bool)
    o[:min(h, 8), :min(w, 10)] = c[:min(h, 8), :min(w, 10)]
    return "".join("1" if v else "0" for v in o.ravel())


SIG = {}
for k, v in GL.items():
    SIG.setdefault(psig(v), []).append(k)


def yellow(a):
    r = a[:, :, 0].astype(int); g = a[:, :, 1].astype(int); b = a[:, :, 2].astype(int)
    return (r > 170) & (g > 150) & (b < 130) & ((r - b) > 70) & ((g - b) > 50)


def cells(m):
    sub = m[R0:R1, C0:C1]
    cs = sub.sum(axis=0)
    out, x = [], 0
    while x < sub.shape[1]:
        if cs[x] > 0:
            y = x
            while y < sub.shape[1] and cs[y] > 0:
                y += 1
            blk = sub[:, x:y]
            ys, xs = np.where(blk)
            bb = blk[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            h, w = bb.shape
            o = np.zeros((8, 10), dtype=bool)
            o[:min(h, 8), :min(w, 10)] = bb[:min(h, 8), :min(w, 10)]
            out.append((C0 + x, C0 + y - 1, "".join("1" if v else "0" for v in o.ravel())))
            x = y
        else:
            x += 1
    return out


def fields(trip, w):
    p = os.path.join(ROOT, trip, "qc151_fields.json")
    if not os.path.exists(p):
        return {}
    for r in json.load(open(p, encoding="utf-8")):
        if r.get("key") == "measure_forensics_w%d" % w:
            return r["value"]
    return {}


print("%-46s %-6s %-6s %-6s %-4s %-10s %-20s %-6s %-6s %s" % (
    "shot", "plate", "hdr", "colh", "cell", "time", "trip_id", "focus", "cur_fr", "fg_title"))
rows = []
for f in sorted(glob.glob(ROOT + "/*/measure_w*_end_x.png")) + sorted(glob.glob(ROOT + "/measure_w*_end_x.png")):
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    a = np.asarray(Image.open(f).convert("RGB"))
    m = yellow(a)
    plate = int(m[5:30, 665:760].sum())
    hdr = int(m[124:139, 99:529].sum())
    colh = int(m[160:175, 99:529].sum())
    cl = cells(m)
    t = ""
    if len(cl) == 10:
        d = []
        for i in (2, 3, 5, 6, 8, 9):
            c = SIG.get(cl[i][2], ["?"])
            d.append(c[0] if len(c) == 1 else "?")
        t = "%s%s:%s%s:%s%s" % tuple(d)
    trip = rel.split("/")[0] if "/" in rel else "(root)"
    w = int(rel.split("measure_w")[1][0])
    jp = os.path.join(ROOT, trip if trip != "(root)" else "", "measure_w%d.json" % w)
    tid = json.load(open(jp, encoding="utf-8")).get("trip_id")
    fv = fields(trip, w)
    print("%-46s %-6d %-6d %-6d %-4d %-10s %-20s %-6s %-6s %s" % (
        rel, plate, hdr, colh, len(cl), t or "-", tid,
        fv.get("focus_ok"), fv.get("current_frame"), fv.get("fg_title")))
    rows.append((rel, plate, hdr, colh, t, tid, fv))

print()
print("summary: plate=361 & hdr~500 & colh=993 & readable time -> score screen")
sc = [r for r in rows if r[1] == 361 and r[5]]
print("  score screens: %d / %d" % (len(sc), len(rows)))
print("  non-score    :", [r[0] for r in rows if not (r[1] == 361 and r[5])])
print()
print("  score screens whose forensics record says focus_ok=True:",
      sum(1 for r in sc if r[6].get("focus_ok") is True), "of", len(sc))
print("  RPM CurrentFrame at shot time == frame_edges last frame:",
      [(r[0], r[6].get("current_frame")) for r in sc if r[6].get("current_frame") is not None][:3])

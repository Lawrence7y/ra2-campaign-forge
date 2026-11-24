"""Independence arithmetic for the 32 frozen windows: dirs, maps, distinct timer bitmaps.
Run: python -I -X utf8 v2r_indep.py"""
import os, glob, json, hashlib, re
from collections import Counter, defaultdict
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
SUB = sorted(glob.glob(os.path.join(R, "*", "measure_w*.json")))
ROOT = sorted(glob.glob(os.path.join(R, "measure_w*.json")))
SLOTS = [(488, 492), (494, 498), (503, 507), (509, 513), (518, 522), (524, 528)]
COLONS = [(485, 486), (500, 501), (515, 516)]


def cls(d):
    fe = d.get("frame_edges") or []
    if not fe:
        return "NO_EDGES", None
    f0, f1 = fe[0][0], fe[-1][0]
    df = f1 - f0
    return ("ADV" if df > 0 else ("LOAD" if f0 == 0 and df == 0 else ("FRZ" if df == 0 else "BACK"))), f0


frz = []
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    rel = os.path.relpath(p, R).replace("\\", "/")
    k, f0 = cls(d)
    if k == "FRZ":
        frz.append((rel, f0, (d.get("map_sha256") or "")[:8], d))

dirs = {r.split("/")[0] for r, _, _, _ in frz}
maps = Counter(m for _, _, m, _ in frz)
print("[I1] FRZ windows =", len(frz), "| dir buckets =", len(dirs), "| distinct map_sha256 =", len(maps))
print("[I2] windows per map:", maps.most_common())

boxes = defaultdict(list)
tab = noimg = nopanel = 0
for rel, f0, m, d in frz:
    parts = rel.split("/")
    w = re.match(r"^measure_w(\d+)\.json$", parts[-1]).group(1)
    q = os.path.join(R, *parts[:-1], f"measure_w{w}_end_x.png")
    if not os.path.exists(q):
        noimg += 1
        continue
    arr = np.asarray(Image.open(q).convert("RGB")).astype(np.int16)
    ym = (arr[:, :, 0] > 150) & (arr[:, :, 1] > 120) & (arr[:, :, 2] < 110)
    ok = all(ym[124:139, a:b + 1].sum() > 0 for a, b in SLOTS) and all(ym[124:139, a:b + 1].sum() > 0 for a, b in COLONS)
    if not ok:
        nopanel += 1
        continue
    tab += 1
    h = hashlib.sha256(arr[124:139, 454:529].tobytes()).hexdigest()[:8]
    boxes[h].append(rel)
print(f"[I3] FRZ windows: own png with scoreboard timer field={tab}  png without field={nopanel}  no png={noimg}")
print(f"[I4] distinct timer-box bitmaps among those {tab} windows: {len(boxes)}")
for h, l in sorted(boxes.items(), key=lambda kv: -len(kv[1])):
    print(f"      box {h}: {len(l)} windows  {l}")

adv_slow = []
for p in SUB + ROOT:
    d = json.load(open(p, encoding="utf-8"))
    k, f0 = cls(d)
    if k == "ADV":
        fps = (d.get("stats") or {}).get("fps_avg")
        rel = os.path.relpath(p, R).replace("\\", "/")
        if fps is not None and fps < 28:
            adv_slow.append((rel, fps, (d.get("map_sha256") or "")[:8], f0, d.get("span_s"),
                             (d.get("stats") or {}).get("max_stall_s")))
print(f"\n[I5] slow ADV windows n={len(adv_slow)} dirs={len({x[0].split('/')[0] for x in adv_slow})} "
      f"maps={Counter(x[2] for x in adv_slow).most_common()}")
qs = [x for x in adv_slow if x[5] and x[4] and x[5] / x[4] >= 0.43]
print(f"[I6] of those, stall/span >= 0.43 (quasi-frozen): {len(qs)}")
for x in sorted(qs, key=lambda y: -(y[5] / y[4])):
    print(f"      {x[0]:38s} fps={x[1]:8.3f} max_stall={x[5]:8.3f} span={x[4]} ratio={x[5]/x[4]:.3f}")
mid = [x for x in adv_slow if 0.2 <= (x[5] or 0) / x[4] < 0.43]
print(f"[I7] mid-range stall (0.20<=ratio<0.43) among slow windows: {len(mid)}")
for x in sorted(mid, key=lambda y: -(y[5] or 0) / y[4])[:8]:
    print(f"      {x[0]:38s} fps={x[1]:8.3f} ratio={(x[5] or 0)/x[4]:.3f}")

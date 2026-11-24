import os, hashlib, json, datetime
from collections import Counter
from collections import defaultdict
from PIL import Image, ImageChops

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
GUARD = os.path.realpath(ROOT)

def ok(p):
    rp = os.path.realpath(p)
    if not (rp == GUARD or rp.startswith(GUARD + os.sep)):
        raise SystemExit("path outside data root: " + rp)
    return rp

def fsha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()

rootbase = ROOT.rsplit("\\", 1)[-1]
rows = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    rp = os.path.realpath(dirpath)
    if not rp.startswith(GUARD):
        continue
    for fn in filenames:
        if fn.startswith("measure_w") and fn.endswith("_end_x.png"):
            p = ok(dirpath + "\\" + fn)
            st = os.stat(p)
            sub = os.path.basename(dirpath)
            if sub == rootbase:
                sub = "<ROOT>"
            rows.append({"label": sub + "/" + fn, "dir": sub, "file": fn, "path": p, "size": st.st_size,
                         "mtime": st.st_mtime,
                         "mtime_s": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")})

print("total end_x pngs:", len(rows))
print("by dir:", dict(Counter(r["dir"] for r in rows)))

for r in rows:
    r["fsha"] = fsha(r["path"])
    im = Image.open(r["path"])
    rgb = im.convert("RGB")
    r["wh"] = im.size
    r["psha"] = hashlib.sha256(rgb.tobytes()).hexdigest()

print()
print("== file-bytes groups (sha256 -> members, only multi)")
g = defaultdict(list)
for r in rows:
    g[r["fsha"]].append(r)
for k, v in sorted(g.items(), key=lambda kv: -len(kv[1])):
    if len(v) > 1:
        print(k[:16], "size=", v[0]["size"], "n=%d" % len(v))
        for r in v:
            print("    ", r["label"], r["mtime_s"])
print("singletons(file):", sum(1 for k, v in g.items() if len(v) == 1))

print()
print("== pixel groups (decoded-RGB sha256 -> members, only multi)")
pg = defaultdict(list)
for r in rows:
    pg[r["psha"]].append(r)
npx = 0
for k, v in sorted(pg.items(), key=lambda kv: -len(kv[1])):
    if len(v) > 1:
        npx += 1
        fshas = set(x["fsha"] for x in v)
        print(k[:16], "n=%d" % len(v), "wh=%s" % (v[0]["wh"],), "bytes_same=%s" % (len(fshas) == 1))
        for r in v:
            print("    ", r["label"], "fsha=", r["fsha"][:16])
print("pixel-dup groups:", npx, " singletons(pixel):", sum(1 for k, v in pg.items() if len(v) == 1))
sub_rows = [r for r in rows if r["dir"] != "<ROOT>"]
print("independent pictures 27-universe =", len(pg), " 25-subdir-universe =", len(set(r["psha"] for r in sub_rows)))
print("file-unique pictures  27-universe =", len(g), " 25-subdir-universe =", len(set(r["fsha"] for r in sub_rows)))

print()
print("== group A mtimes vs own-trip measure json t_abs0")
A = {"archive_T33/measure_w2_end_x.png": ("archive_T33", "w2"),
     "archive_T42/measure_w1_end_x.png": ("archive_T42", "w1"),
     "archive_T42/measure_w2_end_x.png": ("archive_T42", "w2"),
     "archive_T45/measure_w2_end_x.png": ("archive_T45", "w2")}
by_label = dict((r["label"], r) for r in rows)
for lbl in A:
    d, w = A[lbl]
    r = by_label.get(lbl)
    if not r:
        print("MISSING", lbl)
        continue
    jp = ok(GUARD + "\\" + d + "\\measure_" + w + ".json")
    with open(jp, "r", encoding="utf-8") as fh:
        mj = json.load(fh)
    delta = r["mtime"] - mj["t_abs0"]
    print("%s mtime=%.7f (%s)  measure_%s t_abs0=%.7f  delta=%+.4fus (%+.3fms)" % (
        lbl, r["mtime"], r["mtime_s"], w, mj["t_abs0"], delta * 1e6, delta * 1e3))

print()
print("== group B mtimes")
for lbl in ("archive_T36/measure_w1_end_x.png", "archive_T38/measure_w1_end_x.png"):
    r = by_label.get(lbl)
    if r:
        print(lbl, "mtime=%.9f" % r["mtime"], r["mtime_s"], "size=", r["size"], "fsha=", r["fsha"][:16], "psha=", r["psha"][:16])

print()
print("== C12 timer-region diff (430,118)-(640,150), w1 vs w2 per trip")
for d in ("archive_T33", "archive_T34", "archive_T45"):
    p1 = GUARD + "\\" + d + "\\measure_w1_end_x.png"
    p2 = GUARD + "\\" + d + "\\measure_w2_end_x.png"
    if os.path.exists(ok(p1)) and os.path.exists(ok(p2)):
        a = Image.open(p1).convert("RGB").crop((430, 118, 640, 150))
        b = Image.open(p2).convert("RGB").crop((430, 118, 640, 150))
        df = ImageChops.difference(a, b)
        mx = max(hi for lo, hi in df.getextrema())
        print(d, "maxdiff=", mx, "bbox=", df.getbbox())

print()
print("== C10 whole-image diff T42/w1 vs T33/w2")
a = Image.open(by_label["archive_T42/measure_w1_end_x.png"]["path"]).convert("RGB")
b = Image.open(by_label["archive_T33/measure_w2_end_x.png"]["path"]).convert("RGB")
df = ImageChops.difference(a, b)
print("bbox=", df.getbbox(), "extrema=", df.getextrema())

print()
print("== root two pngs")
for r in rows:
    if r["dir"] == "<ROOT>":
        print(r["label"], "size=", r["size"], "mtime=%.9f" % r["mtime"], r["mtime_s"], "fsha=", r["fsha"][:16], "psha=", r["psha"][:16])

print()
print("== full listing sorted")
for r in sorted(rows, key=lambda x: (x["dir"], x["file"])):
    print("%-46s %7d %s fsha=%s psha=%s" % (r["label"], r["size"], r["mtime_s"], r["fsha"][:16], r["psha"][:16])
)

"""V1 probe A: inventory all measure_w*_end_x.png under qc161_u0400_trip (read-only)."""
import os, glob, hashlib
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

files = sorted(glob.glob(os.path.join(ROOT, "*", "measure_w*_end_x.png")))
print("matched under <trip>/ :", len(files))
root_files = sorted(glob.glob(os.path.join(ROOT, "measure_w*_end_x.png")))
print("matched at ROOT dir  :", len(root_files), root_files)

rows = []
for f in files + root_files:
    st = os.stat(f)
    fh = hashlib.sha256(open(f, "rb").read()).hexdigest()
    im = Image.open(f)
    rgb = im.convert("RGB")
    ph = hashlib.sha256(rgb.tobytes()).hexdigest()
    rel = f[len(ROOT) + 1:].replace("\\", "/")
    rows.append((rel, ph, fh))
    print("%-45s %8d %sx%s mode=%s pixsha=%s filesha=%s" % (
        rel, st.st_size, rgb.width, rgb.height, im.mode, ph[:16], fh[:16]))

print()
print("=== duplicate groups by pixsha(RGB raw) ===")
by = {}
for rel, ph, fh in rows:
    by.setdefault(ph, []).append(rel)
dup = [v for v in by.values() if len(v) > 1]
dup.sort(key=lambda x: -len(x))
for i, g in enumerate(dup, 1):
    print("GROUP %d n=%d" % (i, len(g)))
    for x in g:
        print("     ", x)
print("distinct pixsha: %d of %d" % (len(by), len(rows)))

print()
print("=== duplicate groups by filesha(png bytes) ===")
by2 = {}
for rel, ph, fh in rows:
    by2.setdefault(fh, []).append(rel)
dup2 = [v for v in by2.values() if len(v) > 1]
for i, g in enumerate(dup2, 1):
    print("FILEGROUP %d n=%d %s" % (i, len(g), g))
print("distinct filesha: %d of %d" % (len(by2), len(rows)))

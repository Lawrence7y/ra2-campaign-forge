"""V2-RECHECK pixel pass (read-only on source images; crops written into this V2 dir).

Step 1: localize the score panel objectively: diff archive_T33/w1 (has a table per §543)
        against archive_T33/w2 (the 4-way byte-identical image) -> bounding box of difference.
Step 2: for all 27 end pngs, measure distance to the "no-table backdrop" and report bbox fill.
Step 3: within-trip w1 vs w2 pixel diff (tests §543 'maxdiff=0' claims) globally and inside the box.

Run: python -I -X utf8 v2r_pix1.py
"""
import os, glob, hashlib, json
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)

def load(rel):
    im = Image.open(os.path.join(R, rel.replace("/", os.sep)))
    return im, np.asarray(im.convert("RGB")).astype(np.int16)

a_im, a = load("archive_T33/measure_w1_end_x.png")
b_im, b = load("archive_T33/measure_w2_end_x.png")
print("[X1] T33/w1", a_im.size, a_im.mode, "| T33/w2", b_im.size, b_im.mode)
d = np.abs(a - b).max(axis=2)
print("[X2] whole-image maxdiff(T33w1,T33w2) =", d.max(), " pixels differing =", int((d > 0).sum()),
      " frac =", round(float((d > 0).mean()), 5))
ys, xs = np.where(d > 16)
print("[X3] bbox of strong difference rows/cols:",
      "x", (int(xs.min()), int(xs.max())), "y", (int(ys.min()), int(ys.max())),
      " w=", int(xs.max()) - int(xs.min()) + 1, " h=", int(ys.max()) - int(ys.min()) + 1)
# column profile to find the panel rectangle
colcount = (d > 16).sum(axis=0)
rowcount = (d > 16).sum(axis=1)
print("[X4] rows with >200 differing px:", np.where(rowcount > 200)[0][:5], "...", np.where(rowcount > 200)[0][-5:] if (rowcount > 200).any() else "none")
print("[X4] cols with >200 differing px:", np.where(colcount > 200)[0][:5], "...", np.where(colcount > 200)[0][-5:] if (colcount > 200).any() else "none")
Image.fromarray(np.abs(a - b).max(axis=2).astype(np.uint8) * 4).save(os.path.join(OUT, "diff_T33w1_vs_T33w2.png"))

# Reference backdrop = the 4-way identical image
ref_rel = "archive_T33/measure_w2_end_x.png"
_, ref = load(ref_rel)
print("\n[X5] distance of every end png to the backdrop", ref_rel)
pngs = sorted(glob.glob(os.path.join(R, "*", "measure_w*_end_*.png"))) + sorted(glob.glob(os.path.join(R, "measure_w*_end_*.png")))
for q in pngs:
    rel = os.path.relpath(q, R).replace("\\", "/")
    im, arr = load(rel)
    if arr.shape != ref.shape:
        print(f"    {rel:46s} SHAPE MISMATCH {arr.shape}")
        continue
    dd = np.abs(arr - ref).max(axis=2)
    n = int((dd > 24).sum())
    print(f"    {rel:46s} size={im.size} maxdiff={dd.max():4d} ndiff>24={n:8d} frac={n/dd.size:.5f} "
          f"sha={hashlib.sha256(open(q,'rb').read()).hexdigest()[:8]}")

print("\n[X6] within-trip w1 vs w2 (the §543 evidence-2 'maxdiff=0' claims)")
for dr in sorted({p.split(os.sep)[-2] for p in pngs if os.path.dirname(p) != R}):
    w1 = os.path.join(R, dr, "measure_w1_end_x.png")
    w2 = os.path.join(R, dr, "measure_w2_end_x.png")
    if os.path.exists(w1) and os.path.exists(w2):
        _, x1 = load(f"{dr}/measure_w1_end_x.png")
        _, x2 = load(f"{dr}/measure_w2_end_x.png")
        dd = np.abs(x1 - x2)
        gm = int(dd.max())
        px = int((dd.max(axis=2) > 0).sum())
        print(f"    {dr:22s} whole maxdiff={gm:4d} differing_px={px:9d} frac={px/dd.size:.6f} "
              f"byte-identical={hashlib.sha256(open(w1,'rb').read()).hexdigest() == hashlib.sha256(open(w2,'rb').read()).hexdigest()}")

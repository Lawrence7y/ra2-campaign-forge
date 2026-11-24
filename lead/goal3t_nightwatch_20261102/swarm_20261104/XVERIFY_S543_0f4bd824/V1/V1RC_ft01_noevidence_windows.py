"""Read-only probe #15 (mine): the two frozen windows that S543/V1 listed as 'no image evidence'
but whose trip DOES have a score-panel frame_target_01.png - check when that shot was taken."""
import os, json, glob, time
import numpy as np
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
for td in ("l1_20261023", "", "archive_T32", "archive_T47", "l1_20261023b"):
    d = os.path.join(R, td) if td else R
    ft = os.path.join(d, "frame_target_01.png")
    if not os.path.exists(ft):
        print(f"{td or '<root>'}: no frame_target_01.png"); continue
    a = np.asarray(Image.open(ft).convert("RGB"), dtype=np.int16)
    m = (a[..., 0] > 200) & (a[..., 1] > 200) & (a[..., 2] < 110) & ((a[..., 0] - a[..., 2]) > 60)
    t, h = int(m[9:24, 400:800].sum()), int(m[160:175, 99:529].sum())
    st = os.stat(ft)
    js = []
    for p in sorted(glob.glob(os.path.join(d, "measure_w*.json"))):
        dd = json.load(open(p, encoding="utf-8"))
        fe = dd.get("frame_edges") or []
        js.append((os.path.basename(p), (fe[0][0] if fe else None), (fe[-1][0] if fe else None),
                   round(dd["t_abs0"], 1), round(dd["t_abs0"] + dd["span_s"], 1)))
    print(f"{td or '<root>'}: frame_target_01 title={t} hdr={h} mtime={st.st_mtime:.1f} "
          f"({time.strftime('%m-%d %H:%M:%S', time.localtime(st.st_mtime))})")
    for j in js:
        print(f"      {j[0]}: f0={j[1]} f1={j[2]} win=[{j[3]},{j[4]}]  ft01_mtime - win_end = {st.st_mtime - j[4]:+.1f} s")

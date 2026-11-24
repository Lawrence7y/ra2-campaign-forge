import os
import glob
import hashlib
from PIL import Image

BASE_DIR = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
pattern = os.path.join(BASE_DIR, "**", "measure_w*_end_x.png")
png_files = sorted(glob.glob(pattern, recursive=True))

print(f"Total measure_w*_end_x.png found: {len(png_files)}")
for idx, p in enumerate(png_files):
    rel = os.path.relpath(p, BASE_DIR)
    img = Image.open(p)
    raw = img.convert("RGB").tobytes()
    sha = hashlib.sha256(raw).hexdigest()
    print(f"[{idx:02d}] {rel} | size={img.size} | mode={img.mode} | sha256_rgb={sha[:16]}")

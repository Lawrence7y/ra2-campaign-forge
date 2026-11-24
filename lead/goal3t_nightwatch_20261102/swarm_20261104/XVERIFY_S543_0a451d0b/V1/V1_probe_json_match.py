import os
import glob
import json

BASE_DIR = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"

png_files = sorted(glob.glob(os.path.join(BASE_DIR, "*", "measure_w*_end_x.png")))

print(f"Total files: {len(png_files)}")
for p in png_files:
    rel = os.path.relpath(p, BASE_DIR)
    json_path = p.replace("_end_x.png", ".json")
    has_json = os.path.exists(json_path)
    info = ""
    if has_json:
        try:
            data = json.load(open(json_path, encoding="utf-8"))
            edges = data.get("frame_edges", [])
            f0 = edges[0][0] if edges else None
            f1 = edges[-1][0] if edges else None
            df = f1 - f0 if (f0 is not None and f1 is not None) else None
            dur = edges[-1][1] - edges[0][1] if edges else None
            stats = data.get("stats", {})
            fps_avg = stats.get("fps_avg")
            info = f"f0={f0}, f1={f1}, df={df}, dur={dur:.2f}s, fps_avg={fps_avg}"
        except Exception as e:
            info = f"json error: {e}"
    else:
        info = "NO JSON"
    print(f"{rel:40s} | {info}")

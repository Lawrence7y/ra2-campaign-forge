"""V2 asserted l3_1101v4b contributes no window and that §535's '2.9 fps slow crawl' cannot come
from these files. The same directory holds h8_wait_trace.json. Check what that channel says about
whether v4-b's frame counter advances. Read-only."""
import os, json, statistics

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

for dr in ["l3_1101v4b", "l3_1101v4e", "l3_1101v3c"]:
    p = os.path.join(R, dr, "h8_wait_trace.json")
    if not os.path.exists(p):
        print("[W]", dr, "NO h8_wait_trace.json")
        continue
    d = json.load(open(p, encoding="utf-8"))
    print("=" * 90)
    print("[W]", dr, "| keys:", list(d)[:15] if isinstance(d, dict) else type(d))
    s = json.dumps(d, ensure_ascii=False)
    print("    file size:", os.path.getsize(p), "json chars:", len(s))
    print("    head:", s[:700])
    # hunt for frame series
    def find_frames(o, path=""):
        out = []
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, list) and v and isinstance(v[0], (int, float, list, dict)):
                    out.append((path + "/" + k, type(v[0]).__name__, len(v)))
                elif isinstance(v, dict):
                    out.extend(find_frames(v, path + "/" + k))
                elif "frame" in k.lower():
                    out.append((path + "/" + k, "scalar", json.dumps(v)[:120]))
        return out

    for row in find_frames(d)[:25]:
        print("   ", row)

"""Read-only probe #8 (mine): joint fields<->disk reconciliation + byte identity of the 27
end-window pngs against every other png in the trip tree + the l1_20261023e4 forensic payload."""
import os, json, glob, hashlib
from collections import defaultdict

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

recs = {}
for fp in sorted(glob.glob(os.path.join(ROOT, "**", "qc151_fields.json"), recursive=True)):
    d = os.path.relpath(os.path.dirname(fp), ROOT).replace("\\", "/")
    for e in json.load(open(fp, encoding="utf-8")):
        if e.get("group") == "MEASURE" and str(e.get("key", "")).startswith("measure_forensics_w"):
            v = e["value"]
            recs[(d, v.get("window"))] = v
print("qc151_fields.json files:", len(glob.glob(os.path.join(ROOT, "**", "qc151_fields.json"), recursive=True)))
print("forensic measure records:", len(recs))
disk = {os.path.relpath(p, ROOT).replace("\\", "/")
        for p in glob.glob(os.path.join(ROOT, "**", "measure_w*_end_x.png"), recursive=True)}
print("end_x png on disk:", len(disk))

agree, missing, extra = 0, [], []
for (td, win), v in sorted(recs.items()):
    rel = (td + "/" + f"measure_w{win}_end_x.png").lstrip("./")
    claims = bool(v.get("empty_window")) and bool(v.get("forensics_png"))
    ondisk = rel in disk
    if claims == ondisk:
        agree += 1
    else:
        (missing if claims else extra).append(
            (td, win, "empty_window=%s png=%s capture_ok=%s" % (v.get("empty_window"), v.get("forensics_png"), v.get("capture_ok")),
             "current_frame=%s focus_ok=%s fg_title=%r" % (v.get("current_frame"), v.get("focus_ok"), v.get("fg_title"))))
print(f"records agreeing with disk: {agree}/{len(recs)}")
print("RECORD CLAIMS PNG, DISK HAS NONE:", missing)
print("DISK HAS PNG, RECORD DOES NOT CLAIM ONE:", extra)

print("\n-- non-empty-window records whose window still has a png on disk (should be none) --")
for (td, win), v in sorted(recs.items()):
    rel = (td + "/" + f"measure_w{win}_end_x.png").lstrip("./")
    if rel in disk and not v.get("empty_window"):
        print("  ", td, win, v.get("current_frame"))

print("\n-- byte identity of end_x pngs vs all other pngs in the tree --")
bysha = defaultdict(list)
for p in glob.glob(os.path.join(ROOT, "**", "*.png"), recursive=True):
    bysha[fsha(p)].append(os.path.relpath(p, ROOT).replace("\\", "/"))
for rel in sorted(disk):
    sib = sorted(x for x in bysha[fsha(os.path.join(ROOT, rel.replace("/", os.sep)))] if x != rel)
    if sib:
        print(f"{rel:44s} byte-identical to {len(sib)} other file(s): {sib[:6]}{' ...' if len(sib)>6 else ''}")

print("\n-- l1_20261023e4 forensic payloads --")
for (td, win), v in sorted(recs.items()):
    if "20261023E4" in td.upper():
        print("  ", td, win, json.dumps(v, ensure_ascii=False))

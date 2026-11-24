import os

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
GUARD = os.path.realpath(ROOT)
n = 0
hit = 0
locs = {}
for dirpath, dirnames, filenames in os.walk(ROOT):
    rp = os.path.realpath(dirpath)
    if not rp.startswith(GUARD):
        continue
    for fn in filenames:
        if fn.startswith("except_post") and fn.endswith(".txt"):
            p = os.path.realpath(dirpath + "\\" + fn)
            if not p.startswith(GUARD):
                continue
            n += 1
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(400)
            if "EXCEPTION_SINGLE_STEP" in head and "007CFC9F" in head:
                hit += 1
            else:
                print("DIFFERENT:", p)
            key = os.path.basename(dirpath)
            locs[key] = locs.get(key, 0) + 1
print("total except_post files:", n, " with SINGLE_STEP@007CFC9F:", hit)
print("by dir:", locs)

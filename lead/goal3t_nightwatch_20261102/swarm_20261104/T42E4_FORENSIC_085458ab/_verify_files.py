import json, os, datetime, hashlib

ROOT = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
T42 = ROOT + r"\archive_T42"
E4 = ROOT + r"\l1_20261023e4"

def st(p):
    s = os.stat(p)
    return s.st_size, datetime.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], s.st_mtime

print("== C6 launch/carrier evidence")
for lbl, p in [
    ("E4 _launch_result.json", E4 + r"\_launch_result.json"),
    ("E4 carrier_delete_result.json", E4 + r"\carrier_delete_result.json"),
]:
    with open(p, "r", encoding="utf-8") as fh:
        raw = fh.read()
    print("--", lbl, "size=", len(raw))
    try:
        d = json.loads(raw)
        print(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True))
    except Exception as ex:
        print("NOT JSON:", ex, raw[:400])

print()
print("archive_T42 _launch_result.json exists:", os.path.exists(T42 + r"\_launch_result.json"))
sz, mt, _ = st(T42 + r"\T42_console.log")
print("T42_console.log size=%d mtime=%s" % (sz, mt))
with open(ROOT + r"\T42_console.exitcode", "rb") as fh:
    print("T42_console.exitcode content:", fh.read())

print()
print("== C7 archive_T42 mtime census (window start = 2026-10-18 16:10:15)")
cut = datetime.datetime(2026, 10, 18, 16, 10, 15).timestamp()
ents = sorted(os.scandir(T42), key=lambda e: e.stat().st_mtime)
total = 0; old = []
for e in ents:
    if e.is_file():
        total += 1
        m = e.stat().st_mtime
        if m < cut:
            dt = datetime.datetime.fromtimestamp(m)
            old.append((dt.strftime("%H:%M:%S"), e.name))
print("total files:", total)
print("files older than 16:10:15:", len(old))
from collections import Counter
c = Counter(x[0][:5] for x in old)
for k in sorted(c):
    print("  ", k, "x", c[k])
for t, n in old:
    print("   ", t, n)

print()
print("== E4 top-level file census")
ents4 = sorted(os.scandir(E4), key=lambda e: e.stat().st_mtime)
files4 = [e.name for e in ents4 if e.is_file()]
print("count:", len(files4))
mts = [e.stat().st_mtime for e in ents4 if e.is_file()]
print("mtime range: %s .. %s" % (datetime.datetime.fromtimestamp(min(mts)).strftime("%H:%M:%S.%f")[:-3], datetime.datetime.fromtimestamp(max(mts)).strftime("%H:%M:%S.%f")[:-3]))
subdirs = [e.name for e in ents4 if e.is_dir()]
print("subdirs:", subdirs)

# -*- coding: utf-8 -*-
"""RE_ATLAS_REASSESS §0/§1 fingerprint re-computation (hashlib, read-only inputs).
Invoke: python -I -X utf8 <absolute path to this file>
Only reads files; writes nothing. Output is plain UTF-8 text on stdout.
"""
import hashlib
import os
import datetime

ROOT = r"D:\Project\ra2-campaign-forge"
TZ8 = datetime.timezone(datetime.timedelta(hours=8))

TARGETS = [
    r"ra2bench\gamemd.exe",
    r"re_atlas\STATUS.md",
    r"re_atlas\LEDGER.md",
    r"re_atlas\INDEX.md",
    r"re_atlas\CONFLICTS.md",
    r"re_atlas\HANDOFF_TO_GOAL3T.md",
    r"lead\re_atlas_reassess_20261112\step1_fingerprint.stdout.txt",
    r"lead\re_atlas_reassess_20261112\step2_r036_rerun.stdout.md",
    r"lead\re_atlas_reassess_20261112\step2_verify_r035.stdout.txt",
    r"lead\re_atlas_reassess_20261112\step1_re_atlas_manifest.tsv",
]

print("now_local=%s" % datetime.datetime.now(TZ8).strftime("%Y-%m-%d %H:%M:%S%z"))
print("now_utc=%s" % datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z"))
print("field_order=relpath\tbytes\tsha256\tmtime_local(+08:00)\tmtime_utc\tlines")
for rel in TARGETS:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        print("%s\tMISSING" % rel)
        continue
    with open(p, "rb") as f:
        data = f.read()
    st = os.stat(p)
    sha = hashlib.sha256(data).hexdigest()
    lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
    mt_l = datetime.datetime.fromtimestamp(st.st_mtime, TZ8).strftime("%Y-%m-%d %H:%M:%S")
    mt_u = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print("%s\t%d\t%s\t%s\t%s\t%d" % (rel, len(data), sha, mt_l, mt_u, lines))
print("END")

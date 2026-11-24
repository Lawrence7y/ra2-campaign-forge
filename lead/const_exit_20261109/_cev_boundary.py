# -*- coding: utf-8 -*-
"""_cev_boundary.py -- step ⑥: boundary / no-write / no-gate-rerun check."""
import hashlib
import json
import os
import sys
import time
from datetime import datetime

sys.dont_write_bytecode = True
ROOT = r"D:/Project/ra2-campaign-forge"
WD = os.path.join(ROOT, "lead", "const_exit_20261109")
os.chdir(ROOT)

BASELINE = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/k1bit_detect_20261109/_kd_detect_out.json": ("00f77fe0d5582d8eaec42f1b908d9f48c4b94b65b0b09b3b1e4609280f7ac239", 251854),
    "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md": ("a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798", 63656),
    "lead/refsync_scope_20261109/REFSYNC_SCOPE_FIX.md": ("83b215ccbbf2c3e221c247e7bd9c7c221fddcf9472977d2df8902bf1b94ec65e", 49958),
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py": ("179f3af88fac380437311fe4c52f2d8367733f3b92c8b13ab99cb742d12544a2", 38317),
    "lead/detect_triage_20261109/DETECT_TRIAGE.md": ("579b76ce50cdca0e5e2c2cfebaf8b8f8346f673cba7b89822c4c415c28564e50", 45228),
}

fp = {}
for f, (want_sha, want_bytes) in BASELINE.items():
    b = open(f, "rb").read()
    sha, n = hashlib.sha256(b).hexdigest(), len(b)
    fp[f] = dict(sha256=sha, bytes=n, expected_sha256=want_sha,
                 expected_bytes=want_bytes,
                 ok=(sha == want_sha and n == want_bytes))

# All files I created / wrote in this task
mine = sorted(f for f in os.listdir(WD) if f.startswith("_cev_"))
non_cev_writes = [f for f in mine if not f.startswith("_cev_")]

# Protected dirs: any __pycache__ (would prove bytecode writes) and any file
# whose mtime is >= the write-domain's earliest _ce_ file mtime.
PROTECTED = [
    "lead/k1bit_detect_20261109", "lead/detect_triage_20261109",
    "lead/stale_pass_20261109", "lead/refsync_scope_20261109",
    "lead/goal1_a8_fix_20261022", "lead/d27_ruling_20261106",
    "lead/d28_ruling_20261106", "lead/d29_ruling_20261106",
    "lead/d30_ruling_20261106", "lead/masking_effect_20261109",
]
ref = min(os.path.getmtime(os.path.join(WD, f)) for f in os.listdir(WD)
          if f.startswith("_ce_") and f.endswith(".py"))
# use first _ce_* file timestamp as "task start"
start = min(os.path.getmtime(os.path.join(WD, f)) for f in os.listdir(WD)
            if f.startswith("_ce_"))
recent, pycache = [], []
for d in PROTECTED:
    for dp, dn, fn in os.walk(d):
        if "__pycache__" in dn:
            pycache.append(os.path.join(dp, "__pycache__").replace("\\", "/"))
        for f in fn:
            p = os.path.join(dp, f)
            try:
                m = os.path.getmtime(p)
            except OSError:
                continue
            if m >= start:
                recent.append([p.replace("\\", "/"),
                               datetime.fromtimestamp(m).isoformat()])

# Also: writes made by ANY of my scripts?  List every open(...,'w') in my files.
import re
writes = {}
for f in mine:
    if not f.endswith(".py"):
        continue
    t = open(os.path.join(WD, f), encoding="utf-8").read()
    hits = [l.strip() for l in t.split("\n")
            if re.search(r"open\([^)]*['\"][wa]", l) or "json.dump(" in l
            or "Path(" in l and ".write" in l]
    writes[f] = hits

out = dict(fingerprints=fp, n_baselines_ok=sum(1 for v in fp.values() if v["ok"]),
           my_files=mine, non_cev_prefixed_files=non_cev_writes,
           write_domain_mtime_floor_iso=datetime.fromtimestamp(start).isoformat(),
           protected_files_modified_at_or_after_task_start=recent,
           protected_pycache_dirs=pycache,
           write_statements_in_my_scripts=writes)
with open(os.path.join(WD, "_cev_boundary_out.json"), "w", encoding="utf-8") as fo:
    json.dump(out, fo, ensure_ascii=False, indent=1)

print("baselines ok:", out["n_baselines_ok"], "/ 7")
for f, v in fp.items():
    print("  ", "OK" if v["ok"] else "MISMATCH", f, v["bytes"], v["sha256"][:12])
print("my _cev_ files:", len(mine))
for f in mine:
    print("   ", f)
print("non-_cev_ prefixed files created by me:", non_cev_writes)
print("task-start floor:", out["write_domain_mtime_floor_iso"])
print("protected files modified at/after task start:", len(recent))
for p, m in recent[:30]:
    print("   ", m, p)
print("protected __pycache__ dirs:", pycache)
print("\nwrite statements in my scripts:")
for f, hs in writes.items():
    print("  ", f)
    for h in hs:
        print("      ", h[:160])

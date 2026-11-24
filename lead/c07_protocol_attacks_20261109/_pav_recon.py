# -*- coding: utf-8 -*-
# _pav_recon.py — 复核员独立复算攻击报告第〇步侦察论断（只读）。
# 独立实现（不 import 攻样本脚本）；口径对齐报告：SESSION_RE 同门禁 :55-56。
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
SESSION_RE = re.compile(
    r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")
TASK_RE = re.compile(r"TASK-\d{8}-[A-Za-z0-9\-]+")
ANTI_COPY = [
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
]
EXTS = {".md", ".json", ".py", ".txt"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".zcode"}
FOREIGN = "sess_dwf-dwfrun-25327efe-e66d-4587-a1bd-c1192ae072e1-actor_1_1"
SYNTH = "sess_dwf-dwfrun-7c4e21af-95d3-4b82-a6c1-5d09e2f7b3a0-actor_4_2"
TARGET_TASK = "TASK-20261108-C07-01"


def normalize_id(s):
    t = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in t if not ch.isspace() and unicodedata.category(ch) != "Cf").casefold()


reg = set()
for rel in ANTI_COPY:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        obj = json.loads(f.read().decode("utf-8"))
    recs = obj if isinstance(obj, list) else obj.get("records", []) if isinstance(obj, dict) else []
    for r in recs:
        if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
            reg.add(r["reviewerSessionId"])
reg_norm = {normalize_id(x) for x in reg}
print("registered_base=%d ids=%s" % (len(reg), sorted(reg)))

hits = defaultdict(list)      # sid -> [(relpath, line)]
task_hits = defaultdict(list)
nfiles = 0
for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "lead")):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if os.path.splitext(fn)[1].lower() not in EXTS:
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT).replace("\\", "/")
        try:
            if os.path.getsize(p) > 4 * 1024 * 1024:
                continue
            text = open(p, "rb").read().decode("utf-8", errors="ignore")
        except OSError:
            continue
        nfiles += 1
        for i, line in enumerate(text.splitlines(), 1):
            for m in SESSION_RE.finditer(line):
                hits[m.group(0)].append((rel, i))
            for m in TASK_RE.finditer(line):
                if m.group(0) == TARGET_TASK:
                    task_hits[TARGET_TASK].append((rel, i))

print("files_scanned=%d unique_session_ids=%d unregistered=%d"
      % (nfiles, len(hits), sum(1 for s in hits if normalize_id(s) not in reg_norm)))


def doms(locs):
    return sorted({l.split("/")[1] if l.startswith("lead/") else l.split("/")[0] for l, _ in locs})


print("\n-- per-ID summary (all IDs) --")
for sid in sorted(hits, key=lambda s: -len(hits[s])):
    locs = hits[sid]
    cls = "REG" if normalize_id(sid) in reg_norm else "unreg"
    if len(locs) >= 5 or cls == "REG" or sid in (FOREIGN, SYNTH):
        print("[%s] %s occ=%d domains=%d %s" % (cls, sid, len(locs), len(doms(locs)), doms(locs)))
print("(other IDs with <5 occ suppressed)")

print("\n-- target probes --")
for sid in (FOREIGN, SYNTH):
    locs = hits.get(sid, [])
    print("%s occ=%d domains=%s" % (sid, len(locs), doms(locs)))
    for l in locs:
        print("   %s:%d" % l)
print("%s occ=%d domains=%s" % (TARGET_TASK, len(task_hits.get(TARGET_TASK, [])), doms(task_hits.get(TARGET_TASK, []))))
outside_attack = [l for l, _ in task_hits.get(TARGET_TASK, []) if not l.startswith("lead/c07_protocol_attacks_20261109")]
print("TASK outside attack domain=%d %s" % (len(outside_attack), outside_attack[:10]))
synth_outside = [l for l, _ in hits.get(SYNTH, []) if not l.startswith("lead/c07_protocol_attacks_20261109")]
print("SYNTH outside attack domain=%d %s" % (len(synth_outside), synth_outside))

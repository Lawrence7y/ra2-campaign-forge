# -*- coding: utf-8 -*-
"""_dtv_scope2.py -- broader out-of-census enumeration.

For EVERY *.py basename appearing in the two ledgers OR the read-only
deliverable, locate all live files via the Bash-find index, and run kd.analyse
on those not in the 173 census.  Also report which of the resulting CONFIRMED
pieces have their basename on any cited PASS line in the ledgers/deliverable.
Read-only outside the write domain; bytecode writing disabled.
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1]).resolve()
WD = ROOT / "lead/detect_triage_20261109"
KD = ROOT / "lead/k1bit_detect_20261109"
CF = ROOT / "lead/check_family_20261109"
RS = ROOT / "lead/refsync_scope_20261109"

spec = importlib.util.spec_from_file_location("_dtv_kd2", KD / "_kd_detect.py")
kd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kd)

census = set()
for ln in (CF / "_cf_filelist.txt").read_text(encoding="utf-8").splitlines():
    t = ln.strip()
    if t:
        census.add(t[2:] if t.startswith("./") else t)

allpy = []
for ln in (WD / "_dtv_allpy.txt").read_text(encoding="utf-8",
                                           errors="replace").splitlines():
    t = ln.strip()
    if t:
        allpy.append(t[2:] if t.startswith("./") else t)
name_to_all = {}
for rel in allpy:
    name_to_all.setdefault(Path(rel).name, []).append(rel)

ledgers = [ROOT / "lead/PENDING_DECISIONS.md",
           ROOT / "lead/GOAL_THREE_TARGETS_20261018.md"]
deliv = RS / "REFSYNC_SCOPE_FIX.md"
texts = [(p.name, p.read_text(encoding="utf-8")) for p in ledgers + [deliv]]
union_names = set()
for _, t in texts:
    union_names.update(re.findall(r"[A-Za-z0-9_]+\.py", t))

pass_re = re.compile(r"exit\s*=\s*0|PASS|门禁|SELF_TEST", re.I)
cited_names = set()
cited_lines = []
for fname, t in texts:
    for i, s in enumerate(t.splitlines(), 1):
        if pass_re.search(s):
            for nm in re.findall(r"[A-Za-z0-9_]+\.py", s):
                cited_names.add(nm)
                cited_lines.append("%s:%d" % (fname, i))

probes = []
for nm in sorted(union_names):
    for rel in name_to_all.get(nm, []):
        if rel in census:
            continue
        p = ROOT / rel
        if not p.is_file():
            continue
        a = kd.analyse(rel, p.read_bytes())
        if a["verdict"] == "CONFIRMED_K1BIT":
            srcs = []
            for fname, t in texts:
                for i, s in enumerate(t.splitlines(), 1):
                    if pass_re.search(s) and nm in s:
                        srcs.append("%s:%d" % (fname, i))
            probes.append(dict(rel=rel, sha256=a["sha256"], bytes=a["bytes"],
                               has_k=a["has_k"], attribution=a["attribution"],
                               collapse=[c["kind"] for c in a["collapse"]],
                               name_cited_on_pass_line=(nm in cited_names),
                               cited_lines=srcs))

out = dict(n_union_names=len(union_names), n_all_py=len(allpy),
           n_census=len(census), n_cited_names=len(cited_names),
           n_out_of_census_confirmed=len(probes), probes=probes)
(WD / "_dtv_scope2_out.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
print("WROTE", (WD / "_dtv_scope2_out.json").as_posix())

# -*- coding: utf-8 -*-
"""_oev_3.py -- boundary / no-modification / no-new-seal / supporting checks.

Read-only over forbidden domains. Only writes _oev_3_out.json in the allowed
write domain. No game processes, no sampling code.

Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oev_3.py"
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WDIR = ROOT / "lead" / "ordering_evidence_20261109"
TZ8 = timezone(timedelta(hours=8))
OUT: dict = {}


def local(e):
    return datetime.fromtimestamp(e, TZ8).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


RO_DIRS = ["lead/seal_chronology_20261109", "lead/oracle_spec_20261109",
           "lead/cert_realcheck_20261109", "lead/gate_pipeline_20261109",
           "lead/gate_r9sem_20261109"]
RO_FILES = ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]

# boundary: earliest mtime of the reviewed task's own outputs
wd_times = [p.stat().st_mtime for p in WDIR.iterdir()
            if p.is_file() and p.name.startswith("_oe_")]
TASK_START = min(wd_times)
OUT["task_start_inferred_from_oe_files"] = local(TASK_START)
OUT["n_oe_files"] = len(wd_times)

# list any file in the 5 RO dirs / 2 ledgers modified after task start
modified_after = []
ro_file_count = 0
for d in RO_DIRS:
    for dirpath, dirnames, filenames in os.walk(ROOT / d):
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                st = p.stat()
            except OSError:
                continue
            ro_file_count += 1
            if st.st_mtime > TASK_START:
                modified_after.append({"rel": str(p.relative_to(ROOT)).replace("\\", "/"),
                                       "mtime": local(st.st_mtime), "bytes": st.st_size})
for rel in RO_FILES:
    p = ROOT / rel
    st = p.stat()
    ro_file_count += 1
    if st.st_mtime > TASK_START:
        modified_after.append({"rel": rel, "mtime": local(st.st_mtime), "bytes": st.st_size})
OUT["readonly_files_scanned"] = ro_file_count
OUT["readonly_files_modified_after_task_start"] = modified_after

# seal JSON files in cert dir (must be exactly the original one, unchanged)
cert = ROOT / "lead" / "cert_realcheck_20261109"
seal_j = [p for p in cert.iterdir() if p.is_file() and "seal" in p.name.lower()
          and p.suffix.lower() == ".json"]
OUT["seal_json_files_in_cert_dir"] = [
    {"name": p.name, "bytes": p.stat().st_size, "mtime": local(p.stat().st_mtime),
     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in seal_j]
OUT["n_new_seal_json"] = len([p for p in seal_j
                              if p.stat().st_mtime > TASK_START])

# git HEAD / porcelain of RO dirs
def sh(cmd):
    r = subprocess.run(cmd, cwd=str(ROOT), shell=True, capture_output=True)
    return {"rc": r.returncode,
            "out": r.stdout.decode("utf-8", "replace").strip(),
            "err": r.stderr.decode("utf-8", "replace").strip()}


OUT["git_head"] = sh("git log -1 --format='%H %cI'")
OUT["git_ls_seal"] = sh("git ls-files --error-unmatch lead/cert_realcheck_20261109/_cr_seal.json")
OUT["git_status_ro"] = sh("git status --porcelain -- " + " ".join(RO_DIRS + RO_FILES))
OUT["git_status_wd"] = sh("git status --porcelain -- lead/ordering_evidence_20261109/")
# 6-dir git log line counts
gl = {}
for d in RO_DIRS + ["lead/ordering_evidence_20261109"]:
    r = sh('git log --oneline -- "%s"' % d)
    gl[d] = {"n_lines": len([x for x in r["out"].splitlines() if x.strip()]),
             "rc": r["rc"]}
OUT["git_log_per_dir"] = gl

# atime drift: read a RO file once and see if atime changes (no writes)
target = ROOT / "lead" / "seal_chronology_20261109" / "_sc_ctime.py"
a0 = target.stat().st_atime
target.read_bytes()
a1 = target.stat().st_atime
OUT["atime_drift"] = {"file": "_sc_ctime.py", "atime_before": local(a0),
                      "atime_after_one_read": local(a1),
                      "changed_by_our_own_read": a1 != a0,
                      "delta_s": a1 - a0}

# OS-level supporting queries (as the reviewed object claims)
OUT["usn_queryjournal"] = sh("fsutil usn queryjournal D:")
OUT["vss_list_shadows"] = sh("vssadmin list shadows")
OUT["wevtutil_4663"] = sh('wevtutil qe Security /q:"*[System[(EventID=4663)]]" /f:text /c:1')

# signature sidecars in cert dir
sig = re.compile(r"\.(sig|asc|p7s|pem|crt|pub)$|_pubkey|signature", re.I)
OUT["signature_sidecars_cert"] = [p.name for p in cert.iterdir() if p.is_file() and sig.search(p.name)]

# reviewed-object counts: 14 command rows, 8 evidence classes, 6 plans, 15 判不了
md = WDIR.joinpath("_oe_ORDERING_EVIDENCE.md").read_text(encoding="utf-8")
OUT["reviewed_object_counts"] = {
    "command_table_rows": len(re.findall(r"^\| (?:[1-9]|1[0-4]) \| `", md, re.M)),
    "eight_class_rows": len(re.findall(r"^\| [1-8] \| \*\*", md, re.M)),
    "plan_rows_abcdef": len(re.findall(r"^\| \*\*(甲|乙|丙|丁|戊|己)", md, re.M)),
    "judged_impossible_list_items": len(re.findall(r"^\d+\. ", md[md.find("### 5.4"):md.find("## 6")], re.M)),
    "strict_binding_lines": len(re.findall(r"^被核对象 SHA256 = [0-9a-f]{64}，字节数 = \d+$", md, re.M)),
    "md_bytes": len(md.encode("utf-8")),
}

with (WDIR / "_oev_3_out.json").open("w", encoding="utf-8") as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)

print("=== _oev_3.py BOUNDARY / SUPPORTING RESULTS ===")
print("TASK_START inferred:", OUT["task_start_inferred_from_oe_files"], "n_oe_files=", OUT["n_oe_files"])
print("RO files scanned:", ro_file_count)
print("RO files modified AFTER task start:", json.dumps(modified_after, ensure_ascii=False))
print("\nSEAL JSONs in cert dir:", json.dumps(OUT["seal_json_files_in_cert_dir"], ensure_ascii=False, indent=1))
print("n_new_seal_json after task start:", OUT["n_new_seal_json"])
print("\nGIT HEAD:", OUT["git_head"])
print("GIT ls seal:", OUT["git_ls_seal"])
print("GIT status RO:", json.dumps(OUT["git_status_ro"], ensure_ascii=False))
print("GIT status WD:", json.dumps(OUT["git_status_wd"], ensure_ascii=False))
print("GIT log per dir:", json.dumps(gl, ensure_ascii=False))
print("\nATIME DRIFT:", json.dumps(OUT["atime_drift"], ensure_ascii=False, indent=1))
print("\nUSN:", json.dumps(OUT["usn_queryjournal"], ensure_ascii=False)[:900])
print("VSS:", json.dumps(OUT["vss_list_shadows"], ensure_ascii=False)[:900])
print("4663:", json.dumps(OUT["wevtutil_4663"], ensure_ascii=False)[:500])
print("\nSIG SIDECARS:", OUT["signature_sidecars_cert"])
print("\nREVIEWED OBJECT COUNTS:", json.dumps(OUT["reviewed_object_counts"], ensure_ascii=False, indent=1))
print("\nWROTE _oev_3_out.json")

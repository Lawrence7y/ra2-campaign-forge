# -*- coding: utf-8 -*-
"""Targeted cross-checks for the EXIT_CENSUS audit. Read-only on data root."""
import hashlib
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

D = Path("D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip")
dirs = sorted([p for p in D.iterdir() if p.is_dir() and p.name.startswith("archive_T")], key=lambda p: p.name)

print("=" * 90)
print("CHECK A: except_post file distribution per archive (find-style, recursive)")
have, none = [], []
for p in dirs:
    fs = sorted(q for q in p.rglob("except_post_*.txt") if q.is_file())
    (have if fs else none).append(p.name)
    print("  %-22s %d  %s" % (p.name, len(fs), ", ".join(q.name for q in fs)))
print("  DIRS WITH >=1 FILE =", len(have), ":", ", ".join(have))
print("  DIRS WITH 0 FILES  =", len(none), ":", ", ".join(none))
print("  TOTAL FILES IN 37 ARCHIVES =", sum(len(list(p.rglob('except_post_*.txt'))) for p in dirs))

print("=" * 90)
print("CHECK B: full-tree except_post count + sha256 (all of D, not just archives)")
allf = sorted(q for q in D.rglob("except_post_*.txt") if q.is_file())
hs = Counter(hashlib.sha256(q.read_bytes()).hexdigest() for q in allf)
print("  TOTAL =", len(allf))
for h, n in hs.items():
    print("  n=%3d %s" % (n, h))
print("  root-level(depth1) =", len([q for q in allf if q.parent == D]))
print("  in archive_T* =", len([q for q in allf if any(a in q.parts for a in [p.name for p in dirs])]))

print("=" * 90)
print("CHECK C: console log / fields / except / measure file inventory per archive")
for p in dirs:
    cons = sorted(p.glob("*console*"))
    cs = "; ".join("%s=%d" % (q.name, q.stat().st_size) for q in cons) or "无"
    f = p / "qc151_fields.json"
    term = "缺"
    if f.exists():
        try:
            o = json.loads(f.read_bytes().decode("utf-8-sig"))
            vals = {}
            if isinstance(o, list):
                for it in o:
                    if isinstance(it, dict) and "group" in it and "key" in it:
                        vals["%s.%s" % (it.get("group"), it.get("key"))] = it.get("value")
            t = vals.get("TERM.terminate_sent", "<NO_KEY>")
            v = vals.get("MANIFEST.final_verdict", "<NO_KEY>")
            term = "terminate_sent=%r final_verdict=%r" % (t, v)
        except Exception as e:
            term = "解析失败 %s: %s" % (type(e).__name__, e)
    meas = sorted(q.name for q in p.glob("measure_w*.json"))
    print("  %-22s console=[%s] fields:%s measure=%s" % (p.name, cs, term, ",".join(meas) or "无"))

print("=" * 90)
print("CHECK D: archive_T5 timestamps + fields + error.txt line numbers")
t5 = D / "archive_T5"
for q in sorted(t5.iterdir()):
    if q.name in ("error.txt", "qc151_run_log.json", "qc151_fields.json") or q.name.startswith("except_post_"):
        print("  %-48s size=%-8d mtime=%s" % (q.name, q.stat().st_size,
              datetime.fromtimestamp(q.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S")))
et = t5 / "error.txt"
for i, ln in enumerate(et.read_bytes().decode("utf-8", errors="replace").splitlines(), 1):
    print("  error.txt line %2d: %r" % (i, ln))
f = t5 / "qc151_fields.json"
o = json.loads(f.read_bytes().decode("utf-8-sig"))
for it in o:
    if isinstance(it, dict) and any(s in str(it.get("key", "")) for s in ("started", "finalized", "final_exit_code", "final_rewritten_exit_code", "final_verdict", "new_exception_count", "terminate_sent")):
        print("  T5 field %s.%s = %r" % (it.get("group"), it.get("key"), it.get("value")))

print("=" * 90)
print("CHECK E: T22/T23 NAV signature arrays in full (untruncated)")
for n in ("archive_T22", "archive_T23"):
    o = json.loads((D / n / "qc151_fields.json").read_bytes().decode("utf-8-sig"))
    print("  ---", n, "---")
    for it in o:
        if isinstance(it, dict) and (str(it.get("group")) == "NAV" or "stage_timeout" in str(it.get("key")) or "stage_seconds:nav_menu" in str(it.get("key"))):
            print("    %s.%s = %s" % (it.get("group"), it.get("key"), json.dumps(it.get("value"), ensure_ascii=False)))

print("=" * 90)
print("CHECK F: T11/T22/T23 error.txt exists + console SystemExit lines (per-trip independence)")
for n in ("archive_T11", "archive_T22", "archive_T23"):
    p = D / n
    et = p / "error.txt"
    print("  %s error.txt=%s qc151_run_log=%s" % (n, "EXISTS %d bytes" % et.stat().st_size if et.exists() else "缺",
          (p / "qc151_run_log.json").read_bytes().decode("utf-8-sig").strip() if (p / "qc151_run_log.json").exists() else "缺"))
    for lg in sorted(p.glob("*console*")):
        lines = lg.read_bytes().decode("utf-8", errors="replace").splitlines()
        print("    %s: %s" % (lg.name, [ln.strip() for ln in lines if "SystemExit" in ln or "end_stage" in ln or "line 4" in ln]))
print("DONE")

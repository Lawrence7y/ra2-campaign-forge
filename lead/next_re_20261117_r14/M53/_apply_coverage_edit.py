# -*- coding: utf-8 -*-
"""M53 Task A: guarded edit of 3 semantic cells in coverage.tsv (column 4 only).
Guard: baseline sha256 + mtime must still match; else abort without writing.
Writes: _hygiene\coverage.M53.bak (backup), coverage.tsv, M53\_coverage_edit_report.json.
"""
import hashlib, json, os, shutil, sys
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
BAK  = os.path.join(ROOT, "_hygiene", "coverage.M53.bak")
REPORT = os.path.join(ROOT, "M53", "_coverage_edit_report.json")

BASE_SHA = "b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c"
BASE_MTIME = "2026-11-19 22:04:36.637"  # local, to millis

TARGETS = {
    "006C9890": ("replace", "③b①细则#1", "③b 细则#1 级"),
    "00631CC0": ("replace", "③b①细则#1", "③b 细则#1 级"),
    "004AB9B0": ("append",  "", "（③b 细则#1 级：多路守卫链，非跳表）"),
}

def sha(b):
    return hashlib.sha256(b).hexdigest()

def mtime_str(p):
    return datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S.") + \
           ("%03d" % (int(os.path.getmtime(p) * 1000) % 1000))

def main():
    # --- guard 1: mtime + sha before read ---
    mt = mtime_str(COV)
    s0 = sha(open(COV, "rb").read())
    print("GUARD mtime:", mt, "expect:", BASE_MTIME)
    print("GUARD sha  :", s0, "expect:", BASE_SHA)
    if mt != BASE_MTIME or s0 != BASE_SHA:
        print("ABORT: third-party write detected before edit")
        sys.exit(2)

    raw = open(COV, "rb").read()
    if sha(raw) != BASE_SHA:
        print("ABORT: changed between guard and read")
        sys.exit(2)
    if raw[:1] == b"\xef":
        print("ABORT: unexpected BOM")
        sys.exit(2)
    if raw.endswith(b"\n"):
        print("ABORT: unexpected trailing newline")
        sys.exit(2)
    txt = raw.decode("utf-8")
    lines = txt.split("\n")   # 18499 elements; 18498 LF separators

    before = {}
    changed = 0
    for i, ln in enumerate(lines):
        cols = ln.split("\t")
        if not cols:
            continue
        e = cols[0].strip().upper()
        if e in TARGETS:
            if len(cols) != 8:
                print("ABORT: target row has %d cols" % len(cols)); sys.exit(2)
            kind, oldsub, newsub = TARGETS[e]
            orig_sem = cols[3]
            if kind == "replace":
                if orig_sem.count(oldsub) != 1:
                    print("ABORT: %s oldsub count=%d" % (e, orig_sem.count(oldsub))); sys.exit(2)
                cols[3] = orig_sem.replace(oldsub, newsub, 1)
            else:
                if newsub in orig_sem:
                    print("ABORT: %s marker already present" % e); sys.exit(2)
                cols[3] = orig_sem + newsub
            # invariants: entry/grade untouched
            if cols[0] != ln.split("\t")[0] or cols[4] != ln.split("\t")[4]:
                print("ABORT: entry/grade changed"); sys.exit(2)
            before[e] = dict(line=i + 1, name=cols[2], sem_before=orig_sem, sem_after=cols[3])
            lines[i] = "\t".join(cols)
            changed += 1
    if changed != 3:
        print("ABORT: changed=%d, expected 3" % changed); sys.exit(2)

    outTxt = "\n".join(lines)
    out = outTxt.encode("utf-8")
    # --- post-check in memory ---
    if out.count(b"\n") != raw.count(b"\n"):
        print("ABORT: LF count changed"); sys.exit(2)
    if outTxt.count("③b①细则#1") != 2:
        print("ABORT: wrong remaining ③b①细则#1 count"); sys.exit(2)
    if outTxt.count("③b 细则#1 级") != 3:
        print("ABORT: wrong new marker count"); sys.exit(2)
    # verify all non-target lines byte-identical
    newlines = outTxt.split("\n")
    touched = {v["line"] - 1 for v in before.values()}
    for i in range(len(lines)):
        if i not in touched and newlines[i] != txt.split("\n")[i]:
            print("ABORT: non-target line changed at %d" % (i+1)); sys.exit(2)

    # --- backup then write ---
    shutil.copy2(COV, BAK)
    print("BACKUP:", BAK, "sha:", sha(open(BAK, "rb").read()))
    with open(COV, "wb") as f:
        f.write(out)
    s1 = sha(open(COV, "rb").read())
    print("WROTE coverage.tsv new sha:", s1)
    print("bytes before/after: %d / %d" % (len(raw), len(out)))
    print("LF count:", out.count(b"\n"), "trailing newline:", out.endswith(b"\n"))

    report = dict(before_sha=BASE_SHA, after_sha=s1,
                  before_bytes=len(raw), after_bytes=len(out),
                  before_lf=raw.count(b"\n"), after_lf=out.count(b"\n"),
                  rows=before)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("REPORT:", REPORT)

main()

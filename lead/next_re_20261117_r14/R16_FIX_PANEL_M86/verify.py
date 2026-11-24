#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R16-FIX-PANEL-M86 :: verify.py  (re-runnable)

Checks, with explicit PASS/FAIL on each:
  1. before/after mtime, bytes, sha256, line count
  2. line-ending convention (must be pure LF in both, no CRLF/CR mixed in)
  3. reversibility: replacing the NEW M86 block back with the OLD one in the
     after-file must reproduce the before-file sha256 exactly
  4. scope: every changed line must lie inside the M86 block
     (before lines 214..221, after lines 214..223); everything before line 214
     and after the block must be byte-identical
  5. coverage.tsv sha256 must still be the card-open value C269720f...

Inputs (all under this artifact directory / the COVERAGE dir):
  PANEL.before.bak  -- exact pre-edit PANEL.md (backup taken before edit)
  ../COVERAGE/PANEL.md      -- current (post-edit) file
  ../COVERAGE/coverage.tsv  -- must not have changed
  apply_edit.py     -- holds OLD_BLOCK / NEW_BLOCK constants used by the edit
"""
import hashlib
import sys
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parent
PANEL = ROOT / "COVERAGE" / "PANEL.md"
BACKUP = ART / "PANEL.before.bak"
COV = ROOT / "COVERAGE" / "coverage.tsv"

sys.path.insert(0, str(ART))
import apply_edit as ae

EXPECTED_COV_SHA = "c269720f59c07845250a81ca8c6562f62260c1c9ecfc99f160e72f80f58144a5"

results = []
def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(("[PASS] " if ok else "[FAIL] ") + name + " :: " + detail)

def sha(b):
    return hashlib.sha256(b).hexdigest()

def metrics(p):
    b = p.read_bytes()
    return {
        "bytes": len(b),
        "sha": sha(b),
        "mtime": p.stat().st_mtime,
        "split_n": b.count(b"\n") + 1,   # trailing empty element included
        "phys_lines": b.count(b"\n") if b.endswith(b"\n") else b.count(b"\n") + 1,
        "crlf": b.count(b"\r\n"),
        "cr_only": b.count(b"\r") - b.count(b"\r\n"),
        "lf_only": b.count(b"\n") - b.count(b"\r\n"),
        "ends_lf": b.endswith(b"\n"),
    }

def main():
    before_b = BACKUP.read_bytes()
    after_b = PANEL.read_bytes()
    bm, am = metrics(BACKUP), metrics(PANEL)

    print("=== before (PANEL.before.bak) ===")
    print("  bytes=%d  sha256=%s  split-n=%d  physical-lines=%d" %
          (bm["bytes"], bm["sha"], bm["split_n"], bm["phys_lines"]))
    print("=== after  (COVERAGE/PANEL.md) ===")
    print("  bytes=%d  sha256=%s  split-n=%d  physical-lines=%d" %
          (am["bytes"], am["sha"], am["split_n"], am["phys_lines"]))
    print("  byte delta=%+d  line delta=%+d" %
          (am["bytes"] - bm["bytes"], am["phys_lines"] - bm["phys_lines"]))
    print()

    # 1. hash integrity of the backup itself
    check("backup records the true pre-edit panel",
          bm["sha"] == "6d691897069c3225f3755e396f741d524bdb42fd41df6550716b179b7590bebd",
          "backup sha256=%s" % bm["sha"])

    # 2. line endings
    for label, m in (("before", bm), ("after", am)):
        check("pure LF line endings (%s)" % label,
              m["crlf"] == 0 and m["cr_only"] == 0 and m["ends_lf"],
              "CRLF=%d CR-only=%d LF-only=%d endsLF=%s" %
              (m["crlf"], m["cr_only"], m["lf_only"], m["ends_lf"]))

    # 3. block constants still match what is on disk
    check("OLD_BLOCK occurs exactly once in backup",
          before_b.count(ae.OLD_BLOCK) == 1,
          "count=%d" % before_b.count(ae.OLD_BLOCK))
    check("NEW_BLOCK occurs exactly once in after file",
          after_b.count(ae.NEW_BLOCK) == 1,
          "count=%d" % after_b.count(ae.NEW_BLOCK))

    # 4. reversibility
    reverted = after_b.replace(ae.NEW_BLOCK, ae.OLD_BLOCK, 1)
    rev_sha = sha(reverted)
    check("REVERT: after with NEW block swapped back to OLD == before sha256",
          rev_sha == bm["sha"],
          "rebuilt=%s  before=%s" % (rev_sha, bm["sha"]))

    # 5. scope: exact line-level localization
    blines = before_b.decode("utf-8").split("\n")
    alines = after_b.decode("utf-8").split("\n")
    # M86 block: before 1-based 214..221 -> idx 213:221 ; after 214..223 -> idx 213:223
    check("lines 1..213 byte-identical (nothing above M86 changed)",
          blines[:213] == alines[:213],
          "prefix lines=%d equal=%s" % (213, blines[:213] == alines[:213]))
    check("lines after M86 block byte-identical (nothing below changed)",
          blines[221:] == alines[223:],
          "before tail from line 222, after tail from line 224, equal=%s" %
          (blines[221:] == alines[223:]))
    check("before M86 block == OLD_LINES (8 lines, 214..221)",
          blines[213:221] == ae.OLD_LINES,
          "equal=%s" % (blines[213:221] == ae.OLD_LINES))
    check("after  M86 block == NEW_LINES (10 lines, 214..223)",
          alines[213:223] == ae.NEW_LINES,
          "equal=%s" % (alines[213:223] == ae.NEW_LINES))

    # 6. coverage.tsv untouched
    cov_sha = sha(COV.read_bytes())
    check("coverage.tsv sha256 unchanged from card-open value",
          cov_sha == EXPECTED_COV_SHA,
          "now=%s  expected=%s" % (cov_sha, EXPECTED_COV_SHA))

    # 7. required numbers present / wrong number absent, only inside M86 block
    m86 = "\n".join(alines[213:223])
    for frag in ["328 / 1,654\uff0819.83%\uff09", "\u51c0\u589e 9 \u884c",
                 "\u4e0d\u662f +15", "0045A560", "106 \u884c\uff086.41%\uff09",
                 "222 \u884c", "74 \u884c"]:
        check("M86 block contains %r" % frag, frag in m86, "found=%s" % (frag in m86))
    check("wrong 334 / 1,654 (20.19%) removed",
          "334 / 1,654" not in m86,
          "present=%s" % ("334 / 1,654" in m86))

    print()
    nfail = sum(1 for _, ok, _ in results if not ok)
    print("TOTAL: %d checks, %d failed => %s" %
          (len(results), nfail, "ALL PASS" if nfail == 0 else "HAS FAILURES"))
    return 0 if nfail == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

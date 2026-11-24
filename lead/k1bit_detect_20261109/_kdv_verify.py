# -*- coding: utf-8 -*-
"""_kdv_verify.py -- independent rerun + boundary verification for the review.

Runs (via subprocess, exact python -I -X utf8 + absolute paths):
  _kd_detect.py <root>             (173 files)
  _kd_detect.py <root> --one <f>   (4 gates + carrier)
  _kd_selftest.py                  (10 fixtures)
  _kd_literal_vs_semantic.py <root>
Then independently compares the 40-set against _cf_detect_out.json:confirmed,
recomputes 10 orchestrator fingerprints BEFORE and AFTER, and checks the
273-row protected snapshot against current bytes for any modified artifact.

Writes only _kdv_verify_out.json / _kdv_reruns.txt in the write domain.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

WD_NAME = "lead/k1bit_detect_20261109"
BASE = {
    "lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md": ("e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8", 82856),
    "lead/check_family_20261109/_cf_detect_out.json": ("17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2", 130498),
    "lead/check_family_20261109/_cf_census_out.json": ("e5edea52c3f1959796c8132e7f4d04418c9704f992a59df84ec189d564b800fa", 149737),
    "lead/check_family_20261109/_cf_detect.py": ("832355993a2b0f50bbc77c85f52531862d62fc01eab511cd29d78d06c860ffc1", 7587),
    "lead/d27_ruling_20261106/check_d27.py": ("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    "lead/d28_ruling_20261106/check_d28.py": ("5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268", 4539),
    "lead/d29_ruling_20261106/check_d29.py": ("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    "lead/d30_ruling_20261106/check_d30.py": ("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
FOUR = ["lead/d27_ruling_20261106/check_d27.py",
        "lead/d28_ruling_20261106/check_d28.py",
        "lead/d29_ruling_20261106/check_d29.py",
        "lead/d30_ruling_20261106/check_d30.py"]
CARRIER = "lead/refsync_scope_20261109/_rs_carrier_scan.py"


def fingerprint_state(root):
    d = {}
    for rel in BASE:
        raw = (root / rel).read_bytes()
        d[rel] = (hashlib.sha256(raw).hexdigest(), len(raw))
    return d


def mismatch(fp):
    return [rel for rel, (h, b) in fp.items()
            if (h, b) != BASE[rel]]


def protected_snapshot_mismatches(root):
    """Compare the 273-row protected inventory's BEFORE sha with live bytes."""
    p = root / "lead/check_family_20261109/_cfv_snapshot_before.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    bad = []
    for row in d["rows"]:
        rel, h0, b0 = row["rel"], row["sha256"], row["bytes"]
        q = root / rel
        if not q.is_file():
            bad.append(dict(rel=rel, issue="MISSING"))
            continue
        raw = q.read_bytes()
        h, b = hashlib.sha256(raw).hexdigest(), len(raw)
        if h != h0 or b != b0:
            bad.append(dict(rel=rel, issue="CHANGED", bytes=b, bytes_before=b0,
                            sha=h, sha_before=h0))
    return dict(n=d["n"], mismatches=bad)


def run(cmd, log):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    log.append("CMD " + " ".join(cmd))
    log.append("EXIT " + str(r.returncode))
    log.append("STDOUT:\n" + r.stdout.strip())
    if r.stderr.strip():
        log.append("STDERR:\n" + r.stderr.strip())
    return r


def main():
    root = Path(sys.argv[1]).resolve()
    wd = root / WD_NAME
    py = [sys.executable, "-I", "-X", "utf8"]
    before = fingerprint_state(root)
    log = ["=== BEFORE fingerprints mismatches=%d ===" % len(mismatch(before))]
    cmds = [
        py + [str(wd / "_kd_detect.py"), str(root)],
        py + [str(wd / "_kd_selftest.py")],
        py + [str(wd / "_kd_literal_vs_semantic.py"), str(root)],
    ]
    for f in FOUR + [CARRIER]:
        cmds.append(py + [str(wd / "_kd_detect.py"), str(root), "--one", f])
    results = [run(c, log) for c in cmds]
    ones = []
    for f, r in zip(FOUR + [CARRIER], results[3:]):
        try:
            j = json.loads(r.stdout)
            ones.append(dict(rel=f, verdict=j.get("verdict"),
                             collapse=[(c["line"], c["kind"]) for c in j.get("collapse", [])],
                             has_k=j.get("has_k"), onebit=j.get("onebit_exit"),
                             attribution=j.get("attribution")))
        except Exception as e:
            ones.append(dict(rel=f, parse_error=str(e), stdout=r.stdout[:200]))
    kd = json.loads((wd / "_kd_detect_out.json").read_text(encoding="utf-8"))
    cf = json.loads((root / "lead/check_family_20261109/_cf_detect_out.json")
                    .read_text(encoding="utf-8"))
    a, b = set(kd["confirmed"]), set(cf["confirmed"])
    cmp = dict(kd_confirmed=len(a), cf_confirmed=len(b),
               identical=(a == b), cf_only=sorted(b - a), kd_only=sorted(a - b))
    after = fingerprint_state(root)
    snap = protected_snapshot_mismatches(root)
    res = dict(before_mismatches=mismatch(before),
               after_mismatches=mismatch(after),
               all_reruns_exit0=all(r.returncode == 0 for r in results),
               rerun_exit_codes=[r.returncode for r in results],
               counts=kd["counts"], n=kd["n"],
               confirmed_comparison=cmp, ones=ones,
               protected_snapshot=snap,
               selftest_stdout_last_line=results[1].stdout.strip().splitlines()[-1]
               if results[1].stdout.strip() else "")
    (wd / "_kdv_verify_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (wd / "_kdv_reruns.txt").write_text("\n\n".join(log), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("WROTE", (wd / "_kdv_verify_out.json").as_posix(),
          (wd / "_kdv_reruns.txt").as_posix())


if __name__ == "__main__":
    main()

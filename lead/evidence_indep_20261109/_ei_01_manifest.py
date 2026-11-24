# -*- coding: utf-8 -*-
"""_ei_01_manifest.py — hash every file in the six read-only dirs + two ledgers.
Usage: python -I -X utf8 -B <abs path> before|after
Only writes inside lead/evidence_indep_20261109/.
"""
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
DIRS = [
    "lead/gate_pipeline_20261109", "lead/chain_vs_single_20261109",
    "lead/gate_n13_20261109", "lead/gate_v1v2_20261109",
    "lead/gate_fp7_20261108", "lead/count_invariant_20261109",
]
FILES = ["lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md"]


def manifest():
    out = {}
    for rel in DIRS + FILES:
        p = ROOT / rel
        if p.is_file():
            out[rel] = [hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
            continue
        for q in sorted(p.rglob("*")):
            if q.is_file():
                k = q.relative_to(ROOT).as_posix()
                out[k] = [hashlib.sha256(q.read_bytes()).hexdigest(), q.stat().st_size]
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "before"
    m = manifest()
    dest = W / ("_ei_01_manifest_%s.json" % mode)
    dest.write_text(json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print("mode=%s files=%d written=%s" % (mode, len(m), dest.name))
    if mode == "after":
        b = json.loads((W / "_ei_01_manifest_before.json").read_text(encoding="utf-8"))
        added = sorted(set(m) - set(b))
        removed = sorted(set(b) - set(m))
        changed = sorted(k for k in set(m) & set(b) if m[k] != b[k])
        print("added=%d removed=%d changed=%d" % (len(added), len(removed), len(changed)))
        for k in added + removed + changed:
            print("  %s %s" % (k, "ADDED" if k in added else "REMOVED" if k in removed else "CHANGED"))
        print("READONLY_INTEGRITY =", "PASS" if not (added or removed or changed) else "FAIL")
    else:
        print("sample:", list(sorted(m.items()))[:3])


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""_eind_manifest.py — snapshot of all read-only domains (before/after)."""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
DOMAINS = [ROOT / "lead" / d for d in (
    "gate_pipeline_20261109", "chain_vs_single_20261109", "gate_n13_20261109",
    "gate_v1v2_20261109", "gate_fp7_20261108", "count_invariant_20261109")]
DOMAINS += [ROOT / "lead" / "PENDING_DECISIONS.md",
            ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md"]


def snap():
    out = {}
    for d in DOMAINS:
        files = [d] if d.is_file() else [p for p in sorted(d.rglob("*"))
                                        if p.is_file() and "__pycache__" not in p.parts
                                        and ".mimosa" not in p.parts]
        for p in files:
            b = p.read_bytes()
            out[str(p.relative_to(ROOT)).replace("\\", "/")] = [hashlib.sha256(b).hexdigest(), len(b)]
    return out


def main():
    tag = sys.argv[1]
    s = snap()
    (W / ("_eind_manifest_" + tag + ".json")).write_text(
        json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print("manifest", tag, "n_files =", len(s))
    if tag == "after":
        before = json.loads((W / "_eind_manifest_before.json").read_text(encoding="utf-8"))
        added = sorted(set(s) - set(before))
        removed = sorted(set(before) - set(s))
        changed = sorted(k for k in set(s) & set(before) if s[k] != before[k])
        print(json.dumps({"added": added, "removed": removed, "changed": changed,
                          "PASS": not (added or removed or changed)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

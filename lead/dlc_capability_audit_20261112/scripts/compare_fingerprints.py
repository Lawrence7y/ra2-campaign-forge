"""Compare baseline / closing fingerprints; print the closing receipt digests.

Run as:  python -I -X utf8 <ABS_PATH_TO_THIS_FILE> <BASELINE_JSON> <CLOSING_JSON>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def load(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def cmp(name: str, a, b) -> bool:
    ok = a == b
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: baseline={a} closing={b}")
    return ok


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_fingerprints.py <BASELINE> <CLOSING>", file=sys.stderr)
        return 2
    base, close = load(sys.argv[1]), load(sys.argv[2])
    print("== zero-change verdict ==")
    results = []
    for label, key, field in (
        ("existing files (docs/ ra2forge/ mcp/ examples/ README.md) content aggregate",
         "audit_scope", "aggregate_sha256"),
        ("ra2youli top-level FILE LIST hash", "ra2youli_top", "list_sha256"),
        ("ra2youli top-level CONTENT aggregate", "ra2youli_top",
         "content_aggregate_sha256"),
        ("repo top-level entries manifest (informational)", "repo_top",
         "manifest_sha256"),
    ):
        results.append(cmp(label, base[key][field], close[key][field]))

    for key in ("audit_scope", "ra2youli_top"):
        a = {r["path"] if "path" in r else r["name"]: r
             for r in base[key]["files"]}
        b = {r["path"] if "path" in r else r["name"]: r
             for r in close[key]["files"]}
        added, removed = sorted(set(b) - set(a)), sorted(set(a) - set(b))
        changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
        print(f"  {key}: added={added or 'NONE'} removed={removed or 'NONE'} "
              f"changed={changed or 'NONE'}")
        if added or removed or changed:
            results.append(False)

    print("\n== closing receipt digests ==")
    print(f"  ra2youli top file count          = {close['ra2youli_top']['file_count']}")
    print(f"  ra2youli top total bytes         = {close['ra2youli_top']['total_bytes']}")
    print(f"  ra2youli TOP FILE LIST sha256    = {close['ra2youli_top']['list_sha256']}")
    print(f"  ra2youli TOP CONTENT agg sha256  = {close['ra2youli_top']['content_aggregate_sha256']}")
    print(f"  existing files count             = {close['audit_scope']['file_count']}")
    print(f"  existing files CONTENT agg sha256= {close['audit_scope']['aggregate_sha256']}")
    print(f"  repo_top manifest sha256         = {close['repo_top']['manifest_sha256']}")
    print(f"\nOVERALL = {'ALL-MATCH (zero change)' if all(results) else 'DIFFERENCE FOUND'}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""STEP 4: compare two independent builds byte-for-byte with real sha256.

Run as:  python -I -X utf8 <ABS_PATH_TO_THIS_FILE> <BUILD1_DIR> <BUILD2_DIR>

Walks both output trees, matches files by relative path, prints a per-file
MATCH / MISMATCH table and an aggregate tree hash for each side. Does not
normalise anything: if a timestamp or a random value leaked into an artifact,
the MISMATCH is reported as-is.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(root: Path) -> dict[str, tuple[int, str]]:
    out: dict[str, tuple[int, str]] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            out[rel] = (p.stat().st_size, sha256_file(p))
    return out


def aggregate(items: dict[str, tuple[int, str]]) -> str:
    lines = [f"{rel}\t{size}\t{digest}"
             for rel, (size, digest) in sorted(items.items())]
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: repeat_compare.py <BUILD1_DIR> <BUILD2_DIR>", file=sys.stderr)
        return 2
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    if not a.is_dir() or not b.is_dir():
        print("both build dirs must exist", file=sys.stderr)
        return 2
    x, y = collect(a), collect(b)
    print(f"BUILD1 = {a}")
    print(f"BUILD2 = {b}")
    print(f"file counts: build1={len(x)} build2={len(y)}")
    print()
    print(f"{'relative file':<48} {'size1':>9} {'size2':>9}  {'verdict':<10} sha256(1/2)")
    print("-" * 130)
    keys = sorted(set(x) | set(y))
    mismatches = []
    for rel in keys:
        if rel not in x:
            print(f"{rel:<48} {'-':>9} {y[rel][0]:>9}  {'ONLY-IN-2':<10} {y[rel][1]}")
            mismatches.append(rel)
            continue
        if rel not in y:
            print(f"{rel:<48} {x[rel][0]:>9} {'-':>9}  {'ONLY-IN-1':<10} {x[rel][1]}")
            mismatches.append(rel)
            continue
        s1, h1 = x[rel]
        s2, h2 = y[rel]
        verdict = "MATCH" if (s1 == s2 and h1 == h2) else "MISMATCH"
        if verdict == "MISMATCH":
            mismatches.append(rel)
        print(f"{rel:<48} {s1:>9} {s2:>9}  {verdict:<10} {h1} / {h2}")
    print("-" * 130)
    ax, ay = aggregate(x), aggregate(y)
    print(f"aggregate tree sha256 build1 = {ax}")
    print(f"aggregate tree sha256 build2 = {ay}")
    print(f"aggregate verdict = {'MATCH' if ax == ay else 'MISMATCH'}")
    print(f"total MISMATCH files = {len(mismatches)}")
    if mismatches:
        print("mismatch list = " + ", ".join(mismatches))
        print("NOTE: no normalisation applied. Determine whether a timestamp / "
              "random value / absolute path is responsible; do not hide it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

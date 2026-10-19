#!/usr/bin/env python3
"""diff_snapshot.py -- compare two snapshot.py JSONs and give an explicit
zero-writes verdict.

Output (stdout, ASCII):
  ADDED / REMOVED / CONTENT_CHANGED / MTIME_ONLY counts, one detail line each,
  then exactly one verdict line:
    VERDICT: zero-writes            (rc 0)
    VERDICT: WRITES-DETECTED (...)  (rc 1)
  plus NOTE lines for mtime-only changes and snapshot errors.

Exit codes: 0 = zero-writes, 1 = writes detected, 2 = usage/IO error.

Zero-writes rule: no added, no removed, no content-changed files.
mtime-only changes are NOT counted as writes (reading a file must never count
as writing it) but are always listed for review.
"""
import argparse
import json
import sys


def load_snapshot(path):
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict) or doc.get("tool") != "snapshot.py":
        raise ValueError("not a snapshot.py JSON: %s" % path)
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="diff two snapshot.py JSONs; verdict zero-writes (rc 0/1)")
    ap.add_argument("pre", help="pre-modification snapshot JSON")
    ap.add_argument("post", help="post-modification snapshot JSON")
    args = ap.parse_args(argv)

    try:
        a = load_snapshot(args.pre)
        b = load_snapshot(args.post)
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    fa = a.get("files", {})
    fb = b.get("files", {})
    added = sorted(set(fb) - set(fa))
    removed = sorted(set(fa) - set(fb))
    changed = []
    mtime_only = []
    for rel in sorted(set(fa) & set(fb)):
        x, y = fa[rel], fb[rel]
        if x.get("sha256") != y.get("sha256") or x.get("size") != y.get("size"):
            changed.append(rel)
        elif x.get("mtime_ns") != y.get("mtime_ns"):
            mtime_only.append(rel)

    if a.get("root") != b.get("root"):
        print("WARNING: roots differ: %r vs %r" % (a.get("root"), b.get("root")))
    if a.get("excludes") != b.get("excludes"):
        print("WARNING: excludes differ: %r vs %r"
              % (a.get("excludes"), b.get("excludes")))

    for tag, items in (("ADDED", added), ("REMOVED", removed),
                       ("CONTENT_CHANGED", changed), ("MTIME_ONLY", mtime_only)):
        print("%s: %d" % (tag, len(items)))
        for rel in items:
            print("  %s: %s" % (tag, rel))

    writes = len(added) + len(removed) + len(changed)
    if writes:
        print("VERDICT: WRITES-DETECTED (%d file-level writes: %d added, "
              "%d removed, %d content-changed)"
              % (writes, len(added), len(removed), len(changed)))
        rc = 1
    else:
        print("VERDICT: zero-writes")
        rc = 0

    if mtime_only:
        print("NOTE: %d mtime-only change(s) NOT counted as writes; review "
              "each before trusting the verdict." % len(mtime_only))
    err_a = len(a.get("errors", []))
    err_b = len(b.get("errors", []))
    if err_a or err_b:
        print("NOTE: snapshot errors (unreadable files) pre=%d post=%d -- "
              "unreadable files weaken the verdict." % (err_a, err_b))
    return rc


if __name__ == "__main__":
    sys.exit(main())

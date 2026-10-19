#!/usr/bin/env python3
"""snapshot.py -- snapshot a directory tree: relpath + size + mtime_ns +
sha256 for every file, written as one JSON document.

Usage:
  python -B snapshot.py <dir> --out <json> [--exclude PATTERN]...

Exclude semantics: a pattern containing *, ? or [ is fnmatch'd against the
posix-style relative path (and against <dir>/<*> for directory pruning);
otherwise it is treated as a path prefix. Recommended excludes for this
repo: .mimosa, __pycache__, *.pyc, ra2youli, ra2bench, and the verify_kit
output directory itself.

Exit codes: 0 = snapshot written, 2 = usage/IO error.
Unreadable files are recorded in doc["errors"] and do not abort the walk.

The --out file is never included in its own snapshot. Empty directories are
invisible to snapshot/diff (only files are tracked). All disk output goes
through the _vk_io helper (single audited write point).
"""
import argparse
import fnmatch
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

import _vk_io

SCHEMA = 1
CHUNK = 1 << 20


def is_excluded(rel, patterns):
    for pat in patterns:
        if any(c in pat for c in "*?["):
            if fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel + "/", pat + "/*"):
                return True
        else:
            norm = pat.replace("\\", "/").rstrip("/")
            if rel == norm or rel.startswith(norm + "/"):
                return True
    return False


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="directory snapshot -> JSON (relpath/size/mtime_ns/sha256)")
    ap.add_argument("root", help="directory to snapshot")
    ap.add_argument("--out", required=True, help="output JSON path (parent must exist)")
    ap.add_argument("--exclude", action="append", default=[],
                    metavar="PATTERN", help="glob or path prefix, repeatable")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print("ERROR: not a directory: %s" % args.root, file=sys.stderr)
        return 2

    files = {}
    errors = []
    nfiles = 0
    nbytes = 0
    for dirpath, dirnames, filenames in os.walk(
            root, topdown=True, onerror=lambda e: errors.append("walk: %s" % e)):
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        dirnames[:] = sorted(
            d for d in dirnames
            if not is_excluded(rel_dir + "/" + d, args.exclude))
        for name in sorted(filenames):
            fp = os.path.join(dirpath, name)
            rel = os.path.relpath(fp, root).replace(os.sep, "/")
            if is_excluded(rel, args.exclude):
                continue
            try:
                st = os.stat(fp)
                if os.path.realpath(fp) == os.path.realpath(args.out):
                    continue
                digest = sha256_file(fp)
            except OSError as e:
                errors.append("%s: %s" % (rel, e))
                continue
            files[rel] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                          "sha256": digest}
            nfiles += 1
            nbytes += st.st_size

    doc = {
        "schema": SCHEMA,
        "tool": "snapshot.py",
        "root": root.replace(os.sep, "/"),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "excludes": list(args.exclude),
        "file_count": nfiles,
        "total_bytes": nbytes,
        "errors": errors,
        "files": dict(sorted(files.items())),
    }
    payload = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
    try:
        _vk_io.write_text(args.out, payload)
    except (OSError, ValueError) as e:
        print("ERROR: cannot write %s: %s" % (args.out, e), file=sys.stderr)
        return 2
    print("snapshot: %d files, %d bytes, errors=%d -> %s"
          % (nfiles, nbytes, len(errors), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

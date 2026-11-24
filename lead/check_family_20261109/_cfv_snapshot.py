"""Independent read-only-domain fingerprint snapshot (verification only).

Usage: python -I -X utf8 <this> <ROOT> <LIST.txt> <BEFORE|AFTER> <OUT.json>
Reads ONLY files named in LIST.txt. Writes ONLY OUT.json (must be _cfv_*).
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
LIST = Path(sys.argv[2]).resolve()
TAG = sys.argv[3]
OUT = Path(sys.argv[4]).resolve()

rows = []
errors = []
for line in LIST.read_text(encoding="utf-8").splitlines():
    rel = line.strip()
    if not rel:
        continue
    p = ROOT / rel
    try:
        raw = p.read_bytes()
        st = p.stat()
        rows.append({"rel": rel, "bytes": len(raw),
                     "sha256": hashlib.sha256(raw).hexdigest(),
                     "mtime_ns": st.st_mtime_ns})
    except OSError as exc:
        errors.append({"rel": rel, "error": str(exc)})

OUT.write_text(json.dumps({"root": ROOT.as_posix(), "tag": TAG,
                           "n": len(rows), "errors": errors, "rows": rows},
                          ensure_ascii=False, indent=1), encoding="utf-8")
print(f"snapshot tag={TAG} n={len(rows)} errors={len(errors)} -> {OUT.name}")

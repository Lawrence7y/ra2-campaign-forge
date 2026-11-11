"""Build a schema-v1 manifest fixture out of the REAL build1 artifacts.

Run as: python -I -X utf8 <ABS_PATH_TO_THIS_FILE> <BUILD1_PACKAGE_DIR> <OUT_JSON>
Every sha256 below is computed with hashlib over real bytes; nothing is invented.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: make_manifest_fixture.py <PKG_DIR> <OUT_JSON>", file=sys.stderr)
        return 2
    pkg, out = Path(sys.argv[1]), Path(sys.argv[2])
    files = [{"path": p.name, "sha256": sha256_file(p)}
             for p in sorted(pkg.iterdir()) if p.is_file()]
    # target_sha256 is a FORMAT smoke-test value: a real hashlib digest of a
    # real build artifact, NOT a claim about any game executable's identity.
    manifest = {
        "schema_version": 1,
        "package_id": "ra2forge-demo-campaign",
        "version": "1.0.0",
        "target_exe": "gamemd.exe",
        "target_sha256": sha256_file(pkg / "ECH01.MAP"),
        "files": files,
        "dependencies": [],
        "conflicts": [],
    }
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"wrote {out}")
    print(f"files listed = {len(files)}")
    for f in files:
        print(f"  {f['path']}\t{f['sha256']}")
    print("NOTE: target_sha256 is a real hashlib digest of ECH01.MAP used ONLY "
          "to satisfy the 64-hex format rule; it is NOT a game-exe identity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

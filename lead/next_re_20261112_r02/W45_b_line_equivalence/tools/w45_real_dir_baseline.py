#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W45 - read-only real-directory baseline / zero-change proof.

Usage:
    python w45_real_dir_baseline.py --phase pre
    python w45_real_dir_baseline.py --phase post

Writes ONLY inside W45_b_line_equivalence/ (out/real_dir_<phase>.json and
REAL_DIR_PROOF.txt).  The real game directory ra2youli/ is enumerated and
hashed READ-ONLY; it is never written, copied-from-with-change, or touched.

Baseline (W44 REAL_DIR_PROOF.txt / task card):
    647 files / 1,989,215,270 B / 277 maplike
    RA2MD.INI=c91c6a47...  gamemd.exe=73201cc0...
    ddraw.dll=85e0f7d5...   ra2forge_install.json=fe3bdf62...
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W45_b_line_equivalence"
OUT = CARD / "out"
GAME = ROOT / "ra2youli"
MAPLIKE_EXT = {".yrm", ".mpr", ".map"}  # W44 tools/w44_common.py:45
KEY_FILES = ("RA2MD.INI", "gamemd.exe", "ddraw.dll", "ra2forge_install.json")
EXPECTED = {
    "file_count": 647,
    "total_bytes": 1989215270,
    "maplike_count": 277,
    "RA2MD.INI": "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "gamemd.exe": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll": "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
    "ra2forge_install.json": "fe3bdf62f4e871b61bf0d1b1d451b090af1c0b1804440c093089436253cc3914",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest() -> dict:
    rows = []
    for dirpath, dirnames, filenames in os.walk(GAME):
        for name in filenames:
            p = Path(dirpath) / name
            try:
                st = p.stat()
                rows.append({
                    "rel": str(p.relative_to(GAME)).replace("\\", "/"),
                    "size": st.st_size,
                    "mtime_ns": st.st_mtime_ns,
                    "sha256": sha256(p),
                })
            except OSError as e:
                rows.append({"rel": str(p.relative_to(GAME)).replace("\\", "/"),
                             "error": repr(e)})
    rows.sort(key=lambda r: r["rel"].lower())
    hashes = {}
    for n in KEY_FILES:
        q = GAME / n
        hashes[n] = sha256(q) if q.is_file() else None
    return {
        "kind": "w45_real_dir_manifest",
        "real_dir": str(GAME),
        "t_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(rows),
        "total_bytes": sum(r.get("size", 0) for r in rows),
        "maplike_count": sum(1 for r in rows
                             if Path(r["rel"]).suffix.lower() in MAPLIKE_EXT),
        "key_hashes": hashes,
        "rows": rows,
    }


def summary(m: dict) -> dict:
    return {k: m[k] for k in ("file_count", "total_bytes", "maplike_count")}


def write_proof() -> None:
    pre_p = OUT / "real_dir_pre.json"
    post_p = OUT / "real_dir_post.json"
    pre = json.loads(pre_p.read_text(encoding="utf-8")) if pre_p.is_file() else None
    post = json.loads(post_p.read_text(encoding="utf-8")) if post_p.is_file() else None
    L = []
    L.append("W45 B-line equivalence - REAL DIRECTORY ZERO-CHANGE PROOF")
    L.append("real_dir = %s" % GAME)
    L.append("PRE  manifest = %s" % (pre_p if pre else "(not yet measured)"))
    L.append("POST manifest = %s" % (post_p if post else "(not yet measured)"))
    L.append("")
    for label, m in (("PRE ", pre), ("POST", post)):
        if m is None:
            L.append("%s: (pending)" % label)
        else:
            L.append("%s: file_count=%d total_bytes=%d maplike_count=%d"
                     % (label, m["file_count"], m["total_bytes"], m["maplike_count"]))
    if pre and post:
        pm = {(r["rel"], r.get("size"), r.get("sha256")) for r in pre["rows"]}
        qm = {(r["rel"], r.get("size"), r.get("sha256")) for r in post["rows"]}
        added = sorted(qm - pm)
        removed = sorted(pm - qm)
        L.append("added=%d removed=%d changed=%d   IDENTICAL_TREE=%s"
                 % (len(added), len(removed), 0 if not added and not removed else -1,
                    "True" if pm == qm else "False"))
    else:
        L.append("added=? removed=? changed=?   IDENTICAL_TREE=PENDING")
    L.append("")
    L.append("key file SHA-256 (PRE vs POST vs task baseline):")
    for n in KEY_FILES:
        a = pre["key_hashes"][n] if pre else None
        b = post["key_hashes"][n] if post else None
        exp = EXPECTED[n]
        pre_ok = (a == exp) if a else False
        post_ok = (b == exp) if b else False
        L.append("%-24s PRE=%s POST=%s baseline=%s match_PRE=%s match_POST=%s"
                 % (n, a or "-", b or "-", exp[:8], pre_ok, post_ok))
    L.append("")
    L.append("method: full recursive manifest of every file (rel / size / mtime_ns / "
             "sha256), PRE at card start, POST at card end; diff by (rel,size,sha256).")
    L.append("ra2youli was only ever a READ-ONLY enumeration/hash target and a robocopy SOURCE.")
    L.append("NOTE: ra2forge_install.json / .seal are install-transaction results, NOT "
             "config; they are deliberately NOT in the config-restore set (W44 tool defect A).")
    (CARD / "REAL_DIR_PROOF.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("pre", "post"), required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    m = manifest()
    (OUT / ("real_dir_%s.json" % a.phase)).write_text(
        json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    s = summary(m)
    ok = True
    for k, v in (("file_count", 647), ("total_bytes", 1989215270),
                 ("maplike_count", 277)):
        if s[k] != v:
            ok = False
            print("BASELINE MISMATCH %s: got %s expected %s" % (k, s[k], v))
    for n in KEY_FILES:
        if m["key_hashes"][n] != EXPECTED[n]:
            ok = False
            print("HASH MISMATCH %s: %s" % (n, m["key_hashes"][n]))
    print(json.dumps({"phase": a.phase, **s, "key_hashes": m["key_hashes"],
                      "baseline_match": ok}, ensure_ascii=False, indent=1))
    write_proof()
    return 0 if ok else 3


if __name__ == "__main__":
    sys_exit = main()
    raise SystemExit(sys_exit)

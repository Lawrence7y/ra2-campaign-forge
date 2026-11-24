#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W55b - real-directory zero-change + config byte-restore self-proof.

Usage:
    python w55b_real_dir_proof.py --phase pre
    python w55b_real_dir_proof.py --phase post

READ-ONLY with respect to ra2youli/.  It is only enumerated/hashed and used as
a robocopy SOURCE.  All writes go to W55b_equivalence_rerun/.

phase pre:
  * full recursive manifest (rel / size / mtime_ns / sha256) of ra2youli
    -> out/real_dir_pre.json
  * byte copies of every writable config file from the prepared sandbox base
    -> out/cfgbase_<name>   (plus out/config_baseline.json with sha256)
    NOTE: prefix `cfgbase_` is deliberately DIFFERENT from the runner's
    `pristine_` copies so the two never overwrite each other.
phase post:
  * full recursive manifest -> out/real_dir_post.json
  * PRE vs POST diff -> IDENTICAL_TREE (True/False) + added/removed/changed
  * for each config: byte-identical check of (a) real ra2youli file,
    (b) each surviving sandbox_* copy, vs the pristine byte copy
  * writes REAL_DIR_PROOF.txt (IDENTICAL_TREE=... + per-file byte_identical)

Baseline values are the W44/W45 task baselines (647 / 1,989,215,270 / 277
and 4 key SHA-256); a mismatch is REPORTED, not silently ignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W55b_equivalence_rerun"
OUT = CARD / "out"
GAME = ROOT / "ra2youli"
BASE = CARD / "sandbox_base"
MAPLIKE_EXT = {".yrm", ".mpr", ".map"}
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
# Declared writable-config set (task: RA2MD.INI / ddraw.ini / BATTLEMD*.INI 等)
CONFIG_GLOBS = ("*.INI", "*.ini", "*.benchbak", "*.ra2forge.bak",
                "Register.ini", "ra2md.lcf", "ra2.lcf", "Ra2.lcf",
                "ra2opt_play.bat")
CONFIG_MAX_BYTES = 1 << 20


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest() -> dict:
    rows = []
    for dirpath, _dirnames, filenames in os.walk(GAME):
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
    hashes = {n: sha256(GAME / n) if (GAME / n).is_file() else None
              for n in KEY_FILES}
    return {
        "kind": "w55b_real_dir_manifest",
        "real_dir": str(GAME),
        "t_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(rows),
        "total_bytes": sum(r.get("size", 0) for r in rows),
        "maplike_count": sum(1 for r in rows
                             if Path(r["rel"]).suffix.lower() in MAPLIKE_EXT),
        "key_hashes": hashes,
        "rows": rows,
    }


def config_files(root: Path):
    found = {}
    for pat in CONFIG_GLOBS:
        for p in root.glob(pat):
            if p.is_file() and p.stat().st_size <= CONFIG_MAX_BYTES:
                found[p.name] = p
    # explicit must-haves
    for n in ("RA2MD.INI", "ddraw.ini", "BATTLEMD.INI", "BATTLEMD98.INI"):
        p = root / n
        if p.is_file():
            found[n] = p
    return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))


def phase_pre() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    m = manifest()
    (OUT / "real_dir_pre.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")

    src_root = BASE if BASE.is_dir() else GAME
    cfiles = config_files(src_root)
    rows = []
    for name, p in cfiles.items():
        dst = OUT / ("cfgbase_" + name)
        shutil.copyfile(p, dst)
        rows.append({"file": name, "source": str(p),
                     "pristine_copy": str(dst), "size": p.stat().st_size,
                     "sha256": sha256(p), "pristine_sha256": sha256(dst),
                     "byte_identical_to_source": sha256(p) == sha256(dst)})
    (OUT / "config_baseline.json").write_text(
        json.dumps({"phase": "pre", "source_root": str(src_root),
                    "t_utc": datetime.now(timezone.utc).isoformat(),
                    "config_files": rows}, ensure_ascii=False, indent=1,
                   sort_keys=True), encoding="utf-8")
    s = {k: m[k] for k in ("file_count", "total_bytes", "maplike_count")}
    ok = all(s[k] == EXPECTED[k] for k in s) and all(
        m["key_hashes"][n] == EXPECTED[n] for n in KEY_FILES)
    print(json.dumps({"phase": "pre", **s, "key_hashes": m["key_hashes"],
                      "config_count": len(rows),
                      "baseline_match": ok}, ensure_ascii=False, indent=1))
    return 0 if ok else 3


def cmp_bytes(a: Path, b: Path):
    if not a.is_file() or not b.is_file():
        return None
    if a.stat().st_size != b.stat().st_size:
        return False
    return a.read_bytes() == b.read_bytes()


def phase_post() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    m = manifest()
    (OUT / "real_dir_post.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    pre_p = OUT / "real_dir_pre.json"
    pre = json.loads(pre_p.read_text(encoding="utf-8")) if pre_p.is_file() else None

    L = []
    L.append("W55b equivalence rerun - REAL DIRECTORY / CONFIG RESTORE PROOF")
    L.append("real_dir = %s" % GAME)
    L.append("PRE  manifest = %s" % (pre_p if pre else "(not yet measured)"))
    L.append("POST manifest = %s" % (OUT / "real_dir_post.json"))
    L.append("t_utc_post = %s" % m["t_utc"])
    L.append("")

    if pre:
        pm = {(r["rel"], r.get("size"), r.get("sha256")) for r in pre["rows"]}
        qm = {(r["rel"], r.get("size"), r.get("sha256")) for r in m["rows"]}
        added = sorted(qm - pm)
        removed = sorted(pm - qm)
        identical = (pm == qm)
        L.append("PRE : file_count=%d total_bytes=%d maplike_count=%d"
                 % (pre["file_count"], pre["total_bytes"], pre["maplike_count"]))
        L.append("POST: file_count=%d total_bytes=%d maplike_count=%d"
                 % (m["file_count"], m["total_bytes"], m["maplike_count"]))
        L.append("added=%d removed=%d changed=%d   IDENTICAL_TREE=%s"
                 % (len(added), len(removed), 0 if not added and not removed else -1,
                    "True" if identical else "False"))
        if added:
            L.append("  added_list(first10)=%s" % added[:10])
        if removed:
            L.append("  removed_list(first10)=%s" % removed[:10])
    else:
        identical = None
        L.append("PRE : (pending)")
        L.append("POST: file_count=%d total_bytes=%d maplike_count=%d"
                 % (m["file_count"], m["total_bytes"], m["maplike_count"]))
        L.append("IDENTICAL_TREE=PENDING (PRE manifest missing)")

    L.append("")
    L.append("key file SHA-256 (PRE vs POST vs task baseline):")
    for n in KEY_FILES:
        a = pre["key_hashes"][n] if pre else None
        b = m["key_hashes"][n]
        exp = EXPECTED[n]
        L.append("%-24s PRE=%s POST=%s baseline=%s match_PRE=%s match_POST=%s"
                 % (n, a or "-", b or "-", exp[:8],
                    str(a == exp) if a else "n/a", str(b == exp)))

    # ---- config byte-restore self-proof ----
    L.append("")
    L.append("CONFIG BYTE-RESTORE (out/cfgbase_<name> = byte copies taken BEFORE launch):")
    cb_p = OUT / "config_baseline.json"
    cb = json.loads(cb_p.read_text(encoding="utf-8")) if cb_p.is_file() else None
    per_file_rows = []
    if cb:
        for r in cb["config_files"]:
            name = r["file"]
            pristine = Path(r["pristine_copy"])
            sha = r["sha256"]
            real_p = GAME / name
            real_same = cmp_bytes(real_p, pristine)
            real_sha = sha256(real_p) if real_p.is_file() else None
            sandbox_checks = []
            for sd in sorted(CARD.glob("sandbox_*")):
                if not sd.is_dir():
                    continue
                sp = sd / name
                if sp.is_file():
                    sandbox_checks.append({"sandbox": sd.name,
                                           "byte_identical": cmp_bytes(sp, pristine),
                                           "sha256": sha256(sp)})
            row = {"file": name, "size": r["size"], "baseline_sha256": sha,
                   "real_dir_sha256": real_sha,
                   "real_dir_byte_identical": real_same,
                   "sandbox_checks": sandbox_checks,
                   "pristine_copy_present": pristine.is_file()}
            per_file_rows.append(row)
            L.append("%-34s size=%-8d baseline=%s real=%s real_byte_identical=%s sandboxes=%s"
                     % (name, r["size"], sha[:8], (real_sha or "-")[:8],
                        real_same,
                        [(c["sandbox"], c["byte_identical"]) for c in sandbox_checks]))
    else:
        L.append("  (config_baseline.json missing - phase pre not run)")

    # ---- per-trip `finally` restore_configs self-proof (from runner results) ----
    L.append("")
    L.append("PER-TRIP CONFIG RESTORE (runner finally: byte-copy pristine_* back):")
    trip_rows = []
    res_paths = sorted(OUT.glob("*_result.json")) + ([OUT / "dual_track_results.json"]
                                                    if (OUT / "dual_track_results.json").is_file() else [])
    seen_trips = set()
    for rp in res_paths:
        try:
            d = json.loads(rp.read_text(encoding="utf-8"))
        except Exception:
            continue
        for tag, body in (d.items() if rp.name == "dual_track_results.json"
                          else [(rp.stem.replace("_result", ""), d)]):
            if not isinstance(body, dict) or tag in seen_trips:
                continue
            rows = body.get("restore_configs")
            if rows:
                seen_trips.add(tag)
                trip_rows.append({"tag": tag, "rows": rows,
                                  "all_match": all(r.get("match") for r in rows)})
                L.append("  %-6s all_match=%s  %s"
                         % (tag, trip_rows[-1]["all_match"],
                            [(r.get("file"), r.get("match")) for r in rows]))
    if not trip_rows:
        L.append("  (no per-trip restore_configs rows found)")
    all_trip_ok = all(t["all_match"] for t in trip_rows) if trip_rows else None
    L.append("ALL_TRIP_RESTORE_MATCH = %s" % all_trip_ok)

    all_real_ok = all(r["real_dir_byte_identical"] is True for r in per_file_rows) \
        if per_file_rows else None
    L.append("")
    L.append("ALL_CONFIG_BYTE_IDENTICAL_TO_BASELINE = %s" % all_real_ok)
    L.append("ALL_TRIP_RESTORE_MATCH = %s" % all_trip_ok)
    L.append("IDENTICAL_TREE = %s" % identical)
    L.append("")
    L.append("method: full recursive manifest of every file (rel/size/mtime_ns/sha256),")
    L.append("PRE at card start, POST at card end; diff by (rel,size,sha256).")
    L.append("config byte copies (cfgbase_*) were taken from sandbox_base (a robocopy")
    L.append("of ra2youli) BEFORE any game launch; each trip's finally restores")
    L.append("RA2MD.INI/ddraw.ini/RA2MD.INI.benchbak/BATTLEMD.INI from that trip's")
    L.append("pristine_* copies, and the per-trip restore_configs match rows above are")
    L.append("copied verbatim from <tag>_result.json / dual_track_results.json.")
    L.append("ra2youli was ONLY a READ-ONLY enumeration/hash target and a robocopy SOURCE.")
    L.append("NOTE: ra2forge_install.json / .seal are install-transaction results, NOT config;")
    L.append("they are deliberately NOT in the config-restore set (W44 tool defect A).")

    (CARD / "REAL_DIR_PROOF.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    (OUT / "config_restore_post.json").write_text(
        json.dumps({"t_utc": datetime.now(timezone.utc).isoformat(),
                    "identical_tree": identical,
                    "all_config_byte_identical_to_baseline": all_real_ok,
                    "all_trip_restore_match": all_trip_ok,
                    "trip_restore_rows": trip_rows,
                    "per_file": per_file_rows},
                   ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    ok = (identical is True and all_real_ok is True)
    print(json.dumps({"phase": "post", "identical_tree": identical,
                      "all_config_byte_identical": all_real_ok,
                      "all_trip_restore_match": all_trip_ok,
                      "file_count": m["file_count"],
                      "total_bytes": m["total_bytes"],
                      "maplike_count": m["maplike_count"],
                      "config_files": len(per_file_rows)},
                     ensure_ascii=False, indent=1))
    return 0 if ok else 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("pre", "post"), required=True)
    a = ap.parse_args()
    return phase_pre() if a.phase == "pre" else phase_post()


if __name__ == "__main__":
    raise SystemExit(main())

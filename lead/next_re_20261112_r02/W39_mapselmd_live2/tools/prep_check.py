#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W39 · offline pre-flight verification (no game launched).

Re-checks the three things the card requires before running:
  ① W35 sandbox `ra2forge verify` still exits 0
  ② SHA-256 of MAPSELMD.OFFICIAL.INI and MAPSELMD.INI.w35_v11 match the card
  ③ sandbox_game\\MAPSELMD.INI exists and hashes to 11cc1cac... (loose/deployed)
Plus:
  - line/CRLF check on the appended variant (284 lines, all CRLF, 6108 B)
  - full byte-exact manifest of real ra2youli -> out/real_pre.json (baseline)
  - copies the deployed MAPSELMD.INI into out/ as a W39 variant artifact
  - writes out/verify_pre.log and out/prep_check.json
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W35 = RUN / "W35_mapselmd_live"
W39 = RUN / "W39_mapselmd_live2"
OUT = W39 / "out"
GAME = W35 / "sandbox_game"
REAL = ROOT / "ra2youli"
V9 = RUN / "W26_dlc_unseal_fix" / "ra2forge_patched_v9"
MANIFEST_PY = W39 / "tools" / "manifest.py"

EXPECT = {
    "MAPSELMD.OFFICIAL.INI": "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52",
    "MAPSELMD.INI.w35_v11": "11cc1cacb0e0d49d71ddc13b94179fa3c7ebe90c9048be2e076453b8684b0886",
}
EXPECT_SIZE = {"MAPSELMD.OFFICIAL.INI": 5573, "MAPSELMD.INI.w35_v11": 6108}
REAL_BASELINE = {
    "RA2MD.INI": "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d",
    "gamemd.exe": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll": "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
    "ra2forge_install.json": "fe3bdf62f4e871b61bf0d1b1d451b090af1c0b1804440c093089436253cc3914",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r = {"checks": {}}
    ok_all = True

    # --- ② two MAPSELMD variants in W35/out ---
    for name, exp in EXPECT.items():
        p = W35 / "out" / name
        rec = {"path": str(p), "exists": p.is_file()}
        if p.is_file():
            b = p.read_bytes()
            rec.update({"size": len(b), "sha256": sha256_file(p),
                        "expected_sha256": exp,
                        "size_expected": EXPECT_SIZE[name],
                        "size_match": len(b) == EXPECT_SIZE[name],
                        "sha_match": sha256_file(p) == exp})
            if name.endswith("w35_v11"):
                rec["crlf_count"] = b.count(b"\r\n")
                rec["lf_total"] = b.count(b"\n")
                rec["all_crlf"] = (b.count(b"\r\n") == b.count(b"\n"))
                rec["line_count_crlf"] = b.count(b"\r\n")
        else:
            rec["sha_match"] = False
        r["checks"]["variant_" + name] = rec
        ok_all &= bool(rec.get("sha_match"))

    # --- ③ sandbox loose MAPSELMD.INI ---
    dep = GAME / "MAPSELMD.INI"
    rec = {"path": str(dep), "exists": dep.is_file()}
    if dep.is_file():
        b = dep.read_bytes()
        rec.update({"size": len(b), "sha256": sha256_file(dep),
                    "expected": EXPECT["MAPSELMD.INI.w35_v11"],
                    "match": sha256_file(dep) == EXPECT["MAPSELMD.INI.w35_v11"]})
        # keep a W39 copy of the deployed variant as a deliverable artifact
        (OUT / "MAPSELMD.INI.w39_deployed").write_bytes(b)
    else:
        rec["match"] = False
    r["checks"]["sandbox_deployed_mapselmd"] = rec
    ok_all &= bool(rec.get("match"))

    # --- ① verify on W35 sandbox ---
    cmd = [sys.executable, "-m", "ra2forge", "verify", "--game", str(GAME)]
    p = subprocess.run(cmd, cwd=str(V9), capture_output=True, text=True,
                       timeout=120)
    log = ("$ " + " ".join(cmd) + "\n[cwd] " + str(V9) +
           "\n[exit] " + str(p.returncode) + "\n[stdout]\n" +
           (p.stdout or "") + "\n[stderr]\n" + (p.stderr or "") + "\n")
    (OUT / "verify_pre.log").write_text(log, encoding="utf-8")
    r["checks"]["verify_w35_sandbox"] = {
        "exit_code": p.returncode, "log": str(OUT / "verify_pre.log"),
        "exit_0": p.returncode == 0,
        "stdout_tail": (p.stdout or "").strip().splitlines()[-6:],
    }
    ok_all &= (p.returncode == 0)

    # --- real-dir baseline manifest (read-only on ra2youli) ---
    mp = subprocess.run([sys.executable, str(MANIFEST_PY), str(REAL),
                         str(OUT / "real_pre.json")],
                        capture_output=True, text=True, timeout=600)
    r["checks"]["real_pre_manifest"] = {"exit_code": mp.returncode,
                                        "stdout": (mp.stdout or "").strip(),
                                        "stderr": (mp.stderr or "").strip()[-400:]}
    ok_all &= (mp.returncode == 0)
    if (OUT / "real_pre.json").is_file():
        pre = json.loads((OUT / "real_pre.json").read_text(encoding="utf-8"))
        r["checks"]["real_pre_manifest"]["file_count"] = pre["file_count"]
        r["checks"]["real_pre_manifest"]["total_bytes"] = pre["total_bytes"]
        r["checks"]["real_pre_manifest"]["maplike_count"] = pre["maplike_count"]
        bm = {x["rel"]: x["sha256"] for x in pre["files"]}
        hashes = {}
        for k, exp in REAL_BASELINE.items():
            got = bm.get(k)
            hashes[k] = {"got": got, "expected": exp, "match": got == exp}
            ok_all &= (got == exp)
        r["checks"]["real_pre_manifest"]["key_hashes"] = hashes

    r["all_pass"] = bool(ok_all)
    (OUT / "prep_check.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())

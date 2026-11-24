#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W83c OFFLINE - sandbox setup + inplace install.  NO LOCK, NO gamemd.exe.

Env:
  W83c_PKG   = s8 | s20 | s55 | ann     (which package to install)
  W83c_REUSE = 1                        (reuse existing sandbox; uninstall prev)

FRESH path (first package, before ANY game launch):
  1. real-dir PRE full manifest + signed W44 baseline assertions
  2. robocopy REAL -> sandbox (READ-ONLY source)
  3. sandbox PRE full manifest + BYTE-PRISTINE copies of every writable config
     + their SHA-256 (red line #4: "启动前沙箱可写配置字节副本 + 哈希")
  4. verify_pre / uninstall pre-existing v0.3 record / remove the unowned
     orphan BATTLEMD.INI.ra2forge.bak from the SANDBOX COPY ONLY
  5. assert BATTLEMD.INI == official 2733 B baseline
  6. install v15 inplace package (--feature-set); retry --allow-content-conflict
  7. verify --game sandbox --json MUST exit 0
  8. installed-file inventory

REUSE path (subsequent packages): skip 1-3, uninstall current package, then 4-8.

Everything writes ONLY inside W83c_survive_and_annih.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w83c_lib as L
import w83c_common as C

TAG = "offline"
PKG_KEY = os.environ.get("W83c_PKG", "s8").strip().lower()
REUSE = os.environ.get("W83c_REUSE", "0").strip() == "1"
if PKG_KEY not in C.PKG:
    raise SystemExit("W83c_PKG must be one of %r" % sorted(C.PKG))
PKG = C.PKG[PKG_KEY]
FEATURE_SET = C.FEATURE_SET
MAPSEL_OFFICIAL_SHA = "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    sink = L.Sink(TAG + "_" + PKG_KEY)
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline: NO lock taken, NO gamemd.exe launched",
                  pkg=PKG_KEY, reuse=REUSE, pkg_dir=str(PKG),
                  feature_set=str(FEATURE_SET), v15=str(C.V15))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline phase: %r" % residual)
        if C.lock_owner() != "lead":
            raise RuntimeError("lock owner is not lead at offline phase: %r" % C.lock_read())

        official = (C.V15 / "ra2forge" / "data" / "BATTLEMD.OFFICIAL.INI").read_bytes()
        official_sha = sha(official)
        sink.step("official_baseline", size=len(official), sha256=official_sha,
                  mapsel_official_sha=MAPSEL_OFFICIAL_SHA)

        if not REUSE:
            # (1) real-dir PRE manifest + signed baseline assertions
            rp = C.write_manifest(C.OUT / "real_pre.json", C.REAL)
            s = rp["summary"]
            sink.step("real_pre", summary=s)
            assert s["file_count"] == C.BASELINE["file_count"], s
            assert s["total_bytes"] == C.BASELINE["total_bytes"], s
            assert s["maplike_count"] == C.BASELINE["maplike_count"], s
            for name, pref in C.BASELINE.items():
                if name in ("file_count", "total_bytes", "maplike_count"):
                    continue
                h = s["hashes"].get(name)
                assert h and h.startswith(pref), (name, h, pref)
            sink.step("real_pre_baseline_ok", verdict=True)
            proof["real_pre_summary"] = s

            # (2) robocopy REAL -> sandbox (READ-ONLY source)
            if C.GAME.exists():
                raise RuntimeError("sandbox already exists; use W83c_REUSE=1: %s" % C.GAME)
            C.GAME.mkdir(parents=True, exist_ok=True)
            argv = ["robocopy", str(C.REAL), str(C.GAME),
                    "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1",
                    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
            rec = C.run_cmd(sink, "robocopy_sandbox", argv, timeout=900)
            rc = rec["exit_code"]
            if not (0 <= rc <= 7):
                raise RuntimeError("robocopy failed rc=%s" % rc)
            sink.step("robocopy_verdict", rc=rc, success=True)

            # (3) sandbox PRE manifest + pristine BYTE copies + hashes
            sp = C.write_manifest(C.OUT / "sandbox_pre.json", C.GAME)
            sink.step("sandbox_pre", summary=sp["summary"])
            assert sp["summary"]["file_count"] == C.BASELINE["file_count"], sp["summary"]
            assert sp["summary"]["total_bytes"] == C.BASELINE["total_bytes"], sp["summary"]
            proof["sandbox_pre_summary"] = sp["summary"]
            pristine_rows = C.save_pristine(sink)
            proof["pristine_rows"] = pristine_rows
            proof["pristine_n_present"] = sum(1 for r in pristine_rows if r["present"])

            # (4a) verify_pre + uninstall pre-existing v0.3 record
            vpre = C.v15_cmd(sink, "verify_pre",
                             ["verify", "--game", str(C.GAME), "--json"])
            sink.step("verify_pre_exit", exit_code=vpre["exit_code"])
            u = C.v15_cmd(sink, "uninstall_v03",
                          ["uninstall", "--game", str(C.GAME), "--json"])
            sink.step("uninstall_v03_exit", exit_code=u["exit_code"],
                      stdout_tail=u["stdout_tail"][-3000:])
            if u["exit_code"] != 0:
                raise RuntimeError("v0.3 uninstall exit %s" % u["exit_code"])
            vau = C.v15_cmd(sink, "verify_after_uninstall_v03",
                            ["verify", "--game", str(C.GAME), "--json"])
            sink.step("verify_after_v03_exit", exit_code=vau["exit_code"])
        else:
            # REUSE: sandbox + pristine already exist; uninstall current package
            if not C.GAME.is_dir():
                raise RuntimeError("W83c_REUSE=1 but sandbox missing: %s" % C.GAME)
            for fn in ("real_pre.json", "sandbox_pre.json"):
                if not (C.OUT / fn).is_file():
                    raise RuntimeError("W83c_REUSE=1 but %s missing" % fn)
            if not (C.OUT / "pristine" / "BATTLEMD.INI").is_file():
                raise RuntimeError("W83c_REUSE=1 but pristine copies missing")
            u = C.v15_cmd(sink, "uninstall_prev_" + PKG_KEY,
                          ["uninstall", "--game", str(C.GAME), "--json"])
            sink.step("uninstall_prev_exit", exit_code=u["exit_code"],
                      stdout_tail=u["stdout_tail"][-3000:])
            if u["exit_code"] != 0:
                raise RuntimeError("previous uninstall exit %s" % u["exit_code"])

        # (4b) remove the UNOWNED orphan .bak from the SANDBOX COPY ONLY.
        orphan = C.GAME / "BATTLEMD.INI.ra2forge.bak"
        orphan_info = {"present_before": orphan.is_file(),
                       "sha256": L.sha256_file(orphan) if orphan.is_file() else None,
                       "size": orphan.stat().st_size if orphan.is_file() else None}
        if orphan.is_file():
            orphan.unlink()
        orphan_info["removed_from_sandbox_only"] = not orphan.exists()
        sink.step("orphan_bak_prep", **orphan_info)

        # (4c) inplace target must be the official 2733 B baseline
        cur = (C.GAME / "BATTLEMD.INI").read_bytes()
        sink.step("inplace_target_precheck", size=len(cur), sha256=sha(cur),
                  expected_sha256=official_sha,
                  official_match=(sha(cur) == official_sha))
        if sha(cur) != official_sha:
            raise RuntimeError("BATTLEMD.INI in sandbox != official baseline; inplace would refuse")

        # (5) install v15 inplace package
        args = ["install", "--package", str(PKG), "--game", str(C.GAME),
                "--feature-set", str(FEATURE_SET)]
        i0 = C.v15_cmd(sink, "install_" + PKG_KEY + "_plain", args)
        sink.step("install_plain_exit", exit_code=i0["exit_code"],
                  stdout_tail=i0["stdout_tail"][-2500:])
        if i0["exit_code"] != 0:
            i1 = C.v15_cmd(sink, "install_" + PKG_KEY + "_allow",
                           args + ["--allow-content-conflict"])
            sink.step("install_allow_exit", exit_code=i1["exit_code"],
                      stdout_tail=i1["stdout_tail"][-3500:])
            if i1["exit_code"] != 0:
                raise RuntimeError("install exit %s (plain) / %s (allow)"
                                   % (i0["exit_code"], i1["exit_code"]))

        # (6) verify MUST exit 0
        v2 = C.v15_cmd(sink, "verify_after_install_" + PKG_KEY,
                       ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_install_exit", exit_code=v2["exit_code"],
                  stdout_tail=v2["stdout_tail"][-5000:])
        if v2["exit_code"] != 0:
            raise RuntimeError("verify after install exit %s" % v2["exit_code"])

        # (6b) .bak + manifest original_sha256 assertions
        rec_path = C.GAME / "ra2forge_install.json"
        man = json.loads(rec_path.read_text(encoding="utf-8"))
        entries = [e for e in man.get("files", []) if e.get("name") == "BATTLEMD.INI"]
        bak = C.GAME / "BATTLEMD.INI.ra2forge.bak"
        inplace = {
            "pkg": PKG_KEY, "manifest_path": str(rec_path),
            "manifest_size": rec_path.stat().st_size,
            "manifest_sha256": L.sha256_file(rec_path),
            "manifest_tool": man.get("tool"), "manifest_version": man.get("version"),
            "battlemd_entries": entries, "bak_present": bak.is_file(),
            "bak_size": bak.stat().st_size if bak.is_file() else None,
            "bak_sha256": L.sha256_file(bak) if bak.is_file() else None,
            "official_baseline_sha256": official_sha,
            "inplace_rewrite_block": man.get("inplace_rewrite"),
        }
        assert len(entries) == 1, entries
        e = entries[0]
        inplace["original_sha256_recorded"] = e.get("original_sha256")
        inplace["original_sha256_matches_official"] = (e.get("original_sha256") == official_sha)
        inplace["bak_equals_official"] = (bak.is_file() and L.sha256_file(bak) == official_sha)
        inplace["post_install_sha256_recorded"] = e.get("post_install_sha256")
        inplace["post_install_sha_on_disk"] = sha((C.GAME / "BATTLEMD.INI").read_bytes())
        inplace["post_install_sha_matches"] = (
            inplace["post_install_sha256_recorded"] == inplace["post_install_sha_on_disk"])
        inplace["sov1_scenario_on_disk"] = (
            b"Scenario=RA2F_M1.MAP" in (C.GAME / "BATTLEMD.INI").read_bytes())
        sink.step("inplace_install_assertions", **inplace)
        assert inplace["original_sha256_matches_official"]
        assert inplace["bak_equals_official"]
        assert inplace["post_install_sha_matches"]
        assert inplace["sov1_scenario_on_disk"]
        proof["inplace"] = inplace

        # (7) installed-file inventory + installed map == built package map
        installed = []
        for n in ("BATTLEMD.INI", "BATTLEMD.INI.ra2forge.bak", "MAPSELMD.INI",
                  "RA2F_M1.MAP", "expandmd98.mix", "ra2forge_install.json",
                  "ra2forge_install.json.seal"):
            p = C.GAME / n
            installed.append({"file": n, "present": p.is_file(),
                              "size": p.stat().st_size if p.is_file() else None,
                              "sha256": L.sha256_file(p) if p.is_file() else None})
        installed_map = (C.GAME / "RA2F_M1.MAP").read_bytes()
        pkg_map = (PKG / "RA2F_M1.MAP").read_bytes()
        installed_mapsel = (C.GAME / "MAPSELMD.INI").read_bytes()
        pkg_mapsel = (PKG / "MAPSELMD.INI").read_bytes()
        sink.step("installed_inventory", pkg=PKG_KEY, files=installed,
                  map_matches_package=(installed_map == pkg_map),
                  mapsel_matches_package=(installed_mapsel == pkg_mapsel),
                  installed_map_sha256=sha(installed_map))
        assert installed_map == pkg_map, "installed RA2F_M1.MAP != built package map"
        assert installed_mapsel == pkg_mapsel
        proof["installed"] = installed
        proof["map_matches_package"] = True
        ok = True
        sink.step("offline_result", ok=ok, pkg=PKG_KEY)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / ("OFFLINE_%s.json" % PKG_KEY)).write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok, pkg=PKG_KEY,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W76 offline phase — NO LOCK, NO gamemd.exe.

  1. Verify the already-built v15 package (BATTLEMD [SOV1] inplace rewrite,
     5 maps' [Basic] chain/EndOfGame, ElapsedTime->WinnerIs triggers).
  2. Produce the two MAPSELMD variants:
       A (PRIMARY, installed)   : appended stage numeric child keys "1=<next>"
                                  (keys from 1 continuous, W59 mov ebp,1)
       B (FALLBACK, comparison) : v15-native "2=<next>" (W39/W44 proven)
     Faction [Nod] keys are 1..12 continuous (<=100) in BOTH:
     7 official + 5 appended (8..12 = RA2F_M1..M5 stages).
  3. Real-dir PRE full manifest + signed baseline assertions.
  4. robocopy REAL -> sandbox (READ-ONLY source).
  5. sandbox PRE full manifest + byte-pristine copies of writable configs.
  6. verify_pre (v15, read-only).
  7. uninstall pre-existing v0.3 record; remove the unowned orphan
     BATTLEMD.INI.ra2forge.bak from the SANDBOX COPY ONLY (byte-restored at
     cleanup); assert BATTLEMD.INI is the official 2733 B baseline.
  8. install v15 inplace package (--feature-set); retry with
     --allow-content-conflict if needed.
  9. verify --game sandbox --json MUST exit 0; assert .bak present,
     manifest original_sha256 == official baseline sha, post_install sha.
 10. Inventory of installed files + hashes.

Everything writes ONLY inside W76_five_mission_chain.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w76_lib as L
import w76_common as C

TAG = "offline"

OFFICIAL_BATTLEMD_SHA = None  # filled from v15 bundled official bytes
MAPSEL_OFFICIAL_SHA = "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_mapsel_variants(sink) -> dict:
    """Variant A = child keys from 1 continuous; Variant B = v15 native 2=."""
    p = C.PKG / "MAPSELMD.INI"
    raw_b = p.read_bytes()                     # v15 native (2=)
    assert raw_b.count(b"\r\n") == raw_b.count(b"\n"), "MAPSELMD must be 100% CRLF"
    # keep the exact v15 output as the fallback/comparison variant
    (C.WORK / "MAPSELMD.INI.variant_from2").write_bytes(raw_b)
    (C.OUT / "MAPSELMD.INI.variant_from2").write_bytes(raw_b)

    lines_b = raw_b.split(b"\r\n")
    lines_a = []
    changed = []
    in_appended = False
    for i, ln in enumerate(lines_b):
        s = ln.strip()
        if s.startswith(b"[") and s.endswith(b"]"):
            in_appended = s.startswith(b"[RA2F_RA2F_M")
        if in_appended and b"=" in ln:
            k, _, v = ln.partition(b"=")
            if k.strip() == b"2" and v.strip().startswith(b"RA2F_RA2F_M"):
                new = b"1=" + v
                lines_a.append(new)
                changed.append({"line": i + 1, "before": ln.decode("latin-1"),
                                "after": new.decode("latin-1")})
                continue
        lines_a.append(ln)
    raw_a = b"\r\n".join(lines_a)
    assert len(changed) == 4, "expected exactly 4 appended non-final stage child links, got %r" % changed
    # structural self-check: both variants have identical section/line layout
    assert len(lines_a) == len(lines_b)
    assert raw_a.count(b"\r\n") == raw_b.count(b"\r\n")
    # faction keys must be a contiguous 1..10 run in both
    def faction_keys(raw):
        ls = raw.split(b"\r\n")
        j = ls.index(b"[Nod]")
        out = []
        for x in ls[j + 1:]:
            if x.startswith(b"[") and x.endswith(b"]"):
                break
            if b"=" in x:
                k = x.partition(b"=")[0].strip()
                if k.isdigit():
                    out.append(int(k))
        return out
    fk_b = faction_keys(raw_b)
    fk_a = faction_keys(raw_a)
    assert fk_b == list(range(1, 13)) == fk_a, (fk_b, fk_a)

    # PRIMARY lands in the package (that is what install copies into the game)
    p.write_bytes(raw_a)
    (C.WORK / "MAPSELMD.INI.variant_from1").write_bytes(raw_a)
    (C.OUT / "MAPSELMD.INI.variant_from1").write_bytes(raw_a)

    # appended stage child keys, per variant
    def child_keys(raw):
        out = []
        ls = raw.split(b"\r\n")
        for i, ln in enumerate(ls):
            if ln.startswith(b"[RA2F_RA2F_M"):
                for x in ls[i + 1:]:
                    if x.startswith(b"[") and x.endswith(b"]"):
                        break
                    if b"=" in x:
                        k, _, v = x.partition(b"=")
                        if k.strip().isdigit() and v.strip().startswith(b"RA2F_RA2F_M"):
                            out.append({"section": ln.decode("latin-1"),
                                        "key": k.strip().decode(),
                                        "value": v.strip().decode("latin-1")})
        return out
    rep = {
        "variant_A_primary_from1": {
            "path": str(p), "size": len(raw_a), "sha256": sha(raw_a),
            "child_keys": child_keys(raw_a), "faction_keys": fk_a,
            "note": "appended stage numeric children start at 1 (continuous 1..N per stage); faction keys 1..12 (8..12 = RA2F_M1..M5 stages)"},
        "variant_B_fallback_from2": {
            "path": str(C.WORK / "MAPSELMD.INI.variant_from2"),
            "size": len(raw_b), "sha256": sha(raw_b),
            "child_keys": child_keys(raw_b), "faction_keys": fk_b,
            "note": "v15 native / W39 W44 proven: appended stage child '2=<next>'"},
        "rewrites": changed,
        "single_variable": "only the appended stage child numeric key differs (1= vs 2=); faction keys and everything else byte-identical",
    }
    sink.step("mapsel_variants", **rep)
    (C.OUT / "MAPSELMD_VARIANTS.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


def verify_package(sink) -> dict:
    rep = {"package": str(C.PKG)}
    files = []
    for p in sorted(C.PKG.rglob("*"), key=lambda x: x.as_posix().lower()):
        if p.is_file():
            files.append({"rel": p.relative_to(C.PKG).as_posix(),
                          "size": p.stat().st_size, "sha256": L.sha256_file(p)})
    rep["files"] = files
    sink.step("package_inventory", **rep)

    b = (C.PKG / "BATTLEMD.INI").read_bytes()
    rep["battlemd"] = {"size": len(b), "sha256": sha(b),
                       "crlf": b.count(b"\r\n"),
                       "bare_lf": b.count(b"\n") - b.count(b"\r\n"),
                       "sov1_scenario": b.count(b"Scenario=RA2F_M1.MAP"),
                       "official_scenario": b.count(b"Scenario=SOV01umd.MAP")}
    assert rep["battlemd"]["sov1_scenario"] == 1
    assert rep["battlemd"]["official_scenario"] == 0
    assert rep["battlemd"]["bare_lf"] == 0
    assert b"\r\nCD=2\r\nScenario=RA2F_M1.MAP\r\n" in b

    ms = {}
    MAP_NAMES = ("RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP",
                 "RA2F_M4.MAP", "RA2F_M5.MAP")
    for name in MAP_NAMES:
        t = (C.PKG / name).read_bytes().decode("latin-1")
        d = {}
        for ln in t.splitlines():
            if ln.startswith("NextScenario="):
                d["NextScenario"] = ln.split("=", 1)[1]
            elif ln.startswith("EndOfGame="):
                d["EndOfGame"] = ln.split("=", 1)[1]
            elif ln.startswith("SkipMapSelect="):
                d["SkipMapSelect"] = ln.split("=", 1)[1]
        d["survive_trigger"] = ("Objective: survive 8s" in t)
        d["elapsed_time_event"] = (",13," in t or "13," in t)
        d["winner_is_action"] = ("WinnerIs" in t or ",1,0,0,0,0,A" in t)
        d["has_nacnst"] = ("NACNST" in t)
        d["has_mtnk"] = ("MTNK" in t)
        ms[name] = d
    rep["maps"] = ms
    expected_next = {"RA2F_M1.MAP": "RA2F_M2.MAP",
                     "RA2F_M2.MAP": "RA2F_M3.MAP",
                     "RA2F_M3.MAP": "RA2F_M4.MAP",
                     "RA2F_M4.MAP": "RA2F_M5.MAP",
                     "RA2F_M5.MAP": ""}
    expected_eog = {"RA2F_M1.MAP": "no", "RA2F_M2.MAP": "no",
                    "RA2F_M3.MAP": "no", "RA2F_M4.MAP": "no",
                    "RA2F_M5.MAP": "yes"}
    for name in MAP_NAMES:
        assert ms[name]["NextScenario"] == expected_next[name], (name, ms[name])
        assert ms[name]["EndOfGame"] == expected_eog[name], (name, ms[name])
        assert ms[name]["SkipMapSelect"] == "no" and ms[name]["survive_trigger"] and ms[name]["has_nacnst"], (name, ms[name])
    sink.step("package_verify", **rep)
    (C.OUT / "PACKAGE_VERIFY.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline: NO lock taken, NO gamemd.exe launched",
                  design=str(C.DESIGN), feature_set=str(C.FEATURE_SET),
                  v15=str(C.V15), pkg=str(C.PKG))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline phase: %r" % residual)

        # (0) official baseline sha from v15 bundled data
        official = (C.V15 / "ra2forge" / "data" / "BATTLEMD.OFFICIAL.INI").read_bytes()
        global OFFICIAL_BATTLEMD_SHA
        OFFICIAL_BATTLEMD_SHA = sha(official)
        sink.step("official_baseline", size=len(official),
                  sha256=OFFICIAL_BATTLEMD_SHA,
                  mapsel_official_sha=MAPSEL_OFFICIAL_SHA)

        # (1) package verification
        verify_package(sink)

        # (2) MAPSELMD variants (A primary from 1, B fallback from 2)
        build_mapsel_variants(sink)

        # (3) real-dir PRE manifest + signed baseline assertions
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

        # (4) robocopy REAL -> sandbox (READ-ONLY source)
        if C.GAME.exists():
            raise RuntimeError("sandbox already exists; refusing to overwrite: %s" % C.GAME)
        C.GAME.mkdir(parents=True, exist_ok=True)
        argv = ["robocopy", str(C.REAL), str(C.GAME),
                "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1",
                "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
        rec = C.run_cmd(sink, "robocopy_sandbox", argv, timeout=900)
        rc = rec["exit_code"]
        if not (0 <= rc <= 7):
            raise RuntimeError("robocopy failed rc=%s" % rc)
        sink.step("robocopy_verdict", rc=rc, success=True)

        # (5) sandbox PRE manifest + pristine byte copies
        sp = C.write_manifest(C.OUT / "sandbox_pre.json", C.GAME)
        sink.step("sandbox_pre", summary=sp["summary"])
        assert sp["summary"]["file_count"] == C.BASELINE["file_count"], sp["summary"]
        assert sp["summary"]["total_bytes"] == C.BASELINE["total_bytes"], sp["summary"]
        C.save_pristine(sink)

        # (6) verify_pre (v15, read-only)
        vpre = C.v15_cmd(sink, "verify_pre",
                         ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_pre_exit", exit_code=vpre["exit_code"])

        # (7) uninstall pre-existing v0.3 record (W44 §2 flow)
        v03 = C.v15_cmd(sink, "verify_v03",
                        ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_v03_exit", exit_code=v03["exit_code"])
        u = C.v15_cmd(sink, "uninstall_v03",
                      ["uninstall", "--game", str(C.GAME), "--json"])
        sink.step("uninstall_v03_exit", exit_code=u["exit_code"],
                  stdout_tail=u["stdout_tail"][-3000:])
        if u["exit_code"] != 0:
            raise RuntimeError("v0.3 uninstall exit %s" % u["exit_code"])
        vau = C.v15_cmd(sink, "verify_after_uninstall_v03",
                        ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_v03_exit", exit_code=vau["exit_code"])

        # (7b) remove the UNOWNED orphan .bak from the SANDBOX COPY ONLY.
        # It is a 241 B W27-era diagnostic backup, not the official file and
        # not owned by any manifest. v15 inplace_preflight refuses (exit 34)
        # if it remains. We saved a byte-pristine copy in pristine/ and will
        # restore it byte-for-byte during finalize. REAL dir is NEVER touched.
        orphan = C.GAME / "BATTLEMD.INI.ra2forge.bak"
        orphan_info = {"present_before": orphan.is_file(),
                       "sha256": L.sha256_file(orphan) if orphan.is_file() else None,
                       "size": orphan.stat().st_size if orphan.is_file() else None,
                       "pristine_copy": str(C.OUT / "pristine" / "BATTLEMD.INI.ra2forge.bak")}
        if orphan.is_file():
            orphan.unlink()
        orphan_info["removed_from_sandbox_only"] = not orphan.exists()
        sink.step("orphan_bak_prep", **orphan_info)

        # (7c) the inplace target must be the official 2733 B baseline
        cur = (C.GAME / "BATTLEMD.INI").read_bytes()
        sink.step("inplace_target_precheck", size=len(cur), sha256=sha(cur),
                  expected_sha256=OFFICIAL_BATTLEMD_SHA,
                  official_match=(sha(cur) == OFFICIAL_BATTLEMD_SHA))
        if sha(cur) != OFFICIAL_BATTLEMD_SHA:
            raise RuntimeError("BATTLEMD.INI in sandbox != official baseline; inplace would refuse")

        # (8) install v15 inplace package
        i0 = C.v15_cmd(sink, "install_inplace_plain",
                       ["install", "--package", str(C.PKG), "--game", str(C.GAME),
                        "--feature-set", str(C.FEATURE_SET)])
        sink.step("install_plain_exit", exit_code=i0["exit_code"],
                  stdout_tail=i0["stdout_tail"][-2500:])
        if i0["exit_code"] != 0:
            i1 = C.v15_cmd(sink, "install_inplace_allow",
                           ["install", "--package", str(C.PKG), "--game", str(C.GAME),
                            "--feature-set", str(C.FEATURE_SET),
                            "--allow-content-conflict"])
            sink.step("install_allow_exit", exit_code=i1["exit_code"],
                      stdout_tail=i1["stdout_tail"][-3500:])
            if i1["exit_code"] != 0:
                raise RuntimeError("install exit %s (plain) / %s (allow)"
                                   % (i0["exit_code"], i1["exit_code"]))

        # (9) verify MUST exit 0
        v2 = C.v15_cmd(sink, "verify_after_install",
                       ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_install_exit", exit_code=v2["exit_code"],
                  stdout_tail=v2["stdout_tail"][-5000:])
        if v2["exit_code"] != 0:
            raise RuntimeError("verify after install exit %s" % v2["exit_code"])

        # (9b) .bak + manifest original_sha256 assertions
        rec_path = C.GAME / "ra2forge_install.json"
        man = json.loads(rec_path.read_text(encoding="utf-8"))
        entries = [e for e in man.get("files", []) if e.get("name") == "BATTLEMD.INI"]
        bak = C.GAME / "BATTLEMD.INI.ra2forge.bak"
        inplace = {
            "manifest_path": str(rec_path), "manifest_size": rec_path.stat().st_size,
            "manifest_sha256": L.sha256_file(rec_path),
            "manifest_tool": man.get("tool"), "manifest_version": man.get("version"),
            "battlemd_entries": entries,
            "bak_present": bak.is_file(),
            "bak_size": bak.stat().st_size if bak.is_file() else None,
            "bak_sha256": L.sha256_file(bak) if bak.is_file() else None,
            "official_baseline_sha256": OFFICIAL_BATTLEMD_SHA,
            "inplace_rewrite_block": man.get("inplace_rewrite"),
        }
        assert len(entries) == 1, entries
        e = entries[0]
        inplace["original_sha256_recorded"] = e.get("original_sha256")
        inplace["original_sha256_matches_official"] = (
            e.get("original_sha256") == OFFICIAL_BATTLEMD_SHA)
        inplace["bak_equals_official"] = (
            bak.is_file() and L.sha256_file(bak) == OFFICIAL_BATTLEMD_SHA)
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
        (C.OUT / "INPLACE_INSTALL.json").write_text(
            json.dumps(inplace, ensure_ascii=False, indent=2), encoding="utf-8")

        # (10) installed-file inventory
        installed = []
        for n in ("BATTLEMD.INI", "BATTLEMD.INI.ra2forge.bak",
                  "MAPSELMD.INI", "RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP",
                  "RA2F_M4.MAP", "RA2F_M5.MAP",
                  "expandmd98.mix", "ra2forge_install.json"):
            p = C.GAME / n
            installed.append({"file": n, "present": p.is_file(),
                              "size": p.stat().st_size if p.is_file() else None,
                              "sha256": L.sha256_file(p) if p.is_file() else None})
        # confirm the installed MAPSELMD is the PRIMARY (from-1) variant
        inst_ms = (C.GAME / "MAPSELMD.INI").read_bytes()
        a_ms = (C.OUT / "MAPSELMD.INI.variant_from1").read_bytes()
        b_ms = (C.OUT / "MAPSELMD.INI.variant_from2").read_bytes()
        sink.step("installed_inventory", files=installed,
                  mapsel_is_variant_A_from1=(inst_ms == a_ms),
                  mapsel_is_variant_B_from2=(inst_ms == b_ms),
                  mapsel_sha256=sha(inst_ms))
        assert inst_ms == a_ms, "installed MAPSELMD is NOT the primary from-1 variant"
        ok = True
        sink.step("offline_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-6000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(),
                  lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

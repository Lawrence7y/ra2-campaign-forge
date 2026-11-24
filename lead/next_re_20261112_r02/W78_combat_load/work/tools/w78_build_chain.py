#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W78 BUILD chain — Task 3 (time permitting).  Offline, NO LOCK, NO gamemd.exe.

Two-mission chain:
  M1 = the v2 REAL-COMBAT layout (60x60, both sides armed, enemy Hunt,
       win = survive(55)), NextScenario=RA2F_M2.MAP, EndOfGame=no
  M2 = a minimal speedrun mission (win = survive(8)), EndOfGame=yes

MAPSELMD: v15 clone_append produces the M1 stage child link as "2=<M2 stage>".
W76's proven PRIMARY variant rewrites appended-stage child keys to "1=<next>"
(keys from 1 continuous, W59 mov ebp,1).  We apply the same single-variable
rewrite here and keep the v15-native bytes as a comparison variant.

Only writes inside W78_combat_load.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w78_lib as L
import w78_common as C

TAG = "build_chain"

DESIGN_CHAIN = C.WORK / "w78_design_chain.json"
FS_CHAIN = C.WORK / "w78_feature_set_chain.json"
PKG_CHAIN = C.WORK / "pkg_chain" / "W78CombatChain"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_chain_design(sink):
    d = json.loads((C.WORK / "w78_design_v2_time.json").read_text(encoding="utf-8"))
    camp = d["campaign"]
    camp["name"] = "W78CombatChain"
    camp["description"] = "W78 2-mission chain: M1 real combat load -> M2."
    d["package"] = {"id": "org.ra2forge.w78.combatchain", "version": "1.0"}
    m1 = d["missions"][0]
    m1["title"] = "W78 Chain M1 (real combat)"
    m1["briefing"] = ("W78 CHAIN M1: real combat load. Enemy assault force starts "
                      "close; survive 55 s, then advance to M2.")
    m2 = {
        "name": "RA2F_M2",
        "title": "W78 Chain M2 (post-combat)",
        "briefing": "W78 CHAIN M2 reached after real combat load. ElapsedTime(8) win.",
        "theater": "TEMPERATE",
        "size": [40, 40],
        "player": {"house": "Russians", "credits": 5000, "enemy_credits": 0},
        "waypoints": {"0": [20, 20], "1": [20, 20], "2": [8, 8]},
        "structures": [
            {"owner": "Russians", "type": "NACNST", "row": 30, "col": 20},
            {"owner": "Russians", "type": "NAPOWR", "row": 32, "col": 18},
        ],
        "units": [{"owner": "Russians", "type": "MTNK", "row": 31, "col": 22}],
        "infantry": [{"owner": "Russians", "type": "E2", "row": 33, "col": 20}],
        "objectives": [
            {"type": "text", "text": "W78 CHAIN M2 reached after combat", "at_second": 1},
            {"type": "survive", "seconds": 8},
        ],
    }
    d["missions"] = [m1, m2]
    DESIGN_CHAIN.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    fs = json.loads(C.FEATURE_SET.read_text(encoding="utf-8"))
    fs["feature_set_id"] = "W78-CHAIN-INPLACE-2M"
    fs["features"]["maps"]["map_files"] = ["RA2F_M1.MAP", "RA2F_M2.MAP"]
    fs["features"]["maps"]["chain"] = ["RA2F_M1", "RA2F_M2"]
    fs["features"]["mix"]["source_map_set"] = ["RA2F_M1.MAP", "RA2F_M2.MAP"]
    fs["features"]["mapselmd"]["stages"] = ["RA2F_M1.MAP", "RA2F_M2.MAP"]
    FS_CHAIN.write_text(json.dumps(fs, ensure_ascii=False, indent=2), encoding="utf-8")
    sink.step("chain_design_written", design=str(DESIGN_CHAIN), fs=str(FS_CHAIN),
              missions=[m["name"] for m in d["missions"]])
    return DESIGN_CHAIN, FS_CHAIN


def rewrite_mapsel_from1(sink, pkg: Path) -> dict:
    p = pkg / "MAPSELMD.INI"
    raw_b = p.read_bytes()
    assert raw_b.count(b"\r\n") == raw_b.count(b"\n"), "MAPSELMD must be 100% CRLF"
    (C.WORK / "MAPSELMD.INI.chain_from2").write_bytes(raw_b)
    (C.OUT / "MAPSELMD.INI.chain_from2").write_bytes(raw_b)
    lines = raw_b.split(b"\r\n")
    out = []
    changed = []
    in_appended = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith(b"[") and s.endswith(b"]"):
            in_appended = s.startswith(b"[RA2F_RA2F_M")
        if in_appended and b"=" in ln:
            k, _, v = ln.partition(b"=")
            if k.strip() == b"2" and v.strip().startswith(b"RA2F_RA2F_M"):
                new = b"1=" + v
                out.append(new)
                changed.append({"line": i + 1, "before": ln.decode("latin-1"),
                                "after": new.decode("latin-1")})
                continue
        out.append(ln)
    raw_a = b"\r\n".join(out)
    assert len(changed) == 1, "expected exactly 1 appended non-final stage child link, got %r" % changed
    assert len(out) == len(lines)
    assert raw_a.count(b"\r\n") == raw_b.count(b"\r\n")
    # faction [Nod] keys must be contiguous 1..9 (7 official + 2 appended)
    def faction_keys(raw):
        ls = raw.split(b"\r\n")
        j = ls.index(b"[Nod]")
        keys = []
        for x in ls[j + 1:]:
            if x.startswith(b"[") and x.endswith(b"]"):
                break
            if b"=" in x:
                k = x.partition(b"=")[0].strip()
                if k.isdigit():
                    keys.append(int(k))
        return keys
    fk = faction_keys(raw_a)
    assert fk == list(range(1, 10)), fk
    p.write_bytes(raw_a)
    (C.WORK / "MAPSELMD.INI.chain_from1").write_bytes(raw_a)
    (C.OUT / "MAPSELMD.INI.chain_from1").write_bytes(raw_a)
    rep = {"primary_from1": {"size": len(raw_a), "sha256": sha(raw_a),
                             "child_keys": changed, "faction_keys": fk},
           "comparison_from2": {"size": len(raw_b), "sha256": sha(raw_b)},
           "single_variable": "only the appended M1 stage child numeric key differs (1= vs 2=)"}
    sink.step("mapsel_chain_variants", **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build 2-mission chain: NO lock, NO gamemd.exe")
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline phase: %r" % residual)
        design, fs = make_chain_design(sink)
        out_dir = C.WORK / "pkg_chain"
        out_dir.mkdir(parents=True, exist_ok=True)
        rec = C.v15_cmd(sink, "build_chain",
                        ["build", "--design", str(design), "--out", str(out_dir),
                         "--feature-set", str(fs)])
        if rec["exit_code"] != 0:
            raise RuntimeError("chain build exit %s: %s" %
                               (rec["exit_code"], rec["stderr_tail"][-2000:]))
        # NOTE: campaign.name is W78CombatChain -> package dir name
        pkg = out_dir / "W78CombatChain"
        assert pkg.is_dir(), pkg
        (pkg / "ra2forge_package.json").write_text(
            json.dumps({"tool": "ra2forge",
                        "package_id": "org.ra2forge.w78.combatchain",
                        "package_version": "1.0"}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        rep["mapsel"] = rewrite_mapsel_from1(sink, pkg)

        def map_info(name):
            t = (pkg / name).read_bytes().decode("latin-1")
            d = {}
            for ln in t.splitlines():
                for k in ("NextScenario", "EndOfGame", "SkipMapSelect"):
                    if ln.startswith(k + "="):
                        d[k] = ln.split("=", 1)[1]
                if ln.startswith("Size=") and "0,0," in ln:
                    d["Size"] = ln.split("=", 1)[1]
            d["british_units"] = t.count("British,")
            d["elapsed_55"] = (",13,0,55" in t)
            d["elapsed_8"] = (",13,0,8" in t)
            return d
        m1, m2 = map_info("RA2F_M1.MAP"), map_info("RA2F_M2.MAP")
        rep["maps"] = {"RA2F_M1.MAP": m1, "RA2F_M2.MAP": m2}
        b = (pkg / "BATTLEMD.INI").read_bytes()
        rep["battlemd"] = {"size": len(b), "sha256": sha(b),
                           "sov1_scenario": b.count(b"Scenario=RA2F_M1.MAP"),
                           "official_scenario": b.count(b"Scenario=SOV01umd.MAP")}
        assert rep["battlemd"]["sov1_scenario"] == 1 and rep["battlemd"]["official_scenario"] == 0
        assert m1["NextScenario"] == "RA2F_M2.MAP", m1
        assert m1["EndOfGame"] == "no", m1
        assert m2["NextScenario"] == "" and m2["EndOfGame"] == "yes", m2
        assert m1["british_units"] >= 12 and m1["elapsed_55"], m1
        assert m2["elapsed_8"], m2
        assert (pkg / "MAPSELMD.INI").is_file() and (pkg / "expandmd98.mix").is_file()
        rep["pkg"] = str(pkg)
        rep["layout"] = {"m1": "v2 real combat (60x60, 10 Russian tanks+4 inf vs "
                               "6 British tanks+6 inf all Hunt), survive(55)",
                         "m2": "minimal 40x40, survive(8), EndOfGame=yes"}
        ok = True
        sink.step("build_chain_result", ok=ok, **rep["layout"])
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "BUILD_CHAIN_RESULT.json").write_text(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

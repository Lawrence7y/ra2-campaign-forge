#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""W62 / Criterion C — non-intrusion / zero-out-of-scope-write audit (offline).

Implements the FROZEN CRITERIA_SPEC.md §1 (frozen 2026-11-13T23:25:30+08:00).
DO NOT change the declared write-set / protected-set / decision table after
seeing results — project discipline §3.4.

All "installs" are v15 CLI operations on a SYNTHETIC sandbox game directory
inside EVIDENCE/sandbox/.  The sandbox gamemd.exe is an inert placeholder that
is NEVER executed.  No game process is launched, no attach, no live memory,
no .game_instance.lock.  (I launched 0 / attached 0.)

Usage:
  python tool_c_writeaudit.py --run-all --out EVIDENCE      # C-A + C-B + C-NEG
  python tool_c_writeaudit.py --selftest --out EVIDENCE     # C-NEG only (no v15)
  python tool_c_writeaudit.py --audit --before b.json --after a.json \
      --uninst u.json --declared d.json --out result.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SCHEMA_VERSION = "C-W62-1"
SPEC_FROZEN_AT = "2026-11-13T23:25:30+08:00"

# v15 package root (READ-ONLY reference; we only run its CLI, never modify it)
ROOT = Path(r"D:\Project\ra2-campaign-forge")
V15 = (ROOT / "lead" / "next_re_20261112_r02" / "W60_battlemd_inplace"
       / "ra2forge_patched_v15")
OFFICIAL_BATTLEMD = V15 / "ra2forge" / "data" / "BATTLEMD.OFFICIAL.INI"

# CRITERIA_SPEC §1.2 : engine-derived whitelist, declared UP FRONT, fixed.
ENGINE_DERIVED = ("ra2forge_install.json", "ra2forge_install.json.seal")
BACKUP_SUFFIX = ".ra2forge.bak"
# CRITERIA_SPEC §1.3 : explicitly named protected engine files (hard req 3)
NAMED_PROTECTED = ("gamemd.exe", "ddraw.dll", "RA2MD.INI")
# CRITERIA_SPEC §1.5 : uninstall residue whitelist = EMPTY (declared up front)
UNINSTALL_RESIDUE_WHITELIST = frozenset()


# ---------------------------------------------------------------------------
# snapshots
# ---------------------------------------------------------------------------
def snapshot_tree(root) -> dict:
    """{relpath: {size, sha256, mtime_ns}} for every regular file under root."""
    root = Path(root)
    snap = {}
    if not root.is_dir():
        return snap
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        data = p.read_bytes()
        st = p.stat()
        snap[rel] = {
            "size": st.st_size,
            "sha256": hashlib.sha256(data).hexdigest(),
            "mtime_ns": st.st_mtime_ns,
        }
    return snap


def diff_snapshots(before: dict, after: dict) -> dict:
    """CRITERIA_SPEC §1.1 write-set W = added U modified U removed."""
    kb, ka = set(before), set(after)
    added = sorted(ka - kb)
    removed = sorted(kb - ka)
    modified = []
    for k in sorted(kb & ka):
        b, a = before[k], after[k]
        if b["sha256"] != a["sha256"] or b["size"] != a["size"]:
            modified.append(k)
    return {"added": added, "modified": modified, "removed": removed}


def write_set_keys(diff: dict) -> set:
    return set(diff["added"]) | set(diff["modified"]) | set(diff["removed"])


def restore_equal(pre: dict, uninst: dict) -> dict:
    """CRITERIA_SPEC §1.1 / C-4: relpath + size + sha256 only (NOT mtime)."""
    kp, ku = set(pre), set(uninst)
    missing = sorted(kp - ku)
    residual = sorted(ku - kp)
    changed = []
    for k in sorted(kp & ku):
        if (pre[k]["size"] != uninst[k]["size"]
                or pre[k]["sha256"] != uninst[k]["sha256"]):
            changed.append(k)
    ok = not (missing or residual or changed)
    return {"equal": ok, "missing": missing, "residual": residual,
            "changed": changed,
            "residual_outside_whitelist": [r for r in residual
                                          if r not in UNINSTALL_RESIDUE_WHITELIST]}


# ---------------------------------------------------------------------------
# declared write set D (CRITERIA_SPEC §1.2) — independent of v15 runtime output
# ---------------------------------------------------------------------------
def package_members(pkg_dir) -> list[str]:
    """Mirror install.package_files() (install.py:760-793) [本次读码]."""
    pkg = Path(pkg_dir)
    names = []
    ini = None
    for cand in ("BATTLEMD.INI", "BATTLEMD98.INI"):
        if (pkg / cand).is_file():
            ini = cand
            break
    if ini is None:
        raise FileNotFoundError(f"no BATTLEMD*.INI in package {pkg}")
    names.append(ini)
    for cand in ("MAPSELMD.INI", "ra2md.csf"):
        if (pkg / cand).is_file():
            names.append(cand)
    names += sorted(p.name for p in pkg.glob("*.MAP") if p.is_file())
    if (pkg / "expandmd98.mix").is_file():
        names.append("expandmd98.mix")
    return names


def declared_write_set(pkg_dir, pre: dict) -> dict:
    """D = package members U engine-derived U per-member .bak (if pre-existing).

    Returns {"D": sorted list, "members": [...], "declared_rewrite": [...],
             "bak_slots": [...], "engine_derived": [...]}
    """
    members = package_members(pkg_dir)
    d = set(members)
    d |= set(ENGINE_DERIVED)
    bak = []
    for n in members:
        if n in pre:                       # pre-existing -> installer backs it up
            slot = n + BACKUP_SUFFIX
            d.add(slot)
            bak.append(slot)
    # CRITERIA_SPEC §1.2(3): inplace iff BATTLEMD.INI in pkg and no BATTLEMD98.INI
    inplace = ("BATTLEMD.INI" in members) and ("BATTLEMD98.INI" not in members)
    declared_rewrite = ["BATTLEMD.INI"] if inplace else []
    return {
        "D": sorted(d), "members": members,
        "declared_rewrite": declared_rewrite, "inplace": inplace,
        "bak_slots": sorted(bak), "engine_derived": list(ENGINE_DERIVED),
    }


def protected_set(pre: dict, d_set: set) -> dict:
    """CRITERIA_SPEC §1.3: P_prot = every pre-existing file NOT in D.

    Strict superset of the named engine files + *.MIX/*.CSF.  Keeping it strict
    makes any undeclared rewrite FAIL, which is the whole point of C.
    """
    p = {}
    for k in sorted(set(pre) - d_set):
        p[k] = {
            "pre_sha256": pre[k]["sha256"],
            "named_engine_file": k in NAMED_PROTECTED,
            "official_mix": k.upper().endswith(".MIX"),
            "official_csf": k.upper().endswith(".CSF"),
        }
    return p


def protected_hash_check(pre: dict, post: dict, prot: dict) -> dict:
    rows = []
    all_equal = True
    for k, meta in prot.items():
        post_sha = post.get(k, {}).get("sha256")
        eq = (post_sha == meta["pre_sha256"])
        all_equal = all_equal and eq
        rows.append({"path": k, "pre_sha256": meta["pre_sha256"],
                     "post_sha256": post_sha, "equal": eq,
                     "named_engine_file": meta["named_engine_file"],
                     "official_mix": meta["official_mix"],
                     "official_csf": meta["official_csf"]})
    return {"all_equal": all_equal, "rows": rows}


# ---------------------------------------------------------------------------
# the frozen C decision table (CRITERIA_SPEC §1.4)
# ---------------------------------------------------------------------------
def audit(before, after, uninst, declared, *, bak_bytes_pre=None,
          bak_bytes_post=None) -> dict:
    D = set(declared["D"])
    W = diff_snapshots(before, after)
    Wkeys = write_set_keys(W)
    out_of_scope = sorted(Wkeys - D)
    prot = protected_set(before, D)
    prot_check = protected_hash_check(before, after, prot)
    restore = restore_equal(before, uninst)

    report = {
        "schema_version": SCHEMA_VERSION,
        "spec_frozen_at": SPEC_FROZEN_AT,
        "declared": declared,
        "write_set": W,
        "write_set_flat": sorted(Wkeys),
        "out_of_scope_writes": out_of_scope,
        "protected_set": prot,
        "protected_hash_check": prot_check,
        "restore": restore,
        "checks": {},
        "verdict": None,
    }

    # C-1 / C-2  (checks use PASS-semantics: True = satisfied, False = FAIL)
    c1 = (len(out_of_scope) == 0)
    report["checks"]["C-1_actual_write_subset_of_declared"] = c1
    report["checks"]["C-2_no_out_of_scope_writes"] = c1
    # C-3
    c3 = prot_check["all_equal"]
    # also: no protected file may be modified/removed at all
    touched_protected = sorted(
        (set(W["modified"]) | set(W["removed"])) & set(prot))
    report["protected_touched"] = touched_protected
    c3 = c3 and (len(touched_protected) == 0)
    report["checks"]["C-3_protected_byte_identical"] = c3
    # C-4 / C-5
    c4 = restore["equal"]
    c5 = (len(restore["residual_outside_whitelist"]) > 0
          or len(restore["missing"]) > 0 or len(restore["changed"]) > 0)
    report["checks"]["C-4_uninstall_restores_pre_state"] = c4
    report["checks"]["C-5_no_residual_outside_whitelist"] = (not c5)
    # C-6 (inplace only): .bak present, byte-restorable, consumed on uninstall
    c6 = None
    if declared["inplace"]:
        bak = "BATTLEMD.INI" + BACKUP_SUFFIX
        bak_present_post = bak in after
        bak_absent_uninst = bak not in uninst
        target_restored = (
            uninst.get("BATTLEMD.INI", {}).get("sha256")
            == before.get("BATTLEMD.INI", {}).get("sha256"))
        bak_bytes_ok = None
        if bak_bytes_pre is not None and bak_bytes_post is not None:
            bak_bytes_ok = (hashlib.sha256(bak_bytes_pre).hexdigest()
                            == hashlib.sha256(bak_bytes_post).hexdigest())
        c6 = all([bak_present_post, bak_absent_uninst, target_restored,
                  bak_bytes_ok is not False])
        report["inplace_proof"] = {
            "declared_rewrite": declared["declared_rewrite"],
            "bak_slot": bak,
            "bak_present_post_install": bak_present_post,
            "bak_bytes_equal_to_pre_official": bak_bytes_ok,
            "bak_consumed_after_uninstall": bak_absent_uninst,
            "target_sha_restored": target_restored,
            "classified_as": "DECLARED-REWRITE (not out-of-scope)"
                             if "BATTLEMD.INI" in declared["declared_rewrite"]
                             else "n/a",
        }
    report["checks"]["C-6_inplace_bak_and_restore"] = c6

    failed = [k for k, v in report["checks"].items()
              if v is False]
    report["failed_checks"] = failed
    report["verdict"] = "PASS" if not failed else "FAIL"
    return report


# ---------------------------------------------------------------------------
# v15 CLI driver (pure file ops on the synthetic sandbox)
# ---------------------------------------------------------------------------
def run_v15(args: list[str], label: str, log: list) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-B", "-X", "utf8", "-m", "ra2forge", *args]
    proc = subprocess.run(cmd, cwd=str(V15), env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=300)
    entry = {"label": label, "cmd": " ".join(cmd), "exit": proc.returncode,
             "stdout": proc.stdout, "stderr": proc.stderr}
    log.append(entry)
    return entry


def _design(name: str, package_id: str) -> dict:
    return {
        "package": {"id": package_id, "version": "1.0"},
        "campaign": {"name": name, "description": "W62 C-audit synthetic campaign.",
                     "side": "soviet", "id": "RA2F1"},
        "missions": [{
            "name": n, "title": n, "briefing": "W62 C-audit mission.",
            "theater": "TEMPERATE", "size": [60, 60],
            "player": {"house": "Russians"},
            "structures": [
                {"owner": "Russians", "type": "NACNST", "row": 40, "col": 30},
                {"owner": "Americans", "type": "GACNST", "row": 15,
                 "col": 30, "tag": "hq"},
            ],
            "objectives": [{"type": "destroy_building", "structure_tag": "hq"}],
        } for n in ("CP1", "CP2")],
    }


def _inplace_feature_set(fsid: str) -> dict:
    """s5_cases.py:55-71 _inplace_fs() [本次读码]."""
    return {
        "schema_version": "w42-s2-1", "kind": "feature_set",
        "feature_set_id": fsid,
        "features": {
            "maps": {"mode": "sideload", "map_files": ["CP1.MAP", "CP2.MAP"],
                     "chain": ["CP1", "CP2"]},
            "battlemd": {"mode": "inplace", "scenario": "ECH01.MAP",
                         "description_ref": "raw"},
            "mix": {"mode": "repack",
                    "source_map_set": ["CP1.MAP", "CP2.MAP"],
                    "target_name": "expandmd98.mix"},
            "csf": {"mode": "off"},
            "mapselmd": {"mode": "off"},
        },
    }


def make_sandbox_game(game: Path) -> None:
    """Inert golden game dir.  NEVER executed.  Official BATTLEMD.INI is the
    REAL 2733 B baseline so v15 inplace_preflight accepts it."""
    game.mkdir(parents=True, exist_ok=True)
    (game / "gamemd.exe").write_bytes(b"INERT PLACEHOLDER - NEVER EXECUTED\n")
    (game / "ddraw.dll").write_bytes(b"INERT ddraw.dll - official, protected\n")
    (game / "RA2MD.INI").write_bytes(b"[General]\n ; inert fixture\n")
    (game / "BATTLEMD.INI").write_bytes(OFFICIAL_BATTLEMD.read_bytes())
    (game / "langmd.mix").write_bytes(b"OFFICIAL *.MIX - protected, never written\n")
    (game / "language.csf").write_bytes(b"OFFICIAL *.CSF - protected\n")
    (game / "USERMAP1.MAP").write_bytes(b"the user's own map, never recorded\n")


def run_case(case_id: str, base: Path, log: list, *, inplace: bool) -> dict:
    case = base / case_id
    game = case / "game"
    build_out = case / "build_out"
    if case.exists():
        import shutil
        shutil.rmtree(case)
    case.mkdir(parents=True)
    make_sandbox_game(game)

    design = _design("W62C1" if not inplace else "W62C2",
                     "org.ra2forge.w62.c1" if not inplace
                     else "org.ra2forge.w62.c2")
    dp = case / "design.json"
    dp.write_text(json.dumps(design, indent=2, ensure_ascii=False),
                  encoding="utf-8")
    build_args = ["build", "--design", str(dp), "--out", str(build_out)]
    fs_path = None
    if inplace:
        fs_path = case / "fs_inplace.json"
        fs_path.write_text(json.dumps(_inplace_feature_set("W62-INPLACE"),
                                      indent=2, ensure_ascii=False),
                           encoding="utf-8")
        build_args += ["--feature-set", str(fs_path)]

    r_build = run_v15(build_args, f"{case_id}-build", log)
    pkg = build_out / design["campaign"]["name"]
    if r_build["exit"] != 0 or not pkg.is_dir():
        return {"case": case_id, "fatal": "v15 build failed",
                "build": r_build, "verdict": "FAIL"}

    S_pre = snapshot_tree(game)
    install_args = ["install", "--package", str(pkg), "--game", str(game)]
    if inplace:
        install_args += ["--feature-set", str(fs_path)]
    r_inst = run_v15(install_args, f"{case_id}-install", log)
    S_post = snapshot_tree(game)

    declared = declared_write_set(pkg, S_pre)

    # C-6 byte proof: compare the actual .bak bytes against the REAL official
    # baseline bytes (not against a snapshot string) BEFORE uninstall consumes it.
    bak_bytes_pre = bak_bytes_post = None
    if declared["inplace"]:
        p_bak = game / ("BATTLEMD.INI" + BACKUP_SUFFIX)
        if p_bak.is_file():
            bak_bytes_pre = OFFICIAL_BATTLEMD.read_bytes()   # original official
            bak_bytes_post = p_bak.read_bytes()             # installer's backup

    r_uninst = run_v15(["uninstall", "--game", str(game)],
                       f"{case_id}-uninstall", log)
    S_uninst = snapshot_tree(game)

    rep = audit(S_pre, S_post, S_uninst, declared,
                bak_bytes_pre=bak_bytes_pre, bak_bytes_post=bak_bytes_post)
    rep.update({
        "case": case_id, "inplace": inplace,
        "package": str(pkg), "package_members": declared["members"],
        "v15": {"build": r_build, "install": r_inst, "uninstall": r_uninst},
        "snapshots": {"pre": S_pre, "post": S_post, "uninst": S_uninst},
    })
    return rep


def run_negative_control(base: Path) -> dict:
    """C-NEG: inject out-of-scope writes into a synthetic post-snapshot and
    verify the audit tool reports FAIL and NAMES them (CRITERIA_SPEC §1.4 C-NEG)."""
    pre = {
        "gamemd.exe": {"size": 40, "sha256": "a" * 64, "mtime_ns": 1},
        "RA2MD.INI": {"size": 20, "sha256": "b" * 64, "mtime_ns": 1},
        "BATTLEMD.INI": {"size": 2733, "sha256": "c" * 64, "mtime_ns": 1},
    }
    declared = {"D": ["BATTLEMD.INI", "BATTLEMD.INI.ra2forge.bak",
                      "ra2forge_install.json", "ra2forge_install.json.seal"],
                "members": ["BATTLEMD.INI"], "inplace": True,
                "declared_rewrite": ["BATTLEMD.INI"],
                "bak_slots": ["BATTLEMD.INI.ra2forge.bak"],
                "engine_derived": ["ra2forge_install.json",
                                   "ra2forge_install.json.seal"]}
    # compliant post: declared rewrite + .bak + record
    post_ok = dict(pre)
    post_ok["BATTLEMD.INI"] = {"size": 2730, "sha256": "d" * 64, "mtime_ns": 2}
    post_ok["BATTLEMD.INI.ra2forge.bak"] = {"size": 2733, "sha256": "c" * 64,
                                            "mtime_ns": 2}
    post_ok["ra2forge_install.json"] = {"size": 100, "sha256": "e" * 64,
                                        "mtime_ns": 2}
    uninst_ok = dict(pre)

    ok_rep = audit(pre, post_ok, uninst_ok, declared)

    # injected out-of-scope writes: (1) new EVIL.dll  (2) rewrite gamemd.exe
    post_bad = dict(post_ok)
    post_bad["EVIL.dll"] = {"size": 10, "sha256": "f" * 64, "mtime_ns": 3}
    post_bad["gamemd.exe"] = {"size": 40, "sha256": "0" * 64, "mtime_ns": 3}
    bad_rep = audit(pre, post_bad, uninst_ok, declared)

    named = bad_rep["out_of_scope_writes"]
    detected = ("EVIL.dll" in named)
    named_protected = bad_rep.get("protected_touched", [])
    protected_detected = ("gamemd.exe" in named_protected)
    tool_pass = (ok_rep["verdict"] == "PASS"
                 and bad_rep["verdict"] == "FAIL"
                 and detected and protected_detected)
    return {
        "case": "C-NEG", "kind": "synthetic_snapshot_fixture",
        "compliant_control": {"verdict": ok_rep["verdict"],
                              "out_of_scope": ok_rep["out_of_scope_writes"],
                              "checks": ok_rep["checks"],
                              "failed_checks": ok_rep["failed_checks"],
                              "restore": ok_rep["restore"]},
        "injected_control": {"verdict": bad_rep["verdict"],
                             "out_of_scope_writes": named,
                             "protected_touched": named_protected,
                             "failed_checks": bad_rep["failed_checks"]},
        "injected_writes": ["EVIL.dll (added, undeclared)",
                            "gamemd.exe (modified, protected engine file)"],
        "expected": {"compliant": "PASS", "injected": "FAIL"},
        "tool_selftest_pass": tool_pass,
    }


# ---------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(description="W62 Criterion C offline write-audit")
    p.add_argument("--run-all", action="store_true",
                   help="run C-A (normal) + C-B (inplace) + C-NEG via v15 CLI")
    p.add_argument("--selftest", action="store_true",
                   help="C-NEG only, no v15 needed")
    p.add_argument("--audit", action="store_true", help="audit given snapshots")
    p.add_argument("--before"); p.add_argument("--after")
    p.add_argument("--uninst"); p.add_argument("--declared")
    p.add_argument("--out", help="output dir (run-all) or json (audit/selftest)")
    a = p.parse_args(argv)

    if a.audit:
        if not all((a.before, a.after, a.uninst, a.declared)):
            print("ERROR --audit needs --before --after --uninst --declared",
                  file=sys.stderr)
            return 2
        J = lambda x: json.loads(Path(x).read_text(encoding="utf-8"))
        rep = audit(J(a.before), J(a.after), J(a.uninst), J(a.declared))
        txt = json.dumps(rep, indent=2, ensure_ascii=False)
        if a.out:
            Path(a.out).write_text(txt, encoding="utf-8")
        print(txt)
        return 0 if rep["verdict"] == "PASS" else 1

    if a.selftest:
        out = Path(a.out) if a.out else Path("EVIDENCE")
        out.mkdir(parents=True, exist_ok=True)
        rep = run_negative_control(out)
        (out / "c_neg_selftest.json").write_text(
            json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0 if rep["tool_selftest_pass"] else 1

    if a.run_all:
        out = Path(a.out) if a.out else Path("EVIDENCE")
        out.mkdir(parents=True, exist_ok=True)
        sandbox = out / "sandbox"
        sandbox.mkdir(parents=True, exist_ok=True)
        log: list = []
        results = {}
        results["C-A"] = run_case("C-A", sandbox, log, inplace=False)
        results["C-B"] = run_case("C-B", sandbox, log, inplace=True)
        results["C-NEG"] = run_negative_control(sandbox)

        report = {
            "schema_version": SCHEMA_VERSION,
            "spec_frozen_at": SPEC_FROZEN_AT,
            "kind": "w62_c_write_audit",
            "discipline": "pure offline; I launched 0 / attached 0; "
                          "sandbox gamemd.exe is inert and never executed",
            "v15_root": str(V15),
            "results": results,
            "v15_cli_log": log,
        }
        (out / "c_audit.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        # per-case snapshot dumps
        for cid, r in results.items():
            if "snapshots" in r:
                for phase, snap in r["snapshots"].items():
                    (out / f"c_{cid}_{phase}_snapshot.json").write_text(
                        json.dumps(snap, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        for cid, r in results.items():
            v = r.get("verdict") if cid != "C-NEG" else (
                "PASS" if r.get("tool_selftest_pass") else "FAIL")
            extra = ""
            if cid != "C-NEG":
                extra = (f" out_of_scope={r.get('out_of_scope_writes')} "
                         f"failed={r.get('failed_checks')}")
            print(f"[{cid}] verdict={v}{extra}")
        print("C_ALL_PASS=" + str(all(
            (r.get("verdict") == "PASS") if cid != "C-NEG"
            else r.get("tool_selftest_pass") for cid, r in results.items())))
        return 0 if all(
            (r.get("verdict") == "PASS") if cid != "C-NEG"
            else r.get("tool_selftest_pass") for cid, r in results.items()) else 1

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

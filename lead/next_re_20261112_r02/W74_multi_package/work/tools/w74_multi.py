#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W74 · MULTI-PACKAGE COEXISTENCE MEASUREMENT (OFFLINE ONLY).

NO game is launched. NO lock is taken. Only this card's directory is written;
`ra2youli` is a READ-ONLY robocopy source; git is read-only.

Subcommands (each `trial*` starts with a FRESH robocopy of the real dir so the
two uninstall-order trials are independent):

  prep      - reset sandbox, robocopy, remove orphan .bak, uninstall v0.3,
              verify official baseline
  trial1    - install A -> verify -> install B (4 variants) -> snapshots ->
              uninstall#1 ("B"), uninstall#2 ("A") -> final SHA
  trial2    - same, but the two uninstall calls are labelled ("A" then "B")
  control   - install B ALONE into a fresh sandbox (proves B is a valid
              package and that any refusal in trial* is caused by A)
  realproof - real_dir PRE/POST identical_tree self-proof

Every v15 command's argv, cwd, exit code, FULL stdout/stderr is written to
out/cmd_<label>.log and to the ndjson sink. BATTLEMD.INI / manifest / .bak /
seal snapshots go to out/snap_<label>.json and out/manifest_<label>.json.

The scripts w74_lib.py / w74_common.py are COPIES of W63's helpers repointed
to THIS card (their output paths are mine). No other card's script is called.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w74_lib as L
import w74_common as C

OFFICIAL_SHA = "7e40691a3480b1e5ffe6d1cdfccb83f67da4447157607ec3ecb5d2278acf0791"
OFFICIAL_SIZE = 2733
MAPSEL_OFFICIAL_SHA = "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52"

SNAP_NAMES = (
    "BATTLEMD.INI", "BATTLEMD.INI.ra2forge.bak", "MAPSELMD.INI",
    "expandmd98.mix", "ra2forge_install.json", "ra2forge_install.json.seal",
    "BATTLEMD98.INI", "ra2md.csf",
)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sov1_scenario(p: Path):
    """Return the [SOV1] Scenario= value, or None."""
    if not p.is_file():
        return None
    raw = p.read_bytes()
    txt = raw.decode("latin-1", "replace")
    i = txt.find("[SOV1]")
    if i < 0:
        return None
    j = txt.find("[", i + 6)
    block = txt[i:j if j > 0 else len(txt)]
    for ln in block.splitlines():
        if ln.strip().startswith("Scenario="):
            return ln.strip().split("=", 1)[1]
    return None


def snapshot(sink, label: str) -> dict:
    """Read-only state snapshot of the sandbox for manifest/backup/sha facts."""
    g = C.GAME
    rep = {"label": label, "game_dir": str(g)}
    files = {}
    for n in SNAP_NAMES:
        p = g / n
        if p.is_file():
            b = p.read_bytes()
            files[n] = {"present": True, "size": len(b), "sha256": sha(b)}
        else:
            files[n] = {"present": False, "size": None, "sha256": None}
    rep["files"] = files
    rep["battlemd"] = {
        "sha256": files["BATTLEMD.INI"]["sha256"],
        "size": files["BATTLEMD.INI"]["size"],
        "equals_official": (files["BATTLEMD.INI"]["sha256"] == OFFICIAL_SHA),
        "sov1_scenario": sov1_scenario(g / "BATTLEMD.INI"),
    }
    rep["bak"] = {
        "present": files["BATTLEMD.INI.ra2forge.bak"]["present"],
        "sha256": files["BATTLEMD.INI.ra2forge.bak"]["sha256"],
        "equals_official": (files["BATTLEMD.INI.ra2forge.bak"]["sha256"]
                            == OFFICIAL_SHA),
    }
    # manifest raw + parsed
    mp = g / "ra2forge_install.json"
    if mp.is_file():
        raw = mp.read_bytes()
        rep["manifest_raw_sha256"] = sha(raw)
        rep["manifest_raw_size"] = len(raw)
        try:
            man = json.loads(raw.decode("utf-8-sig"))
        except Exception as e:  # noqa: BLE001
            man = {"__parse_error__": repr(e)}
        rep["manifest"] = man
        rep["manifest_package_id"] = man.get("package_id") if isinstance(man, dict) else None
        rep["manifest_package_version"] = man.get("package_version") if isinstance(man, dict) else None
        rep["manifest_version"] = man.get("version") if isinstance(man, dict) else None
        rep["manifest_feature_set_id"] = man.get("feature_set_id") if isinstance(man, dict) else None
        entries = [e for e in (man.get("files") or []) if isinstance(e, dict)
                   and e.get("name") == "BATTLEMD.INI"] if isinstance(man, dict) else []
        rep["manifest_battlemd_entries"] = entries
        rep["original_sha256_recorded"] = (entries[0].get("original_sha256")
                                           if entries else None)
        rep["post_install_sha256_recorded"] = (entries[0].get("post_install_sha256")
                                               if entries else None)
        rep["inplace_rewrite_block"] = man.get("inplace_rewrite") if isinstance(man, dict) else None
        # archive a full copy for before/after diffing
        (C.OUT / ("manifest_%s.json" % label)).write_bytes(raw)
    else:
        rep["manifest_raw_sha256"] = None
        rep["manifest"] = None
        rep["manifest_package_id"] = None
        (C.OUT / ("manifest_%s.json" % label)).write_text("<ABSENT>\n", encoding="utf-8")
    # seal
    sp = g / "ra2forge_install.json.seal"
    rep["seal"] = json.loads(sp.read_text(encoding="utf-8-sig")) if sp.is_file() else None
    # loose RA2F maps / RA2F bak files
    rep["ra2f_maps"] = sorted(p.name for p in g.glob("RA2F_*.MAP") if p.is_file())
    rep["ra2forge_baks"] = sorted(p.name for p in g.glob("*.ra2forge.bak") if p.is_file())
    # MAPSELMD / mix identity
    rep["mapsel_is_official"] = (files["MAPSELMD.INI"]["sha256"] == MAPSEL_OFFICIAL_SHA)
    sink.step("snapshot", **rep)
    (C.OUT / ("snap_%s.json" % label)).write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rep


def v15(sink, label, args, timeout=420) -> dict:
    rec = C.v15_cmd(sink, label, args, timeout=timeout)
    sink.step("v15_result", label=label, exit_code=rec["exit_code"],
              stdout=rec.get("stdout_tail", ""), stderr=rec.get("stderr_tail", ""))
    return rec


def prep(sink, tag: str) -> dict:
    """Fresh sandbox from the real dir (READ-ONLY source), W63-proven prep."""
    rep = {"phase": "prep", "tag": tag}
    if C.GAME.exists():
        shutil.rmtree(C.GAME)
        rep["removed_old_sandbox"] = True
    C.GAME.mkdir(parents=True, exist_ok=True)

    argv = ["robocopy", str(C.REAL), str(C.GAME),
            "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1",
            "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
    rc_rec = C.run_cmd(sink, "%s_robocopy_sandbox" % tag, argv, timeout=900)
    rc = rc_rec["exit_code"]
    rep["robocopy_rc"] = rc
    if not (0 <= rc <= 7):
        raise RuntimeError("robocopy failed rc=%s (0..7 is success)" % rc)

    sp = C.write_manifest(C.OUT / ("%s_sandbox_pre.json" % tag), C.GAME)
    rep["sandbox_pre_summary"] = sp["summary"]
    C.save_pristine(sink)

    vpre = v15(sink, "%s_verify_pre" % tag,
               ["verify", "--game", str(C.GAME), "--json"])
    rep["verify_pre_exit"] = vpre["exit_code"]

    u = v15(sink, "%s_uninstall_v03" % tag,
            ["uninstall", "--game", str(C.GAME), "--json"])
    rep["uninstall_v03_exit"] = u["exit_code"]
    rep["uninstall_v03_stdout"] = u.get("stdout_tail", "")
    if u["exit_code"] != 0:
        raise RuntimeError("v0.3 uninstall exit %s" % u["exit_code"])

    vau = v15(sink, "%s_verify_after_v03" % tag,
              ["verify", "--game", str(C.GAME), "--json"])
    rep["verify_after_v03_exit"] = vau["exit_code"]

    # W63 §7b: remove the UNOWNED orphan .bak from the SANDBOX COPY ONLY.
    orphan = C.GAME / "BATTLEMD.INI.ra2forge.bak"
    oi = {"present_before": orphan.is_file(),
          "sha256": L.sha256_file(orphan) if orphan.is_file() else None,
          "size": orphan.stat().st_size if orphan.is_file() else None}
    if orphan.is_file():
        orphan.unlink()
    oi["removed_from_sandbox_only"] = not orphan.exists()
    rep["orphan_bak_prep"] = oi
    sink.step("orphan_bak_prep", **oi)

    cur = (C.GAME / "BATTLEMD.INI").read_bytes()
    rep["official_precheck"] = {
        "size": len(cur), "sha256": sha(cur),
        "expected_sha256": OFFICIAL_SHA,
        "official_match": sha(cur) == OFFICIAL_SHA and len(cur) == OFFICIAL_SIZE}
    if not rep["official_precheck"]["official_match"]:
        raise RuntimeError("BATTLEMD.INI in sandbox != official baseline: %r"
                           % rep["official_precheck"])
    snap = snapshot(sink, "%s_pre_official" % tag)
    rep["pre_snapshot_label"] = snap["label"]
    sink.step("prep_done", **rep)
    (C.OUT / ("PREP_%s.json" % tag)).write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rep


INSTALL_A_ARGS = None  # built in trial()


def install_a(sink, tag) -> dict:
    args = ["install", "--package", str(C.PKG_A), "--game", str(C.GAME),
            "--feature-set", str(C.FEATURE_SET_A)]
    r = v15(sink, "%s_install_A" % tag, args)
    return {"exit_code": r["exit_code"], "stdout": r.get("stdout_tail", ""),
            "stderr": r.get("stderr_tail", ""), "argv": args}


def install_b(sink, tag, variant_suffix, extra) -> dict:
    args = ["install", "--package", str(C.PKG_B), "--game", str(C.GAME),
            "--feature-set", str(C.FEATURE_SET_B)] + list(extra)
    r = v15(sink, "%s_install_B%s" % (tag, variant_suffix), args)
    return {"variant": variant_suffix or "plain", "extra_args": list(extra),
            "exit_code": r["exit_code"], "stdout": r.get("stdout_tail", ""),
            "stderr": r.get("stderr_tail", ""), "argv": args,
            "log": r.get("log")}


def uninstall(sink, tag, label) -> dict:
    args = ["uninstall", "--game", str(C.GAME), "--json"]
    r = v15(sink, "%s_uninstall_%s" % (tag, label), args)
    return {"label": label, "exit_code": r["exit_code"],
            "stdout": r.get("stdout_tail", ""), "stderr": r.get("stderr_tail", ""),
            "argv": args, "log": r.get("log")}


def verify(sink, tag, label) -> dict:
    r = v15(sink, "%s_verify_%s" % (tag, label),
            ["verify", "--game", str(C.GAME), "--json"])
    return {"label": label, "exit_code": r["exit_code"],
            "stdout": r.get("stdout_tail", ""), "stderr": r.get("stderr_tail", "")}


def trial(sink, tag: str, uninstall_order_first: str) -> dict:
    """One full A->B->uninstall->uninstall cycle in a FRESH sandbox."""
    rep = {"trial": tag, "uninstall_call_1_label": uninstall_order_first,
           "note": ("v15 uninstall takes NO package argument; it acts on the "
                    "single global ra2forge_install.json. The two 'orders' are "
                    "therefore the same two CLI calls, distinguished only by "
                    "which conceptual package the caller meant.")}
    prep_rep = prep(sink, tag)
    rep["prep"] = {"robocopy_rc": prep_rep["robocopy_rc"],
                   "uninstall_v03_exit": prep_rep["uninstall_v03_exit"],
                   "official_precheck": prep_rep["official_precheck"]}

    # ---- Q1: install A, verify ----
    ia = install_a(sink, tag)
    rep["install_A"] = ia
    if ia["exit_code"] != 0:
        raise RuntimeError("install A exit %s (expected 0)" % ia["exit_code"])
    va = verify(sink, tag, "after_A")
    rep["verify_after_A"] = va
    snap_a = snapshot(sink, "%s_after_A" % tag)
    rep["snap_after_A_label"] = snap_a["label"]
    rep["state_after_A"] = {
        "battlemd_sha256": snap_a["battlemd"]["sha256"],
        "battlemd_equals_official": snap_a["battlemd"]["equals_official"],
        "sov1_scenario": snap_a["battlemd"]["sov1_scenario"],
        "manifest_package_id": snap_a["manifest_package_id"],
        "manifest_package_version": snap_a["manifest_package_version"],
        "original_sha256_recorded": snap_a["original_sha256_recorded"],
        "original_sha256_is_official": (snap_a["original_sha256_recorded"]
                                        == OFFICIAL_SHA),
        "bak_present": snap_a["bak"]["present"],
        "bak_equals_official": snap_a["bak"]["equals_official"],
        "seal_present": snap_a["files"]["ra2forge_install.json.seal"]["present"],
    }

    # ---- Q1: install B (4 variants; all should be refused, zero-write) ----
    variants = [
        ("", []),
        ("_allow", ["--allow-content-conflict"]),
        ("_adopt", ["--adopt-legacy"]),
        ("_force", ["--force"]),
    ]
    bs = []
    for suf, extra in variants:
        b = install_b(sink, tag, suf, extra)
        s = snapshot(sink, "%s_after_B%s" % (tag, suf))
        b["state_after"] = {
            "battlemd_sha256": s["battlemd"]["sha256"],
            "battlemd_equals_official": s["battlemd"]["equals_official"],
            "sov1_scenario": s["battlemd"]["sov1_scenario"],
            "manifest_package_id": s["manifest_package_id"],
            "original_sha256_recorded": s["original_sha256_recorded"],
            "bak_present": s["bak"]["present"],
            "bak_equals_official": s["bak"]["equals_official"],
            "seal_present": s["files"]["ra2forge_install.json.seal"]["present"],
            "ra2f_maps": s["ra2f_maps"],
            "manifest_raw_sha256": s["manifest_raw_sha256"],
        }
        b["byte_identical_to_after_A"] = (s["manifest_raw_sha256"]
                                          == snap_a["manifest_raw_sha256"])
        bs.append(b)
    rep["install_B_variants"] = bs

    vb = verify(sink, tag, "after_B")
    rep["verify_after_B"] = vb
    snap_ab = snapshot(sink, "%s_after_B_final" % tag)
    # Q2 facts, measured after the SECOND install attempt
    rep["Q2_after_second_install"] = {
        "manifest_raw_sha256": snap_ab["manifest_raw_sha256"],
        "manifest_package_id": snap_ab["manifest_package_id"],
        "manifest_package_version": snap_ab["manifest_package_version"],
        "manifest_version": snap_ab["manifest_version"],
        "manifest_file_entries": [e.get("name") for e in
                                  (snap_ab["manifest"] or {}).get("files", [])],
        "original_sha256_recorded": snap_ab["original_sha256_recorded"],
        "original_sha256_is_official": (snap_ab["original_sha256_recorded"]
                                        == OFFICIAL_SHA),
        "bak_present": snap_ab["bak"]["present"],
        "bak_sha256": snap_ab["bak"]["sha256"],
        "bak_equals_official": snap_ab["bak"]["equals_official"],
        "battlemd_sha256": snap_ab["battlemd"]["sha256"],
        "battlemd_equals_official": snap_ab["battlemd"]["equals_official"],
        "sov1_scenario": snap_ab["battlemd"]["sov1_scenario"],
        "manifest_unchanged_vs_after_A": (snap_ab["manifest_raw_sha256"]
                                          == snap_a["manifest_raw_sha256"]),
        "battlemd_unchanged_vs_after_A": (snap_ab["battlemd"]["sha256"]
                                          == snap_a["battlemd"]["sha256"]),
    }

    # ---- Q3: two uninstall calls (labelled per the requested order) ----
    first = uninstall(sink, tag, "call1_" + uninstall_order_first)
    snap_u1 = snapshot(sink, "%s_after_uninstall_call1" % tag)
    first["state_after"] = {
        "battlemd_sha256": snap_u1["battlemd"]["sha256"],
        "battlemd_equals_official": snap_u1["battlemd"]["equals_official"],
        "sov1_scenario": snap_u1["battlemd"]["sov1_scenario"],
        "manifest_present": snap_u1["files"]["ra2forge_install.json"]["present"],
        "bak_present": snap_u1["bak"]["present"],
        "ra2f_maps": snap_u1["ra2f_maps"],
        "ra2forge_baks": snap_u1["ra2forge_baks"],
    }
    second_label = "B" if uninstall_order_first == "A" else "A"
    second = uninstall(sink, tag, "call2_" + second_label)
    snap_u2 = snapshot(sink, "%s_after_uninstall_call2" % tag)
    second["state_after"] = {
        "battlemd_sha256": snap_u2["battlemd"]["sha256"],
        "battlemd_equals_official": snap_u2["battlemd"]["equals_official"],
        "sov1_scenario": snap_u2["battlemd"]["sov1_scenario"],
        "manifest_present": snap_u2["files"]["ra2forge_install.json"]["present"],
        "bak_present": snap_u2["bak"]["present"],
        "ra2f_maps": snap_u2["ra2f_maps"],
        "ra2forge_baks": snap_u2["ra2forge_baks"],
    }
    rep["uninstall_calls"] = [first, second]
    vf = verify(sink, tag, "final")
    rep["verify_final"] = vf
    rep["Q3_final"] = {
        "battlemd_sha256": snap_u2["battlemd"]["sha256"],
        "battlemd_size": snap_u2["battlemd"]["size"],
        "equals_official": snap_u2["battlemd"]["equals_official"],
        "expected_sha256": OFFICIAL_SHA,
        "manifest_present": snap_u2["files"]["ra2forge_install.json"]["present"],
        "seal_present": snap_u2["files"]["ra2forge_install.json.seal"]["present"],
        "bak_present": snap_u2["bak"]["present"],
        "ra2f_maps": snap_u2["ra2f_maps"],
        "ra2forge_baks": snap_u2["ra2forge_baks"],
    }
    sink.step("trial_done", **rep)
    (C.OUT / ("TRIAL_%s.json" % tag)).write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rep


def control(sink) -> dict:
    """Install B ALONE into a fresh sandbox: proves B is a valid package."""
    tag = "control"
    rep = {"trial": tag, "purpose": "B alone, no A present"}
    pr = prep(sink, tag)
    rep["prep_official_precheck"] = pr["official_precheck"]
    args = ["install", "--package", str(C.PKG_B), "--game", str(C.GAME),
            "--feature-set", str(C.FEATURE_SET_B)]
    r = v15(sink, "%s_install_B_alone" % tag, args)
    rep["install_B_alone"] = {"exit_code": r["exit_code"],
                              "stdout": r.get("stdout_tail", ""),
                              "stderr": r.get("stderr_tail", ""), "argv": args}
    v = verify(sink, tag, "after_B_alone")
    rep["verify_after_B_alone"] = v
    s = snapshot(sink, "%s_after_B_alone" % tag)
    rep["state_after_B_alone"] = {
        "battlemd_sha256": s["battlemd"]["sha256"],
        "sov1_scenario": s["battlemd"]["sov1_scenario"],
        "manifest_package_id": s["manifest_package_id"],
        "original_sha256_recorded": s["original_sha256_recorded"],
        "bak_present": s["bak"]["present"],
        "bak_equals_official": s["bak"]["equals_official"],
        "ra2f_maps": s["ra2f_maps"],
    }
    u = uninstall(sink, tag, "B_alone")
    s2 = snapshot(sink, "%s_after_uninstall_B_alone" % tag)
    rep["uninstall_B_alone"] = {"exit_code": u["exit_code"],
                                 "stdout": u.get("stdout_tail", "")}
    rep["final_equals_official"] = s2["battlemd"]["equals_official"]
    rep["final_battlemd_sha256"] = s2["battlemd"]["sha256"]
    sink.step("control_done", **rep)
    (C.OUT / "TRIAL_control.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rep


def realproof(sink) -> dict:
    pre = C.write_manifest(C.OUT / "real_pre.json", C.REAL)
    rep = {"real_pre_summary": pre["summary"], "payload": pre}
    (C.OUT / "REAL_PRE_SHA.json").write_text(
        json.dumps(pre["summary"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    return rep


def realproof_post(sink, pre_payload) -> dict:
    post = C.write_manifest(C.OUT / "real_post.json", C.REAL)
    d = C.diff_manifests(pre_payload, post)
    rep = {
        "real_pre_summary": pre_payload["summary"],
        "real_post_summary": post["summary"],
        "diff": {"added": d["added"], "removed": d["removed"],
                 "changed": d["changed"], "mtime_diff": d["mtime_diff"],
                 "identical_tree": d["identical_tree"]},
        "IDENTICAL_TREE": d["identical_tree"],
        "note": ("full 647-file byte-level SHA comparison of ra2youli before "
                 "and after this offline card; proves no write to ra2youli"),
    }
    (C.OUT / "REAL_DIR_PROOF.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sink.step("real_dir_proof", **rep)
    return rep


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    sink = L.Sink("w74_" + cmd)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=cmd,
                  note="W74 OFFLINE multi-package coexistence measurement; "
                       "NO lock, NO gamemd.exe launched, ra2youli read-only",
                  official_sha256=OFFICIAL_SHA,
                  pkg_a=str(C.PKG_A), pkg_b=str(C.PKG_B), v15=str(C.V15))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual,
                  n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline phase: %r" % residual)

        pre_payload = None
        if cmd in ("all", "realproof"):
            pre_payload = realproof(sink)["payload"]

        results = {}
        if cmd in ("all", "control"):
            results["control"] = control(sink)
        if cmd in ("all", "trial1"):
            results["trial1"] = trial(sink, "t1", "B")   # "uninstall B, then A"
        if cmd in ("all", "trial2"):
            results["trial2"] = trial(sink, "t2", "A")   # "uninstall A, then B"
        if cmd == "prep":
            results["prep"] = prep(sink, "standalone")

        if pre_payload is not None:
            results["realproof"] = realproof_post(sink, pre_payload)

        (C.OUT / ("RESULT_%s.json" % cmd)).write_text(
            json.dumps(results, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        ok = True
        sink.step("w74_result", ok=True, results=results)
    except Exception as e:  # noqa: BLE001
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-8000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=cmd, ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

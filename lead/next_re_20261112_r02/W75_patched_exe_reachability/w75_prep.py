#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W75 · OFFLINE PREP (before any real-machine launch).
  1. Verify SHAs: real gamemd.exe, W61 patched gamemd_v14r.exe, lengths.
  2. robocopy READ-ONLY real dir -> this card's sandbox_game.
  3. Copy W61 patched exe into THIS card (own working copy; W61 product untouched).
  4. Keep a pristine byte copy of the ORIGINAL exe for trip B / final restore.
  5. Byte-copy + sha256 baseline of writable configs into out/pristine/.
  6. Full 647-file inventory of REAL (real_pre.json) and SANDBOX (sandbox_pre.json).
Writes ONLY inside W75_patched_exe_reachability. NEVER writes ra2youli."""
from __future__ import annotations
import json, shutil, subprocess, sys
from pathlib import Path
import w75_lib as L

OUT = L.OUT
OUT.mkdir(parents=True, exist_ok=True)
S = L.Sink("prep")
report = {"phase": "offline_prep", "ok": False}


def fail(msg):
    S.step("PREP_FAIL", error=msg)
    print("PREP_FAIL: " + msg, file=sys.stderr, flush=True)
    raise RuntimeError(msg)


def main():
    # ---- 0. hard guard: real dir must be the read-only source ----------
    real_exe = L.REAL / "gamemd.exe"
    patch_src = L.W61_PATCHED
    if not real_exe.is_file():
        fail("real gamemd.exe missing: %s" % real_exe)
    if not patch_src.is_file():
        fail("W61 patched exe missing: %s" % patch_src)

    # ---- 1. offline SHA verification -----------------------------------
    real_len = real_exe.stat().st_size
    real_sha = L.sha256_file(real_exe)
    patch_len = patch_src.stat().st_size
    patch_sha = L.sha256_file(patch_src)
    chk = {
        "real_exe": str(real_exe),
        "real_len": real_len, "real_sha256": real_sha,
        "real_len_ok": real_len == L.EXPECTED["gamemd_len"],
        "real_sha_ok": real_sha == L.EXPECTED["real_gamemd_sha"],
        "patch_src": str(patch_src),
        "patch_len": patch_len, "patch_sha256": patch_sha,
        "patch_len_ok": patch_len == L.EXPECTED["gamemd_len"],
        "patch_sha_ok": patch_sha == L.EXPECTED["patch_gamemd_sha"],
        "equal_len_to_original": real_len == patch_len,
    }
    S.step("sha_verify", **chk)
    report["sha_verify"] = chk
    if not (chk["real_len_ok"] and chk["real_sha_ok"]
            and chk["patch_len_ok"] and chk["patch_sha_ok"]
            and chk["equal_len_to_original"]):
        fail("SHA / length mismatch -- refusing to touch real machine")
    print("SHA VERIFY PASS: real=73201cc0...  patch=b9021544...  len=%d" % real_len,
          flush=True)

    # ---- 2. real dir PRE inventory (before robocopy) --------------------
    real_pre = L.inventory_tree(L.REAL)
    (OUT / "real_pre.json").write_text(
        json.dumps(real_pre, ensure_ascii=False, indent=1), encoding="utf-8")
    S.step("real_pre_inventory", file_count=real_pre["file_count"],
           total_bytes=real_pre["total_bytes"])
    report["real_pre"] = {"file_count": real_pre["file_count"],
                          "total_bytes": real_pre["total_bytes"]}
    if (real_pre["file_count"] != L.EXPECTED["real_file_count"]
            or real_pre["total_bytes"] != L.EXPECTED["real_total_bytes"]):
        fail("real dir baseline count/bytes mismatch: %d / %d"
             % (real_pre["file_count"], real_pre["total_bytes"]))

    # ---- 3. robocopy READ-ONLY source -> sandbox ------------------------
    if L.GAME.exists():
        fail("sandbox_game already exists -- refusing to overwrite blindly")
    cmd = ["robocopy", str(L.REAL), str(L.GAME),
           "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1", "/NFL", "/NDL",
           "/NP"]
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900)
    log = "COMMAND: %s\nEXIT: %d\nSTDOUT:\n%s\nSTDERR:\n%s\n" % (
        " ".join(cmd), r.returncode, r.stdout, r.stderr)
    (OUT / "cmd_robocopy_sandbox.log").write_text(log, encoding="utf-8")
    S.step("robocopy", rc=r.returncode,
           stdout_tail=(r.stdout or "")[-900:], stderr_tail=(r.stderr or "")[-400:])
    # robocopy rc 0..7 are success codes; >=8 is failure
    if r.returncode >= 8:
        fail("robocopy failed rc=%d" % r.returncode)
    report["robocopy_rc"] = r.returncode

    sandbox_pre = L.inventory_tree(L.GAME)
    (OUT / "sandbox_pre.json").write_text(
        json.dumps(sandbox_pre, ensure_ascii=False, indent=1), encoding="utf-8")
    d = L.diff_trees(real_pre, sandbox_pre, compare_mtime=False)
    S.step("sandbox_pre_vs_real", **{k: d[k] for k in
           ("added", "removed", "changed", "identical_tree")})
    report["sandbox_pre"] = {"file_count": sandbox_pre["file_count"],
                             "total_bytes": sandbox_pre["total_bytes"],
                             "identical_to_real": d["identical_tree"]}
    if not d["identical_tree"]:
        fail("sandbox tree differs from real after robocopy")
    print("ROBOCOPY PASS: %d files / %d B, identical to real"
          % (sandbox_pre["file_count"], sandbox_pre["total_bytes"]), flush=True)

    # ---- 4. own working copies of the two exes --------------------------
    own_patch = OUT / "gamemd_patched.exe"        # W61 product COPY (untouched)
    pristine_exe = OUT / "pristine_gamemd.exe"    # ORIGINAL byte copy
    shutil.copyfile(patch_src, own_patch)
    shutil.copyfile(real_exe, pristine_exe)
    own_patch_sha = L.sha256_file(own_patch)
    pristine_sha = L.sha256_file(pristine_exe)
    S.step("own_exe_copies",
           patched_copy=str(own_patch), patched_copy_sha=own_patch_sha,
           pristine_copy=str(pristine_exe), pristine_copy_sha=pristine_sha,
           patched_copy_matches_W61=own_patch_sha == patch_sha,
           pristine_copy_matches_real=pristine_sha == real_sha,
           W61_source_unmodified=L.sha256_file(patch_src) == patch_sha)
    if own_patch_sha != patch_sha or pristine_sha != real_sha:
        fail("own exe copies failed sha check")
    report["own_exe_copies"] = {"patched_sha": own_patch_sha,
                                "pristine_sha": pristine_sha}

    # ---- 5. writable config byte copies + sha256 baseline ---------------
    (OUT / "pristine").mkdir(parents=True, exist_ok=True)
    cfg_rows = []
    for n in L.CONFIG_FILES:
        src = L.GAME / n
        if src.is_file():
            dst = OUT / "pristine" / n
            shutil.copyfile(src, dst)
            cfg_rows.append({"file": n, "size": src.stat().st_size,
                             "sha256": L.sha256_file(src),
                             "copy_sha256": L.sha256_file(dst),
                             "byte_identical": L.sha256_file(src) == L.sha256_file(dst),
                             "baseline": "present"})
        else:
            cfg_rows.append({"file": n, "baseline": "absent"})
    (OUT / "config_baseline.json").write_text(
        json.dumps({"configs": cfg_rows}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    S.step("config_baseline", n_present=sum(1 for r in cfg_rows
           if r["baseline"] == "present"),
           n_absent=sum(1 for r in cfg_rows if r["baseline"] == "absent"),
           all_byte_identical=all(r.get("byte_identical", True)
                                  for r in cfg_rows))
    report["config_baseline"] = {"n_present": sum(1 for r in cfg_rows
                                 if r["baseline"] == "present"),
                                 "n_absent": sum(1 for r in cfg_rows
                                 if r["baseline"] == "absent")}

    # ---- 6. baseline file that the game may append to -------------------
    extra = {}
    for n in ("except.txt", "ra2render.log"):
        p = L.GAME / n
        extra[n] = {"size": p.stat().st_size if p.is_file() else None,
                    "sha256": L.sha256_file(p) if p.is_file() else None}
    (OUT / "log_baseline.json").write_text(json.dumps(extra, indent=1),
                                            encoding="utf-8")
    S.step("log_baseline", **extra)

    # ---- 7. lock state at prep time (read only) -------------------------
    S.step("lock_state_at_prep", lock=L.lock_read(),
           gamemd_processes=L.list_gamemd())

    report["ok"] = True
    S.step("PREP_OK")
    (OUT / "PREP.json").write_text(json.dumps(report, ensure_ascii=False,
                                               indent=1), encoding="utf-8")
    print("PREP OK", flush=True)


if __name__ == "__main__":
    main()

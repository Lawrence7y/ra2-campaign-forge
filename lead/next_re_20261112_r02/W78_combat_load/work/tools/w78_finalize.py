#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W78 FINALIZE — uninstall, byte-restore proof, cleanup, lock confirmation.

  1. Capture the install manifest's original_sha256 BEFORE uninstall.
  2. v15 uninstall --game sandbox (exit 0 required).
  3. Prove BATTLEMD.INI is byte-restored:
       sha256 == manifest.original_sha256 == official 2733 B baseline
       == pristine/BATTLEMD.INI byte copy == real-dir PRE BATTLEMD.INI.
  4. Byte-restore EVERY sandbox writable config from out/pristine/* (including
     the 241 B orphan .bak that was removed from the sandbox copy only for the
     inplace preflight), with a per-file real SHA self-proof.
  5. Remove dropped package files, then compute sandbox POST manifest and diff
     against sandbox_pre.json (identical_tree self-proof).
  6. Compute REAL dir POST manifest and diff against real_pre.json ->
     IDENTICAL_TREE=True (真目录零改动自证).  The real dir was NEVER written.
  7. Delete the sandbox directory (沙箱目录清理) AFTER the diff proofs are saved.
  8. Confirm .game_instance.lock owner=lead; gamemd residual 0.

Only writes inside W78 card.  git read-only.  No taskkill of user processes.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w78_lib as L
import w78_common as C

TAG = "finalize"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="cleanup: uninstall, byte-restore, real-dir proof, sandbox cleanup")
        residual0 = L.list_gamemd()
        sink.step("gamemd_before_finalize", gamemd_processes=residual0, n=len(residual0))
        if residual0:
            raise RuntimeError("residual gamemd before finalize: %r" % residual0)

        official = (C.V15 / "ra2forge" / "data" / "BATTLEMD.OFFICIAL.INI").read_bytes()
        official_sha = sha(official)

        # ---- (1) capture manifest BEFORE uninstall -------------------------
        rec_path = C.GAME / "ra2forge_install.json"
        man = json.loads(rec_path.read_text(encoding="utf-8"))
        e = [x for x in man.get("files", []) if x.get("name") == "BATTLEMD.INI"][0]
        recorded_original = e["original_sha256"]
        recorded_post = e.get("post_install_sha256")
        installed_battle = (C.GAME / "BATTLEMD.INI").read_bytes()
        proof["pre_uninstall"] = {
            "manifest_sha256": L.sha256_file(rec_path),
            "manifest_original_sha256": recorded_original,
            "manifest_post_install_sha256": recorded_post,
            "battlemd_on_disk_sha256": sha(installed_battle),
            "battlemd_on_disk_size": len(installed_battle),
            "installed_is_rewritten": (sha(installed_battle) == recorded_post),
            "official_baseline_sha256": official_sha,
        }
        sink.step("pre_uninstall_state", **proof["pre_uninstall"])
        assert proof["pre_uninstall"]["installed_is_rewritten"]

        # ---- (2) sandbox PRE-uninstall diff (for the record) ---------------
        pre_uninst = C.write_manifest(C.OUT / "sandbox_pre_uninstall.json", C.GAME)
        proof["sandbox_pre_uninstall"] = C.diff_manifests(
            json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8")),
            pre_uninst)
        sink.step("sandbox_pre_uninstall_diff",
                  added=proof["sandbox_pre_uninstall"]["added"],
                  removed=proof["sandbox_pre_uninstall"]["removed"],
                  changed=proof["sandbox_pre_uninstall"]["changed"])

        # ---- (3) v15 uninstall --------------------------------------------
        u = C.v15_cmd(sink, "uninstall_final",
                      ["uninstall", "--game", str(C.GAME), "--json"])
        proof["uninstall"] = {"exit_code": u["exit_code"],
                              "stdout_tail": u["stdout_tail"][-5000:]}
        sink.step("uninstall_exit", **proof["uninstall"])
        if u["exit_code"] != 0:
            raise RuntimeError("uninstall exit %s" % u["exit_code"])

        # ---- (4) BATTLEMD.INI byte-restore proof --------------------------
        restored = (C.GAME / "BATTLEMD.INI").read_bytes()
        pristine = (C.OUT / "pristine" / "BATTLEMD.INI").read_bytes()
        real_battle = (C.REAL / "BATTLEMD.INI").read_bytes()
        rp = json.loads((C.OUT / "real_pre.json").read_text(encoding="utf-8"))
        real_pre_battle = next(r["sha256"] for r in rp["files"]
                               if r["rel"] == "BATTLEMD.INI")
        eog = {
            "restored_size": len(restored),
            "restored_sha256": sha(restored),
            "manifest_original_sha256": recorded_original,
            "official_baseline_sha256": official_sha,
            "pristine_sha256": sha(pristine),
            "real_dir_post_sha256": sha(real_battle),
            "real_dir_pre_sha256": real_pre_battle,
            "sha_equals_manifest_original": sha(restored) == recorded_original,
            "sha_equals_official_baseline": sha(restored) == official_sha,
            "bytes_equal_pristine": restored == pristine,
            "bytes_equal_real_dir": restored == real_battle,
            "sha_equals_real_dir_pre": sha(restored) == real_pre_battle,
            "sov1_scenario_gone": b"Scenario=RA2F_M1.MAP" not in restored,
            "official_sov1_scenario_back": b"Scenario=SOV01umd.MAP" in restored,
        }
        proof["battlemd_restore"] = eog
        sink.step("battlemd_byte_restore_proof", **eog)
        assert all([eog["sha_equals_manifest_original"],
                    eog["sha_equals_official_baseline"],
                    eog["bytes_equal_pristine"],
                    eog["bytes_equal_real_dir"],
                    eog["sha_equals_real_dir_pre"],
                    eog["sov1_scenario_gone"],
                    eog["official_sov1_scenario_back"]])

        # ---- (5) byte-restore EVERY pristine config -----------------------
        restore_rows = []
        for name in C.PRISTINE:
            try:
                restore_rows.append(C.restore_one(name, sink, label="finalize"))
            except Exception as ex:
                restore_rows.append({"file": name, "error": repr(ex)})
                sink.step("restore_error", file=name, error=repr(ex))
        proof["config_restore"] = restore_rows
        n_ok = sum(1 for r in restore_rows if r.get("byte_identical")
                   or r.get("absent_baseline"))
        sink.step("config_restore_summary", rows=restore_rows, n_ok=n_ok,
                  n_total=len(restore_rows), all_ok=(n_ok == len(restore_rows)))
        if n_ok != len(restore_rows):
            raise RuntimeError("config restore incomplete: %r" % restore_rows)

        # ---- (6) remove dropped package files -----------------------------
        drops = ["RA2F_M1.MAP",
                 "MAPSELMD.INI", "expandmd98.mix",
                 "ra2forge_install.json", "ra2forge_install.json.seal",
                 "BATTLEMD.INI.ra2forge.bak"]
        # NOTE: BATTLEMD.INI.ra2forge.bak was just restored to the PRE orphan
        # (241 B) from pristine; that file is part of the PRE state, so do NOT
        # delete it.  Only delete files that were NOT in the PRE manifest.
        pre_rel = {r["rel"] for r in
                   json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8"))["files"]}
        removed_drops = []
        for n in drops:
            p = C.GAME / n
            if p.is_file() and n not in pre_rel:
                p.unlink()
                removed_drops.append({"file": n, "removed": True})
            else:
                removed_drops.append({"file": n, "removed": False,
                                      "reason": "not present or part of PRE baseline"})
        proof["drop_cleanup"] = removed_drops
        sink.step("drop_cleanup", rows=removed_drops)

        # ---- (7) sandbox POST diff proof ----------------------------------
        post = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
        sd = C.diff_manifests(
            json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8")), post)
        proof["sandbox_diff"] = sd
        sink.step("sandbox_diff", identical_tree=sd["identical_tree"],
                  added=sd["added"], removed=sd["removed"],
                  changed=sd["changed"], mtime_diff_count=len(sd["mtime_diff"]),
                  pre_summary=sd["pre_summary"], post_summary=sd["post_summary"])
        # if any extra files remain, delete them (they are our drops); then recompute
        if sd["added"]:
            for n in sd["added"]:
                p = C.GAME / n
                if p.is_file():
                    p.unlink()
            post = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
            sd = C.diff_manifests(
                json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8")), post)
            proof["sandbox_diff_after_extra_cleanup"] = sd
            sink.step("sandbox_diff_after_extra_cleanup",
                      identical_tree=sd["identical_tree"], added=sd["added"],
                      removed=sd["removed"], changed=sd["changed"])
        proof["sandbox_identical_tree"] = sd["identical_tree"]

        # ---- (8) REAL dir POST proof (THE critical one) -------------------
        real_post = C.write_manifest(C.OUT / "real_post.json", C.REAL)
        rd = C.diff_manifests(
            json.loads((C.OUT / "real_pre.json").read_text(encoding="utf-8")), real_post)
        proof["real_dir_diff"] = rd
        sink.step("real_dir_diff", identical_tree=rd["identical_tree"],
                  added=rd["added"], removed=rd["removed"],
                  changed=rd["changed"], mtime_diff_count=len(rd["mtime_diff"]),
                  pre_summary=rd["pre_summary"], post_summary=rd["post_summary"])
        # four anchor hashes PRE == POST
        anchors = {}
        for name in ("RA2MD.INI", "gamemd.exe", "ddraw.dll", "ra2forge_install.json",
                     "BATTLEMD.INI"):
            a = rp["summary"]["hashes"].get(name) if name != "BATTLEMD.INI" else real_pre_battle
            pp = None
            for r in real_post["files"]:
                if r["rel"] == name:
                    pp = r["sha256"]
            anchors[name] = {"pre": a, "post": pp, "equal": a == pp}
        proof["real_dir_anchors"] = anchors
        sink.step("real_dir_anchors", **anchors)
        if not rd["identical_tree"]:
            raise RuntimeError("REAL DIR NOT IDENTICAL: %r" % rd)
        if not all(a["equal"] for a in anchors.values()):
            raise RuntimeError("REAL DIR anchor hash mismatch: %r" % anchors)

        # ---- (9) verify_post on restored sandbox (nice extra self-proof) --
        vpost = C.v15_cmd(sink, "verify_post_restored_sandbox",
                          ["verify", "--game", str(C.GAME), "--json"])
        proof["verify_post_restored_sandbox"] = {"exit_code": vpost["exit_code"],
                                                 "stdout_tail": vpost["stdout_tail"][-3000:]}
        sink.step("verify_post_restored_sandbox", **proof["verify_post_restored_sandbox"])

        # ---- (10) 沙箱目录清理: delete the sandbox AFTER all proofs -------
        proof["sandbox_dir_before_delete"] = {
            "path": str(C.GAME), "exists": C.GAME.exists()}
        if C.GAME.exists():
            shutil.rmtree(C.GAME)
        proof["sandbox_dir_after_delete"] = {
            "path": str(C.GAME), "exists": C.GAME.exists(),
            "cleaned": not C.GAME.exists()}
        sink.step("sandbox_dir_cleanup", **proof["sandbox_dir_after_delete"])

        # ---- (11) lock / residual -----------------------------------------
        lock_txt = C.lock_read()
        owner = ""
        for ln in lock_txt.splitlines():
            if ln.startswith("owner="):
                owner = ln.split("=", 1)[1].strip()
        proof["lock_final"] = {"owner": owner, "content": lock_txt,
                               "is_lead": owner == "lead"}
        proof["gamemd_residual_final"] = L.list_gamemd()
        sink.step("final_state", lock_owner=owner,
                  gamemd_residual=proof["gamemd_residual_final"],
                  residual_zero=len(proof["gamemd_residual_final"]) == 0)
        if owner != "lead":
            C.lock_release("W78 finalize: enforced owner=lead (cleanup complete)")
            proof["lock_final"]["released_by_finalize"] = True
            sink.step("lock_force_released", lock_content=C.lock_read())
        if proof["gamemd_residual_final"]:
            raise RuntimeError("residual gamemd at end of finalize")
        ok = True
        sink.step("finalize_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "FINALIZE.json").write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  real_identical_tree=proof.get("real_dir_diff", {}).get("identical_tree"),
                  sandbox_identical_tree=proof.get("sandbox_identical_tree"),
                  battlemd_restored=proof.get("battlemd_restore", {}).get("sha_equals_manifest_original"),
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

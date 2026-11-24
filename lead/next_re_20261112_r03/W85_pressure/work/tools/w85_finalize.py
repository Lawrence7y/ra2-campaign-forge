#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W85 FINALIZE - uninstall, byte-restore proof, real-dir proof, lock confirm.

  1. Capture install manifest original_sha256 BEFORE uninstall.
  2. v15 uninstall --game sandbox (exit 0 required) -> BATTLEMD.INI back to
     the pre-W85 state (= v0.3-era official baseline in this card's flow).
  3. Byte-restore EVERY pristine config (brings v0.3 record files back).
  4. Remove W85 dropped package files not in the sandbox PRE baseline.
  5. sandbox POST manifest vs sandbox_pre.json -> identical_tree self-proof
     (沙箱副本逐字节还原).
  6. REAL dir POST manifest vs real_pre.json -> IDENTICAL_TREE=True +
     anchor hashes (gamemd.exe/ddraw.dll/RA2MD.INI/BATTLEMD.INI/
     ra2forge_install.json) -> 真目录零改动 + v0.3 未动.
  7. Keep the sandbox dir for audit (card requires the restore proof; the
     identical-tree diff IS the proof; deletion is optional and NOT done).
  8. Confirm .game_instance.lock owner=lead; gamemd residual 0.

Only writes inside W85_pressure.  git read-only.  No blanket taskkill.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w85_lib as L
import w85_common as C

TAG = "finalize"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="cleanup: uninstall W85 package, byte-restore pristine "
                       "(v0.3 state back), real-dir zero-change proof, lock confirm")
        residual0 = L.list_gamemd()
        sink.step("gamemd_before_finalize", gamemd_processes=residual0, n=len(residual0))
        if residual0:
            raise RuntimeError("residual gamemd before finalize: %r" % residual0)

        official = (C.V15 / "ra2forge" / "data" / "BATTLEMD.OFFICIAL.INI").read_bytes()
        official_sha = sha(official)

        # ---- (1) capture manifest BEFORE uninstall -------------------------
        rec_path = C.GAME / "ra2forge_install.json"
        if not rec_path.is_file():
            raise RuntimeError("ra2forge_install.json missing in sandbox; "
                               "was a package installed?")
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
            "installed_is_rewritten": (sha(installed_battle) == recorded_post),
            "official_baseline_sha256": official_sha,
        }
        sink.step("pre_uninstall_state", **proof["pre_uninstall"])

        # ---- (2) v15 uninstall --------------------------------------------
        u = C.v15_cmd(sink, "uninstall_final",
                      ["uninstall", "--game", str(C.GAME), "--json"])
        proof["uninstall"] = {"exit_code": u["exit_code"],
                              "stdout_tail": u["stdout_tail"][-5000:]}
        sink.step("uninstall_exit", **proof["uninstall"])
        if u["exit_code"] != 0:
            raise RuntimeError("uninstall exit %s" % u["exit_code"])

        # ---- (3) BATTLEMD.INI byte-restore proof --------------------------
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
            "pristine_is_v03_state": sha(pristine) != official_sha,
            "real_dir_post_sha256": sha(real_battle),
            "real_dir_pre_sha256": real_pre_battle,
            "sha_equals_manifest_original": sha(restored) == recorded_original,
            "bytes_equal_pristine": restored == pristine,
            "bytes_equal_real_dir": restored == real_battle,
            "sha_equals_real_dir_pre": sha(restored) == real_pre_battle,
            "ra2f_scenario_gone": b"Scenario=RA2F_M1.MAP" not in restored,
        }
        proof["battlemd_restore"] = eog
        sink.step("battlemd_byte_restore_proof", **eog)
        # v0.3 的 BATTLEMD.INI = pristine 里的那份（非官方基线也允许：沙箱 PRE
        # 就是 v0.3 状态）。判据：还原件 == pristine == 真目录现状。
        assert eog["sha_equals_manifest_original"], eog
        assert eog["bytes_equal_pristine"], eog
        assert eog["bytes_equal_real_dir"], eog
        assert eog["sha_equals_real_dir_pre"], eog
        assert eog["ra2f_scenario_gone"], eog

        # ---- (4) byte-restore EVERY pristine config -----------------------
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

        # ---- (5) remove dropped package files not in PRE baseline ---------
        drops = ["RA2F_M1.MAP", "MAPSELMD.INI", "ra2forge_install.json",
                 "ra2forge_install.json.seal", "BATTLEMD.INI.ra2forge.bak"]
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

        # ---- (6) sandbox POST diff proof (沙箱逐字节还原自证) --------------
        post = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
        sd = C.diff_manifests(
            json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8")), post)
        proof["sandbox_diff"] = sd
        sink.step("sandbox_diff", identical_tree=sd["identical_tree"],
                  added=sd["added"], removed=sd["removed"],
                  changed=sd["changed"], mtime_diff_count=len(sd["mtime_diff"]),
                  pre_summary=sd["pre_summary"], post_summary=sd["post_summary"])
        if sd["added"]:
            for n in sd["added"]:
                p = C.GAME / n
                if p.is_file():
                    sink.step("drop_extra_file", file=n,
                              sha256=L.sha256_file(p), size=p.stat().st_size)
                    p.unlink()
            post = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
            sd = C.diff_manifests(
                json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8")), post)
            proof["sandbox_diff_after_extra_cleanup"] = sd
            sink.step("sandbox_diff_after_extra_cleanup",
                      identical_tree=sd["identical_tree"], added=sd["added"],
                      removed=sd["removed"], changed=sd["changed"])
        proof["sandbox_identical_tree"] = sd["identical_tree"]
        if not sd["identical_tree"]:
            raise RuntimeError("SANDBOX NOT IDENTICAL: %r" % sd)

        # ---- (7) REAL dir POST proof (THE critical one) -------------------
        real_post = C.write_manifest(C.OUT / "real_post.json", C.REAL)
        rd = C.diff_manifests(
            json.loads((C.OUT / "real_pre.json").read_text(encoding="utf-8")), real_post)
        proof["real_dir_diff"] = rd
        sink.step("real_dir_diff", identical_tree=rd["identical_tree"],
                  added=rd["added"], removed=rd["removed"],
                  changed=rd["changed"], mtime_diff_count=len(rd["mtime_diff"]),
                  pre_summary=rd["pre_summary"], post_summary=rd["post_summary"])
        anchors = {}
        for name in ("RA2MD.INI", "gamemd.exe", "ddraw.dll", "ra2forge_install.json",
                     "BATTLEMD.INI"):
            a = rp["summary"]["hashes"].get(name) if name != "BATTLEMD.INI" \
                else real_pre_battle
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

        # ---- (8) lock / residual (sandbox KEPT for audit) ------------------
        lock_txt = C.lock_read()
        owner = C.lock_owner()
        proof["lock_final"] = {"owner": owner, "content": lock_txt,
                               "is_lead": owner == "lead"}
        proof["gamemd_residual_final"] = L.list_gamemd()
        proof["sandbox_kept_for_audit"] = {"path": str(C.GAME),
                                           "exists": C.GAME.exists()}
        sink.step("final_state", lock_owner=owner,
                  gamemd_residual=proof["gamemd_residual_final"],
                  residual_zero=len(proof["gamemd_residual_final"]) == 0,
                  sandbox_kept=True)
        if owner != "lead":
            C.lock_release("W85 finalize: enforced owner=lead (cleanup complete, "
                           "sandbox tree byte-identical to PRE, real dir zero change)")
            proof["lock_final"]["released_by_finalize"] = True
            sink.step("lock_force_released", lock_content=C.lock_read())
        if proof["gamemd_residual_final"]:
            raise RuntimeError("residual gamemd at end of finalize")
        ok = True
        sink.step("finalize_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "FINALIZE.json").write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  real_identical_tree=proof.get("real_dir_diff", {}).get("identical_tree"),
                  sandbox_identical_tree=proof.get("sandbox_identical_tree"),
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

# -*- coding: utf-8 -*-
r"""W70 per-cycle driver: prep / restore / cleanup of ONE sandbox instance.

Usage:  python w70_cycle.py <prep|restore|cleanup> <tag>
  tag examples: t2, trip2, trip3

Every cycle uses a FRESH sandbox copy (robocopy ra2youli -> W70/sandbox_game),
so T2 and each T1 trip are independent.  The REAL dir is NEVER written.

  prep    : robocopy (read-only source), byte-pristine copies of writable
            configs, uninstall the pre-existing v0.3 record, remove the
            unowned orphan .bak from the SANDBOX COPY ONLY, assert BATTLEMD.INI
            == official baseline, install the reused W63 package (inplace),
            verify exit 0, capture manifest.original_sha256.
  restore : v15 uninstall, PROVE BATTLEMD.INI byte-restore
            (sha == manifest.original_sha256 == official == pristine == real),
            byte-restore every pristine config, remove dropped package files.
            (This is the "装包->卸载->逐字节还原" leg of T2.)
  cleanup : re-restore pristine configs (game launch may have written .sav /
            video settings), delete any file not in the PRE manifest, compute
            sandbox POST full manifest and diff (identical_tree self-proof),
            delete the sandbox dir, confirm lock/residual.

NO lock is taken in these OFFLINE phases (they never launch gamemd.exe).
All writes land in W70/out and W70/sandbox_game.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w70_lib as L
import w70_common as C


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tag():
    return sys.argv[2] if len(sys.argv) > 2 else "cycle"


def _official_sha() -> str:
    return sha((C.V15 / "ra2forge" / "data" /
                "BATTLEMD.OFFICIAL.INI").read_bytes())


# --------------------------------------------------------------------------
def prep(tag: str) -> int:
    sink = L.Sink(tag + "_prep")
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=tag + "_prep",
                  note="OFFLINE prep: no lock, no gamemd.exe",
                  pkg=str(C.PKG), feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("gamemd_guard_offline", processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("live gamemd.exe at prep: %r" % residual)

        official_sha = _official_sha()
        assert (C.OUT / "real_pre.json").is_file(), "run w70_base.py first"

        # ---- robocopy REAL -> sandbox (READ-ONLY source) --------------------
        if C.GAME.exists():
            raise RuntimeError("sandbox already exists; refusing to overwrite: %s"
                               % C.GAME)
        C.GAME.mkdir(parents=True, exist_ok=True)
        argv = ["robocopy", str(C.REAL), str(C.GAME),
                "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1",
                "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
        rec = C.run_cmd(sink, tag + "_robocopy", argv, timeout=900)
        if not (0 <= rec["exit_code"] <= 7):
            raise RuntimeError("robocopy rc=%s" % rec["exit_code"])
        sink.step("robocopy_verdict", rc=rec["exit_code"], success=True)

        # ---- sandbox PRE manifest + byte-pristine copies -------------------
        sp = C.write_manifest(C.OUT / ("sandbox_pre_%s.json" % tag), C.GAME)
        sink.step("sandbox_pre", summary=sp["summary"])
        assert sp["summary"]["file_count"] == C.BASELINE["file_count"], sp["summary"]
        assert sp["summary"]["total_bytes"] == C.BASELINE["total_bytes"], sp["summary"]
        C.save_pristine(sink)

        # ---- verify_pre / uninstall pre-existing v0.3 / verify -------------
        vpre = C.v15_cmd(sink, tag + "_verify_pre",
                         ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_pre_exit", exit_code=vpre["exit_code"])
        u03 = C.v15_cmd(sink, tag + "_uninstall_v03",
                        ["uninstall", "--game", str(C.GAME), "--json"])
        sink.step("uninstall_v03_exit", exit_code=u03["exit_code"],
                  stdout_tail=u03["stdout_tail"][-2500:])
        if u03["exit_code"] != 0:
            raise RuntimeError("v0.3 uninstall exit %s" % u03["exit_code"])
        vau = C.v15_cmd(sink, tag + "_verify_after_v03",
                        ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_v03_exit", exit_code=vau["exit_code"])

        # ---- unowned orphan .bak, SANDBOX COPY ONLY ------------------------
        orphan = C.GAME / "BATTLEMD.INI.ra2forge.bak"
        oi = {"present_before": orphan.is_file(),
              "sha256": L.sha256_file(orphan) if orphan.is_file() else None,
              "size": orphan.stat().st_size if orphan.is_file() else None,
              "pristine_copy": str(C.OUT / "pristine" /
                                   "BATTLEMD.INI.ra2forge.bak")}
        if orphan.is_file():
            orphan.unlink()
        oi["removed_from_sandbox_only"] = not orphan.exists()
        sink.step("orphan_bak_prep", **oi)

        # ---- inplace target must be official baseline ----------------------
        cur = (C.GAME / "BATTLEMD.INI").read_bytes()
        sink.step("inplace_target_precheck", size=len(cur), sha256=sha(cur),
                  expected_sha256=official_sha,
                  official_match=(sha(cur) == official_sha))
        if sha(cur) != official_sha:
            raise RuntimeError("BATTLEMD.INI != official baseline; inplace would refuse")

        # ---- install the SAME reused build (no package edits) --------------
        i0 = C.v15_cmd(sink, tag + "_install",
                       ["install", "--package", str(C.PKG), "--game", str(C.GAME),
                        "--feature-set", str(C.FEATURE_SET)])
        sink.step("install_exit", exit_code=i0["exit_code"],
                  stdout_tail=i0["stdout_tail"][-2500:])
        if i0["exit_code"] != 0:
            i1 = C.v15_cmd(sink, tag + "_install_allow",
                           ["install", "--package", str(C.PKG), "--game",
                            str(C.GAME), "--feature-set", str(C.FEATURE_SET),
                            "--allow-content-conflict"])
            sink.step("install_allow_exit", exit_code=i1["exit_code"],
                      stdout_tail=i1["stdout_tail"][-3000:])
            if i1["exit_code"] != 0:
                raise RuntimeError("install exit %s / %s"
                                   % (i0["exit_code"], i1["exit_code"]))

        # ---- verify MUST exit 0 -------------------------------------------
        v2 = C.v15_cmd(sink, tag + "_verify_after_install",
                       ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_install_exit", exit_code=v2["exit_code"],
                  stdout_tail=v2["stdout_tail"][-4000:])
        if v2["exit_code"] != 0:
            raise RuntimeError("verify after install exit %s" % v2["exit_code"])

        # ---- manifest original_sha256 + .bak assertions --------------------
        rec_path = C.GAME / "ra2forge_install.json"
        man = json.loads(rec_path.read_text(encoding="utf-8"))
        entries = [e for e in man.get("files", []) if e.get("name") == "BATTLEMD.INI"]
        bak = C.GAME / "BATTLEMD.INI.ra2forge.bak"
        inplace = {
            "manifest_path": str(rec_path),
            "manifest_sha256": L.sha256_file(rec_path),
            "battlemd_entries": entries,
            "bak_present": bak.is_file(),
            "bak_sha256": L.sha256_file(bak) if bak.is_file() else None,
            "official_baseline_sha256": official_sha,
        }
        assert len(entries) == 1, entries
        e = entries[0]
        inplace["original_sha256_recorded"] = e.get("original_sha256")
        inplace["original_sha256_matches_official"] = (
            e.get("original_sha256") == official_sha)
        inplace["bak_equals_official"] = (
            bak.is_file() and L.sha256_file(bak) == official_sha)
        inplace["post_install_sha_on_disk"] = sha(
            (C.GAME / "BATTLEMD.INI").read_bytes())
        inplace["sov1_scenario_on_disk"] = (
            b"Scenario=RA2F_M1.MAP" in (C.GAME / "BATTLEMD.INI").read_bytes())
        sink.step("inplace_install_assertions", **inplace)
        assert inplace["original_sha256_matches_official"]
        assert inplace["bak_equals_official"]
        assert inplace["sov1_scenario_on_disk"]
        (C.OUT / ("INPLACE_INSTALL_%s.json" % tag)).write_text(
            json.dumps(inplace, ensure_ascii=False, indent=2), encoding="utf-8")

        # ---- installed inventory; MAPSELMD must equal the PACKAGE bytes ----
        inst_ms = (C.GAME / "MAPSELMD.INI").read_bytes()
        pkg_ms = (C.PKG / "MAPSELMD.INI").read_bytes()
        installed = []
        for n in ("BATTLEMD.INI", "BATTLEMD.INI.ra2forge.bak", "MAPSELMD.INI",
                  "RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP",
                  "expandmd98.mix", "ra2forge_install.json"):
            p = C.GAME / n
            installed.append({"file": n, "present": p.is_file(),
                              "size": p.stat().st_size if p.is_file() else None,
                              "sha256": L.sha256_file(p) if p.is_file() else None})
        sink.step("installed_inventory", files=installed,
                  mapsel_equals_package_variantA=(inst_ms == pkg_ms),
                  mapsel_sha256=sha(inst_ms))
        assert inst_ms == pkg_ms, "installed MAPSELMD != reused package bytes"
        ok = True
        sink.step("prep_result", ok=ok,
                  original_sha256=inplace["original_sha256_recorded"])
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=tag + "_prep", ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


# --------------------------------------------------------------------------
def restore(tag: str) -> int:
    sink = L.Sink(tag + "_restore")
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=tag + "_restore",
                  note="OFFLINE uninstall + byte-restore proof (no lock, no gamemd)")
        residual = L.list_gamemd()
        sink.step("gamemd_guard_offline", processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("live gamemd.exe at restore: %r" % residual)

        official_sha = _official_sha()

        # ---- capture manifest original_sha256 BEFORE uninstall -------------
        rec_path = C.GAME / "ra2forge_install.json"
        man = json.loads(rec_path.read_text(encoding="utf-8"))
        e = [x for x in man.get("files", []) if x.get("name") == "BATTLEMD.INI"][0]
        recorded_original = e["original_sha256"]
        recorded_post = e.get("post_install_sha256")
        installed_battle = (C.GAME / "BATTLEMD.INI").read_bytes()
        proof["pre_uninstall"] = {
            "manifest_original_sha256": recorded_original,
            "manifest_post_install_sha256": recorded_post,
            "battlemd_on_disk_sha256": sha(installed_battle),
            "battlemd_on_disk_size": len(installed_battle),
            "installed_is_rewritten": (sha(installed_battle) == recorded_post),
            "official_baseline_sha256": official_sha,
        }
        sink.step("pre_uninstall_state", **proof["pre_uninstall"])
        assert proof["pre_uninstall"]["installed_is_rewritten"]

        # ---- v15 uninstall -------------------------------------------------
        u = C.v15_cmd(sink, tag + "_uninstall_final",
                      ["uninstall", "--game", str(C.GAME), "--json"])
        proof["uninstall"] = {"exit_code": u["exit_code"],
                              "stdout_tail": u["stdout_tail"][-5000:]}
        sink.step("uninstall_exit", **proof["uninstall"])
        if u["exit_code"] != 0:
            raise RuntimeError("uninstall exit %s" % u["exit_code"])

        # ---- BATTLEMD.INI byte-restore proof (T2 core) --------------------
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
            "real_dir_sha256": sha(real_battle),
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

        # ---- byte-restore EVERY pristine config ----------------------------
        rows = []
        for name in C.PRISTINE:
            try:
                rows.append(C.restore_one(name, sink, label=tag + "_restore"))
            except Exception as ex:
                rows.append({"file": name, "error": repr(ex)})
                sink.step("restore_error", file=name, error=repr(ex))
        proof["config_restore"] = rows
        n_ok = sum(1 for r in rows if r.get("byte_identical")
                   or r.get("absent_baseline"))
        sink.step("config_restore_summary", rows=rows, n_ok=n_ok,
                  n_total=len(rows), all_ok=(n_ok == len(rows)))
        if n_ok != len(rows):
            raise RuntimeError("config restore incomplete: %r" % rows)

        # ---- remove dropped package files (not in PRE manifest) -----------
        sp = json.loads((C.OUT / ("sandbox_pre_%s.json" % tag)).read_text(
            encoding="utf-8"))
        pre_rel = {r["rel"] for r in sp["files"]}
        drops = ["RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP",
                 "MAPSELMD.INI", "expandmd98.mix",
                 "ra2forge_install.json", "ra2forge_install.json.seal",
                 "BATTLEMD.INI.ra2forge.bak"]
        removed = []
        for n in drops:
            p = C.GAME / n
            if p.is_file() and n not in pre_rel:
                p.unlink()
                removed.append({"file": n, "removed": True})
            else:
                removed.append({"file": n, "removed": False,
                                "reason": "not present or part of PRE baseline"})
        proof["drop_cleanup"] = removed
        sink.step("drop_cleanup", rows=removed)
        ok = True
        sink.step("restore_result", ok=ok,
                  battlemd_restored=eog["sha_equals_manifest_original"],
                  original_sha256=recorded_original)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / ("RESTORE_%s.json" % tag)).write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=tag + "_restore", ok=ok,
                  battlemd_restored=proof.get("battlemd_restore", {}).get(
                      "sha_equals_manifest_original"),
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


# --------------------------------------------------------------------------
def cleanup(tag: str) -> int:
    sink = L.Sink(tag + "_cleanup")
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=tag + "_cleanup",
                  note="OFFLINE cleanup: re-restore configs, drop game-generated "
                       "files, sandbox identical_tree proof, delete sandbox")
        residual = L.list_gamemd()
        sink.step("gamemd_guard_offline", processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("live gamemd.exe at cleanup: %r" % residual)

        # re-restore pristine configs (game launch may have written settings)
        rows = []
        for name in C.PRISTINE:
            try:
                rows.append(C.restore_one(name, sink, label=tag + "_cleanup"))
            except Exception as ex:
                rows.append({"file": name, "error": repr(ex)})
        proof["config_restore"] = rows

        sp = json.loads((C.OUT / ("sandbox_pre_%s.json" % tag)).read_text(
            encoding="utf-8"))
        pre_rel = {r["rel"] for r in sp["files"]}

        # delete .sav / .svg and ANY file not in PRE manifest
        removed = []
        for p in sorted(C.GAME.glob("*"), key=lambda x: x.name.lower()):
            if p.is_file() and p.name not in pre_rel:
                removed.append({"file": p.name, "size": p.stat().st_size,
                                "sha256": L.sha256_file(p)})
                p.unlink()
        proof["extra_files_removed"] = removed
        sink.step("extra_files_removed", rows=removed, n=len(removed))

        # RESTORE PRE-existing files the game rewrote (e.g. SOV01UMD.sav, which
        # is a real save present in the baseline and auto-overwritten on mission
        # entry).  Byte source = the unchanged, READ-ONLY real dir.  Real SHA
        # self-proof: restored == real bytes == PRE manifest sha256.
        first = C.write_manifest(C.OUT / ("sandbox_precleanup_%s.json" % tag), C.GAME)
        pre_by_rel = {r["rel"]: r for r in sp["files"]}
        cur_by_rel = {r["rel"]: r for r in first["files"]}
        restored_rows = []
        for rel, pr in pre_by_rel.items():
            cr = cur_by_rel.get(rel)
            if cr and (cr["size"] != pr["size"] or cr["sha256"] != pr["sha256"]):
                src = C.REAL / rel
                dst = C.GAME / rel
                if src.is_file():
                    rb = src.read_bytes()
                    dst.write_bytes(rb)
                    row = {"file": rel, "action": "restored_from_real_dir",
                           "pre_size": pr["size"], "pre_sha256": pr["sha256"],
                           "changed_size": cr["size"],
                           "changed_sha256": cr["sha256"],
                           "restored_size": len(rb),
                           "restored_sha256": sha(rb),
                           "equals_pre_sha256": sha(rb) == pr["sha256"],
                           "equals_real_dir": dst.read_bytes() == rb}
                    restored_rows.append(row)
                    sink.step("restore_game_rewritten_file", **row)
        proof["game_rewritten_files_restored"] = restored_rows
        sink.step("game_rewritten_restore_summary", rows=restored_rows,
                  n=len(restored_rows),
                  all_ok=all(r["equals_pre_sha256"] for r in restored_rows))
        if not all(r["equals_pre_sha256"] for r in restored_rows):
            raise RuntimeError("game-rewritten PRE file restore failed: %r"
                               % restored_rows)

        # sandbox POST full diff
        post = C.write_manifest(C.OUT / ("sandbox_post_%s.json" % tag), C.GAME)
        sd = C.diff_manifests(sp, post)
        proof["sandbox_diff"] = sd
        sink.step("sandbox_diff", identical_tree=sd["identical_tree"],
                  added=sd["added"], removed=sd["removed"],
                  changed=sd["changed"],
                  pre_summary=sd["pre_summary"], post_summary=sd["post_summary"])
        if not sd["identical_tree"]:
            raise RuntimeError("sandbox NOT identical to PRE: %r" % sd)
        proof["sandbox_identical_tree"] = sd["identical_tree"]

        # delete sandbox AFTER proofs saved
        before = C.GAME.exists()
        if before:
            shutil.rmtree(C.GAME)
        proof["sandbox_dir_deleted"] = {"before_exists": before,
                                        "after_exists": C.GAME.exists(),
                                        "cleaned": not C.GAME.exists()}
        sink.step("sandbox_dir_cleanup", **proof["sandbox_dir_deleted"])

        lock_txt = C.lock_read()
        owner = ""
        for ln in lock_txt.splitlines():
            if ln.startswith("owner="):
                owner = ln.split("=", 1)[1].strip()
        proof["lock_owner"] = owner
        proof["gamemd_residual"] = L.list_gamemd()
        sink.step("cycle_end_state", lock_owner=owner,
                  lock_is_lead=(owner == "lead"),
                  gamemd_residual=proof["gamemd_residual"],
                  residual_zero=(len(proof["gamemd_residual"]) == 0))
        if owner != "lead":
            C.lock_release("W70 %s cleanup: enforced owner=lead" % tag)
            sink.step("lock_force_released", lock_content=C.lock_read())
        if proof["gamemd_residual"]:
            raise RuntimeError("residual gamemd at cleanup end")
        ok = True
        sink.step("cleanup_result", ok=ok,
                  identical_tree=proof["sandbox_identical_tree"])
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / ("CLEANUP_%s.json" % tag)).write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=tag + "_cleanup", ok=ok,
                  sandbox_identical_tree=proof.get("sandbox_identical_tree"),
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: w70_cycle.py <prep|restore|cleanup> <tag>")
        return 2
    action, tag = sys.argv[1], _tag()
    return {"prep": prep, "restore": restore, "cleanup": cleanup}[action](tag)


if __name__ == "__main__":
    raise SystemExit(main())

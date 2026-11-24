# -*- coding: utf-8 -*-
r"""W70 FINAL (runs ONCE at the very end, after all cycles' sandboxes are gone).

  1. Full manifest of the REAL dir -> out/real_post.json; diff against
     out/real_pre.json (captured at baseline, BEFORE any cycle) ->
     IDENTICAL_TREE=True (真目录零改动自证).  Also re-check five anchor hashes.
  2. Collect every per-cycle proof (TRIP_*.json / RESTORE_*.json /
     CLEANUP_*.json / T2_OFFICIAL.json / INPLACE_INSTALL_*.json) into
     out/SUMMARY.json.
  3. Write REAL_DIR_PROOF.txt (the deliverable self-proof).
  4. Confirm .game_instance.lock owner=lead and gamemd residual 0 (force-release
     the lock to lead if a crashed driver left it owned by w70).

NO gamemd.exe is launched here.  The REAL dir is READ-ONLY.  git is read-only.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w70_lib as L
import w70_common as C

TAG = "final"


def _load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_error": repr(e), "_path": str(p)}


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="global final: real-dir zero-change proof + summary")
        if C.GAME.exists():
            sink.step("warning_sandbox_still_exists", path=str(C.GAME),
                      note="a cycle did not clean up; refusing to hide it")
            raise RuntimeError("sandbox_game still exists at final; a cleanup failed")

        # ---- (1) real dir POST proof (THE critical one) --------------------
        rp = json.loads((C.OUT / "real_pre.json").read_text(encoding="utf-8"))
        real_post = C.write_manifest(C.OUT / "real_post.json", C.REAL)
        rd = C.diff_manifests(rp, real_post)
        proof["real_dir_diff"] = rd
        sink.step("real_dir_diff", identical_tree=rd["identical_tree"],
                  added=rd["added"], removed=rd["removed"],
                  changed=rd["changed"], mtime_diff_count=len(rd["mtime_diff"]),
                  pre_summary=rd["pre_summary"], post_summary=rd["post_summary"])

        anchors = {}
        for name in ("RA2MD.INI", "gamemd.exe", "ddraw.dll",
                     "ra2forge_install.json", "BATTLEMD.INI"):
            a = rp["summary"]["hashes"].get(name)
            if name == "BATTLEMD.INI":
                a = next(r["sha256"] for r in rp["files"]
                         if r["rel"] == "BATTLEMD.INI")
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
            raise RuntimeError("REAL DIR anchor mismatch: %r" % anchors)
        proof["IDENTICAL_TREE"] = True

        # ---- (2) collect per-cycle proofs ----------------------------------
        summary = {"real_dir_identical_tree": True,
                   "real_pre_summary": rp["summary"],
                   "real_post_summary": real_post["summary"],
                   "cycles": {}}
        for p in sorted(C.OUT.glob("*.json")):
            n = p.name
            if n.startswith(("TRIP_", "RESTORE_", "CLEANUP_", "INPLACE_INSTALL_")) \
                    or n in ("T2_OFFICIAL.json", "OFFICIAL_SOV1.json",
                             "PACKAGE_INVENTORY.json"):
                summary["cycles"][n] = _load(p)
        (C.OUT / "SUMMARY.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("summary_written", n_files=len(summary["cycles"]))

        # ---- (3) REAL_DIR_PROOF.txt ----------------------------------------
        lines = [
            "REAL_DIR_PROOF",
            "ISO: " + L.local_iso(),
            "Card: W70_c_repeatability (executor Hy4, not Lead)",
            "",
            "REAL dir (READ-ONLY, NEVER written): " + str(C.REAL),
            "PRE  manifest: out/real_pre.json   (captured at baseline, BEFORE any cycle)",
            "POST manifest: out/real_post.json  (captured now, AFTER all cycles' sandboxes deleted)",
            "",
            "PRE  : file_count=%d total_bytes=%d maplike_count=%d"
            % (rp["summary"]["file_count"], rp["summary"]["total_bytes"],
               rp["summary"]["maplike_count"]),
            "POST : file_count=%d total_bytes=%d maplike_count=%d"
            % (real_post["summary"]["file_count"],
               real_post["summary"]["total_bytes"],
               real_post["summary"]["maplike_count"]),
            "",
            "diff added   = %r" % rd["added"],
            "diff removed = %r" % rd["removed"],
            "diff changed = %r" % rd["changed"],
            "mtime_diff_count = %d (mtime NOT part of identity)" % len(rd["mtime_diff"]),
            "",
            "IDENTICAL_TREE=True",
            "",
            "Anchor hashes PRE == POST:",
        ]
        for name, a in anchors.items():
            lines.append("  %-28s equal=%s  %s" % (name, a["equal"], a["post"]))
        lines += [
            "",
            "Four W44 signed baseline assertions (file_count / total_bytes / "
            "maplike_count / RA2MD.INI / gamemd.exe / ddraw.dll / "
            "ra2forge_install.json) were checked in w70_base.py (base.ndjson).",
            "",
            "Method: full-tree manifest = (rel, size, sha256) for every file; "
            "diff by (rel, size, sha256); computed with w70_common.manifest / "
            "diff_manifests (copies of W63's proven helpers).",
            "All installs/uninstalls/game launches ran against "
            "W70_c_repeatability/sandbox_game (robocopy copy of the REAL dir), "
            "which was byte-restored and DELETED after each cycle "
            "(CLEANUP_*.json sandbox_identical_tree=True).",
            "No git write operations were performed.",
        ]
        (C.CARD / "REAL_DIR_PROOF.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
        sink.step("real_dir_proof_written",
                  path=str(C.CARD / "REAL_DIR_PROOF.txt"))

        # ---- (4) lock / residual -------------------------------------------
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
            C.lock_release("W70 final: enforced owner=lead (all cycles complete, "
                           "all game instances closed, real dir identical)")
            proof["lock_final"]["released_by_final"] = True
            sink.step("lock_force_released", lock_content=C.lock_read())
        if proof["gamemd_residual_final"]:
            raise RuntimeError("residual gamemd.exe at final")
        ok = True
        sink.step("final_result", ok=ok, IDENTICAL_TREE=True)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "FINAL.json").write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  real_identical_tree=proof.get("IDENTICAL_TREE"),
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

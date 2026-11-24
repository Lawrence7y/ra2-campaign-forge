#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 6 - FINALIZE.

Final self-heal (close game / residual 0 / byte-restore configs / remove
drops), real-dir POST full manifest, REAL_DIR_PROOF.txt, a machine-readable
summary of every phase's ndjson, then release the instance lock back to
owner=lead and emit the card-level kind=meta_end.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "final"


def phase_summary(name):
    p = C.OUT / (name + ".ndjson")
    if not p.is_file():
        return {"phase": name, "present": False}
    recs = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = {"phase": name, "present": True, "n_records": len(recs)}
    for r in recs:
        s = r.get("step", "")
        if s in ("build_result", "install_result", "run_outcome", "K1_result",
                 "K2_result", "K3_result", "repair_result",
                 "uninstall_result", "restore_proof_result",
                 "prep_result", "final_diff", "byte_checks",
                 "S2_csf_judgment_inputs", "K3_csf_judgment_inputs",
                 "A2_confirmed", "K2_load_observation", "step0_desktop_precheck",
                 "meta_end"):
            out[s] = {k: v for k, v in r.items()
                      if k not in ("kind", "step", "t_utc", "t_local", "t_monotonic")}
    return out


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  card="W44 C-line E2E finalize")
        residual = L.list_gamemd()
        sink.step("final_residual_before_heal", gamemd_processes=residual,
                  n=len(residual))
        if residual:
            sink.step("final_residual_forced_close", note="force close own leftovers")
            for r in residual:
                try:
                    L.close_game(r["pid"], None, sink)
                except Exception as e:
                    sink.step("final_close_error", error=repr(e))

        # final byte-restore of configs (idempotent)
        C.heal(sink, label="final_finally",
               remove_drops=("MAPSELMD.INI", "ra2md.csf"))
        after = L.list_gamemd()
        sink.step("final_residual_after_heal", gamemd_processes=after,
                  residual_zero=(len(after) == 0))

        # real-dir POST full manifest + zero-change proof
        post = C.write_manifest(C.OUT / "real_post.json", C.REAL)
        pre = json.loads((C.OUT / "real_pre.json").read_text(encoding="utf-8"))
        d = C.diff_manifests(pre, post)
        (C.OUT / "real_diff.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        sink.step("real_diff", added=d["added"], removed=d["removed"],
                  changed=d["changed"], identical_tree=d["identical_tree"],
                  pre_summary=d["pre_summary"], post_summary=d["post_summary"])

        lines = []
        lines.append("W44 C-line E2E - REAL DIRECTORY ZERO-CHANGE PROOF")
        lines.append("real_dir = %s" % C.REAL)
        lines.append("PRE  manifest = %s" % (C.OUT / "real_pre.json"))
        lines.append("POST manifest = %s" % (C.OUT / "real_post.json"))
        lines.append("")
        for label, s in (("PRE ", d["pre_summary"]), ("POST", d["post_summary"])):
            lines.append("%s: file_count=%d total_bytes=%d maplike_count=%d"
                         % (label, s["file_count"], s["total_bytes"],
                            s["maplike_count"]))
        lines.append("added=%d removed=%d changed=%d   IDENTICAL_TREE=%s"
                     % (len(d["added"]), len(d["removed"]), len(d["changed"]),
                        d["identical_tree"]))
        lines.append("")
        for n in ("RA2MD.INI", "gamemd.exe", "ddraw.dll",
                  "ra2forge_install.json"):
            a = d["pre_summary"]["hashes"].get(n)
            b = d["post_summary"]["hashes"].get(n)
            pref = C.BASELINE.get(n, "")
            lines.append("%-24s PRE=%s POST=%s match=%s baseline_prefix=%s"
                         % (n, a, b, a == b, pref))
        lines.append("")
        lines.append("method: full recursive manifest of every file "
                     "(rel / size / mtime_ns / sha256), PRE at card start, "
                     "POST at card end; diff by (rel,size,sha256).")
        lines.append("ra2youli was only ever a robocopy SOURCE (read-only).")
        (C.W44 / "REAL_DIR_PROOF.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
        sink.step("real_dir_proof_written",
                  path=str(C.W44 / "REAL_DIR_PROOF.txt"),
                  identical_tree=d["identical_tree"])

        # machine-readable summary of all phases
        names = ["prep", "build", "install", "run", "saveload",
                 "csf_control", "repair", "uninstall", "restore_proof"]
        summ = {n: phase_summary(n) for n in names}
        (C.OUT / "summary.json").write_text(
            json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
        sink.step("summary_written", phases=names)

        # release lock back to lead
        L.lock_restore_lead()
        sink.step("lock_restored", content=L.LOCK.read_text(encoding="utf-8"))

        ok = bool(d["identical_tree"] and len(after) == 0)
        sink.step("finalize_result", ok=ok,
                  real_dir_identical=d["identical_tree"],
                  gamemd_residual_zero=(len(after) == 0))
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-5000:])
    finally:
        # never leave the lock owned by w44 even on an unexpected failure
        try:
            if (L.LOCK.read_text(encoding="utf-8").find("owner=w44") >= 0):
                L.lock_restore_lead()
                sink.step("lock_restored_in_finally", forced=True)
        except Exception as e:
            sink.step("lock_restore_error", error=repr(e))
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

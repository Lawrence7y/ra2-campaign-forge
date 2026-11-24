#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W91 FINALIZE - uninstall package, byte-restore, pre/post manifest proof.

NO gamemd.exe is launched here.  Sequence:
  1. guard: no residual gamemd; lock owner=w90 (session lock untouched)
  2. ra2forge uninstall --game sandbox --json (MUST exit 0)
  3. engine-dropped artifacts (e.g. RA2F_M1.sav) recorded then removed from
     the SANDBOX COPY ONLY so the post manifest diffs clean
  4. byte-restore every pristine config + hash self-proof
  5. sandbox_post manifest, diff vs sandbox_pre -> identical_tree
  6. real_post manifest (ra2youli, READ-ONLY), diff vs real_pre ->
     identical_tree + W44 baseline assertions
  7. 4-anchor hash table (gamemd.exe / ddraw.dll / RA2MD.INI / BATTLEMD.INI)
     pre/post on the REAL dir + residual process check
  8. FINALIZE.json + finalize.ndjson (lock content recorded verbatim; the
     orchestrator restores owner=lead after this script returns)
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w91_lib as L
import w91_common as C

TAG = "finalize"


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    proof = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="W91 finalize: uninstall + restore + manifest proofs; "
                       "no game launch; real dir read-only")
        residual = L.list_gamemd()
        sink.step("pre_guard", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at finalize: %r" % residual)
        owner = C.lock_owner()
        sink.step("lock_owner_at_finalize", owner=owner,
                  lock_content=C.lock_read())
        if owner not in ("w91", "lead"):
            raise RuntimeError("unexpected lock owner: %r" % owner)

        # (2) uninstall final package
        u = C.v15_cmd(sink, "uninstall_final",
                      ["uninstall", "--game", str(C.GAME), "--json"])
        sink.step("uninstall_final_exit", exit_code=u["exit_code"],
                  stdout_tail=u["stdout_tail"][-3000:])
        proof["uninstall_exit_code"] = u["exit_code"]
        if u["exit_code"] != 0:
            raise RuntimeError("final uninstall exit %s" % u["exit_code"])
        v = C.v15_cmd(sink, "verify_after_uninstall",
                      ["verify", "--game", str(C.GAME), "--json"])
        proof["verify_after_uninstall_exit"] = v["exit_code"]
        sink.step("verify_after_uninstall_exit", exit_code=v["exit_code"])

        # (3) engine-dropped artifacts in the SANDBOX COPY ONLY.
        # Judged by DIFF vs the sandbox_pre manifest (NOT by filename globs -
        # a glob like save*.sav would eat the baseline SAVE0029.SAV shipped
        # with ra2youli; first finalize run removed it once and it was
        # byte-restored from the real dir, sha-proven, then this fix landed).
        pre_sp = json.loads((C.OUT / "sandbox_pre.json").read_text(
            encoding="utf-8"))
        pre_names = {r["rel"] for r in pre_sp["files"]}
        cur = C.manifest(C.GAME)
        dropped = []
        for row in cur:
            rel = row["rel"]
            if rel in pre_names:
                continue
            if Path(rel).suffix.lower() not in (".sav", ".svg"):
                continue
            p = C.GAME / rel
            prow = {"file": rel, "size": p.stat().st_size,
                    "sha256": L.sha256_file(p)}
            p.unlink()
            prow["removed_from_sandbox_only"] = not p.exists()
            dropped.append(prow)
        sink.step("engine_dropped_removed", rows=dropped)
        proof["engine_dropped_removed"] = dropped

        # (4) byte-restore pristine configs
        proof["config_restore"] = [C.restore_one(n, sink, label="finalize")
                                   for n in C.PRISTINE]

        # (5) sandbox post manifest diff
        sp = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
        pre_sp = json.loads((C.OUT / "sandbox_pre.json").read_text(
            encoding="utf-8"))
        d_sb = C.diff_manifests(pre_sp, sp)
        proof["sandbox_diff"] = d_sb
        sink.step("sandbox_diff", identical_tree=d_sb["identical_tree"],
                  added=d_sb["added"], removed=d_sb["removed"],
                  changed=d_sb["changed"])

        # (6) real dir post manifest diff (READ-ONLY)
        rp = C.write_manifest(C.OUT / "real_post.json", C.REAL)
        pre_rp = json.loads((C.OUT / "real_pre.json").read_text(
            encoding="utf-8"))
        d_rl = C.diff_manifests(pre_rp, rp)
        proof["real_diff"] = d_rl
        s = rp["summary"]
        baseline_ok = (s["file_count"] == C.BASELINE["file_count"]
                       and s["total_bytes"] == C.BASELINE["total_bytes"]
                       and s["maplike_count"] == C.BASELINE["maplike_count"])
        proof["real_post_baseline_ok"] = baseline_ok
        sink.step("real_diff", identical_tree=d_rl["identical_tree"],
                  added=d_rl["added"], removed=d_rl["removed"],
                  changed=d_rl["changed"], baseline_ok=baseline_ok,
                  summary=s)

        # (7) 4-anchor table on the REAL dir (hashes computed directly on the
        # live files; the manifest summary only carries BASELINE-named keys,
        # which excludes BATTLEMD.INI)
        anchors = {}
        for name in ("gamemd.exe", "ddraw.dll", "RA2MD.INI", "BATTLEMD.INI"):
            p = C.REAL / name
            post_h = L.sha256_file(p) if p.is_file() else None
            pre_row = next((r for r in pre_rp["files"]
                            if r["rel"] == name), None)
            pre_h = pre_row["sha256"] if pre_row else None
            anchors[name] = {"pre_sha256": pre_h, "post_sha256": post_h,
                             "identical": (pre_h is not None
                                           and pre_h == post_h)}
        proof["anchors_real_dir"] = anchors
        sink.step("anchors_real_dir", **anchors)
        residual2 = L.list_gamemd()
        proof["residual_gamemd_after_all"] = residual2
        proof["lock_content_final"] = C.lock_read()
        ok = (d_sb["identical_tree"] and d_rl["identical_tree"]
              and baseline_ok and not residual2
              and all(a["identical"] for a in anchors.values()))
        sink.step("finalize_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "FINALIZE.json").write_text(
            json.dumps(proof, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(),
                  lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


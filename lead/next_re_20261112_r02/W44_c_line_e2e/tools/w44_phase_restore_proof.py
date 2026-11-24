#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 5b - RESTORE PROOF with the CORRECT baseline.

The PREP-time sandbox_pre.json is the "v0.3 legacy package INSTALLED" state.
Uninstalling that legacy package is an explicit step of this card (section 2),
so the post-uninstall state cannot be compared to it.

The correct baseline is: a fresh read-only copy of ra2youli with ONLY the
v0.3 legacy uninstall applied (the exact state just before the v12 install).
This script builds that baseline in W44/baseline_clean/, then compares the
main sandbox against it file-by-file, restores any residual game-produced
drift byte-exactly from the baseline, and re-checks IDENTICAL_TREE.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "restore_proof"
BASE = C.W44 / "baseline_clean"


def build_baseline(sink):
    if (C.OUT / "baseline_clean.json").is_file() and BASE.is_dir():
        sink.step("baseline_reused", path=str(BASE))
        return json.loads((C.OUT / "baseline_clean.json").read_text(encoding="utf-8"))
    BASE.mkdir(parents=True, exist_ok=True)
    argv = ["robocopy", str(C.REAL), str(BASE),
            "/E", "/COPY:DAT", "/DCOPY:DAT", "/R:1", "/W:1",
            "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
    rec = C.run_cmd(sink, "robocopy_baseline", argv, timeout=600)
    if not (0 <= rec["exit_code"] <= 7):
        raise RuntimeError("baseline robocopy rc=%s" % rec["exit_code"])
    u = C.v12_cmd(sink, "baseline_uninstall_v03",
                  ["uninstall", "--game", str(BASE), "--json"])
    sink.step("baseline_uninstall_exit", exit_code=u["exit_code"],
              stdout_tail=u["stdout_tail"][-3000:])
    if u["exit_code"] != 0:
        raise RuntimeError("baseline uninstall exit %s" % u["exit_code"])
    v = C.v12_cmd(sink, "baseline_verify",
                  ["verify", "--game", str(BASE), "--json"])
    sink.step("baseline_verify_exit", exit_code=v["exit_code"])
    b = C.write_manifest(C.OUT / "baseline_clean.json", BASE)
    sink.step("baseline_manifest", summary=b["summary"])
    return b


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="correct baseline = fresh ra2youli copy with ONLY the "
                       "v0.3 legacy uninstall applied")
        base = build_baseline(sink)
        basemap = {r["rel"]: r for r in base["files"]}

        cur = C.write_manifest(C.OUT / "sandbox_post_preclean.json", C.GAME)
        curmap = {r["rel"]: r for r in cur["files"]}
        added = sorted(set(curmap) - set(basemap))
        removed = sorted(set(basemap) - set(curmap))
        changed = sorted(k for k in (set(curmap) & set(basemap))
                         if curmap[k]["size"] != basemap[k]["size"]
                         or curmap[k]["sha256"] != basemap[k]["sha256"])
        sink.step("diff_before_clean", added=added, removed=removed,
                  changed=changed)

        actions = []
        for rel in added:
            p = C.GAME / rel
            try:
                p.unlink()
                actions.append({"rel": rel, "action": "removed_extra", "ok": True})
            except Exception as e:
                actions.append({"rel": rel, "action": "remove_failed",
                                "error": repr(e)})
        for rel in removed + changed:
            src = BASE / rel
            dst = C.GAME / rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
                actions.append({"rel": rel, "action": "restored_from_baseline",
                                "sha256": L.sha256_file(dst),
                                "expected": basemap[rel]["sha256"],
                                "byte_identical": dst.read_bytes() == src.read_bytes()})
            except Exception as e:
                actions.append({"rel": rel, "action": "restore_failed",
                                "error": repr(e)})
        sink.step("restore_actions", n=len(actions), actions=actions)

        post = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
        d = C.diff_manifests(base, post)
        (C.OUT / "sandbox_diff_final.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        sink.step("final_diff", added=d["added"], removed=d["removed"],
                  changed=d["changed"], identical_tree=d["identical_tree"],
                  pre_summary=d["pre_summary"], post_summary=d["post_summary"])

        checks = []
        for n in ("MAPSELMD.INI", "ra2md.csf"):
            p = C.GAME / n
            checks.append({"check": "no_loose_" + n,
                           "present": p.is_file(), "pass": not p.is_file()})
        for n in ("BATTLEMD.INI", "RA2MD.INI", "ddraw.ini",
                  "gamemd.exe", "ddraw.dll", "ECH01.MAP", "ECH02.MAP",
                  "ECH03.MAP", "BATTLEMD98.INI", "expandmd98.mix",
                  "ECH01.sav"):
            p = C.GAME / n
            want = basemap.get(n, {}).get("sha256")
            got = L.sha256_file(p) if p.is_file() else None
            checks.append({"check": "byte_identical_" + n, "sha256": got,
                           "expected": want, "present": p.is_file(),
                           "pass": (got == want)})
        for n in ("ra2forge_install.json", "ra2forge_install.json.seal"):
            p = C.GAME / n
            checks.append({"check": "no_" + n, "present": p.is_file(),
                           "pass": not p.is_file()})
        sink.step("byte_checks", checks=checks,
                  all_pass=all(c["pass"] for c in checks))

        v = C.v12_cmd(sink, "verify_final_proof",
                      ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_final_proof_exit", exit_code=v["exit_code"])

        ok = bool(d["identical_tree"]
                  and all(c["pass"] for c in checks)
                  and v["exit_code"] == 0)
        sink.step("restore_proof_result", ok=ok,
                  identical_tree=d["identical_tree"],
                  all_byte_checks_pass=all(c["pass"] for c in checks),
                  verify_exit=v["exit_code"])
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-5000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

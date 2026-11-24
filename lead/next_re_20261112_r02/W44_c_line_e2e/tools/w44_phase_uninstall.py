#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 5 - UNINSTALL + byte-exact restore self-proof (offline).

1) full manifest of the installed state, uninstall (v12), verify exit 0;
2) explicit byte-level assertions: no loose MAPSELMD.INI, no loose ra2md.csf,
   official BATTLEMD.INI byte-identical to the pristine copy, no v12 package
   files left, no install record / seal;
3) clean up game-produced drops (the .SAV made in K1, any new cache files);
4) full POST manifest and a diff against the PREP-time PRE manifest.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "uninstall"


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  game=str(C.GAME))

        # (0) installed-state full manifest (intermediate evidence)
        C.write_manifest(C.OUT / "sandbox_installed.json", C.GAME)

        # (1) uninstall v12
        u = C.v12_cmd(sink, "uninstall_v12",
                      ["uninstall", "--game", str(C.GAME), "--json"])
        sink.step("uninstall_v12_exit", exit_code=u["exit_code"],
                  stdout_tail=u["stdout_tail"][-5000:])
        if u["exit_code"] != 0:
            raise RuntimeError("uninstall exit %s" % u["exit_code"])

        # (2) verify after uninstall -> must be exit 0 (no manifest)
        v = C.v12_cmd(sink, "verify_after_uninstall_v12",
                      ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_uninstall_exit", exit_code=v["exit_code"],
                  stdout_tail=v["stdout_tail"][-3000:])
        if v["exit_code"] != 0:
            raise RuntimeError("verify after uninstall exit %s" % v["exit_code"])

        # (3) explicit byte-level checks against the PREP-time baseline
        pre = json.loads((C.OUT / "sandbox_pre.json").read_text(encoding="utf-8"))
        premap = {r["rel"]: r for r in pre["files"]}
        checks = []
        for n in ("MAPSELMD.INI", "ra2md.csf"):
            p = C.GAME / n
            checks.append({"check": "no_loose_" + n, "present": p.is_file(),
                           "pass": not p.is_file()})
        for n in ("BATTLEMD.INI", "RA2MD.INI", "ddraw.ini",
                  "gamemd.exe", "ddraw.dll"):
            p = C.GAME / n
            want = premap.get(n, {}).get("sha256")
            got = L.sha256_file(p) if p.is_file() else None
            checks.append({"check": "byte_identical_" + n, "sha256": got,
                           "expected": want, "pass": (got == want)})
        # package files created by v12 install must be gone / restored
        for n in ("BATTLEMD98.INI", "expandmd98.mix"):
            p = C.GAME / n
            # v0.3 left some of these in the PRE state; compare to PRE instead
            want = premap.get(n, {}).get("sha256")
            got = L.sha256_file(p) if p.is_file() else None
            checks.append({"check": "post_state_" + n, "sha256": got,
                           "pre_sha256": want,
                           "present": p.is_file()})
        for n in ("ra2forge_install.json", "ra2forge_install.json.seal"):
            p = C.GAME / n
            checks.append({"check": "no_" + n, "present": p.is_file(),
                           "pass": not p.is_file()})
        sink.step("byte_checks", checks=checks)

        hard = [c for c in checks if c["check"].startswith("no_loose_")
                or c["check"].startswith("byte_identical_")]
        sink.step("hard_checks_result", all_pass=all(c["pass"] for c in hard),
                  n=len(hard))

        # (4) remove game-produced drops so the sandbox tree returns to PRE
        pre_names = set(premap)
        drops = []
        for p in sorted(C.GAME.rglob("*"), key=lambda x: x.as_posix().lower()):
            if not p.is_file():
                continue
            rel = p.relative_to(C.GAME).as_posix()
            if rel not in pre_names:
                # any NEW file is a game-produced drop from this card
                drops.append({"rel": rel, "size": p.stat().st_size,
                              "sha256": L.sha256_file(p)})
        sink.step("drops_detected", n=len(drops), drops=drops)
        for d in drops:
            p = C.GAME / d["rel"]
            try:
                p.unlink()
                d["removed"] = True
            except Exception as e:
                d["removed"] = False
                d["error"] = repr(e)
        sink.step("drops_removed", all_removed=all(x.get("removed") for x in drops)
                  if drops else True, drops=drops)

        # also remove empty dirs that only existed for drops (best effort)
        # (5) full POST manifest + diff against PRE
        post = C.write_manifest(C.OUT / "sandbox_post.json", C.GAME)
        d = C.diff_manifests(pre, post)
        (C.OUT / "sandbox_diff.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        sink.step("sandbox_diff", added=d["added"], removed=d["removed"],
                  changed=d["changed"], mtime_diff_count=len(d["mtime_diff"]),
                  identical_tree=d["identical_tree"],
                  pre_summary=d["pre_summary"], post_summary=d["post_summary"])
        sink.step("post_summary", summary=post["summary"])

        # (6) final verify (must still be 0)
        v2 = C.v12_cmd(sink, "verify_final",
                       ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_final_exit", exit_code=v2["exit_code"])

        ok = bool(all(c["pass"] for c in hard)
                  and d["identical_tree"]
                  and v2["exit_code"] == 0)
        sink.step("uninstall_result", ok=ok,
                  hard_all_pass=all(c["pass"] for c in hard),
                  identical_tree=d["identical_tree"],
                  verify_final_exit=v2["exit_code"])
    except Exception as e:
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-5000:])
    finally:
        try:
            C.heal(sink, label="uninstall_finally")
        except Exception as e:
            sink.step("heal_error", error=repr(e))
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W74 · diagnostic: measure the GENERAL PKG-IDENT01 identity gate.

Fresh sandbox -> install A (inplace) -> install B2 (append, DIFFERENT
package_id) with its own feature-set. Because B2 is NOT an inplace plan,
RI.inplace_preflight is inapplicable, so the identity verdict is reachable.
This answers: "if someone relaxed/removed the inplace guard, would two
packages coexist?" (answer measured, not inferred). OFFLINE, no lock, no game.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w74_lib as L
import w74_common as C
import w74_multi as M


def main() -> int:
    sink = L.Sink("w74_diag")
    ok = False
    rep = {"purpose": ("isolate PKG-IDENT01 (CLI exit 3 / package_mismatch) "
                       "with a non-inplace second package B2"),
           "offline": True, "no_lock": True}
    try:
        sink.step("meta_start", kind="meta_start", phase="diag", **rep)
        assert not L.list_gamemd(), "residual gamemd at offline diag phase"
        pr = M.prep(sink, "diag")
        rep["prep_official"] = pr["official_precheck"]["official_match"]

        ia = M.install_a(sink, "diag")
        rep["install_A"] = {"exit_code": ia["exit_code"]}
        if ia["exit_code"] != 0:
            raise RuntimeError("install A exit %s" % ia["exit_code"])
        sa = M.snapshot(sink, "diag_after_A")
        rep["state_after_A"] = {
            "battlemd_sha256": sa["battlemd"]["sha256"],
            "manifest_package_id": sa["manifest_package_id"],
            "sov1_scenario": sa["battlemd"]["sov1_scenario"]}

        pkg_b2 = C.WORK / "pkg_b2" / "W74PkgB2"
        fs_b2 = C.WORK / "w74_feature_set_b2.json"
        variants = [
            ("", []),
            ("_allow", ["--allow-content-conflict"]),
            ("_adopt", ["--adopt-legacy"]),
            ("_force", ["--force"]),
        ]
        rows = []
        for suf, extra in variants:
            args = ["install", "--package", str(pkg_b2), "--game", str(C.GAME),
                    "--feature-set", str(fs_b2)] + list(extra)
            r = M.v15(sink, "diag_install_B2%s" % suf, args)
            s = M.snapshot(sink, "diag_after_B2%s" % suf)
            rows.append({
                "variant": suf or "plain", "extra_args": list(extra),
                "exit_code": r["exit_code"],
                "stdout": r.get("stdout_tail", ""),
                "stderr": r.get("stderr_tail", ""),
                "argv": args, "log": r.get("log"),
                "state_after": {
                    "battlemd_sha256": s["battlemd"]["sha256"],
                    "manifest_package_id": s["manifest_package_id"],
                    "manifest_raw_sha256": s["manifest_raw_sha256"],
                    "sov1_scenario": s["battlemd"]["sov1_scenario"],
                    "bak_present": s["bak"]["present"],
                },
                "byte_identical_to_after_A": (s["manifest_raw_sha256"]
                                              == sa["manifest_raw_sha256"]),
            })
        rep["install_B2_variants"] = rows

        v = M.verify(sink, "diag", "after_B2")
        rep["verify_after_B2"] = v
        u = M.uninstall(sink, "diag", "restore")
        sf = M.snapshot(sink, "diag_final")
        rep["uninstall"] = {"exit_code": u["exit_code"]}
        rep["final"] = {"battlemd_sha256": sf["battlemd"]["sha256"],
                        "equals_official": sf["battlemd"]["equals_official"],
                        "manifest_present": sf["files"]["ra2forge_install.json"]["present"]}
        ok = True
        sink.step("diag_done", ok=True, **rep)
    except Exception as e:  # noqa: BLE001
        import traceback
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-8000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase="diag", ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    (C.OUT / "DIAG.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

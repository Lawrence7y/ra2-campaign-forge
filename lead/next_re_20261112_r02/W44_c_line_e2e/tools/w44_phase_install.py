#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W44 phase 3 - INSTALL into the sandbox (offline).

Per W27 CAMPAIGN_LIVE.md section 2: uninstall the pre-existing v0.3 package,
verify, install the new package (with --allow-content-conflict for the two
official maps restored by the old uninstall), verify exit 0.
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w44_lib as L
import w44_common as C

TAG = "install"


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  package=str(C.PKG), game=str(C.GAME))

        # (1) verify the pre-existing v0.3 record
        v0 = C.v12_cmd(sink, "verify_v03", ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_v03_exit", exit_code=v0["exit_code"])

        # (2) uninstall old v0.3 (W27 §2 flow)
        u = C.v12_cmd(sink, "uninstall_v03", ["uninstall", "--game", str(C.GAME), "--json"])
        sink.step("uninstall_v03_exit", exit_code=u["exit_code"],
                  stdout_tail=u["stdout_tail"][-3000:])
        if u["exit_code"] != 0:
            raise RuntimeError("v0.3 uninstall exit %s" % u["exit_code"])

        # (3) verify after uninstall (no manifest -> exit 0)
        v1 = C.v12_cmd(sink, "verify_after_uninstall_v03",
                       ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_v03_exit", exit_code=v1["exit_code"])

        # (4) install the new v12 package WITHOUT the flag first (W27 §2
        #     reproduced the preflight content-conflict refusal)
        i0 = C.v12_cmd(sink, "install_new_plain",
                       ["install", "--package", str(C.PKG), "--game", str(C.GAME)])
        sink.step("install_new_plain_exit", exit_code=i0["exit_code"],
                  stdout_tail=i0["stdout_tail"][-2000:])

        if i0["exit_code"] == 0:
            sink.step("install_new_plain_succeeded", note="no content conflict this run")
        else:
            # (5) release ONLY definite content conflicts
            i1 = C.v12_cmd(sink, "install_new_allow",
                           ["install", "--package", str(C.PKG), "--game", str(C.GAME),
                            "--allow-content-conflict"])
            sink.step("install_new_allow_exit", exit_code=i1["exit_code"],
                      stdout_tail=i1["stdout_tail"][-3000:])
            if i1["exit_code"] != 0:
                raise RuntimeError("install --allow-content-conflict exit %s"
                                   % i1["exit_code"])

        # (6) verify after install -> must be exit 0
        v2 = C.v12_cmd(sink, "verify_after_install",
                       ["verify", "--game", str(C.GAME), "--json"])
        sink.step("verify_after_install_exit", exit_code=v2["exit_code"],
                  stdout_tail=v2["stdout_tail"][-4000:])
        if v2["exit_code"] != 0:
            raise RuntimeError("verify after install exit %s" % v2["exit_code"])

        # (7) record the install record + which files are tracked
        rec = C.GAME / "ra2forge_install.json"
        if rec.is_file():
            sink.step("install_record", size=rec.stat().st_size,
                      sha256=L.sha256_file(rec),
                      text=rec.read_text(encoding="utf-8", errors="replace")[:6000])
        for n in ("MAPSELMD.INI", "ra2md.csf", "BATTLEMD98.INI",
                  "BATTLEMD.INI", "ECH01.MAP", "ECH02.MAP", "expandmd98.mix"):
            p = C.GAME / n
            sink.step("installed_file", file=n, present=p.is_file(),
                      size=p.stat().st_size if p.is_file() else None,
                      sha256=L.sha256_file(p) if p.is_file() else None)
        ok = True
        sink.step("install_result", ok=ok)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W40 · extra LIVE diagnostics D (bad magic) and E (override visible label).

D: 4-byte bad-magic loose CSF -> verifies W29's 0x734799 -> 0x6BD85A branch.
E: full clone with GUI:SinglePlayer's value replaced by our marker -> verifies
   that the loose CSF actually changes what the UI RENDERS.

Reuses w40_live.run_one (same WMI launch / step0 gate / self-heal / finally).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402
import w40_live as W  # noqa: E402

OUT = L.OUT
VAR_D = OUT / "ra2md.csf.badmagic"
VAR_E = OUT / "ra2md.csf.override"
MARK = "W40_CSF_LIVE_OK_20261113"


def main() -> int:
    meta = L.Sink("w40_extra_meta")
    meta.step("card_start", kind="meta_start", card="W40_csf_live_extra",
              purpose="sharpen the two boundaries: bad magic vs label completeness; UI render proof",
              lock_before=L.LOCK.read_text(encoding="utf-8") if L.LOCK.is_file() else None)
    results = []
    try:
        L.lock_claim("w40-extra", "W40 extra diagnostics D/E running (2 serial instances)")
        meta.step("lock_claimed", owner="w40-extra",
                  lock_text=L.LOCK.read_text(encoding="utf-8"))
        results.append(W.run_one(
            "w40_D_badmagic", VAR_D, False,
            ["Unable to initialize", "ra2.csf", "XXXX", "MISSING"], meta))
        if any("STEP0_ABORT" in str(r.get("fatal", "")) for r in results):
            raise RuntimeError("STEP0_ABORT_DESKTOP_BLOCKED (extra stopped)")
        results.append(W.run_one(
            "w40_E_override", VAR_E, False,
            [MARK, "GUI:SinglePlayer", "MISSING", "MISSING:"], meta))
    except Exception as e:
        meta.step("FATAL", error=repr(e), traceback=__import__("traceback").format_exc()[-4000:])
    finally:
        heal = []
        for r in L.list_gamemd():
            try:
                L.close_game(r["pid"], None, meta)
                heal.append({"pid": r["pid"], "closed": True})
            except Exception as e:
                heal.append({"pid": r["pid"], "error": repr(e)})
        try:
            if W.CSF_LOOSE.is_file():
                W.CSF_LOOSE.unlink()
        except Exception as e:
            heal.append({"csf_remove_error": repr(e)})
        try:
            if W.BATTLE98_ASBUILT.is_file():
                W.BATTLE98.write_bytes(W.BATTLE98_ASBUILT.read_bytes())
        except Exception as e:
            heal.append({"battle98_error": repr(e)})
        try:
            heal.append({"restore_configs": L.restore_configs(meta)})
        except Exception as e:
            heal.append({"restore_configs_error": repr(e)})
        final = {
            "gamemd_residual": L.list_gamemd(),
            "loose_ra2md_csf_present": W.CSF_LOOSE.is_file(),
            "RA2MD_INI_sha256": L.sha256_file(W.GAME / "RA2MD.INI"),
            "ddraw_ini_sha256": L.sha256_file(W.GAME / "ddraw.ini"),
            "BATTLEMD98_INI_sha256": L.sha256_file(W.BATTLE98),
        }
        meta.step("final_self_heal", heal=heal, **final)
        meta.step("meta_end", kind="meta_end", card="W40_csf_live_extra",
                  results=[{k: r.get(k) for k in ("tag", "outcome", "exit_code",
                                                  "fatal", "natural_exit",
                                                  "dialog", "pid")} for r in results],
                  **final)
        L.lock_restore_lead()
        meta.step("lock_restored", owner="lead",
                  lock_text=L.LOCK.read_text(encoding="utf-8"))
        meta.close()

    (OUT / "live_extra_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8")
    print(json.dumps([{k: r.get(k) for k in
                       ("tag", "outcome", "exit_code", "natural_exit",
                        "fatal", "pid", "dialog")} for r in results],
                     ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

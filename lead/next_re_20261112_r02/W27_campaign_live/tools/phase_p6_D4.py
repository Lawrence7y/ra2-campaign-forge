#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P6 DIAGNOSTIC D4 (sandbox only, restored byte-exactly).

Changes the appended battle id in BATTLEMD98.INI from RA2F1 to YURI1
(the third official YR campaign id; this install's loose BATTLEMD.INI has
no YURI1 entry) to test whether GUI:CampaignMenu keys off recognised
battle ids rather than Description/CSF. If a third badge appears, click it
and observe whether our A1 map starts; that would be Q1/Q2 evidence on an
appended campaign without hijacking SOV1.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

INI = L.GAME / "BATTLEMD98.INI"
ORIG = L.OUT / "BATTLEMD98.INI.asbuilt"
DIAG = L.OUT / "BATTLEMD98.INI.D4_yuri1"


def main():
    sink = L.Sink("p6_D4_yuri1")
    pid = hwnd = hproc = None
    try:
        raw = INI.read_bytes()
        ORIG.write_bytes(raw)
        mod = raw.replace(b"15=RA2F1", b"15=YURI1").replace(b"[RA2F1]", b"[YURI1]")
        if mod == raw or b"YURI1" not in mod:
            raise RuntimeError("D4 replacement failed")
        INI.write_bytes(mod)
        DIAG.write_bytes(mod)
        sink.step("D4_setup", original_sha256=L.sha256_file(ORIG),
                  modified_sha256=L.sha256_file(INI), bytes=len(mod),
                  note="sandbox-only diagnostic variant")
        pre = L.list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("residual gamemd before launch; STOP")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        hproc = L.open_proc(pid)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 120:
            if L.find_btn(pid, "GUI:SinglePlayer"):
                break
            time.sleep(2.0)
        L.force_foreground(hwnd)
        cb = L.rpm(hproc, 0x00A83D08, 4)
        sink.step("battle_table_count_D4",
                  count=int.from_bytes(cb, "little") if cb else None)
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="to_SP")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="to_CampaignMenu")
        cs = L.snap(pid, sink, "D4_campaign_menu")
        L.screenshot(sink, "p6_D4_campaign_menu", hwnd)
        r = L.memory_search(hproc, ["YURI1", "RA2F1", "W27LIVE", "MISSING:",
                                    "ECH01.MAP"], sink, "D4_memory")
        sink.step("D4_verdict_data",
                  static_controls=[{"rect": c["rect"], "text": c["text"]}
                                   for c in cs if c["cls"] == "Static"],
                  visible_buttons=[c["text"] for c in cs
                                   if c["cls"] == "Button" and c["visible"]],
                  yuri1_ascii=r["hits"]["YURI1|ascii"]["count"],
                  ra2f1_ascii=r["hits"]["RA2F1|ascii"]["count"])
        # try clicking below the two badges in case a third badge exists
        L.real_mouse_click(sink, "D4_click_below_badges", 210, 470, wait_s=2.0)
        cs2 = L.snap(pid, sink, "D4_after_third_badge_click")
        L.screenshot(sink, "p6_D4_after_click", hwnd)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-4000:])
    finally:
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        try:
            L.close_game(pid, hwnd, sink)
        except Exception as e:
            sink.step("close_error", error=repr(e))
        try:
            if ORIG.is_file():
                INI.write_bytes(ORIG.read_bytes())
            sink.step("D4_restore", sha256=L.sha256_file(INI),
                      expected=L.sha256_file(ORIG),
                      byte_identical=INI.read_bytes() == ORIG.read_bytes())
        except Exception as e:
            sink.step("D4_restore_error", error=repr(e))
        try:
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_error", error=repr(e))
        try:
            sink.step("p6_done", gamemd_residual=L.list_gamemd())
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

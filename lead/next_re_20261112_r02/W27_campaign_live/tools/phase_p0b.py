#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P0b campaign-menu recon (one serial instance).

Discovers how the appended BATTLEMD98.INI campaign shows up on the
GUI:CampaignMenu screen: control-text enumeration (primary), hidden
ListBox item read (window message), read-only RPM string search, and a
passive screen capture used ONLY to target clicks (never as control text).
Also calibrates physical mouse clicks against the named GUI:SinglePlayer
button. No mission is started; ends with close + config restore.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

NEEDLES = ["W27LIVE", "W27 A1", "W27 A2", "ECH01.MAP", "ECH02.MAP",
           "RA2F1", "MISSING:", "DESC:ALL1", "DESC:SOV1", "DESC:YURI1",
           "ALL01umd.MAP", "SOV01umd.MAP", "YURI1"]


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", pid=pid,
                      elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return True
        time.sleep(2.0)
    raise RuntimeError("main menu timeout")


def main():
    sink = L.Sink("p0b_campaign_recon")
    pid = hwnd = hproc = None
    try:
        pre = L.list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("residual gamemd before launch; STOP per card")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        hproc = L.open_proc(pid)
        wait_main_menu(pid, sink)
        L.force_foreground(hwnd)
        L.screenshot(sink, "p0b_S0_main_menu", hwnd)
        cs0 = L.snap(pid, sink, "S0_main_menu")

        # --- calibrate physical mouse against a NAMED control -------------
        sp = next((c for c in cs0 if c["text"] == "GUI:SinglePlayer"), None)
        if sp:
            cx = (sp["rect"][0] + sp["rect"][2]) // 2
            cy = (sp["rect"][1] + sp["rect"][3]) // 2
            L.real_mouse_click(sink, "calibrate_GUI_SinglePlayer_screen_xy",
                               cx, cy, wait_s=1.5)
            cs1 = L.snap(pid, sink, "S1_after_physical_click",
                         "did a physical click at the named button's rect "
                         "navigate to the Single Player menu?")
            cal_ok = any(c["text"] == "GUI:NewCampaign" and c["visible"]
                         for c in cs1)
            sink.step("calibration_verdict", physical_mouse_click_worked=bool(cal_ok),
                      clicked_xy=[cx, cy],
                      sp_menu_buttons=[c["text"] for c in cs1
                                       if c["cls"] == "Button" and c["visible"]])
            if not cal_ok:
                L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.5,
                        label="fallback_BM_CLICK_SinglePlayer")
                L.snap(pid, sink, "S1_after_fallback")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
                label="S2_click_NewCampaign")
        cs2 = L.snap(pid, sink, "S2_campaign_menu", "GUI:CampaignMenu reached")
        L.screenshot(sink, "p0b_S2_campaign_menu", hwnd)
        L.all_listboxes(pid, hproc, sink, "S2_visible_boxes")

        # --- hidden ListBox 1109 explicitly (do not require visible) ------
        for c in cs2:
            if c["cls"] in ("ListBox", "ComboBox"):
                n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                sink.step("box_probe", hwnd=c["hwnd"], cls=c["cls"],
                          visible=c["visible"], rect=c["rect"],
                          lb_getcount=n,
                          lb_getcursel=int(L.smt(c["hwnd"], L.LB_GETCURSEL)))
                if n:
                    L.read_listbox(hproc, c["hwnd"], sink,
                                   "box_%s" % c["hwnd"])

        L.memory_search(hproc, NEEDLES, sink, "S2_campaign_memory")

        # --- keyboard navigation attempt (no data modification) ----------
        L.key(0x28, sink, "S3_key_down_1")     # VK_DOWN
        cs3 = L.snap(pid, sink, "S3_after_VK_DOWN")
        L.screenshot(sink, "p0b_S3_after_down", hwnd)
        L.memory_search(hproc, ["W27LIVE", "MISSING:"], sink,
                        "S3_after_down_memory")
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
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_error", error=repr(e))
        try:
            sink.step("p0b_done", gamemd_residual=L.list_gamemd())
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

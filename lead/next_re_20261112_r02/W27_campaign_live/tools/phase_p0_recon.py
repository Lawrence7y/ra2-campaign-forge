#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P0 recon launch (one game instance, serial).

Goal: discover the campaign-menu control vocabulary and whether the appended
BATTLEMD98.INI entry is visible/selectable, using ONLY window/control text
reads (plus read-only RPM for listbox item names and a bounded string search).
No mission is started in this phase. Ends with a full close + config restore.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

MARKERS = ["W27LIVE", "W27 A1", "W27 A2", "ECH01.MAP", "ECH02.MAP", "RA2F1"]
CAMPAIGN_BTN_CANDIDATES = [
    "GUI:Campaign", "GUI:NewCampaign", "GUI:CampaignSelect",
    "GUI:AlliedCampaign", "GUI:SovietCampaign", "GUI:YuriCampaign",
    "GUI:Allied", "GUI:Soviet", "GUI:Yuri", "GUI:PlayCampaign",
]


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", pid=pid,
                      elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return True
        time.sleep(2.0)
    raise RuntimeError("main menu timeout %ss" % timeout_s)


def main():
    sink = L.Sink("p0_recon")
    pid = None
    hwnd = None
    hproc = None
    try:
        pre = L.list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=pre,
                  n=len(pre))
        if pre:
            raise RuntimeError("residual gamemd before launch; STOP per card")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        hwnd = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        hwnd = hwnd or L.game_hwnd(pid)
        sink.step("game_window", pid=pid, hwnd=hwnd,
                  title=L.wtxt(hwnd) if hwnd else None,
                  cls=L.wcls(hwnd) if hwnd else None)
        hproc = L.open_proc(pid)
        sink.step("process_handle", pid=pid, hproc=bool(hproc),
                  counters=L.read_counters(hproc) if hproc else None)
        wait_main_menu(pid, sink)
        if hwnd:
            sink.step("force_foreground", result=L.force_foreground(hwnd))
        cs = L.snap(pid, sink, "S0_main_menu",
                    "main menu, no input yet")
        L.all_listboxes(pid, hproc, sink, "S0")
        L.memory_search(hproc, MARKERS, sink, "S0_main_menu_memory")

        # --- layer 1: Single Player -------------------------------------
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.5,
                label="S1_click_SinglePlayer")
        cs = L.snap(pid, sink, "S1_single_player_menu",
                    "after clicking GUI:SinglePlayer")
        L.all_listboxes(pid, hproc, sink, "S1")
        L.memory_search(hproc, MARKERS, sink, "S1_memory")

        # --- layer 2: campaign entry ------------------------------------
        found = None
        for name in CAMPAIGN_BTN_CANDIDATES:
            h = L.find_btn(pid, name)
            if h:
                found = name
                break
        sink.step("campaign_button_discovery", candidates=CAMPAIGN_BTN_CANDIDATES,
                  found=found,
                  all_button_texts=[c["text"] for c in cs
                                    if c["cls"] == "Button" and c["text"]])
        if found:
            L.click(pid, found, sink, wait_s=1.5,
                    label="S2_click_" + found)
            cs2 = L.snap(pid, sink, "S2_campaign_screen",
                         "after clicking " + found)
            L.all_listboxes(pid, hproc, sink, "S2")
            for b in L.all_listboxes(pid, hproc, sink, "S2_detail"):
                if b["cls"] == "ListBox":
                    L.read_listbox(hproc, b["hwnd"], sink,
                                   "S2_" + str(b["hwnd"]))
            L.memory_search(hproc, MARKERS, sink, "S2_memory")
        else:
            # dump every visible button text so a later phase can use it
            sink.step("S2_skipped", reason="no campaign-named button found",
                      visible_buttons=[c["text"] for c in cs
                                       if c["cls"] == "Button" and c["visible"]])

        # --- optional layer 3: try GUI:LoadGame from SP menu -------------
        # (only to learn the save/load control vocabulary; no save performed)
        # back out first with Escape
        L.key(L.VK_ESCAPE, sink, "S3_escape_back")
        L.snap(pid, sink, "S3_after_escape")
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
            sink.step("p0_done", gamemd_residual=L.list_gamemd())
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

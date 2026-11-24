#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P1a campaign-list exploration (one serial instance).

Tries, in order, to reach the appended RA2F1 campaign from the
GUI:CampaignMenu screen. Each attempt logs the control text / window title,
the counters, a screenshot (targeting only) and a bounded read-only memory
search for the A1 map marker "W27 A1". Stops as soon as our A1 map is loaded
(W27 A1 present in the engine's memory) or the process leaves the menus.
No crash-restart: this phase always closes its own instance at the end.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

A1_MARK = ["W27 A1", "W27LIVE A1"]
BAR_CENTERS_LOGICAL = [
    (477, 157), (477, 189), (477, 221), (477, 253),
    (477, 285), (477, 317), (477, 349),
]
BADGE_CENTERS_LOGICAL = [(210, 85), (210, 285)]   # Static 1770 / 1772


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2))
            return
        time.sleep(2.0)
    raise RuntimeError("main menu timeout")


def state(pid, hproc, sink, label):
    cs = L.snap(pid, sink, "state_" + label)
    counters = L.read_counters(hproc) if hproc else None
    vis = [c["text"] for c in cs if c["visible"] and c["text"]]
    sink.step("quick_state", label=label, counters=counters,
              visible_control_texts=vis)
    return cs, counters, vis


def check_a1(hproc, sink, label):
    r = L.memory_search(hproc, A1_MARK, sink, "probe_" + label,
                        cap_bytes=384 << 20)
    n = sum(v["count"] for v in r["hits"].values())
    sink.step("a1_marker_check", label=label, total_hits=n,
              per_encoding={k: v["count"] for k, v in r["hits"].items()})
    return n > 0


def main():
    sink = L.Sink("p1a_explore")
    pid = hwnd = hproc = None
    a1_found = False
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
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="to_SP")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=1.8, label="to_CampaignMenu")
        state(pid, hproc, sink, "S2_baseline")
        L.screenshot(sink, "p1a_S2_baseline", hwnd)

        # attempt 1: GUI:Back / 上一頁 (paging?)
        L.click(pid, "GUI:Back", sink, wait_s=1.5, label="A1_click_GUI_Back")
        cs, cnt, vis = state(pid, hproc, sink, "after_GUI_Back")
        L.screenshot(sink, "p1a_after_GUI_Back", hwnd)
        at_sp = any(t == "GUI:NewCampaign" for t in vis)
        sink.step("paging_verdict", back_returned_to_SP_menu=bool(at_sp),
                  visible=vis)
        if at_sp:
            L.click(pid, "GUI:NewCampaign", sink, wait_s=1.8,
                    label="reenter_CampaignMenu")
            state(pid, hproc, sink, "reentered_CampaignMenu")

        # attempt 2: keyboard paging (VK_DOWN / VK_UP / VK_RETURN)
        for i, vk in enumerate([0x28, 0x28, 0x28, 0x26, 0x0D]):
            L.key(vk, sink, "kbd_%d_vk_%d" % (i, vk))
            cs, cnt, vis = state(pid, hproc, sink, "kbd_%d" % i)
            L.screenshot(sink, "p1a_kbd_%d" % i, hwnd)
            if any(t in ("GUI:Briefing", "GUI:Play", "GUI:StartGame",
                         "GUI:ResumeMission") for t in vis):
                sink.step("keyboard_nav_left_menus", visible=vis)
                break

        # attempt 3: physical clicks on the paged list bars
        for i, (x, y) in enumerate(BAR_CENTERS_LOGICAL):
            L.real_mouse_click(sink, "bar_%d" % i, x, y, wait_s=1.0)
            cs, cnt, vis = state(pid, hproc, sink, "bar_%d" % i)
            if check_a1(hproc, sink, "bar_%d" % i):
                a1_found = True
                L.screenshot(sink, "p1a_A1_FOUND_bar_%d" % i, hwnd)
                break
            if any(t in ("GUI:Briefing", "GUI:Play", "GUI:StartGame",
                         "GUI:ResumeMission") for t in vis):
                L.screenshot(sink, "p1a_newscreen_bar_%d" % i, hwnd)
                sink.step("bar_click_changed_screen", bar=i, visible=vis)
                if check_a1(hproc, sink, "bar_%d_newscreen" % i):
                    a1_found = True
                    break
                # return to campaign menu via GUI:Back if present
                if L.find_btn(pid, "GUI:Back"):
                    L.click(pid, "GUI:Back", sink, wait_s=1.2,
                            label="bar_%d_recover_back" % i)

        # attempt 4: physical clicks on the two campaign badges
        if not a1_found:
            for i, (x, y) in enumerate(BADGE_CENTERS_LOGICAL):
                L.real_mouse_click(sink, "badge_%d" % i, x, y, wait_s=1.2)
                cs, cnt, vis = state(pid, hproc, sink, "badge_%d" % i)
                L.screenshot(sink, "p1a_badge_%d" % i, hwnd)
                if check_a1(hproc, sink, "badge_%d" % i):
                    a1_found = True
                    break
                if any(t in ("GUI:Briefing", "GUI:Play", "GUI:StartGame",
                             "GUI:ResumeMission") for t in vis):
                    sink.step("badge_click_changed_screen", badge=i, visible=vis)
                    break

        sink.step("explore_conclusion", a1_mission_loaded=a1_found)
        L.memory_search(hproc, ["W27 A1", "W27 A2", "W27LIVE", "RA2F1",
                                "ECH01.MAP", "ECH02.MAP"], sink,
                        "final_memory")
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
            sink.step("p1a_done", gamemd_residual=L.list_gamemd(),
                      a1_mission_loaded=a1_found)
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

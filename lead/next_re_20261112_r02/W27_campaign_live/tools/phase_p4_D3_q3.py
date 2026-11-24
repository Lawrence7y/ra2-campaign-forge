#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P4: DIAGNOSTIC D3 + Q3 cross-process save/load (sandbox only).

D3: in the sandbox ONLY, point [SOV1] Scenario at ECH02.MAP (the A2 map)
and start it directly. This discriminates:
  - loads OK  => the A2 map file is fine; P3's "Unable to start selected map"
                came from the NextScenario/chain resolution, not the map.
  - fails     => the map itself is not engine-loadable.
If it loads, Q3 is exercised on the DLC map: in-game save -> record file
(name/size/sha256) -> complete process exit with residual 0 -> relaunch ->
GUI:LoadSavedGame -> load -> compare control texts / frame / screen.

All observations: window/control text, window title, elapsed time,
read-only RPM counters, bounded read-only RPM string search, passive
screenshots. No save-file edits, no memory writes, no injection.
BATTLEMD.INI restored byte-exactly at the end; configs restored after
each instance.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_lib as L  # noqa: E402

BATTLE = L.GAME / "BATTLEMD.INI"
BATTLE_ORIG = L.OUT / "BATTLEMD.INI.asbuilt"
BATTLE_D3 = L.OUT / "BATTLEMD.INI.D3_sov1_ech02"
MARKERS = ["W27LIVE", "W27 A2", "W27 A1", "ECH02.MAP", "ECH01.MAP",
           "MISSING:"]


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2))
            return
        time.sleep(2.0)
    raise RuntimeError("main menu timeout")


def screen(pid, hproc, sink, label):
    cs = L.controls(pid)
    cnt = L.read_counters(hproc) if hproc else None
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    sink.step("screen", label=label, counters=cnt, visible_control_texts=vis,
              all_controls=[{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"],
                             "id": c["ctrl_id"], "hwnd": c["hwnd"]} for c in cs])
    return cs, cnt, vis


def launch_one(sink, tag):
    pre = L.list_gamemd()
    sink.step("pre_launch_guard", tag=tag, gamemd_processes=pre, n=len(pre))
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
    hproc = L.open_proc(pid)
    wait_main_menu(pid, sink)
    L.force_foreground(hwnd)
    sink.step("instance_ready", tag=tag, pid=pid, hwnd=hwnd,
              title=L.wtxt(hwnd) if hwnd else None)
    return pid, hwnd, hproc


def finish_one(sink, tag, pid, hwnd, hproc):
    try:
        if hproc:
            L.k32.CloseHandle(hproc)
    except Exception:
        pass
    steps = L.close_game(pid, hwnd, sink)
    sink.step("instance_closed", tag=tag, steps=steps,
              all_gamemd_residual=L.list_gamemd())
    L.restore_configs(sink)


def start_campaign(pid, hproc, sink, tag):
    L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
            label=tag + "_click_SinglePlayer")
    L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
            label=tag + "_click_NewCampaign")
    screen(pid, hproc, sink, tag + "_campaign_menu")
    L.real_mouse_click(sink, tag + "_click_SOVIET_badge", 210, 285, wait_s=2.5)
    L.key(0x0D, sink, tag + "_Enter_skip_movie_1")
    L.key(0x0D, sink, tag + "_Enter_skip_movie_2")
    # poll up to 90 s for either in-game (frame advancing) or an error dialog
    t0 = time.monotonic()
    last = None
    while time.monotonic() - t0 < 90:
        cs, cnt, vis = screen(pid, hproc, sink, tag + "_wait_start")
        last = (cs, cnt, vis)
        if any("OK" in v for v in vis):
            sink.step(tag + "_map_error_dialog", visible=vis,
                      elapsed_s=round(time.monotonic() - t0, 2))
            L.screenshot(sink, tag + "_map_error", None)
            return "error_dialog", cs, cnt, vis
        if cnt and cnt.get("frame", 0) > 60:
            sink.step(tag + "_ingame", counters=cnt, visible=vis,
                      elapsed_s=round(time.monotonic() - t0, 2))
            L.screenshot(sink, tag + "_ingame", None)
            return "ingame", cs, cnt, vis
        time.sleep(1.5)
    sink.step(tag + "_start_timeout", elapsed_s=round(time.monotonic() - t0, 2))
    return "timeout", *(last or (None, None, []))


def main():
    sink = L.Sink("p4_D3_q3")
    pid = hwnd = hproc = None
    q3 = "未验证"
    d3 = "未验证"
    try:
        raw = BATTLE.read_bytes()
        BATTLE_ORIG.write_bytes(raw)
        old = b"Scenario=SOV01umd.MAP"
        new = b"Scenario=ECH02.MAP"
        sink.step("D3_setup_check", old_count=raw.count(old),
                  original_sha256=L.sha256_file(BATTLE), original_bytes=len(raw))
        if raw.count(old) != 1:
            raise RuntimeError("D3 expected exactly one SOV1 Scenario line")
        BATTLE.write_bytes(raw.replace(old, new))
        BATTLE_D3.write_bytes(BATTLE.read_bytes())
        sink.step("D3_file_written", sha256=L.sha256_file(BATTLE),
                  bytes=len(BATTLE.read_bytes()))

        before_all = L.save_inventory(sink, "pre_all_saves")

        # ---------------- INSTANCE 1: D3 + save ------------------------
        pid, hwnd, hproc = launch_one(sink, "J1")
        screen(pid, hproc, sink, "J1_S0_main_menu")
        state, cs, cnt, vis = start_campaign(pid, hproc, sink, "J1")
        d3 = ("A2 map loads directly (engine ok)" if state == "ingame"
              else "A2 map FAILED to start: " + state)
        sink.step("D3_verdict", verdict=d3, state=state, counters=cnt,
                  visible=vis)
        L.memory_search(hproc, MARKERS, sink, "J1_ingame_memory")

        if state == "ingame":
            # ---- Q3 step 1: save in-game -------------------------------
            before = L.save_inventory(sink, "J1_before_save")
            L.key(L.VK_ESCAPE, sink, "J1_Esc_open_ingame_menu")
            cs, cnt, vis = screen(pid, hproc, sink, "J1_esc_menu")
            L.screenshot(sink, "J1_esc_menu", None)
            if L.find_btn(pid, "GUI:SaveGame"):
                L.click(pid, "GUI:SaveGame", sink, wait_s=2.0,
                        label="J1_click_SaveGame")
            cs, cnt, vis = screen(pid, hproc, sink, "J1_save_dialog")
            L.screenshot(sink, "J1_save_dialog", None)
            for c in cs:
                if c["cls"] in ("ListBox", "ComboBox"):
                    n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                    sink.step("save_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                              rect=c["rect"], lb_getcount=n)
                    if n:
                        L.read_listbox(hproc, c["hwnd"], sink, "save_items")
                if c["cls"] == "Edit":
                    sink.step("save_dialog_edit", hwnd=c["hwnd"],
                              rect=c["rect"], ctrl_id=c["ctrl_id"])
            sv = [c for c in cs if c["cls"] == "Button" and c["visible"]
                  and c["text"] and c["text"] not in
                  ("GUI:Back", "GUI:MainMenu", "GUI:DeleteGame", "GUI:OK")]
            sink.step("save_dialog_visible_buttons",
                      buttons=[{"text": c["text"], "hwnd": c["hwnd"],
                                "rect": c["rect"]} for c in sv])
            # The save dialog needs a slot + a typed name before 儲存 works.
            # All of these are ordinary UI input (no save-file edits).
            boxes = [c for c in cs if c["cls"] == "ListBox"
                     and int(L.smt(c["hwnd"], L.LB_GETCOUNT)) > 0]
            if boxes:
                L.smt(boxes[0]["hwnd"], L.LB_SETCURSEL, 0)
                sink.step("save_select_slot", hwnd=boxes[0]["hwnd"], index=0)
                r = boxes[0]["rect"]
                L.real_mouse_click(sink, "save_click_first_slot",
                                   (r[0] + r[2]) // 2, r[1] + 10, wait_s=0.6)
            edits = [c for c in cs if c["cls"] == "Edit"]
            if edits:
                r = edits[0]["rect"]
                L.real_mouse_click(sink, "save_focus_name_field",
                                   (r[0] + r[2]) // 2, (r[1] + r[3]) // 2,
                                   wait_s=0.6)
                L.type_ascii(sink, "save_type_name", "W27Q3SAVE")
                L.wm_settext(sink, "save_wm_settext", edits[0]["hwnd"],
                             "W27Q3SAVE")
            if sv:
                L.click_hwnd(sv[0]["hwnd"], sink,
                             "J1_click_save_" + sv[0]["text"], wait_s=3.0)
            cs2, cnt2, vis2 = screen(pid, hproc, sink, "J1_after_save")
            L.screenshot(sink, "J1_after_save", None)
            after = L.save_inventory(sink, "J1_after_save_files")
            bmap = {x["name"]: x for x in before}
            added = [f for f in after if f["name"] not in bmap]
            changed = [f for f in after if f["name"] in bmap
                       and f["sha256"] != bmap[f["name"]]["sha256"]]
            sink.step("Q3_save_file", added=added, changed=changed,
                      before_n=len(before), after_n=len(after))
            if not (added or changed):
                sink.step("Q3_save_retry", note="still no save; click 儲存 again")
                if sv:
                    L.click_hwnd(sv[0]["hwnd"], sink,
                                 "J1_click_save_retry", wait_s=3.0)
                after = L.save_inventory(sink, "J1_after_save_retry")
                added = [f for f in after if f["name"] not in bmap]
                changed = [f for f in after if f["name"] in bmap
                           and f["sha256"] != bmap[f["name"]]["sha256"]]
                sink.step("Q3_save_file_retry", added=added, changed=changed)
            saved = None
            for f in (added + changed):
                src = L.GAME / f["name"]
                if src.is_file():
                    dst = L.OUT / ("save_" + f["name"])
                    dst.write_bytes(src.read_bytes())
                    sink.step("Q3_save_copied", src=str(src), dst=str(dst),
                              sha256=L.sha256_file(dst), size=dst.stat().st_size)
                    saved = {"name": f["name"], "sha256": f["sha256"],
                             "size": f["size"]}
                    break

            # ---------------- full exit ---------------------------------
            finish_one(sink, "J1", pid, hwnd, hproc)
            pid = hwnd = hproc = None
            sink.step("Q3_process_exit", residual=L.list_gamemd(),
                      note="完全退出，核对 gamemd 残留 0")

            # ---------------- INSTANCE 2: relaunch + load ---------------
            if saved:
                pid, hwnd, hproc = launch_one(sink, "J2")
                screen(pid, hproc, sink, "J2_S0_main_menu")
                L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                        label="J2_click_SinglePlayer")
                L.click(pid, "GUI:LoadSavedGame", sink, wait_s=2.5,
                        label="J2_click_LoadSavedGame")
                cs, cnt, vis = screen(pid, hproc, sink, "J2_load_dialog")
                L.screenshot(sink, "J2_load_dialog", None)
                load_box = None
                for c in cs:
                    if c["cls"] in ("ListBox", "ComboBox"):
                        n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                        sink.step("load_dialog_box", hwnd=c["hwnd"],
                                  cls=c["cls"], rect=c["rect"], n=n)
                        if n:
                            L.read_listbox(hproc, c["hwnd"], sink, "load_items")
                            load_box = c["hwnd"]
                if load_box:
                    n = int(L.smt(load_box, L.LB_GETCOUNT))
                    for i in range(n):
                        d = int(L.smt(load_box, L.LB_GETITEMDATA, i)) & 0xFFFFFFFF
                        nm = L.read_utf16_ptr(hproc, d) or ""
                        if saved["name"].lower().split(".")[0] in nm.lower():
                            L.smt(load_box, L.LB_SETCURSEL, i)
                            sink.step("Q3_load_selected", index=i, name=nm)
                            break
                lb = [c for c in cs if c["cls"] == "Button" and c["visible"]
                      and c["text"] in ("GUI:Load", "GUI:LoadGame")]
                if not lb:
                    lb = [c for c in cs if c["cls"] == "Button" and c["visible"]
                          and c["text"] and c["text"] not in
                          ("GUI:Back", "GUI:MainMenu", "GUI:DeleteGame")]
                sink.step("load_dialog_buttons",
                          buttons=[{"text": c["text"], "hwnd": c["hwnd"]}
                                   for c in lb])
                if lb:
                    L.click_hwnd(lb[0]["hwnd"], sink,
                                 "J2_click_load_" + lb[0]["text"], wait_s=4.0)
                # observe up to 90 s
                t0 = time.monotonic()
                in_game_evidence = False
                while time.monotonic() - t0 < 90:
                    c2, k2, v2 = screen(pid, hproc, sink, "J2_after_load")
                    if k2 and k2.get("frame", 0) > 30:
                        in_game_evidence = True
                        sink.step("Q3_load_ingame", counters=k2, visible=v2,
                                  elapsed_s=round(time.monotonic() - t0, 2))
                        break
                    if any("OK" in v for v in v2):
                        sink.step("Q3_load_error_dialog", visible=v2)
                        L.screenshot(sink, "J2_load_error", None)
                        break
                    time.sleep(1.5)
                L.screenshot(sink, "J2_after_load", None)
                m2 = L.memory_search(hproc, MARKERS, sink, "J2_loaded_memory")
                L.key(L.VK_ESCAPE, sink, "J2_Esc_ingame_menu_check")
                c3, k3, v3 = screen(pid, hproc, sink, "J2_esc_menu")
                L.screenshot(sink, "J2_esc_menu", None)
                sink.step("Q3_load_observation", in_game_evidence=in_game_evidence,
                          esc_menu_visible=v3,
                          save_name=saved["name"], save_sha256=saved["sha256"],
                          save_size=saved["size"],
                          markers={k: v["count"] for k, v in m2["hits"].items()})
                q3 = ("成立（D3 诊断变体）" if in_game_evidence else "未验证")
                finish_one(sink, "J2", pid, hwnd, hproc)
                pid = hwnd = hproc = None
            else:
                q3 = "未验证（无存档文件产生）"
        sink.step("p4_results", d3=d3, q3=q3)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        try:
            if pid:
                finish_one(sink, "finally", pid, hwnd, hproc)
        except Exception as e:
            sink.step("final_close_error", error=repr(e))
        try:
            if BATTLE_ORIG.is_file():
                BATTLE.write_bytes(BATTLE_ORIG.read_bytes())
            sink.step("D3_restore", sha256=L.sha256_file(BATTLE),
                      expected=L.sha256_file(BATTLE_ORIG),
                      byte_identical=BATTLE.read_bytes() == BATTLE_ORIG.read_bytes())
        except Exception as e:
            sink.step("D3_restore_error", error=repr(e))
        try:
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_error", error=repr(e))
        try:
            sink.step("p4_done", gamemd_residual=L.list_gamemd(),
                      d3=d3, q3=q3)
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

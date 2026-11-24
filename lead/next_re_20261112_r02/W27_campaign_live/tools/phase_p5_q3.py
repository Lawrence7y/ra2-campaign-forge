#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P5: Q3 cross-process save/load on the DLC A2 map (sandbox only).

Setup D3 (sandbox-only, restored at end): [SOV1] Scenario=ECH02.MAP.
Robust campaign start with badge-click retries and foreground enforcement.
Then: in-game save (ordinary UI input: select slot, type name, click 儲存),
record the SAV file (name/size/sha256, copy into out/), complete process exit
with residual-0 check, relaunch, GUI:LoadSavedGame, select the save, load,
and record control text / window title / counters / screen evidence.

No save-file or memory writes, no injection. All observations are
window/control text, window title, elapsed time, read-only RPM counters,
bounded read-only RPM string search, and passive screenshots.
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
MARKERS = ["W27LIVE", "W27 A2", "ECH02.MAP", "MISSING:"]


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
    sink.step("force_foreground", tag=tag, result=L.force_foreground(hwnd))
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


def start_campaign(pid, hwnd, hproc, sink, tag):
    L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
            label=tag + "_click_SinglePlayer")
    L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
            label=tag + "_click_NewCampaign")
    screen(pid, hproc, sink, tag + "_campaign_menu")
    # badge click with retries (physical mouse; calibrated in P0b)
    for attempt in range(4):
        sink.step("force_foreground", tag=tag, attempt=attempt,
                  result=L.force_foreground(hwnd))
        L.real_mouse_click(sink, tag + "_badge_click_%d" % attempt,
                           210, 285, wait_s=2.0)
        cs, cnt, vis = screen(pid, hproc, sink,
                              tag + "_after_badge_%d" % attempt)
        still_menu = any(v == "GUI:CampaignMenu" for v in vis)
        sink.step("badge_attempt", attempt=attempt, still_on_campaign_menu=still_menu,
                  visible=vis)
        if not still_menu:
            break
        # alternate slightly in case of a hit-test edge
        L.real_mouse_click(sink, tag + "_badge_click_alt_%d" % attempt,
                           200, 275, wait_s=1.5)
    L.key(0x0D, sink, tag + "_Enter_skip_movie_1")
    L.key(0x0D, sink, tag + "_Enter_skip_movie_2")
    t0 = time.monotonic()
    while time.monotonic() - t0 < 90:
        cs, cnt, vis = screen(pid, hproc, sink, tag + "_wait_start")
        if any("OK" in v for v in vis):
            sink.step(tag + "_map_error_dialog", visible=vis)
            L.screenshot(sink, tag + "_map_error", None)
            return "error_dialog", cs, cnt, vis
        if cnt and cnt.get("frame", 0) > 60:
            sink.step(tag + "_ingame", counters=cnt, visible=vis,
                      elapsed_s=round(time.monotonic() - t0, 2))
            L.screenshot(sink, tag + "_ingame", None)
            return "ingame", cs, cnt, vis
        time.sleep(1.5)
    sink.step(tag + "_start_timeout")
    return "timeout", None, None, []


def main():
    sink = L.Sink("p5_q3")
    pid = hwnd = hproc = None
    q3 = "未验证"
    saved = None
    try:
        raw = BATTLE.read_bytes()
        BATTLE_ORIG.write_bytes(raw)
        old = b"Scenario=SOV01umd.MAP"
        new = b"Scenario=ECH02.MAP"
        if raw.count(old) != 1:
            raise RuntimeError("expected exactly one SOV1 Scenario line")
        BATTLE.write_bytes(raw.replace(old, new))
        BATTLE_D3.write_bytes(BATTLE.read_bytes())
        sink.step("D3_setup", original_sha256=L.sha256_file(BATTLE_ORIG),
                  modified_sha256=L.sha256_file(BATTLE),
                  bytes=len(BATTLE.read_bytes()))
        before_all = L.save_inventory(sink, "pre_all_saves")

        # ---------------- INSTANCE 1: save -----------------------------
        pid, hwnd, hproc = launch_one(sink, "K1")
        screen(pid, hproc, sink, "K1_S0_main_menu")
        state, cs, cnt, vis = start_campaign(pid, hwnd, hproc, sink, "K1")
        sink.step("K1_start_state", state=state, counters=cnt, visible=vis)
        if state != "ingame":
            raise RuntimeError("could not get in-game for Q3: %s" % state)
        L.memory_search(hproc, MARKERS, sink, "K1_ingame_memory")

        before = L.save_inventory(sink, "K1_before_save")
        L.key(L.VK_ESCAPE, sink, "K1_Esc_open_ingame_menu")
        cs, cnt, vis = screen(pid, hproc, sink, "K1_esc_menu")
        L.screenshot(sink, "K1_esc_menu", None)
        L.click(pid, "GUI:SaveGame", sink, wait_s=2.0,
                label="K1_click_SaveGame")
        cs, cnt, vis = screen(pid, hproc, sink, "K1_save_dialog")
        L.screenshot(sink, "K1_save_dialog", None)
        for c in cs:
            if c["cls"] in ("ListBox", "ComboBox"):
                n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                sink.step("save_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                          rect=c["rect"], n=n)
                if n:
                    L.read_listbox(hproc, c["hwnd"], sink, "save_items")
        sv = [c for c in cs if c["cls"] == "Button" and c["visible"]
              and c["text"] == "GUI:Save"]
        boxes = [c for c in cs if c["cls"] == "ListBox"
                 and int(L.smt(c["hwnd"], L.LB_GETCOUNT)) > 0]
        edits = [c for c in cs if c["cls"] == "Edit"]
        sink.step("save_dialog_plan", save_buttons=[c["text"] for c in sv],
                  n_boxes=len(boxes), n_edits=len(edits))
        if boxes:
            L.smt(boxes[0]["hwnd"], L.LB_SETCURSEL, 0)
            r = boxes[0]["rect"]
            L.real_mouse_click(sink, "K1_click_first_slot",
                               (r[0] + r[2]) // 2, r[1] + 10, wait_s=0.6)
        if edits:
            r = edits[0]["rect"]
            L.real_mouse_click(sink, "K1_focus_name_field",
                               (r[0] + r[2]) // 2, (r[1] + r[3]) // 2,
                               wait_s=0.6)
            L.type_ascii(sink, "K1_type_save_name", "W27Q3SAVE")
            L.wm_settext(sink, "K1_wm_settext", edits[0]["hwnd"], "W27Q3SAVE")
        cs2, cnt2, vis2 = screen(pid, hproc, sink, "K1_after_name")
        L.screenshot(sink, "K1_after_name", None)
        if sv:
            L.click_hwnd(sv[0]["hwnd"], sink, "K1_click_GUI_Save", wait_s=3.0)
        cs3, cnt3, vis3 = screen(pid, hproc, sink, "K1_after_save")
        L.screenshot(sink, "K1_after_save", None)
        after = L.save_inventory(sink, "K1_after_save_files")
        bmap = {x["name"]: x for x in before}
        added = [f for f in after if f["name"] not in bmap]
        changed = [f for f in after if f["name"] in bmap
                   and f["sha256"] != bmap[f["name"]]["sha256"]]
        sink.step("Q3_save_file", added=added, changed=changed,
                  before_n=len(before), after_n=len(after))
        if not (added or changed):
            sink.step("Q3_save_retry", note="click GUI:Save once more")
            if sv:
                L.click_hwnd(sv[0]["hwnd"], sink, "K1_click_GUI_Save_retry",
                             wait_s=3.0)
            after = L.save_inventory(sink, "K1_after_save_retry")
            added = [f for f in after if f["name"] not in bmap]
            changed = [f for f in after if f["name"] in bmap
                       and f["sha256"] != bmap[f["name"]]["sha256"]]
            sink.step("Q3_save_file_retry", added=added, changed=changed)
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

        finish_one(sink, "K1", pid, hwnd, hproc)
        pid = hwnd = hproc = None
        sink.step("Q3_process_exit", residual=L.list_gamemd(),
                  note="完全退出，核对 gamemd 残留 0")

        # ---------------- INSTANCE 2: relaunch + load ------------------
        if saved:
            pid, hwnd, hproc = launch_one(sink, "K2")
            screen(pid, hproc, sink, "K2_S0_main_menu")
            L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                    label="K2_click_SinglePlayer")
            L.click(pid, "GUI:LoadSavedGame", sink, wait_s=2.5,
                    label="K2_click_LoadSavedGame")
            cs, cnt, vis = screen(pid, hproc, sink, "K2_load_dialog")
            L.screenshot(sink, "K2_load_dialog", None)
            for c in cs:
                if c["cls"] in ("ListBox", "ComboBox"):
                    n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                    sink.step("load_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                              rect=c["rect"], n=n)
                    if n:
                        L.read_listbox(hproc, c["hwnd"], sink, "load_items")
            lb = [c for c in cs if c["cls"] == "Button" and c["visible"]
                  and c["text"] in ("GUI:Load", "GUI:LoadGame")]
            sink.step("load_dialog_buttons", buttons=[c["text"] for c in lb])
            # select our save by item name (read-only listbox item names)
            selected = None
            for c in cs:
                if c["cls"] not in ("ListBox", "ComboBox"):
                    continue
                n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                for i in range(n):
                    d = int(L.smt(c["hwnd"], L.LB_GETITEMDATA, i)) & 0xFFFFFFFF
                    nm = L.read_utf16_ptr(hproc, d) or ""
                    if "W27Q3SAVE" in nm or saved["name"].lower().split(".")[0] in nm.lower():
                        L.smt(c["hwnd"], L.LB_SETCURSEL, i)
                        selected = {"index": i, "name": nm, "hwnd": c["hwnd"]}
                        break
                if selected:
                    break
            sink.step("Q3_load_selected", selected=selected,
                      target_save=saved["name"])
            if lb:
                L.click_hwnd(lb[0]["hwnd"], sink,
                             "K2_click_GUI_Load", wait_s=4.0)
            t0 = time.monotonic()
            in_game_evidence = False
            while time.monotonic() - t0 < 90:
                c2, k2, v2 = screen(pid, hproc, sink, "K2_after_load")
                if any("OK" in v for v in v2):
                    sink.step("Q3_load_error_dialog", visible=v2)
                    L.screenshot(sink, "K2_load_error", None)
                    break
                if k2 and k2.get("frame", 0) > 30:
                    in_game_evidence = True
                    sink.step("Q3_load_ingame", counters=k2, visible=v2,
                              elapsed_s=round(time.monotonic() - t0, 2))
                    break
                time.sleep(1.5)
            L.screenshot(sink, "K2_after_load", None)
            m2 = L.memory_search(hproc, MARKERS, sink, "K2_loaded_memory")
            L.key(L.VK_ESCAPE, sink, "K2_Esc_ingame_menu_check")
            c3, k3, v3 = screen(pid, hproc, sink, "K2_esc_menu")
            L.screenshot(sink, "K2_esc_menu", None)
            # is the copied save still byte-identical after load?
            dst = L.OUT / ("save_" + saved["name"])
            sink.step("Q3_load_observation", in_game_evidence=in_game_evidence,
                      esc_menu_visible=v3, counters=k3,
                      save_name=saved["name"], save_sha256=saved["sha256"],
                      save_size=saved["size"],
                      save_copy_sha256_after=L.sha256_file(dst) if dst.is_file() else None,
                      save_copy_matches=saved["sha256"] == (L.sha256_file(dst) if dst.is_file() else None),
                      markers={k: v["count"] for k, v in m2["hits"].items()})
            q3 = ("成立（D3 诊断变体）" if in_game_evidence else "未验证")
            finish_one(sink, "K2", pid, hwnd, hproc)
            pid = hwnd = hproc = None
        else:
            q3 = "未验证（没有产生存档文件）"
        sink.step("p5_results", q3=q3)
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
            sink.step("p5_done", gamemd_residual=L.list_gamemd(), q3=q3)
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

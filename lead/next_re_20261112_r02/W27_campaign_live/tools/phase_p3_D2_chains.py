#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · P3 DIAGNOSTIC D2 + Q2/Q3 chain test (NOT the as-built package).

D2 is the project's own documented one-line workaround
(docs/re/a3_campaign_install_runbook.md:53): in the SANDBOX ONLY, change
[SOV1] Scenario=SOV01umd.MAP -> Scenario=ECH01.MAP so the Soviet campaign
badge loads our DLC map in CAMPAIGN mode. This lets us exercise:
  Q2  NextScenario chain ECH01.MAP -> ECH02.MAP (A1 win -> A2)
  Q3  in-game save -> full process exit -> relaunch -> load save -> state

The as-built BATTLEMD98.INI is untouched; BATTLEMD.INI is restored
byte-exactly at the end and `verify` re-run. Every stage logs control text /
window title / elapsed time / counters / passive screenshots (as "畫面"
evidence) / bounded read-only RPM string search. No save-file edits, no
memory writes, no injection.

Two serial game instances (one for save, one for load); each is closed with
residual-0 check. Configs restored after each.
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
BATTLE_D2 = L.OUT / "BATTLEMD.INI.D2_sov1_ech01"

A1 = ["W27 A1", "W27LIVE A1"]
A2 = ["W27 A2", "W27LIVE A2"]
MAPS = ["ECH01.MAP", "ECH02.MAP"]


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return
        time.sleep(2.0)
    raise RuntimeError("main menu timeout")


def snap_counters(pid, hproc, sink, label):
    cs = L.controls(pid)
    counters = L.read_counters(hproc) if hproc else None
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    sink.step("screen", label=label, counters=counters,
              visible_control_texts=vis,
              all_controls=[{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"],
                             "id": c["ctrl_id"]} for c in cs])
    return cs, counters, vis


def poll(pid, hproc, sink, label, timeout_s, want_any=None, interval=1.0):
    """Poll control texts/counters until any wanted text appears."""
    t0 = time.monotonic()
    seen = []
    while time.monotonic() - t0 < timeout_s:
        cs, cnt, vis = snap_counters(pid, hproc, sink, label)
        seen.append({"t": round(time.monotonic() - t0, 2), "vis": vis,
                     "frame": (cnt or {}).get("frame"),
                     "mode": (cnt or {}).get("mode")})
        if want_any:
            hit = [w for w in want_any if any(w.lower() in (v or "").lower()
                                              for v in vis)]
            if hit:
                sink.step("poll_hit", label=label, hits=hit,
                          elapsed_s=round(time.monotonic() - t0, 2))
                return True, cs, cnt, vis
        time.sleep(interval)
    sink.step("poll_timeout", label=label, timeout_s=timeout_s,
              n_samples=len(seen), wanted=want_any)
    return False, None, None, []


def marker(hproc, sink, label, needles):
    r = L.memory_search(hproc, needles, sink, "marker_" + label,
                        cap_bytes=384 << 20)
    return {k: v["count"] for k, v in r["hits"].items()}


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
    return steps


def main():
    sink = L.Sink("p3_D2_chains")
    pid = hwnd = hproc = None
    results = {"q2": "未验证", "q3": "未验证"}
    try:
        # ---------------- D2 setup (sandbox only) ----------------------
        raw = BATTLE.read_bytes()
        BATTLE_ORIG.write_bytes(raw)
        old = b"Scenario=SOV01umd.MAP"
        new = b"Scenario=ECH01.MAP"
        sink.step("D2_setup_check", old_count=raw.count(old),
                  original_sha256=L.sha256_file(BATTLE),
                  original_bytes=len(raw))
        if raw.count(old) != 1:
            raise RuntimeError("D2 expected exactly one SOV1 Scenario line")
        modified = raw.replace(old, new)
        BATTLE.write_bytes(modified)
        BATTLE_D2.write_bytes(modified)
        sink.step("D2_file_written", sha256=L.sha256_file(BATTLE),
                  bytes=len(modified), note="sandbox-only diagnostic variant; "
                  "as-built BATTLEMD98.INI untouched")

        L.save_inventory(sink, "pre_all_saves")

        # ---------------- INSTANCE 1: Q2 + save ------------------------
        pid, hwnd, hproc = launch_one(sink, "I1_save")
        snap_counters(pid, hproc, sink, "I1_S0_main_menu")
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                label="I1_click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
                label="I1_click_NewCampaign")
        snap_counters(pid, hproc, sink, "I1_S2_campaign_menu")
        L.screenshot(sink, "p3_I1_campaign_menu", hwnd)

        # click Soviet badge (logical centre of Static 1772 rect)
        L.real_mouse_click(sink, "I1_click_SOVIET_badge", 210, 285, wait_s=3.0)
        L.screenshot(sink, "p3_I1_after_soviet_badge", hwnd)
        snap_counters(pid, hproc, sink, "I1_after_badge")

        # intro movie / briefing: skip movies with Enter, then poll for any
        # actionable visible button (not Back/MainMenu). Log every screen.
        L.key(0x0D, sink, "I1_Enter_skip_movie_1")
        L.key(0x0D, sink, "I1_Enter_skip_movie_2")
        ok, cs, cnt, vis = poll(
            pid, hproc, sink, "I1_wait_briefing", 45,
            want_any=["GUI:Play", "GUI:StartGame", "GUI:Continue",
                      "GUI:Briefing", "GUI:Brief", "GUI:ResumeMission"],
            interval=1.5)
        L.screenshot(sink, "p3_I1_briefing_or_later", hwnd)
        if not ok:
            # generic: any visible button other than Back/MainMenu
            for c in (L.controls(pid)):
                if (c["cls"] == "Button" and c["visible"] and c["text"]
                        and c["text"] not in ("GUI:Back", "GUI:MainMenu")):
                    ok = True
                    sink.step("I1_generic_actionable_button",
                              text=c["text"], hwnd=c["hwnd"])
                    cs = L.controls(pid)
                    break
            if not ok:
                L.key(0x0D, sink, "I1_Enter_again")
                ok, cs, cnt, vis = poll(
                    pid, hproc, sink, "I1_wait_briefing2", 60,
                    want_any=["GUI:Play", "GUI:StartGame", "GUI:Continue",
                              "GUI:Briefing", "GUI:Brief", "GUI:ResumeMission"],
                    interval=1.5)
                L.screenshot(sink, "p3_I1_briefing_or_later2", hwnd)

        # if a named start button exists, click it
        for name in ("GUI:Play", "GUI:StartGame", "GUI:Continue"):
            if L.find_btn(pid, name):
                L.click(pid, name, sink, wait_s=2.0,
                        label="I1_click_" + name)
                break
        else:
            # click the first visible non-Back button by hwnd
            cands = [c for c in (cs or []) if c["cls"] == "Button"
                     and c["visible"] and c["text"] not in ("GUI:Back",)]
            if cands:
                L.click_hwnd(cands[0]["hwnd"], sink,
                             "I1_click_visible_button_" + cands[0]["text"],
                             wait_s=2.0)

        # wait for in-game (frame advancing + A1 marker)
        L.screenshot(sink, "p3_I1_after_start", hwnd)
        snap_counters(pid, hproc, sink, "I1_after_start_click")
        t0 = time.monotonic()
        a1_seen = False
        while time.monotonic() - t0 < 90:
            cs, cnt, vis = snap_counters(pid, hproc, sink, "I1_waiting_A1")
            if cnt and cnt.get("frame", 0) > 30:
                m = marker(hproc, sink, "I1_A1", A1 + MAPS)
                if any(v > 0 for k, v in m.items() if "W27 A1" in k):
                    a1_seen = True
                    sink.step("I1_A1_loaded", elapsed_s=round(time.monotonic() - t0, 2),
                              markers=m, counters=cnt)
                    break
            time.sleep(2.0)
        sink.step("I1_A1_status", a1_loaded=a1_seen)
        L.screenshot(sink, "p3_I1_A1_ingame", hwnd)

        # ---- Q2: wait for the win / score screen (GUI:Continue) -------
        ok, cs, cnt, vis = poll(pid, hproc, sink, "I1_wait_victory", 120,
                                want_any=["GUI:Continue"], interval=1.5)
        if ok:
            sink.step("Q2_victory_screen", visible=vis)
            L.screenshot(sink, "p3_I1_victory_screen", hwnd)
            L.click(pid, "GUI:Continue", sink, wait_s=3.0,
                    label="Q2_click_GUI_Continue")
            # wait for A2 map marker
            t0 = time.monotonic()
            a2_seen = False
            while time.monotonic() - t0 < 120:
                cs2, cnt2, vis2 = snap_counters(pid, hproc, sink,
                                                "I1_waiting_A2")
                m = marker(hproc, sink, "I1_A2", A2 + MAPS)
                if any(v > 0 for k, v in m.items() if "W27 A2" in k):
                    a2_seen = True
                    sink.step("Q2_A2_loaded", elapsed_s=round(time.monotonic() - t0, 2),
                              markers=m, counters=cnt2, visible=vis2)
                    break
                time.sleep(2.0)
            results["q2"] = "成立（D2 诊断变体）" if a2_seen else "未验证"
            L.screenshot(sink, "p3_I1_A2_ingame", hwnd)
            snap_counters(pid, hproc, sink, "I1_A2_state")
        else:
            results["q2"] = "未验证（未出现胜利/结算屏）"
            L.screenshot(sink, "p3_I1_no_victory", hwnd)

        # ---- Q3 step 1: in-game save ----------------------------------
        before = L.save_inventory(sink, "I1_before_save")
        L.key(L.VK_ESCAPE, sink, "I1_Esc_open_ingame_menu")
        cs, cnt, vis = snap_counters(pid, hproc, sink, "I1_esc_menu")
        L.screenshot(sink, "p3_I1_esc_menu", hwnd)
        if L.find_btn(pid, "GUI:SaveGame"):
            L.click(pid, "GUI:SaveGame", sink, wait_s=2.0,
                    label="I1_click_SaveGame")
        cs, cnt, vis = snap_counters(pid, hproc, sink, "I1_save_dialog")
        L.screenshot(sink, "p3_I1_save_dialog", hwnd)
        # dump listboxes / edits / buttons of the save dialog
        for c in (cs or []):
            if c["cls"] in ("ListBox", "ComboBox"):
                n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                sink.step("save_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                          rect=c["rect"], lb_getcount=n)
                if n:
                    L.read_listbox(hproc, c["hwnd"], sink, "save_dialog_items")
        # Click the visible save/OK button (excluding Back/Cancel-ish)
        sv = [c for c in (cs or []) if c["cls"] == "Button" and c["visible"]
              and c["text"] and c["text"] not in
              ("GUI:Back", "GUI:MainMenu", "GUI:DeleteGame")]
        sink.step("save_dialog_visible_buttons",
                  buttons=[{"text": c["text"], "hwnd": c["hwnd"],
                            "rect": c["rect"]} for c in sv])
        if sv:
            L.click_hwnd(sv[0]["hwnd"], sink,
                         "I1_click_save_button_" + sv[0]["text"], wait_s=3.0)
        after = L.save_inventory(sink, "I1_after_save")
        added = [f for f in after if f["name"] not in {x["name"] for x in before}]
        changed = [f for f in after if f["name"] in {x["name"] for x in before}
                   and f["sha256"] != next(x["sha256"] for x in before
                                           if x["name"] == f["name"])]
        sink.step("Q3_save_file", added=added, changed=changed,
                  before_n=len(before), after_n=len(after))
        # copy the save into out/ for delivery
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
        L.screenshot(sink, "p3_I1_after_save", hwnd)

        # ---------------- full exit + residual check -------------------
        finish_one(sink, "I1", pid, hwnd, hproc)
        pid = hwnd = hproc = None
        sink.step("Q3_process_exit", residual=L.list_gamemd(),
                  note="完全退出，核对 gamemd 残留 0")

        # ---------------- INSTANCE 2: relaunch + load ------------------
        if saved:
            pid, hwnd, hproc = launch_one(sink, "I2_load")
            snap_counters(pid, hproc, sink, "I2_S0_main_menu")
            L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
                    label="I2_click_SinglePlayer")
            L.click(pid, "GUI:LoadSavedGame", sink, wait_s=2.5,
                    label="I2_click_LoadSavedGame")
            cs, cnt, vis = snap_counters(pid, hproc, sink, "I2_load_dialog")
            L.screenshot(sink, "p3_I2_load_dialog", hwnd)
            # enumerate load listbox items
            load_box = None
            for c in (cs or []):
                if c["cls"] in ("ListBox", "ComboBox"):
                    n = int(L.smt(c["hwnd"], L.LB_GETCOUNT))
                    sink.step("load_dialog_box", hwnd=c["hwnd"], cls=c["cls"],
                              rect=c["rect"], lb_getcount=n)
                    if n:
                        L.read_listbox(hproc, c["hwnd"], sink, "load_items")
                        load_box = c["hwnd"]
            # try to select by item name
            if load_box:
                n = int(L.smt(load_box, L.LB_GETCOUNT))
                for i in range(n):
                    d = int(L.smt(load_box, L.LB_GETITEMDATA, i)) & 0xFFFFFFFF
                    nm = L.read_utf16_ptr(hproc, d) or ""
                    if saved["name"].lower().split(".")[0] in nm.lower():
                        L.smt(load_box, L.LB_SETCURSEL, i)
                        sink.step("Q3_load_selected", index=i, name=nm,
                                  action="LB_SETCURSEL")
                        break
            # click the load button
            lb = [c for c in (cs or []) if c["cls"] == "Button"
                  and c["text"] in ("GUI:Load", "GUI:LoadGame")
                  and c["visible"]]
            if not lb:
                lb = [c for c in (cs or []) if c["cls"] == "Button"
                      and c["visible"] and c["text"] and
                      c["text"] not in ("GUI:Back", "GUI:MainMenu",
                                        "GUI:DeleteGame")]
            sink.step("load_dialog_buttons",
                      buttons=[{"text": c["text"], "hwnd": c["hwnd"]} for c in lb])
            if lb:
                L.click_hwnd(lb[0]["hwnd"], sink,
                             "I2_click_load_" + lb[0]["text"], wait_s=4.0)
            # observe load result
            ok2, cs2, cnt2, vis2 = poll(pid, hproc, sink, "I2_after_load", 90,
                                        want_any=["GUI:ResumeMission",
                                                  "GUI:AbortMission",
                                                  "GUI:SaveGame"],
                                        interval=1.5)
            L.screenshot(sink, "p3_I2_after_load", hwnd)
            m2 = marker(hproc, sink, "I2_loaded", A1 + A2 + MAPS)
            sink.step("Q3_load_observation", poll_hit=ok2, visible=vis2,
                      counters=cnt2, markers=m2,
                      save_name=saved["name"], save_sha256=saved["sha256"])
            L.key(L.VK_ESCAPE, sink, "I2_Esc_ingame_menu_check")
            cs3, cnt3, vis3 = snap_counters(pid, hproc, sink, "I2_esc_menu")
            L.screenshot(sink, "p3_I2_esc_menu", hwnd)
            results["q3"] = "成立（D2 诊断变体）" if ok2 else "未验证"
            finish_one(sink, "I2", pid, hwnd, hproc)
            pid = hwnd = hproc = None
        else:
            results["q3"] = "未验证（无存档文件产生）"

        sink.step("chain_results", **results)
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
            sink.step("D2_restore", sha256=L.sha256_file(BATTLE),
                      expected=L.sha256_file(BATTLE_ORIG) if BATTLE_ORIG.is_file() else None,
                      byte_identical=(BATTLE_ORIG.is_file() and
                                      BATTLE.read_bytes() == BATTLE_ORIG.read_bytes()))
        except Exception as e:
            sink.step("D2_restore_error", error=repr(e))
        try:
            L.restore_configs(sink)
        except Exception as e:
            sink.step("restore_error", error=repr(e))
        try:
            sink.step("p3_done", gamemd_residual=L.list_gamemd(),
                      chain_results=results)
        except Exception:
            pass
        sink.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

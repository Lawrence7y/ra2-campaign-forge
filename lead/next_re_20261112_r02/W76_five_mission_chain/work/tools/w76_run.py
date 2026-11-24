#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W76 REAL-MACHINE trip (route a): Soviet badge -> M1 -> M2 -> M3 -> M4 -> M5.

LOCK DISCIPLINE (per trip):
  * BEFORE launch: read .game_instance.lock; require owner==lead; require 0 live
    gamemd.exe. If not, wait (bounded) then refuse.
  * Take lock -> owner=w76.
  * ALWAYS (success OR failure) release back to owner=lead with a status note.
  * Never hold the lock across trips.

REAL-MACHINE DISCIPLINE:
  * WMI Win32_Process.Create launches ONLY the sandbox gamemd.exe.
  * Read-only OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) +
    ReadProcessMemory; EnumWindows/EnumChildWindows; PIL.ImageGrab.
  * NO WriteProcessMemory / breakpoints / thread attach / injection / exe edits.
  * close_game only touches the pid WE launched (WM_CLOSE first).
  * No taskkill of any user process.

OBSERVATION POINTS (W59 / LEAD_VERIFY_W59.md):
  Scen* = *(DWORD*)0x00A8B230
    +0x125C char[0x104]  current/next scenario filename (Start_Scenario arg)
    +0x35A0 WORD         stage index
    +0x34AC BYTE         EndOfGame
    +0x34AE BYTE         SkipScore
    +0x34B0 BYTE         SkipMapSelect
    +0x34CC DWORD        BattleIdx
  frame = *(DWORD*)0x00A8ED84

Every level: read immediately on entry + screenshot; on victory + screenshot;
after GUI:Continue + screenshot.  On any error dialog: capture popup text,
0x125C current value, MSG:UnableMapSelect markers, and the static branch.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w76_lib as L
import w76_common as C

TAG = "run"
VARIANT = "A_from1"          # installed MAPSELMD variant (child keys 1=)
EXPECTED = ["RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP",
            "RA2F_M4.MAP", "RA2F_M5.MAP"]
N_MISSIONS = len(EXPECTED)
# Task 2: Lead's +0x35A0 prediction (REVIEW\LEAD_VERIFY_W63.md §8, [静态推断·较强]):
#   "+0x35A0 stores the key of the stage record CONSUMED when advancing into
#    the current mission, not the current mission's own key."
# With MAPSELMD [Nod] keys 8..12 = M1..M5 stages, Lead predicts:
#   M1=0 (entered via battle Scenario= directly, no stage table),
#   M2=8, M3=9, M4=10, M5=11; key 12 (M5's own stage) never consumed.
LEAD_PREDICTION = {1: 0, 2: 8, 3: 9, 4: 10, 5: 11}
ERR_TOKENS = ("GUI:OK", "確定", "无法啟始", "無法啟始", "无法启动", "無法啟動",
              "UnableMapSelect", "確定")
ERR_MARKERS = ["UnableMapSelect", "Invalid stage", "MSG:UnableMapSelect",
               "RA2F_M1.MAP", "RA2F_M2.MAP", "RA2F_M3.MAP",
               "RA2F_M4.MAP", "RA2F_M5.MAP",
               "RA2F_RA2F_M1", "RA2F_RA2F_M2", "RA2F_RA2F_M3",
               "RA2F_RA2F_M4", "RA2F_RA2F_M5"]


class TripError(RuntimeError):
    def __init__(self, msg, **detail):
        super().__init__(msg)
        self.detail = detail


def w59(sink, hproc, label):
    p = L.read_w59_point(hproc, label)
    sink.step("w59_point", **p)
    return p


def collect_fields(p, lvl):
    """Task 2: one row per mission entry — all W59 offsets + Lead prediction."""
    k = int(lvl[1:])
    row = {
        "mission": lvl,
        "label": p.get("label"),
        "0x125C_scen_filename": p.get("scen_filename"),
        "0x35A0_stage_idx": p.get("scen_stage_idx"),
        "0x34AC_end_of_game": p.get("scen_end_of_game"),
        "0x34AE_skip_score": p.get("scen_skip_score"),
        "0x34B0_skip_mapsel": p.get("scen_skip_mapsel"),
        "0x34CC_battle_idx": p.get("scen_battle_idx"),
        "scen_next": p.get("scen_next"),
        "frame": p.get("frame"),
        "lead_prediction_0x35A0": LEAD_PREDICTION.get(k),
    }
    row["matches_lead_prediction"] = (
        row["0x35A0_stage_idx"] == row["lead_prediction_0x35A0"])
    return row


def screenshot(sink, hwnd, label):
    try:
        return str(L.screenshot(sink, label, hwnd))
    except Exception as e:
        sink.step("screenshot_error", label=label, error=repr(e))
        return None


def visible(pid):
    return sorted({c["text"] for c in L.controls(pid)
                   if c["visible"] and c["text"]})


def snap(sink, pid, hproc, label):
    cs = L.controls(pid)
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    p = w59(sink, hproc, label + "_w59")
    sink.step("screen_state", label=label,
              visible_control_texts=vis,
              all_controls=[{"cls": c["cls"], "text": c["text"],
                             "vis": c["visible"], "rect": c["rect"]} for c in cs])
    return cs, vis, p


def is_error_dialog(vis):
    return any(any(t.lower() in (v or "").lower() for t in ERR_TOKENS)
               for v in vis)


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready",
                      elapsed_s=round(time.monotonic() - t0, 2),
                      evidence_control="GUI:SinglePlayer")
            return
        time.sleep(1.5)
    raise TripError("main menu timeout (%ss)" % timeout_s)


def wait_ingame(sink, pid, hproc, hwnd, want_fn, timeout_s=100):
    """Wait until Scen+0x125C == want_fn and frame>30; log frame trajectory."""
    t0 = time.monotonic()
    traj = []
    while time.monotonic() - t0 < timeout_s:
        cs, vis, p = snap(sink, pid, hproc, "waiting_" + want_fn)
        traj.append({"t": round(time.monotonic() - t0, 1),
                     "fn": p.get("scen_filename"), "frame": p.get("frame"),
                     "stage": p.get("scen_stage_idx"),
                     "eog": p.get("scen_end_of_game")})
        if is_error_dialog(vis):
            screenshot(sink, hwnd, "error_" + want_fn)
            raise TripError("error dialog while waiting for " + want_fn,
                            visible=vis, w59=p)
        for btn in ("GUI:Play", "GUI:StartGame"):
            if L.find_btn(pid, btn):
                L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
        fn = (p.get("scen_filename") or "")
        if want_fn.lower() in fn.lower() and (p.get("frame") or 0) > 30:
            shot = screenshot(sink, hwnd, "enter_" + want_fn.replace(".MAP", ""))
            sink.step("level_entered", level=want_fn,
                      elapsed_s=round(time.monotonic() - t0, 2),
                      w59=p, screenshot=shot, frame_trajectory=traj[-12:])
            return p
        time.sleep(1.5)
    screenshot(sink, hwnd, "timeout_" + want_fn.replace(".MAP", ""))
    raise TripError("timeout waiting to enter " + want_fn,
                    frame_trajectory=traj[-20:])


def wait_victory(sink, pid, hproc, hwnd, level, timeout_s=100):
    """Victory = GUI:Continue visible; frame advance stalls on the score screen."""
    t0 = time.monotonic()
    frames = []
    while time.monotonic() - t0 < timeout_s:
        cs, vis, p = snap(sink, pid, hproc, "wait_victory_" + level)
        frames.append(p.get("frame"))
        if is_error_dialog(vis):
            screenshot(sink, hwnd, "error_victory_" + level)
            raise TripError("error dialog while waiting victory of " + level,
                            visible=vis, w59=p)
        if any("GUI:Continue" == (v or "") or "continue" in (v or "").lower()
               for v in vis):
            f1 = p.get("frame")
            time.sleep(2.0)
            p2 = w59(sink, hproc, "victory_frame_confirm_" + level)
            f2 = p2.get("frame")
            shot = screenshot(sink, hwnd, "victory_" + level)
            sink.step("level_victory", level=level,
                      elapsed_s=round(time.monotonic() - t0, 2),
                      frame_at_continue=f1, frame_2s_later=f2,
                      frame_stalled=(f1 == f2), w59=p2, screenshot=shot,
                      frame_trajectory=frames[-20:])
            return p2
        time.sleep(1.0)
    screenshot(sink, hwnd, "no_victory_" + level)
    raise TripError("GUI:Continue never appeared for " + level,
                    frame_trajectory=frames[-20:])


def click_continue(sink, pid, label):
    L.click(pid, "GUI:Continue", sink, wait_s=2.0, label=label)


def wait_advance(sink, pid, hproc, hwnd, from_level, want_fn, timeout_s=100):
    """After Continue: expect Scen+0x125C to become want_fn with frame advancing."""
    t0 = time.monotonic()
    traj = []
    while time.monotonic() - t0 < timeout_s:
        if not L.process_alive(pid):
            screenshot(sink, hwnd, "process_exited_after_" + from_level)
            raise TripError("process exited after Continue of " + from_level,
                            frame_trajectory=traj[-20:])
        cs, vis, p = snap(sink, pid, hproc, "post_continue_" + from_level)
        traj.append({"t": round(time.monotonic() - t0, 1),
                     "fn": p.get("scen_filename"), "frame": p.get("frame"),
                     "stage": p.get("scen_stage_idx"),
                     "eog": p.get("scen_end_of_game")})
        if is_error_dialog(vis):
            shot = screenshot(sink, hwnd, "error_dialog_after_" + from_level)
            me = L.memory_search(hproc, ERR_MARKERS, sink,
                                 "error_memory_after_" + from_level)
            hits = {k: v["count"] for k, v in me["hits"].items()}
            raise TripError("MSG:UnableMapSelect-style error after Continue of "
                            + from_level,
                            popup_visible_control_texts=vis,
                            popup_screenshot=shot, w59=p, marker_counts=hits,
                            frame_trajectory=traj[-20:])
        fn = (p.get("scen_filename") or "")
        if want_fn.lower() in fn.lower() and (p.get("frame") or 0) > 10:
            f1 = p.get("frame")
            time.sleep(2.5)
            p2 = w59(sink, hproc, "advance_frame_confirm_" + want_fn)
            f2 = p2.get("frame")
            shot = screenshot(sink, hwnd, "enter_" + want_fn.replace(".MAP", ""))
            sink.step("level_advance", from_level=from_level, to_level=want_fn,
                      elapsed_s=round(time.monotonic() - t0, 2),
                      frame_t1=f1, frame_t2=f2,
                      frame_advancing=(f1 is not None and f2 is not None and f2 > f1),
                      w59=p2, screenshot=shot, frame_trajectory=traj[-12:])
            # Task 2 / W63 detail: transition-order evidence. W63 saw 0x125C
            # change to the new map name BEFORE +0x35A0 is written (stage==0
            # intermediate state). Log the FULL trajectory (not just last 12)
            # so the "first change / later write" ordering is auditable.
            mid = [s for s in traj
                   if s["fn"] and want_fn.lower() in s["fn"].lower()
                   and s["stage"] in (0, None)]
            sink.step("transition_samples_full", from_level=from_level,
                      to_level=want_fn, n_samples=len(traj), samples=traj)
            sink.step("transition_ordering", from_level=from_level,
                      to_level=want_fn,
                      fn_changed_before_stage_written=bool(mid),
                      n_intermediate_samples=len(mid),
                      intermediate_samples=mid[:10])
            return p2
        time.sleep(1.5)
    screenshot(sink, hwnd, "advance_timeout_after_" + from_level)
    raise TripError("timeout waiting advance " + from_level + " -> " + want_fn,
                    frame_trajectory=traj[-20:])


def observe_final(sink, pid, hproc, hwnd, timeout_s=70):
    """M5 EndOfGame=yes: after Continue, NO 6th Start_Scenario. Record 0x34AC,
    0x125C, frame trajectory, visible controls, screenshot."""
    t0 = time.monotonic()
    traj = []
    saw_eog_screen = False
    while time.monotonic() - t0 < timeout_s:
        if not L.process_alive(pid):
            sink.step("final_process_exited", elapsed_s=round(time.monotonic() - t0, 2))
            break
        cs, vis, p = snap(sink, pid, hproc, "final_after_M5_continue")
        traj.append({"t": round(time.monotonic() - t0, 1),
                     "fn": p.get("scen_filename"), "frame": p.get("frame"),
                     "stage": p.get("scen_stage_idx"),
                     "eog": p.get("scen_end_of_game"),
                     "vis": vis[:12]})
        if any(k in " ".join(vis).lower() for k in
               ("continue", "mainmenu", "quit", "ok", "確定", "score", "victory")):
            saw_eog_screen = True
        time.sleep(1.5)
    shot = screenshot(sink, hwnd, "final_after_M5_continue")
    last = traj[-1] if traj else {}
    # A 6th scenario would show a NEW scen_filename (not any of M1..M5) with
    # a fresh frame. Generalized from W63's "no 4th start" to 5-mission chain.
    expected_upper = {m.upper() for m in EXPECTED}
    extra = [x for x in traj
             if x["fn"] and x["fn"].upper() not in expected_upper]
    sink.step("final_endofgame_observation",
              elapsed_s=round(time.monotonic() - t0, 2),
              end_of_game_byte=last.get("eog"),
              scen_filename_traj=[x["fn"] for x in traj],
              frame_traj=[x["frame"] for x in traj],
              stage_traj=[x["stage"] for x in traj],
              saw_settlement_or_menu=saw_eog_screen,
              extra_scenario_candidates=extra,
              no_extra_start=(len(extra) == 0),
              screenshot=shot, full_trajectory=traj)
    return {"last": last, "extra": extra, "traj": traj, "screenshot": shot,
            "no_extra_start": len(extra) == 0}


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None, "lock_taken": False}
    ok = False
    trip_outcome = "unknown"
    levels = {}       # per-level 进关/通关/推进 judgments
    trajectory = []   # 0x125C trajectory
    entry_fields = []  # task 2: one W59 field row per mission entry
    field_table = None
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  variant=VARIANT, expected=EXPECTED,
                  note="lock will be taken per trip; released in finally")
        # ---- (0) LOCK GATE -------------------------------------------------
        pre = L.list_gamemd()
        lock_txt = C.lock_read()
        owner = ""
        for ln in lock_txt.splitlines():
            if ln.startswith("owner="):
                owner = ln.split("=", 1)[1].strip()
        sink.step("lock_gate_before", lock_content=lock_txt, owner=owner,
                  gamemd_processes=pre, n=len(pre))
        if owner != "lead" or pre:
            # bounded wait (do not steal another writer's lock)
            t0 = time.monotonic()
            while time.monotonic() - t0 < 60:
                time.sleep(5)
                owner2 = ""
                for ln in C.lock_read().splitlines():
                    if ln.startswith("owner="):
                        owner2 = ln.split("=", 1)[1].strip()
                if owner2 == "lead" and not L.list_gamemd():
                    owner = owner2
                    break
            sink.step("lock_gate_after_wait", owner=owner,
                      gamemd_processes=L.list_gamemd())
            if owner != "lead" or L.list_gamemd():
                raise TripError("lock gate refused: owner=%r, live gamemd=%r"
                                % (owner, L.list_gamemd()))
        C.lock_claim_w76("W76 route(a) E2E trip: variant %s, M1->M2->M3->M4->M5 five-mission real-machine run" % VARIANT)
        state["lock_taken"] = True
        sink.step("lock_claimed", owner="w76", content=C.lock_read())

        # ---- (1) launch ----------------------------------------------------
        if L.list_gamemd():
            raise TripError("residual gamemd before launch (not ours)")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        state["pid"] = pid
        L.desktop_precheck(sink)          # MUST be within 30 s of WMI launch
        hwnd = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 60:
            hwnd = L.game_hwnd(pid)
            if hwnd:
                break
            time.sleep(1.0)
        state["hwnd"] = hwnd
        hproc = L.open_proc(pid)
        state["hproc"] = hproc
        if not hproc:
            raise TripError("OpenProcess(PROCESS_VM_READ) returned NULL")
        wait_main_menu(pid, sink)
        L.force_foreground(hwnd)
        sink.step("instance_ready", pid=pid, hwnd=hwnd,
                  rect=L.rect(hwnd) if hwnd else None,
                  title=L.wtxt(hwnd) if hwnd else None)
        snap(sink, pid, hproc, "S0_main_menu")
        screenshot(sink, hwnd, "S0_main_menu")

        # ---- (2) campaign menu --------------------------------------------
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="click_NewCampaign")
        cs, vis, p = snap(sink, pid, hproc, "S2_campaign_menu")
        screenshot(sink, hwnd, "S2_campaign_menu")
        sink.step("campaign_menu", visible=vis, w59=p)

        # ---- (3) Soviet badge ([SOV1] rewritten) ---------------------------
        wr = L.rect(hwnd) or [0, 0, 1707, 960]
        L.force_foreground(hwnd)
        bx, by = wr[0] + 210, wr[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        screenshot(sink, hwnd, "after_SOVIET_badge")
        snap(sink, pid, hproc, "after_badge")
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # ---- (4) MISSION LOOP: M1..M5 --------------------------------------
        # Generalized from W63's 3-mission block. Each mission: enter -> victory
        # -> click GUI:Continue. M1 enters via the rewritten [SOV1] badge;
        # M2..M5 enter via wait_advance (post-Continue Start_Scenario).
        for idx, want_fn in enumerate(EXPECTED):
            lvl = "M%d" % (idx + 1)
            if idx == 0:
                p = wait_ingame(sink, pid, hproc, hwnd, want_fn, timeout_s=110)
            else:
                p = wait_advance(sink, pid, hproc, hwnd, "M%d" % idx,
                                 want_fn, timeout_s=110)
                levels["M%d" % idx]["advance"] = True
            levels[lvl] = {"enter": True, "victory": False,
                           "advance": None if idx < N_MISSIONS - 1 else False,
                           "end_of_game": None}
            trajectory.append({"phase": "enter_" + lvl, "w59": p})
            entry_fields.append(collect_fields(p, lvl))
            v = wait_victory(sink, pid, hproc, hwnd, lvl, timeout_s=110)
            levels[lvl]["victory"] = True
            trajectory.append({"phase": "victory_" + lvl, "w59": v})
            click_continue(sink, pid, "click_Continue_" + lvl)

        # ---- (5) EndOfGame termination (after M5's Continue) ---------------
        fin = observe_final(sink, pid, hproc, hwnd, timeout_s=70)
        levels["M5"]["end_of_game"] = fin["last"].get("eog")
        levels["M5"]["no_extra_start"] = fin["no_extra_start"]
        levels["M5"]["final_screenshot"] = fin["screenshot"]
        trajectory.append({"phase": "final_after_M5_continue",
                           "w59": fin["last"], "no_extra_start": fin["no_extra_start"]})

        # ---- (6) Task 2 field table: +0x35A0 vs Lead prediction ------------
        field_table = {
            "lead_source": "REVIEW/LEAD_VERIFY_W63.md §8 [静态推断·较强]",
            "lead_claim": ("Scen+0x35A0 = the MAPSELMD [Nod] key of the stage "
                           "record CONSUMED to advance into the current mission, "
                           "NOT the current mission's own key"),
            "mapsel_nod_keys": {"8": "M1 stage", "9": "M2 stage",
                                "10": "M3 stage", "11": "M4 stage",
                                "12": "M5 stage (Lead: never consumed)"},
            "rows": entry_fields,
            "all_match": all(r["matches_lead_prediction"] for r in entry_fields),
        }
        sink.step("task2_field_table", **field_table)
        (C.OUT / "FIELD_TABLE.json").write_text(
            json.dumps(field_table, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")

        trip_outcome = ("FULL_CHAIN_M1_M5" if fin["no_extra_start"]
                        else "EXTRA_SCENARIO_STARTED")
        ok = (all(levels[l]["enter"] and levels[l]["victory"] for l in levels)
              and all(levels["M%d" % i]["advance"]
                      for i in range(1, N_MISSIONS))
              and fin["no_extra_start"]
              and levels["M5"]["end_of_game"] == 1)
        sink.step("trip_result", ok=ok, outcome=trip_outcome, levels=levels,
                  task2_all_match=field_table["all_match"])
    except TripError as e:
        trip_outcome = "BLOCKED: " + str(e)
        sink.step("trip_blocked", outcome=trip_outcome, detail=e.detail)
        # classify the static branch for diagnosis (W59 six questions)
        sink.step("block_static_branch", note=
                  "map failure branches: "
                  "(no) 0x5AE220->0x5CF760 Scenario= reverse lookup -> 0x5AE320 Invalid stage! -> MSG:UnableMapSelect; "
                  "(yes) 0x5ADF20->0x5CF810 stage idx -> child Scenario= vs NextScenario mismatch -> 0x5AE0CD AL=0 silent; "
                  "EOG gate: 0x6859BF mov al,[Scen+0x34AC] / 0x6859C7 je -> ==0 advances, !=0 ret; "
                  "key cap: 0x5CF04F cmp edi,0x64 / 0x5CF367 cmp ebp,0x64; "
                  "stage idx write: 0x5AE0B8 mov [ebx+0x35a0],ax; "
                  "Start_Scenario arg: 0x685C4E lea ecx,[eax+0x125c] -> 0x683AB0")
    except Exception as e:
        trip_outcome = "FATAL: " + repr(e)
        sink.step("FATAL", error=repr(e),
                  traceback=traceback.format_exc()[-6000:])
    finally:
        # (a) always close ONLY the game we launched
        pid, hwnd, hproc = state["pid"], state["hwnd"], state["hproc"]
        try:
            if hproc:
                L.k32.CloseHandle(hproc)
        except Exception:
            pass
        close_steps = []
        if pid:
            try:
                close_steps = L.close_game(pid, hwnd, sink)
            except Exception as e:
                sink.step("close_error", error=repr(e))
        residual = L.list_gamemd()
        sink.step("trip_cleanup", close_steps=close_steps,
                  gamemd_residual=residual, residual_zero=(len(residual) == 0))
        # (b) ALWAYS release the lock to lead with a status note
        if state["lock_taken"]:
            C.lock_release("W76 route(a) trip FINISHED (ok=%s, outcome=%s): "
                           "self-launched gamemd closed, residual=%d; restored owner=lead."
                           % (ok, trip_outcome, len(residual)))
        sink.step("lock_released", lock_content=C.lock_read())
        # (c) persist the trajectory / judgments for the report
        payload = {"variant": VARIANT, "ok": ok, "outcome": trip_outcome,
                   "levels": levels, "trajectory": trajectory,
                   "entry_fields": entry_fields,
                   "task2_field_table": field_table,
                   "lead_prediction": LEAD_PREDICTION,
                   "expected_0x125C": EXPECTED,
                   "w59_offsets": {"scen_ptr": "0x00A8B230",
                                   "filename": "+0x125C", "stage_idx": "+0x35A0",
                                   "end_of_game": "+0x34AC",
                                   "skip_score": "+0x34AE",
                                   "skip_mapsel": "+0x34B0",
                                   "battle_idx": "+0x34CC",
                                   "frame": "0x00A8ED84"}}
        trip_name = os.environ.get("W76_TRIP", "").strip()
        trip_path = (C.OUT / ("TRIP_%s.json" % trip_name)
                     if trip_name else (C.OUT / "TRIP_RESULT.json"))
        (C.OUT / "TRIP_RESULT.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        if trip_name:
            trip_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  outcome=trip_outcome, levels=levels,
                  trip_extra_copy=str(trip_path) if trip_name else None,
                  gamemd_residual=residual, lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

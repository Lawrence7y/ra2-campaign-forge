#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W78 REAL-MACHINE trip — real combat load, single mission, EndOfGame=yes.

Env:
  W78_VARIANT = annih (default) | time
  W78_TRIP    = trip1 (default) | trip2 | ...

LOCK DISCIPLINE (per trip):
  * BEFORE launch: read .game_instance.lock; require owner==lead; 0 live gamemd.
  * Take lock -> owner=w78. ALWAYS release back to owner=lead in finally.
  * Never hold the lock across trips.

REAL-MACHINE DISCIPLINE:
  * WMI Win32_Process.Create launches ONLY the sandbox gamemd.exe.
  * Read-only OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) +
    ReadProcessMemory; EnumWindows/EnumChildWindows; PIL.ImageGrab.
  * NO WriteProcessMemory / breakpoints / thread attach / injection / exe edits.
  * close_game only touches the pid WE launched (WM_CLOSE first).
  * No blanket taskkill of user processes.

OBSERVATION POINTS (W59 / LEAD_VERIFY_W59.md, transcribed by W63/W76):
  Scen* = *(DWORD*)0x00A8B230
    +0x125C char[0x104]  current/next scenario filename
    +0x35A0 WORD         stage index
    +0x34AC BYTE         EndOfGame
    +0x34AE BYTE         SkipScore
    +0x34B0 BYTE         SkipMapSelect
    +0x34CC DWORD        BattleIdx
  frame = *(DWORD*)0x00A8ED84  (32 ms game timer, ~31.25 counts/s)

COMBAT OBSERVATION (new for W78):
  * Sample W59 + frame + visible controls every ~1 s for a MINIMUM of 60 s
    wall-clock after entering the mission (do NOT exit early).
  * Screenshot series at t=0,5,10,15,20,25,30,40,50,60 s.
  * Detect victory/defeat (GUI:Continue / GUI:Retry / GUI:MainMenu), capture the
    settlement screen, but KEEP sampling until the minimum window elapses.
  * After Continue: observe terminal state for ~25 s, assert no extra
    Start_Scenario (no new 0x125C filename).
  * "Combat happened" evidence = (a) screenshot series of the live battle,
    (b) game-generated settlement-screen kill/loss statistics, (c) frame
    trajectory; grades recorded in COMBAT_LOAD_RESULT.md.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w78_lib as L
import w78_common as C

VARIANT = os.environ.get("W78_VARIANT", "annih").strip().lower()
TRIP = os.environ.get("W78_TRIP", "trip1").strip() or "trip1"
TAG = "run_" + TRIP
WANT_FN = "RA2F_M1.MAP"
OBSERVE_SEC = 60          # minimum wall-clock combat observation (45-60 s band)
POST_WAIT_SEC = 90        # extra grace for a result after the minimum window
TERMINAL_SEC = 25         # post-Continue terminal observation
SAMPLE_INTERVAL = 1.0
SHOT_MARKS = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60]
TRIP_OUT = C.OUT / TRIP
# Trip 2 lesson: GUI:OK / GUI:OK+GUI:Cancel is RA2's ordinary defeat / "restart
# this mission?" dialog, NOT a map-load error.  Only the W59/W76 map-error
# strings are error markers here; a broad GUI:OK test false-positives on a
# legitimate settlement.
ERR_TOKENS = ("无法啟始", "無法啟始", "无法启动", "無法啟動",
              "UnableMapSelect", "Invalid stage", "MSG:UnableMapSelect")
VICTORY_TOKENS = ("GUI:Continue", "GUI:Retry", "GUI:MainMenu", "continue",
                  "retry", "mainmenu", "繼續", "重試")


class TripError(RuntimeError):
    def __init__(self, msg, **detail):
        super().__init__(msg)
        self.detail = detail


def shot(sink, hwnd, label):
    try:
        p = L.screenshot(sink, TRIP + "_" + label, hwnd)
        # also keep a copy in the per-trip folder
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(p), str(TRIP_OUT / p.name))
        return str(p)
    except Exception as e:
        sink.step("screenshot_error", label=label, error=repr(e))
        return None


def visible(pid):
    return sorted({c["text"] for c in L.controls(pid)
                   if c["visible"] and c["text"]})


def snap(sink, pid, hproc, label):
    cs = L.controls(pid)
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    p = L.read_w59_point(hproc, label)
    sink.step("w59_point", **p)
    return cs, vis, p


def is_error_dialog(vis):
    return any(any(t.lower() in (v or "").lower() for t in ERR_TOKENS)
               for v in vis)


def is_settlement(vis):
    # Deliberately narrow: only the score/settlement screen's own controls.
    # A broad substring test risks matching in-game HUD/menu controls.
    s = {(v or "").lower() for v in vis}
    if {"gui:ok", "gui:cancel"} <= s:
        return True   # RA2 defeat / "restart this mission?" dialog
    for v in vis:
        t = (v or "").lower()
        if t in ("gui:continue", "gui:retry", "gui:mainmenu"):
            return True
        if "continue" in t or "retry" in t:
            return True
        if "繼續" in (v or "") or "重試" in (v or ""):
            return True
    return False


def settlement_kind(vis):
    s = {(v or "").lower() for v in vis}
    if "gui:continue" in s or any("continue" in t for t in s):
        return "victory_score_screen"
    if {"gui:ok", "gui:cancel"} <= s:
        return "defeat_restart_dialog"
    return "other_settlement"


def wait_main_menu(pid, sink, timeout_s=120):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2))
            return
        time.sleep(1.5)
    raise TripError("main menu timeout (%ss)" % timeout_s)


def wait_ingame(sink, pid, hproc, hwnd, timeout_s=110):
    t0 = time.monotonic()
    traj = []
    while time.monotonic() - t0 < timeout_s:
        cs, vis, p = snap(sink, pid, hproc, "waiting_" + WANT_FN)
        traj.append({"t": round(time.monotonic() - t0, 1),
                     "fn": p.get("scen_filename"), "frame": p.get("frame"),
                     "stage": p.get("scen_stage_idx"), "eog": p.get("scen_end_of_game")})
        if is_error_dialog(vis):
            shot(sink, hwnd, "error_enter")
            raise TripError("error dialog while waiting to enter " + WANT_FN,
                            visible=vis, w59=p)
        for btn in ("GUI:Play", "GUI:StartGame"):
            if L.find_btn(pid, btn):
                L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
        fn = (p.get("scen_filename") or "")
        if WANT_FN.lower() in fn.lower() and (p.get("frame") or 0) > 30:
            s = shot(sink, hwnd, "enter")
            sink.step("level_entered", level=WANT_FN,
                      elapsed_s=round(time.monotonic() - t0, 2),
                      w59=p, screenshot=s, frame_trajectory=traj[-12:])
            return p
        time.sleep(1.5)
    shot(sink, hwnd, "timeout_enter")
    raise TripError("timeout waiting to enter " + WANT_FN,
                    frame_trajectory=traj[-20:])


def observe_combat(sink, pid, hproc, hwnd):
    """Continuous observation for >= OBSERVE_SEC s; never exit early."""
    t0 = time.monotonic()
    samples = []
    victory = None            # {"t":..., "w59":..., "vis":..., "screenshot":...}
    next_mark = 0
    hard_cap = OBSERVE_SEC + POST_WAIT_SEC
    while True:
        t = time.monotonic() - t0
        cs, vis, p = snap(sink, pid, hproc, "combat_t%.1f" % t)
        row = {"t": round(t, 2),
               "frame": p.get("frame"), "mode": p.get("mode"),
               "0x125C": p.get("scen_filename"),
               "0x35A0": p.get("scen_stage_idx"),
               "0x34AC": p.get("scen_end_of_game"),
               "0x34AE": p.get("scen_skip_score"),
               "0x34B0": p.get("scen_skip_mapsel"),
               "0x34CC": p.get("scen_battle_idx"),
               "scen_next": p.get("scen_next"),
               "battle_cnt": p.get("battle_cnt"),
               "visible": vis[:14]}
        samples.append(row)
        sink.step("combat_sample", **row)

        if is_error_dialog(vis):
            shot(sink, hwnd, "error_dialog_t%.0f" % t)
            raise TripError("error dialog during combat", visible=vis, w59=p)

        if victory is None and is_settlement(vis):
            s = shot(sink, hwnd, "settlement")
            victory = {"t": round(t, 2), "w59": p, "visible": vis,
                       "screenshot": s, "frame_at": p.get("frame"),
                       "kind": settlement_kind(vis)}
            sink.step("settlement_detected", **{k: v for k, v in victory.items()
                                                if k != "w59"})
            sink.step("settlement_w59", w59=p)

        while next_mark < len(SHOT_MARKS) and t >= SHOT_MARKS[next_mark]:
            shot(sink, hwnd, "combat_t%02d" % SHOT_MARKS[next_mark])
            next_mark += 1

        if not L.process_alive(pid):
            sink.step("game_process_exited_during_observation", t=round(t, 2))
            break
        if t >= OBSERVE_SEC and victory is not None:
            break
        if t >= hard_cap:
            sink.step("observation_hard_cap", t=round(t, 2), victory=bool(victory))
            break
        time.sleep(SAMPLE_INTERVAL)

    # frame-stall confirmation on the settlement screen
    stall = None
    if victory is not None and L.process_alive(pid):
        p2 = L.read_w59_point(hproc, "settlement_frame_confirm")
        f1, f2 = victory["frame_at"], p2.get("frame")
        stall = {"frame_at_settlement": f1, "frame_2s_later": f2,
                 "frame_stalled": (f1 is not None and f1 == f2)}
        sink.step("settlement_frame_stall", **stall)
        victory["frame_stall"] = stall
        # a second, zoomed settlement capture after the screen settles
        time.sleep(2.0)
        victory["screenshot_confirm"] = shot(sink, hwnd, "settlement_confirm")

    traj = {"n_samples": len(samples),
            "frames": [s["frame"] for s in samples],
            "t": [s["t"] for s in samples],
            "eog": [s["0x34AC"] for s in samples],
            "stage": [s["0x35A0"] for s in samples],
            "fn": [s["0x125C"] for s in samples]}
    sink.step("combat_trajectory", **traj)
    return {"samples": samples, "trajectory": traj, "victory": victory,
            "elapsed_s": round(time.monotonic() - t0, 2),
            "min_window_met": (time.monotonic() - t0) >= OBSERVE_SEC}


def observe_terminal(sink, pid, hproc, hwnd):
    t0 = time.monotonic()
    traj = []
    while time.monotonic() - t0 < TERMINAL_SEC:
        if not L.process_alive(pid):
            sink.step("terminal_process_exited", elapsed_s=round(time.monotonic() - t0, 2))
            break
        cs, vis, p = snap(sink, pid, hproc, "terminal")
        traj.append({"t": round(time.monotonic() - t0, 1),
                     "fn": p.get("scen_filename"), "frame": p.get("frame"),
                     "stage": p.get("scen_stage_idx"),
                     "eog": p.get("scen_end_of_game"), "vis": vis[:12]})
        time.sleep(1.5)
    s = shot(sink, hwnd, "terminal")
    last = traj[-1] if traj else {}
    extra = [x for x in traj if x["fn"] and WANT_FN.lower() not in x["fn"].lower()]
    rep = {"elapsed_s": round(time.monotonic() - t0, 2),
           "end_of_game_byte": last.get("eog"),
           "scen_filename_traj": [x["fn"] for x in traj],
           "frame_traj": [x["frame"] for x in traj],
           "stage_traj": [x["stage"] for x in traj],
           "extra_scenario_candidates": extra,
           "no_extra_start": len(extra) == 0,
           "screenshot": s, "full_trajectory": traj}
    sink.step("terminal_observation", **{k: v for k, v in rep.items()
                                         if k != "full_trajectory"})
    sink.step("terminal_full", **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None, "lock_taken": False}
    ok = False
    outcome = "unknown"
    result = {"variant": VARIANT, "trip": TRIP, "want_fn": WANT_FN,
              "observe_sec": OBSERVE_SEC}
    combat = None
    terminal = None
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG, variant=VARIANT,
                  trip=TRIP, observe_sec=OBSERVE_SEC, shot_marks=SHOT_MARKS,
                  note="lock per trip; released in finally")
        # ---- (0) LOCK GATE -------------------------------------------------
        pre = L.list_gamemd()
        lock_txt = C.lock_read()
        owner = C.lock_owner()
        sink.step("lock_gate_before", lock_content=lock_txt, owner=owner,
                  gamemd_processes=pre, n=len(pre))
        if owner != "lead" or pre:
            t0 = time.monotonic()
            while time.monotonic() - t0 < 60:
                time.sleep(5)
                if C.lock_owner() == "lead" and not L.list_gamemd():
                    owner = "lead"
                    break
            sink.step("lock_gate_after_wait", owner=C.lock_owner(),
                      gamemd_processes=L.list_gamemd())
            if C.lock_owner() != "lead" or L.list_gamemd():
                raise TripError("lock gate refused: owner=%r, live gamemd=%r"
                                % (C.lock_owner(), L.list_gamemd()))
        C.lock_claim_w78("W78 real-combat-load trip %s variant=%s: enter %s, "
                         "observe >=%ss of real combat, capture settlement"
                         % (TRIP, VARIANT, WANT_FN, OBSERVE_SEC))
        state["lock_taken"] = True
        sink.step("lock_claimed", owner="w78", content=C.lock_read())

        # ---- (1) launch ----------------------------------------------------
        if L.list_gamemd():
            raise TripError("residual gamemd before launch (not ours)")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        state["pid"] = pid
        L.desktop_precheck(sink)
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
        shot(sink, hwnd, "S0_main_menu")

        # ---- (2) campaign menu --------------------------------------------
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="click_NewCampaign")
        snap(sink, pid, hproc, "S2_campaign_menu")
        shot(sink, hwnd, "S2_campaign_menu")

        # ---- (3) Soviet badge ([SOV1] rewritten) ---------------------------
        wr = L.rect(hwnd) or [0, 0, 1707, 960]
        L.force_foreground(hwnd)
        bx, by = wr[0] + 210, wr[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        shot(sink, hwnd, "after_SOVIET_badge")
        snap(sink, pid, hproc, "after_badge")
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # ---- (4) enter the mission ----------------------------------------
        entry = wait_ingame(sink, pid, hproc, hwnd)
        result["entry_w59"] = entry

        # ---- (5) CONTINUOUS COMBAT OBSERVATION (>= OBSERVE_SEC) -----------
        combat = observe_combat(sink, pid, hproc, hwnd)
        result["combat_observation"] = {"elapsed_s": combat["elapsed_s"],
                                        "min_window_met": combat["min_window_met"],
                                        "n_samples": combat["trajectory"]["n_samples"],
                                        "victory": combat["victory"],
                                        "trajectory": combat["trajectory"]}
        sink.step("combat_samples_full", samples=combat["samples"])

        # ---- (6) Continue -> terminal state --------------------------------
        if combat["victory"] is not None:
            clicked = False
            for btn in ("GUI:Continue", "GUI:Retry", "GUI:MainMenu",
                        "GUI:Cancel"):
                if L.find_btn(pid, btn):
                    L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
                    clicked = True
                    break
            sink.step("settlement_button_clicked", clicked=clicked,
                      visible_at_settlement=combat["victory"]["visible"])
            terminal = observe_terminal(sink, pid, hproc, hwnd)
            result["terminal"] = terminal
            outcome = "RESULT_AND_TERMINATION_OK"
            ok = bool(terminal["no_extra_start"] and combat["min_window_met"])
        else:
            outcome = "NO_RESULT_WITHIN_%ds" % (OBSERVE_SEC + POST_WAIT_SEC)
            terminal = observe_terminal(sink, pid, hproc, hwnd)
            result["terminal"] = terminal
            ok = False
        sink.step("trip_result", ok=ok, outcome=outcome, variant=VARIANT,
                  victory_t=(combat["victory"] or {}).get("t"))
    except TripError as e:
        outcome = "BLOCKED: " + str(e)
        sink.step("trip_blocked", outcome=outcome, detail=e.detail)
    except Exception as e:
        outcome = "FATAL: " + repr(e)
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
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
        if state["lock_taken"]:
            C.lock_release("W78 trip %s (%s) FINISHED (ok=%s, outcome=%s): "
                           "self-launched gamemd closed, residual=%d; restored owner=lead."
                           % (TRIP, VARIANT, ok, outcome, len(residual)))
        sink.step("lock_released", lock_content=C.lock_read())
        payload = {"variant": VARIANT, "trip": TRIP, "ok": ok,
                   "outcome": outcome, "result": result,
                   "w59_offsets": {"scen_ptr": "0x00A8B230",
                                   "filename": "+0x125C", "stage_idx": "+0x35A0",
                                   "end_of_game": "+0x34AC",
                                   "skip_score": "+0x34AE",
                                   "skip_mapsel": "+0x34B0",
                                   "battle_idx": "+0x34CC",
                                   "frame": "0x00A8ED84"}}
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        (C.OUT / ("TRIP_%s.json" % TRIP)).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        (TRIP_OUT / "TRIP_RESULT.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  outcome=outcome, variant=VARIANT,
                  gamemd_residual=residual, lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

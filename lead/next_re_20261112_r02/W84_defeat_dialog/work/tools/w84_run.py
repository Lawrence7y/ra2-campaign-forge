#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W84 REAL-MACHINE trip - one mission, EndOfGame=yes, per-trip lock.

Env:
  W84_MODE = df | wv      (label only; which package is installed decides the arm)
  W84_TRIP = trip_df1 | trip_wv1 | ...

PURPOSE: capture the MISSING THIRD TERMINAL STATE -- the defeat restart
dialog ("確定要重新執行此場任務嗎？"), sighted only twice before
(W78 trip2 misclassified as error dialog; W79 UNKNOWNS U4 [待运行验证]).

LOCK DISCIPLINE (red line #1, per trip, never held across trips):
  * BEFORE launch: read .game_instance.lock; require owner==lead; 0 live gamemd.
  * Take lock -> owner=w84. ALWAYS release back to owner=lead in finally.

REAL-MACHINE DISCIPLINE:
  * WMI Win32_Process.Create launches ONLY the sandbox gamemd.exe.
  * Read-only OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) + RPM.
  * NO WriteProcessMemory / breakpoints / injection / exe edits.
  * close_game only touches the pid WE launched (WM_CLOSE first).
  * No blanket taskkill.

THREE-WAY TERMINAL DETECTION (strict, red line #5):
  (1) VICTORY_SCORE_SCREEN : GUI:Continue AND (GUI:HeadsTaken | GUI:StandaloneScore
      | GUI:ParTime | GUI:YourTime).
  (2) DEFEAT_RESTART_DIALOG: {GUI:OK, GUI:Cancel} both visible (W78 trip2
      ndjson ground truth: ["GUI:Blank","GUI:Cancel","GUI:OK","Yuri's
      Revenge"]).  NEVER CLICKED -- clicking OK restarts the mission and
      pollutes the capture.
  (3) NO_RESULT_WITHIN_180s: neither appeared within the hard cap.
  Genuine map-load errors are a SEPARATE narrow class.

DEFEAT EVIDENCE CAPTURE (W84 core deliverable), done ONCE at detection:
  * full Win32 control enumeration of every window of the pid
    (cls/text/visible/rect/ctrl_id) -- raw control id/text list;
  * full-window screenshot + cropped dialog screenshot (around the GUI:OK
    control rect, no numbers read from pixels -- screenshots are evidence
    only, classification uses controls + RPM only);
  * bounded READ-ONLY memory search for the dialog text needles
    (確定要重新執行此場任務嗎 / 重新執行 / restart) ascii+utf16le -- textual
    proof without OCR;
  * RPM W59 tuple at detection: 0x125C scen filename, 0x34AC EndOfGame,
    0x35A0 stage, frame 0x00A8ED84 (+ 2 s stall re-read).
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
import w84_lib as L
import w84_common as C

MODE = os.environ.get("W84_MODE", "df").strip().lower()
TRIP = os.environ.get("W84_TRIP", "trip_df1").strip() or "trip_df1"
# Minimum observation AFTER a detected VICTORY score screen.  Default keeps
# the W83c 60 s rule, but the unclicked score screen can self-exit the game
# around t~55 s (trip_wv1), so a shorter window is selectable for the win
# control arm.  The DEFEAT arm always keeps the full 60 s minimum.
VICTORY_MIN_SEC = int(os.environ.get("W84_VICTORY_MIN_SEC", "60").strip() or "60")
TAG = "run_" + TRIP
WANT_FN = "RA2F_M1.MAP"
FPS = 31.25                    # frame = *(DWORD*)0x00A8ED84, 32 ms counter
OBSERVE_SEC = 60               # minimum wall-clock observation after entry
POST_WAIT_SEC = 120            # extra grace -> hard cap 180 s (W84 card spec)
TERMINAL_SEC = 20              # post-terminal observation
SAMPLE_INTERVAL = 1.0
SHOT_MARKS = [0, 5, 10, 15, 20, 25, 30, 40, 50, 60,
              75, 90, 105, 120, 135, 150, 165, 180]
TRIP_OUT = C.OUT / TRIP

# Genuine MAP-LOAD errors only.  A defeat/retry dialog is NOT in this list.
ERR_TOKENS = ("无法啟始", "無法啟始", "无法启动", "無法啟動",
              "UnableMapSelect", "Invalid stage", "MSG:UnableMapSelect")
# Score-screen specific controls (never present on the in-game HUD).
SCORE_MARKERS = ("gui:headstaken", "gui:standalonescore", "gui:partime",
                 "gui:yourtime", "gui:score")
VICTORY_MARKERS = ("gui:continue", "繼續戰役", "continue")
# Text needles for the defeat box (memory search; textual proof w/o OCR).
DEFEAT_NEEDLES = ("確定要重新執行此場任務嗎", "重新執行此場任務", "重新執行",
                  "重新执行", "確定要重新", "要重新執行", "restart",
                  "Restart", "RESTART")


class TripError(RuntimeError):
    def __init__(self, msg, **detail):
        super().__init__(msg)
        self.detail = detail


def shot(sink, hwnd, label, bbox=None):
    try:
        p = L.screenshot(sink, TRIP + "_" + label, hwnd, bbox=bbox)
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(p), str(TRIP_OUT / p.name))
        return str(p)
    except Exception as e:
        sink.step("screenshot_error", label=label, error=repr(e))
        return None


def snap(sink, pid, hproc, label):
    cs = L.controls(pid)
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    p = L.read_w59_point(hproc, label)
    sink.step("w59_point", **p)
    return cs, vis, p


def is_map_error(vis):
    return any(any(t.lower() in (v or "").lower() for t in ERR_TOKENS)
               for v in vis)


def terminal_kind(vis):
    """Return one of: victory_score_screen | defeat_restart_dialog | None."""
    s = {(v or "").lower() for v in vis}
    has_continue = any(m in s for m in VICTORY_MARKERS) or \
        any(("continue" in t or "繼續" in t) for t in s)
    has_score = any(m in s for m in SCORE_MARKERS)
    if has_continue and has_score:
        return "victory_score_screen"
    # RA2 defeat / "restart this mission?" 是/否 box: GUI:OK + GUI:Cancel.
    # W78 trip2 ndjson ground truth: ["GUI:Blank","GUI:Cancel","GUI:OK",...]
    if "gui:ok" in s and "gui:cancel" in s:
        return "defeat_restart_dialog"
    return None


def capture_defeat_dialog(sink, pid, hproc, hwnd):
    """Full evidence bundle for the defeat restart dialog (W84 core)."""
    cs = L.controls(pid)
    full = [{"cls": c["cls"], "text": c["text"], "visible": c["visible"],
             "rect": c["rect"], "ctrl_id": c["ctrl_id"], "hwnd": int(c["hwnd"])}
            for c in cs]
    vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
    okc = next((c for c in cs if c["visible"] and (c["text"] or "") == "GUI:OK"), None)
    cancelc = next((c for c in cs if c["visible"] and (c["text"] or "") == "GUI:Cancel"), None)
    blankc = next((c for c in cs if c["visible"] and (c["text"] or "") == "GUI:Blank"), None)
    # crop around the dialog: expand the OK-button rect generously so the
    # whole box is inside; screenshots are stored as evidence, never read for
    # numbers (red line #7).
    crop_path = None
    anchor = okc or cancelc or blankc
    if anchor and anchor.get("rect"):
        l, t_, r, b = anchor["rect"]
        bbox = (max(0, l - 240), max(0, t_ - 140), r + 240, b + 180)
        try:
            p = L.screenshot(sink, TRIP + "_defeat_dialog_crop", hwnd, bbox=bbox)
            TRIP_OUT.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(p), str(TRIP_OUT / p.name))
            crop_path = str(p)
        except Exception as e:
            sink.step("crop_error", error=repr(e))
    mem = None
    try:
        mem = L.memory_search(hproc, DEFEAT_NEEDLES, sink,
                              "defeat_dialog_text", cap_bytes=320 << 20)
    except Exception as e:
        sink.step("memory_search_error", error=repr(e))
    ev = {"controls_full": full,
          "visible_all": vis,
          "ok_ctrl": ({"rect": okc["rect"], "ctrl_id": okc["ctrl_id"],
                       "hwnd": int(okc["hwnd"])} if okc else None),
          "cancel_ctrl": ({"rect": cancelc["rect"], "ctrl_id": cancelc["ctrl_id"],
                           "hwnd": int(cancelc["hwnd"])} if cancelc else None),
          "blank_ctrl": ({"rect": blankc["rect"], "ctrl_id": blankc["ctrl_id"],
                          "hwnd": int(blankc["hwnd"])} if blankc else None),
          "dialog_crop_screenshot": crop_path,
          "memory_text_search": mem}
    sink.step("defeat_dialog_controls_full",
              visible_all=vis, controls_full=full)
    return ev


def config_pre_snapshot(sink):
    """Red line #4: hash every writable sandbox config BEFORE this trip's launch."""
    rows = []
    for name in C.PRISTINE:
        p = C.GAME / name
        rows.append({"file": name,
                     "present": p.is_file(),
                     "size": p.stat().st_size if p.is_file() else None,
                     "sha256": L.sha256_file(p) if p.is_file() else None})
    sink.step("config_pre_snapshot", rows=rows,
              note="byte copies + hashes were saved once at offline setup "
                   "(out/pristine/); this is the per-trip pre-launch hash record")
    return rows


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
        if is_map_error(vis):
            shot(sink, hwnd, "map_error_enter")
            raise TripError("map-load error while waiting to enter " + WANT_FN,
                            visible=vis, w59=p)
        for btn in ("GUI:Play", "GUI:StartGame"):
            if L.find_btn(pid, btn):
                L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
        fn = (p.get("scen_filename") or "")
        if WANT_FN.lower() in fn.lower() and (p.get("frame") or 0) > 30:
            s = shot(sink, hwnd, "enter")
            rec = {"kind": "level_entered", "level": WANT_FN,
                   "elapsed_s": round(time.monotonic() - t0, 2),
                   "t_monotonic": time.monotonic(),
                   "t_utc": L.utc_iso(), "t_local": L.local_iso(),
                   "w59": p, "screenshot": s, "frame_trajectory": traj[-12:]}
            sink.step("level_entered", **rec)
            return p, rec
        time.sleep(1.5)
    shot(sink, hwnd, "timeout_enter")
    raise TripError("timeout waiting to enter " + WANT_FN,
                    frame_trajectory=traj[-20:])


def observe(sink, pid, hproc, hwnd, entry_rec):
    """Continuous observation; NEVER exits before OBSERVE_SEC unless process
    dies; three-way terminal classification; hard cap 180 s."""
    t0 = time.monotonic()
    samples = []
    term = None                 # first terminal-state record
    next_mark = 0
    hard_cap = OBSERVE_SEC + POST_WAIT_SEC
    min_obs_used = OBSERVE_SEC
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
               "visible": vis[:16]}
        samples.append(row)
        sink.step("combat_sample", **row)

        if is_map_error(vis):
            shot(sink, hwnd, "map_error_t%.0f" % t)
            raise TripError("genuine map-load error during combat",
                            visible=vis, w59=p)

        kind = terminal_kind(vis)
        if term is None and kind is not None:
            label = "defeat_full" if kind == "defeat_restart_dialog" else "settlement"
            s = shot(sink, hwnd, label)
            term = {"kind": kind, "t": round(t, 2),
                    "t_monotonic": time.monotonic(),
                    "t_utc": L.utc_iso(), "t_local": L.local_iso(),
                    "w59": p, "visible": vis, "screenshot": s,
                    "frame_at": p.get("frame"),
                    "game_seconds": (p.get("frame") / FPS
                                     if p.get("frame") is not None else None),
                    "wall_from_entry_s": round(
                        time.monotonic() - entry_rec["t_monotonic"], 2)}
            if kind == "defeat_restart_dialog":
                term["dialog_evidence"] = capture_defeat_dialog(sink, pid, hproc, hwnd)
            sink.step("terminal_detected", **{k: v for k, v in term.items()
                                              if k not in ("w59", "dialog_evidence")})
            sink.step("terminal_w59", w59=p)
            if kind == "defeat_restart_dialog" and term.get("dialog_evidence"):
                ev = term["dialog_evidence"]
                sink.step("defeat_dialog_evidence_summary",
                          visible_all=ev["visible_all"],
                          ok_ctrl=ev["ok_ctrl"], cancel_ctrl=ev["cancel_ctrl"],
                          blank_ctrl=ev["blank_ctrl"],
                          crop_screenshot=ev["dialog_crop_screenshot"],
                          memory_hits={k: v["count"] for k, v in
                                       (ev["memory_text_search"] or {"hits": {}})
                                       ["hits"].items()})

        while next_mark < len(SHOT_MARKS) and t >= SHOT_MARKS[next_mark]:
            shot(sink, hwnd, "combat_t%02d" % SHOT_MARKS[next_mark])
            next_mark += 1

        if not L.process_alive(pid):
            sink.step("game_process_exited_during_observation", t=round(t, 2))
            break
        min_obs = OBSERVE_SEC
        if term is not None and term["kind"] == "victory_score_screen":
            min_obs = min(OBSERVE_SEC, VICTORY_MIN_SEC)
        min_obs_used = min_obs
        if t >= min_obs and term is not None:
            break
        if t >= hard_cap:
            sink.step("observation_hard_cap", t=round(t, 2),
                      terminal=term["kind"] if term else None)
            break
        time.sleep(SAMPLE_INTERVAL)

    # frame-stall confirmation on the terminal screen
    stall = None
    if term is not None and L.process_alive(pid):
        p2 = L.read_w59_point(hproc, "terminal_frame_confirm")
        f1, f2 = term["frame_at"], p2.get("frame")
        stall = {"frame_at_terminal": f1, "frame_2s_later": f2,
                 "frame_stalled": (f1 is not None and f1 == f2)}
        sink.step("terminal_frame_stall", **stall)
        term["frame_stall"] = stall
        time.sleep(2.0)
        term["screenshot_confirm"] = shot(sink, hwnd, "settlement_confirm")

    traj = {"n_samples": len(samples),
            "frames": [s["frame"] for s in samples],
            "t": [s["t"] for s in samples],
            "eog": [s["0x34AC"] for s in samples],
            "stage": [s["0x35A0"] for s in samples],
            "fn": [s["0x125C"] for s in samples]}
    sink.step("combat_trajectory", **traj)
    return {"samples": samples, "trajectory": traj, "terminal": term,
            "elapsed_s": round(time.monotonic() - t0, 2),
            "min_obs_used": min_obs_used,
            "min_window_met": (time.monotonic() - t0) >= min_obs_used}


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
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None, "lock_taken": False}
    ok = False
    outcome = "unknown"
    result = {"mode": MODE, "trip": TRIP, "want_fn": WANT_FN,
              "observe_sec": OBSERVE_SEC, "hard_cap_s": OBSERVE_SEC + POST_WAIT_SEC,
              "fps_assumed": FPS}
    terminal_rep = None
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG, mode=MODE,
                  trip=TRIP, observe_sec=OBSERVE_SEC, shot_marks=SHOT_MARKS,
                  note="lock per trip; three-way terminal detection (180 s cap); "
                       "defeat dialog evidence capture; release in finally")
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
        C.lock_claim_w84("W84 real-machine trip %s mode=%s: capture the defeat "
                         "restart dialog (missing third terminal state), never "
                         "click OK/Cancel" % (TRIP, MODE))
        state["lock_taken"] = True
        sink.step("lock_claimed", owner="w84", content=C.lock_read())

        # ---- (0b) config pre-launch hash snapshot --------------------------
        result["config_pre"] = config_pre_snapshot(sink)

        # ---- (1) launch ----------------------------------------------------
        if L.list_gamemd():
            raise TripError("residual gamemd before launch (not ours)")
        launcher = L.launch_game(sink)
        pid = L.wait_for_pid(launcher, sink)
        state["pid"] = pid
        result["pid"] = pid
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

        # ---- (3) Soviet badge ----------------------------------------------
        wr = L.rect(hwnd) or [0, 0, 1707, 960]
        L.force_foreground(hwnd)
        bx, by = wr[0] + 210, wr[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        shot(sink, hwnd, "after_SOVIET_badge")
        snap(sink, pid, hproc, "after_badge")
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # ---- (4) enter the mission ----------------------------------------
        entry, entry_rec = wait_ingame(sink, pid, hproc, hwnd)
        result["entry_w59"] = entry
        result["entry"] = entry_rec

        # ---- (5) continuous observation -----------------------------------
        obs = observe(sink, pid, hproc, hwnd, entry_rec)
        result["observation"] = {
            "elapsed_s": obs["elapsed_s"],
            "min_window_met": obs["min_window_met"],
            "n_samples": obs["trajectory"]["n_samples"],
            "terminal": obs["terminal"],
            "trajectory": obs["trajectory"]}
        sink.step("combat_samples_full", samples=obs["samples"])
        term = obs["terminal"]

        # ---- (6) terminal handling ----------------------------------------
        if term is not None and term["kind"] == "victory_score_screen":
            clicked = False
            for btn in ("GUI:Continue", "繼續戰役"):
                if L.find_btn(pid, btn):
                    L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
                    clicked = True
                    break
            sink.step("settlement_button_clicked", clicked=clicked,
                      visible_at_settlement=term["visible"])
            terminal_rep = observe_terminal(sink, pid, hproc, hwnd)
            result["terminal"] = terminal_rep
            outcome = "VICTORY_RESULT_AND_TERMINATION_OK"
            ok = bool(terminal_rep["no_extra_start"] and obs["min_window_met"])
        elif term is not None and term["kind"] == "defeat_restart_dialog":
            # TASK FAILURE, NOT AN ERROR.  Do NOT click OK/Cancel (OK would
            # restart the mission).  Full evidence already captured inline.
            sink.step("defeat_dialog_recorded",
                      note="RA2 'restart this mission?' box = our side was "
                           "annihilated; deliberately NOT clicked, NOT labelled "
                           "error; full control/text/memory evidence captured",
                      visible=term["visible"])
            terminal_rep = observe_terminal(sink, pid, hproc, hwnd)
            result["terminal"] = terminal_rep
            outcome = "TASK_FAILED_DEFEAT_RESTART_DIALOG"
            ok = True   # a clean, correctly-classified terminal state
        else:
            outcome = "NO_RESULT_WITHIN_%ds" % (OBSERVE_SEC + POST_WAIT_SEC)
            terminal_rep = observe_terminal(sink, pid, hproc, hwnd)
            result["terminal"] = terminal_rep
            ok = True   # timeout is a valid, correctly-classified terminal state
        sink.step("trip_result", ok=ok, outcome=outcome, mode=MODE,
                  terminal_kind=(term or {}).get("kind"),
                  terminal_t=(term or {}).get("t"),
                  frame_at=(term or {}).get("frame_at"))
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
            C.lock_release("W84 trip %s (%s) FINISHED (ok=%s, outcome=%s): "
                           "self-launched gamemd (pid=%s) closed, residual=%d; "
                           "restored owner=lead."
                           % (TRIP, MODE, ok, outcome, pid, len(residual)))
        sink.step("lock_released", lock_content=C.lock_read())
        payload = {"mode": MODE, "trip": TRIP, "ok": ok,
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
                  outcome=outcome, mode=MODE,
                  gamemd_residual=residual, lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

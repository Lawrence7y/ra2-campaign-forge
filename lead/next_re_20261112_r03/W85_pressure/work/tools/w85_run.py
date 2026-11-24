#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W85 REAL-MACHINE trip - one arm, one mission, per-trip lock.

Env:
  W85_ARM = pressure | control   (label only; which package is installed
                                  decides the arm; the runner verifies the
                                  installed map matches the arm's package)

PURPOSE (pilot): heavy-force engagement vs static control on the SAME map,
same layout, same object counts; single variable = enemy units mission
(Hunt vs Guard).  Primary statistic (pre-registered per LEAD ruling 2026-11-14):
window-thread CPU consumption rate = cumulative thread CPU time / measured
wall time in the analysis window (single-core occupancy).  Median/p95 per-tick
are secondary.  NO per-tick-cost or FPS interpretation of CPU/count.

PRE-REGISTERED VERDICT RULES (frozen BEFORE any trip, from LEAD message):
  ratio = rate_pressure / rate_control (same window rule both arms).
  If ratio < 1.10 AND pressure 0xA8ED50 nonzero-tick ratio >= 3x control's
  (combat genuinely heavier): conclusion text = 「本场景、本剂量范围内未观测到
  与兵力成比例的负载抬升」.  If ratio >= 1.10: 初估抬升 X%，需下一轮剂量反应
  确认.  NO significance language (no 显著/p/CI) -- pilot only.

INDEPENDENT LOAD EVIDENCE (>=2 required, collected here):
  E1 0xA8ED50 nonzero-tick ratio / peak / value histogram (both arms);
  E2 screenshot pixel differences (engagement vs control, within-arm
     consecutive) -- computed offline by w85_analyze.py;
  E3 candidate proxies B0CE88 / 87E8E0 per tick (secondary);
  E4 actual 0xA8ED84 counter rate (counts/s) under load (ruling guard).

LOCK DISCIPLINE (per trip, never held across offline phases):
  * BEFORE launch: require lock owner==lead (or absent -> bootstrap lead),
    0 live gamemd.  Claim owner=w85.  ALWAYS release back to owner=lead
    in finally.

REAL-MACHINE DISCIPLINE:
  * WMI Win32_Process.Create launches ONLY the sandbox gamemd.exe.
  * Read-only OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) + RPM;
    read-only OpenThread(THREAD_QUERY_INFORMATION) + GetThreadTimes +
    QueryThreadCycleTime on the window thread.
  * NO WriteProcessMemory / breakpoints / injection / exe edits.
  * close_game only touches the pid WE launched.  No blanket taskkill.

PER-TRIP CONFIG: RA2MD.INI / ddraw.ini / RA2MD.INI.benchbak byte-restored
from pristine copies after the trip (keeps both arms on identical display
config).  BATTLEMD.INI is the INSTALLED PACKAGE file -- NOT restored per trip
(finalize handles the full tree proof).
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w85_lib as L
import w85_common as C

ARM = os.environ.get("W85_ARM", "pressure").strip().lower()
if ARM not in ("pressure", "control"):
    raise SystemExit("W85_ARM must be pressure|control")
TAG = "run_" + ARM
WANT_FN = "RA2F_M1.MAP"
FPS = 31.25                    # nominal: frame = *(DWORD*)0x00A8ED84, 32 ms timer
TARGET_INGAME_S = 300.0        # sampling target from first frame>0
MIN_VALID_S = 240.0            # pre-registered minimum valid ingame window
HARD_CAP_S = 360.0             # hard cap
SAMPLE_INTERVAL_MS = 6.0       # 6 ms级采样（卡面要求）
SHOT_MARKS = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
TRIP_OUT = C.OUT / ("trip_" + ARM)

ERR_TOKENS = ("无法啟始", "無法啟始", "无法启动", "無法啟動",
              "UnableMapSelect", "Invalid stage", "MSG:UnableMapSelect")
SCORE_MARKERS = ("gui:headstaken", "gui:standalonescore", "gui:partime",
                 "gui:yourtime", "gui:score")
VICTORY_MARKERS = ("gui:continue", "繼續戰役", "continue")
DEFEAT_NEEDLES = ("確定要重新執行此場任務嗎", "重新執行此場任務", "重新執行",
                  "重新执行", "確定要重新", "要重新執行")

# 采样地址（与 W12/W19/W20 口径一致；只读）
ADDR = {
    "frame": 0x00A8ED84,       # dword: 32 ms game timer counter
    "mode": 0x00A8B238,        # dword
    "A8ED50": 0x00A8ED50,      # dword: candidate BulletCnt (semantics unproven)
    "B0CE88": 0x00B0CE88,      # dword: candidate proxy (semantics undefined)
    "X87E8E0": 0x0087E8E0,     # dword: candidate proxy (semantics undefined)
}
SCEN_PTR = 0x00A8B230
PER_TRIP_CONFIG_RESTORE = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak")

# ---- thread instrumentation bindings (W20-proven, read-only) ----
u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
winmm = ctypes.WinDLL("winmm")
PF = ctypes.POINTER(wt.FILETIME)
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.GetThreadTimes.restype = wt.BOOL
k32.GetThreadTimes.argtypes = [wt.HANDLE, PF, PF, PF, PF]
k32.QueryThreadCycleTime.restype = wt.BOOL
k32.QueryThreadCycleTime.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_ulonglong)]
THREAD_QUERY_INFORMATION = 0x0040


def ft_ms(f):
    return (((int(f.dwHighDateTime) & 0xFFFFFFFF) << 32)
            | (int(f.dwLowDateTime) & 0xFFFFFFFF)) / 1e4


def win_tid_of(hwnd):
    q = wt.DWORD(0)
    ret = u.GetWindowThreadProcessId(hwnd, ctypes.byref(q))
    return int(ret) or None


def query_thread(hh):
    c = wt.FILETIME(); e = wt.FILETIME(); k = wt.FILETIME(); uu = wt.FILETIME()
    if not k32.GetThreadTimes(hh, ctypes.byref(c), ctypes.byref(e),
                              ctypes.byref(k), ctypes.byref(uu)):
        return None
    cyc = ctypes.c_ulonglong(0)
    okc = k32.QueryThreadCycleTime(hh, ctypes.byref(cyc))
    return ft_ms(k), ft_ms(uu), (int(cyc.value) if okc else None)


def fg_is(pid):
    fg = u.GetForegroundWindow()
    p = wt.DWORD(0)
    u.GetWindowThreadProcessId(fg, ctypes.byref(p))
    return p.value == pid


class TripError(RuntimeError):
    def __init__(self, msg, **detail):
        super().__init__(msg)
        self.detail = detail


def shot(sink, hwnd, label, bbox=None):
    try:
        p = L.screenshot(sink, TRIP_TAG_SHOT(label), hwnd, bbox=bbox)
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(p), str(TRIP_OUT / p.name))
        return str(TRIP_OUT / p.name)
    except Exception as e:
        sink.step("screenshot_error", label=label, error=repr(e))
        return None


def TRIP_TAG_SHOT(label):
    return "%s_%s" % (TAG, label)


def read_sample_addrs(hproc):
    vals, failed = {}, []
    for k, a in ADDR.items():
        b = L.rpm(hproc, a, 4)
        if b is None:
            failed.append(k)
            continue
        vals[k] = int.from_bytes(b, "little")
    if failed:
        return None, failed
    return vals, []


def read_scen(hproc):
    out = {}
    b = L.rpm(hproc, SCEN_PTR, 4)
    scen = int.from_bytes(b, "little") if b else None
    out["scen_ptr"] = scen
    if scen and scen > 0x10000:
        out["scen_filename"] = L.read_cstr(hproc, scen + 0x125C, 260)
        b_eog = L.rpm(hproc, scen + 0x34AC, 1)
        out["scen_end_of_game"] = b_eog[0] if b_eog else None
        b_stg = L.rpm(hproc, scen + 0x35A0, 2)
        out["scen_stage_idx"] = int.from_bytes(b_stg, "little") if b_stg else None
    return out


def is_map_error(vis):
    return any(any(t.lower() in (v or "").lower() for t in ERR_TOKENS)
               for v in vis)


def terminal_kind(vis):
    s = {(v or "").lower() for v in vis}
    # engine fatal error dialog (graceful internal error, process alive but
    # halted) -- observed at heavy engagement doses; treat as terminal.
    if any("internal error" in t for t in s):
        return "engine_internal_error_dialog"
    has_continue = any(m in s for m in VICTORY_MARKERS) or \
        any(("continue" in t or "繼續" in t) for t in s)
    has_score = any(m in s for m in SCORE_MARKERS)
    if has_continue and has_score:
        return "victory_score_screen"
    if "gui:ok" in s and "gui:cancel" in s:
        return "defeat_restart_dialog"
    return None


def wait_main_menu(pid, sink, timeout_s=150):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if L.find_btn(pid, "GUI:SinglePlayer"):
            sink.step("main_menu_ready", elapsed_s=round(time.monotonic() - t0, 2))
            return
        time.sleep(1.5)
    raise TripError("main menu timeout (%ss)" % timeout_s)


def wait_ingame(sink, pid, hproc, hwnd, timeout_s=240):
    t0 = time.monotonic()
    traj = []
    while time.monotonic() - t0 < timeout_s:
        cs = L.controls(pid)
        vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
        p = read_scen(hproc)
        b = L.rpm(hproc, ADDR["frame"], 4)
        frame = int.from_bytes(b, "little") if b else None
        traj.append({"t": round(time.monotonic() - t0, 1),
                     "fn": p.get("scen_filename"), "frame": frame,
                     "stage": p.get("scen_stage_idx")})
        if is_map_error(vis):
            shot(sink, hwnd, "map_error_enter")
            raise TripError("map-load error while waiting to enter " + WANT_FN,
                            visible=vis, scen=p)
        for btn in ("GUI:Play", "GUI:StartGame"):
            if L.find_btn(pid, btn):
                L.click(pid, btn, sink, wait_s=2.0, label="click_" + btn)
        fn = (p.get("scen_filename") or "")
        if WANT_FN.lower() in fn.lower() and (frame or 0) > 30:
            s = shot(sink, hwnd, "enter")
            rec = {"kind": "level_entered", "level": WANT_FN,
                   "elapsed_s": round(time.monotonic() - t0, 2),
                   "t_monotonic": time.monotonic(),
                   "t_utc": L.utc_iso(), "t_local": L.local_iso(),
                   "scen": p, "frame": frame, "screenshot": s,
                   "frame_trajectory": traj[-12:]}
            sink.step("level_entered", **rec)
            return rec
        time.sleep(1.0)
    shot(sink, hwnd, "timeout_enter")
    raise TripError("timeout waiting to enter " + WANT_FN,
                    frame_trajectory=traj[-30:])


def config_pre_snapshot(sink):
    rows = []
    for name in C.PRISTINE:
        p = C.GAME / name
        rows.append({"file": name,
                     "present": p.is_file(),
                     "size": p.stat().st_size if p.is_file() else None,
                     "sha256": L.sha256_file(p) if p.is_file() else None})
    sink.step("config_pre_snapshot", rows=rows,
              note="pristine byte copies were saved once at offline setup "
                   "(out/pristine/); per-trip pre-launch hash record")
    return rows


def restore_per_trip_configs(sink):
    rows = []
    for name in PER_TRIP_CONFIG_RESTORE:
        src = C.OUT / "pristine" / name
        dst = C.GAME / name
        if not src.is_file():
            rows.append({"file": name, "restored": False, "note": "no pristine copy"})
            continue
        if dst.is_file():
            shutil.copyfile(src, dst)
        rows.append({"file": name,
                     "post_sha256": L.sha256_file(dst) if dst.is_file() else None,
                     "expected": L.sha256_file(src),
                     "byte_identical": (dst.is_file()
                                        and dst.read_bytes() == src.read_bytes())})
    sink.step("per_trip_config_restore", rows=rows,
              all_ok=all(r.get("byte_identical") for r in rows))
    return rows


def main() -> int:
    sink = L.Sink(TAG)
    state = {"pid": None, "hwnd": None, "hproc": None, "lock_taken": False}
    ok = False
    outcome = "unknown"
    result = {"arm": ARM, "want_fn": WANT_FN,
              "sample_interval_ms_target": SAMPLE_INTERVAL_MS,
              "target_ingame_s": TARGET_INGAME_S, "min_valid_s": MIN_VALID_S,
              "hard_cap_s": HARD_CAP_S, "fps_assumed_nominal": FPS}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG, arm=ARM,
                  note="pilot trip: pressure vs control, single variable = "
                       "enemy mission Hunt/Guard; primary = thread CPU "
                       "consumption rate; lock per trip")
        # ---- (0) installed-map identity check ------------------------------
        pkg_map = C.PKG[ARM] / "RA2F_M1.MAP"
        installed_map = C.GAME / "RA2F_M1.MAP"
        if not installed_map.is_file():
            raise TripError("installed RA2F_M1.MAP missing in sandbox; run "
                            "w85_offline.py with W85_PKG=%s first" % ARM)
        map_match = (installed_map.read_bytes() == pkg_map.read_bytes())
        result["installed_map_matches_arm_package"] = map_match
        sink.step("installed_map_identity", arm=ARM, match=map_match,
                  installed_sha256=L.sha256_file(installed_map))
        if not map_match:
            raise TripError("sandbox installed map does not match arm package %s" % ARM)

        # ---- (0b) LOCK GATE -------------------------------------------------
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
        C.lock_claim_w85("W85 real-machine trip arm=%s: pilot pressure vs "
                         "control, same map/layout/objects, single variable "
                         "= enemy mission Hunt/Guard" % ARM)
        state["lock_taken"] = True
        sink.step("lock_claimed", owner="w85", content=C.lock_read())

        # ---- (0c) config pre-launch hash snapshot ---------------------------
        result["config_pre"] = config_pre_snapshot(sink)

        # ---- (1) launch -----------------------------------------------------
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
        shot(sink, hwnd, "S0_main_menu")

        # ---- (2) campaign menu --------------------------------------------
        L.click(pid, "GUI:SinglePlayer", sink, wait_s=1.2, label="click_SinglePlayer")
        L.click(pid, "GUI:NewCampaign", sink, wait_s=2.0, label="click_NewCampaign")
        shot(sink, hwnd, "S2_campaign_menu")

        # ---- (3) Soviet badge ----------------------------------------------
        wr = L.rect(hwnd) or [0, 0, 1707, 960]
        L.force_foreground(hwnd)
        bx, by = wr[0] + 210, wr[1] + 285
        L.real_mouse_click(sink, "click_SOVIET_badge", bx, by, wait_s=3.0)
        shot(sink, hwnd, "after_SOVIET_badge")
        L.key(L.VK_RETURN, sink, "Enter_skip_1")
        L.key(L.VK_RETURN, sink, "Enter_skip_2")

        # ---- (4) enter the mission ----------------------------------------
        entry = wait_ingame(sink, pid, hproc, hwnd)
        result["entry"] = entry
        entry_t = entry["t_monotonic"]

        # ---- (5) sampling: 6 ms cadence, zero input ------------------------
        # thread handle for the window thread (read-only instrumentation)
        th = {"tid": win_tid_of(hwnd) if hwnd else None, "hh": None,
              "n_open_fail": 0}
        try:
            tbp_ret = int(winmm.timeBeginPeriod(1))
        except Exception as e:
            tbp_ret = "error:%r" % e
        sink.step("timebeginperiod", ret=tbp_ret)

        nd_path = TRIP_OUT / "run.ndjson"
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        nd = nd_path.open("w", encoding="utf-8", newline="\n")

        def wrow(rec):
            nd.write(json.dumps(rec, ensure_ascii=False, sort_keys=True,
                                default=str, separators=(",", ":")) + "\n")
            nd.flush()

        interval_ns = int(round(SAMPLE_INTERVAL_MS * 1e6))
        seq = 0
        prev_t_ns = None
        sched_anchor = None
        prev_cyc = None
        prev_cpu_ms = None
        a8ed50_first = None
        t_first_pos = None
        stop_reason = None
        term = None
        next_shot = 0
        last_ui_check = 0.0
        n_fg_loss = 0
        n_read_fail = 0
        n_winthread_fail = 0
        sg_t = time.perf_counter_ns()
        t_loop0 = time.perf_counter_ns()
        ec = wt.DWORD(0)
        STILL_ACTIVE = 259
        sink.step("sampling_begin", arm=ARM, pid=pid,
                  note="zero input from here; 6 ms cadence; screenshots at "
                       "marks; UI/terminal check at 1 Hz")
        while True:
            t_ns = time.perf_counter_ns()
            vals, failed = read_sample_addrs(hproc)
            if failed:
                n_read_fail += 1
            # ---- window thread CPU (main channel), read-only ----
            wt_err = None
            wtid = None
            wk = wu = wcyc = None
            if hwnd and u.IsWindow(hwnd):
                wtid = win_tid_of(hwnd)
            if wtid is None:
                tops = [h for h in L.top_windows(pid)
                        if L.wcls(h) == L.GAME_WND_CLASS]
                if tops:
                    hwnd = tops[0]
                    state["hwnd"] = hwnd
                    wtid = win_tid_of(hwnd)
            if wtid:
                if th["tid"] != wtid or th["hh"] is None:
                    hh = k32.OpenThread(THREAD_QUERY_INFORMATION, False, wtid)
                    if hh:
                        th["tid"], th["hh"] = wtid, hh
                    else:
                        th["n_open_fail"] += 1
                hh = th["hh"]
                if hh:
                    q = query_thread(hh)
                    if q is not None:
                        wk, wu, wcyc = q
                    else:
                        wt_err = "GetThreadTimes_fail"
                        n_winthread_fail += 1
                else:
                    wt_err = "OpenThread_fail"
                    n_winthread_fail += 1
            else:
                wt_err = "window_gone"
                n_winthread_fail += 1
            cyc_d = None
            if wcyc is not None and prev_cyc is not None:
                cyc_d = wcyc - prev_cyc
            if wcyc is not None:
                prev_cyc = wcyc
            cpu_d = None
            if wk is not None and wu is not None and prev_cpu_ms is not None:
                cpu_d = (wk + wu) - prev_cpu_ms
            if wk is not None and wu is not None:
                prev_cpu_ms = wk + wu
            if vals is not None and a8ed50_first is None \
                    and (vals.get("A8ED50") or 0) != 0:
                a8ed50_first = {"t_perf_ns": t_ns, "value": vals["A8ED50"],
                                "frame": vals.get("frame"),
                                "ingame": t_first_pos is not None}
                sink.step("a8ed50_first_nonzero", **a8ed50_first)
            seq += 1
            interval_ms = ((t_ns - prev_t_ns) / 1e6) if prev_t_ns is not None else None
            if sched_anchor is None:
                sched_anchor = t_ns
            sched_anchor += interval_ns
            if (t_ns - sched_anchor) > 4 * interval_ns:
                sched_anchor = t_ns
            fg = fg_is(pid)
            if not fg:
                n_fg_loss += 1
            elapsed_ingame = ((t_ns - t_first_pos) / 1e9) if t_first_pos else None
            rec = {"kind": "sample", "seq": seq, "arm": ARM,
                   "t_perf_ns": t_ns, "t_utc": L.utc_iso(),
                   "t_monotonic": time.monotonic(),
                   "elapsed_ingame_s": (round(elapsed_ingame, 6)
                                        if elapsed_ingame is not None else None),
                   "interval_ms_actual": (round(interval_ms, 4)
                                          if interval_ms is not None else None),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed,
                   "win_foreground": fg,
                   "win_tid": wtid, "win_thread_err": wt_err,
                   "win_kernel_ms": wk, "win_user_ms": wu,
                   "win_cpu_ms": (round(wk + wu, 6)
                                  if (wk is not None and wu is not None) else None),
                   "win_cycle": wcyc, "win_cyc_delta": cyc_d,
                   "win_cpu_ms_delta": (round(cpu_d, 6)
                                        if cpu_d is not None else None)}
            if vals is not None:
                rec.update(vals)
            wrow(rec)
            prev_t_ns = t_ns
            # first frame>0 after StartGame => ingame clock starts
            if t_first_pos is None and vals is not None \
                    and vals.get("frame", 0) > 0:
                t_first_pos = t_ns
                sink.step("first_frame_positive",
                          {"frame": vals["frame"],
                           "after_startgame_s": round((t_ns - sg_t) / 1e9, 3)})
            # ---- 1 Hz UI/terminal/scen check + screenshot marks ----
            now_mono = time.monotonic()
            if now_mono - last_ui_check >= 1.0:
                last_ui_check = now_mono
                cs = L.controls(pid)
                vis = sorted({c["text"] for c in cs if c["visible"] and c["text"]})
                sc = read_scen(hproc)
                sink.step("ui_check_1hz", t_ingame=elapsed_ingame, visible=vis[:20],
                          scen_fn=sc.get("scen_filename"),
                          eog=sc.get("scen_end_of_game"))
                if is_map_error(vis):
                    shot(sink, hwnd, "map_error_t")
                    stop_reason = "map_load_error"
                    break
                kind = terminal_kind(vis)
                if kind and term is None:
                    s = shot(sink, hwnd, "terminal_" + kind)
                    term = {"kind": kind,
                            "t_ingame_s": (round(elapsed_ingame, 2)
                                           if elapsed_ingame is not None else None),
                            "t_utc": L.utc_iso(), "visible": vis,
                            "screenshot": s,
                            "scen": sc}
                    sink.step("terminal_detected", **{k: v for k, v in term.items()
                                                      if k != "scen"})
                while next_shot < len(SHOT_MARKS) and elapsed_ingame is not None \
                        and elapsed_ingame >= SHOT_MARKS[next_shot]:
                    shot(sink, hwnd, "combat_t%03d" % SHOT_MARKS[next_shot])
                    next_shot += 1
            # ---- stop rules (cheap per-sample; Toolhelp residual check at 1Hz) ----
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            if not alive:
                stop_reason = "process_exited"
                sink.step("game_process_exited", t_ingame=elapsed_ingame,
                          exit_code=ec.value)
                break
            if elapsed_ingame is not None:
                if elapsed_ingame >= TARGET_INGAME_S:
                    stop_reason = "target_reached"
                    break
                if elapsed_ingame >= HARD_CAP_S:
                    stop_reason = "hard_cap"
                    break
            elif (time.perf_counter_ns() - sg_t) / 1e9 > 420.0:
                stop_reason = "no_first_frame_timeout"
                break
            now2 = time.perf_counter_ns()
            d = (sched_anchor - now2) / 1e9
            if d > 0:
                time.sleep(d)
        dur_ingame = ((time.perf_counter_ns() - t_first_pos) / 1e9
                      if t_first_pos is not None else 0.0)
        nd.close()
        valid = (t_first_pos is not None and dur_ingame >= MIN_VALID_S
                 and stop_reason not in ("map_load_error",))
        result["sampling"] = {
            "n_samples": seq, "ingame_duration_s": round(dur_ingame, 3),
            "stop_reason": stop_reason, "min_valid_met": valid,
            "n_read_fail": n_read_fail, "n_winthread_fail": n_winthread_fail,
            "n_fg_loss_samples": n_fg_loss,
            "a8ed50_first_nonzero": a8ed50_first,
            "ndjson": str(nd_path),
            "loop_wall_s": round((time.perf_counter_ns() - t_loop0) / 1e9, 3)}
        sink.step("sampling_end", **result["sampling"])
        if term is not None:
            result["terminal"] = term
        if not valid:
            if term is not None and term["kind"] == "defeat_restart_dialog":
                outcome = ("INSUFFICIENT_WINDOW_DEFEAT_DIALOG_AT_%.0fs"
                           % (term["t_ingame_s"] or -1))
            elif term is not None:
                outcome = ("INSUFFICIENT_WINDOW_TERMINAL_%s" % term["kind"])
            else:
                outcome = "NO_RESULT_%s" % stop_reason
            ok = True   # a cleanly classified failure is a valid pilot datum
        else:
            outcome = "VALID_WINDOW_%s" % stop_reason
            ok = True
        sink.step("trip_result", ok=ok, outcome=outcome, arm=ARM,
                  ingame_s=result["sampling"]["ingame_duration_s"],
                  min_valid_met=valid, terminal=(term or {}).get("kind"))
    except TripError as e:
        outcome = "BLOCKED: " + str(e)
        sink.step("trip_blocked", outcome=outcome, detail=e.detail)
        try:
            nd.close()
        except Exception:
            pass
    except Exception as e:
        outcome = "FATAL: " + repr(e)
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
        try:
            nd.close()
        except Exception:
            pass
    finally:
        pid, hwnd, hproc = state["pid"], state["hwnd"], state["hproc"]
        try:
            winmm.timeEndPeriod(1)
        except Exception:
            pass
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
        restore_rows = restore_per_trip_configs(sink)
        sink.step("trip_cleanup", close_steps=close_steps,
                  gamemd_residual=residual, residual_zero=(len(residual) == 0))
        if state["lock_taken"]:
            C.lock_release("W85 trip arm=%s FINISHED (outcome=%s): "
                           "self-launched gamemd (pid=%s) closed, residual=%d; "
                           "restored owner=lead."
                           % (ARM, outcome, pid, len(residual)))
        sink.step("lock_released", lock_content=C.lock_read())
        result["outcome"] = outcome
        result["ok"] = ok
        result["close_steps"] = close_steps
        result["gamemd_residual"] = residual
        result["config_restore_rows"] = restore_rows
        result["w59_offsets"] = {"scen_ptr": "0x00A8B230", "filename": "+0x125C",
                                 "stage_idx": "+0x35A0", "end_of_game": "+0x34AC",
                                 "frame": "0x00A8ED84",
                                 "A8ED50": "0x00A8ED50", "B0CE88": "0x00B0CE88",
                                 "X87E8E0": "0x0087E8E0"}
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        (TRIP_OUT / "TRIP_RESULT.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        (C.OUT / ("TRIP_RESULT_%s.json" % ARM)).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok, arm=ARM,
                  outcome=outcome, gamemd_residual=residual,
                  lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

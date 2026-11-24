#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W94 REAL-MACHINE trip - ONE trip of ONE matrix cell (parameterized W90 run).

Env (all supplied by batch_runner.py; never launched by hand):
  W94_CELL        = cell id, e.g. c1    (design = w94_design_<cell>.json;
                     pkg = pkg_<cell>; the runner verifies the installed map
                     matches the cell package)
  W94_TRIP        = trip dir NAME under out/, e.g. trip_c4_r2.  MUST NOT exist;
                     never reused (W88 U1/D5 lesson).  Under --resume the
                     orchestrator moves incomplete leftovers to out/aborted/
                     first, so a fresh dir always exists.
  W94_TARGET_S    = sampling target seconds from first frame>0 (default 155)
  W94_MIN_VALID_S = minimum valid window seconds (default 150)
  W94_HARD_CAP_S  = hard cap seconds (default 200)
  W94_SAMPLE_MS   = sampling cadence ms (default 6)
  W94_RENDER      = 1 (optional: attach the W86 RPM framebeat read-only channel
                     AFTER the game is in-mission; stdout+CSV land in
                     <trip>/render_channel/; failure recorded, trip continues)

D1 FORENSICS: same as W90 - except*.txt (fresh vs pre_existing classified by
  mtime; ra2youli ships a 2026-11-13 except.txt, 26,272 B) + WER events +
  ndjson tail, captured IMMEDIATELY on engine-error terminal or process exit,
  BEFORE any cleanup.

D2 OUTCOME SEMANTICS (unchanged from W90 v2): ok=true ONLY for >=MIN_VALID
  window with no terminal, or victory screen; defeat dialog / engine error /
  abnormal exit => ok=false.

D4 INPUT ARCHIVE: installed RA2F_M1.MAP / BATTLEMD.INI / MAPSELMD.INI +
  cell design JSON into <trip>/installed_inputs/ + sha256.

REAL-MACHINE DISCIPLINE (inherited unchanged from W90):
  * WMI Win32_Process.Create launches ONLY the sandbox gamemd.exe.
  * Read-only RPM + read-only thread time queries.  NO injection/debugger.
  * close_game only touches the pid WE launched.  No blanket taskkill.
  * Per-trip: RA2MD.INI / ddraw.ini byte-restored from pristine + hash proof.
  * LOCK: batch_runner writes owner=w94-batchrun at trip start AND at trip end
    (even on crash).  This runner only GATES on it (owner must start with
    "w94", zero gamemd before launch) and never rewrites the lock itself.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w94_lib as L
import w94_common as C

CELL = os.environ.get("W94_CELL", "").strip()
TRIP_NAME = os.environ.get("W94_TRIP", "").strip()
if not CELL or not re.fullmatch(r"[A-Za-z0-9_\-]+", CELL):
    raise SystemExit("W94_CELL missing/invalid cell id: %r" % CELL)
if not TRIP_NAME or not re.fullmatch(r"trip_[A-Za-z0-9_\-]+", TRIP_NAME):
    raise SystemExit("W94_TRIP missing/invalid trip dir name: %r" % TRIP_NAME)
# HARD REQUIREMENT (inherited): unique trip dirs, never silently reused.  The
# orchestrator guarantees freshness; this runner fails closed anyway.
TRIP_OUT = C.OUT / TRIP_NAME
if TRIP_OUT.exists():
    raise SystemExit("trip dir already exists (never reuse): %s" % TRIP_OUT)
TAG = "run_" + TRIP_NAME
STEP = CELL   # compatibility alias used by the W90-derived code paths
# [W96 fix] _trip_suffix was referenced (result dict + TRIP_RESULT_<step><suffix>
# file name) but never defined in the W94 copy => NameError at trip start.
# Naming contract: trip_<cell>_r<k> -> TRIP_RESULT_<cell>_r<k>.json
_trip_suffix = TRIP_NAME[5 + len(CELL):]
assert TRIP_NAME == "trip_" + CELL + _trip_suffix and _trip_suffix.startswith("_"), \
    (TRIP_NAME, CELL, _trip_suffix)
WANT_FN = "RA2F_M1.MAP"
FPS = 31.25                    # nominal: frame = *(DWORD*)0x00A8ED84, 32 ms timer
TARGET_INGAME_S = float(os.environ.get("W94_TARGET_S", "155") or 155)
MIN_VALID_S = float(os.environ.get("W94_MIN_VALID_S", "150") or 150)
HARD_CAP_S = float(os.environ.get("W94_HARD_CAP_S", "200") or 200)
SAMPLE_INTERVAL_MS = float(os.environ.get("W94_SAMPLE_MS", "6") or 6)
SHOT_MARKS = list(range(0, int(HARD_CAP_S) + 1, 30))
POST_ENGINE_ERROR_SAMPLE_S = 5.0   # keep sampling briefly after the dialog

ERR_TOKENS = ("无法啟始", "無法啟始", "无法启动", "無法啟動",
              "UnableMapSelect", "Invalid stage", "MSG:UnableMapSelect")
SCORE_MARKERS = ("gui:headstaken", "gui:standalonescore", "gui:partime",
                 "gui:yourtime", "gui:score")
VICTORY_MARKERS = ("gui:continue", "繼續戰役", "continue")
DEFEAT_NEEDLES = ("確定要重新執行此場任務嗎", "重新執行此場任務", "重新執行",
                  "重新执行", "確定要重新", "要重新執行")

ADDR = {
    "frame": 0x00A8ED84,
    "mode": 0x00A8B238,
    "A8ED50": 0x00A8ED50,
    "B0CE88": 0x00B0CE88,
    "X87E8E0": 0x0087E8E0,
}
SCEN_PTR = 0x00A8B230
PER_TRIP_CONFIG_RESTORE = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak")
INSTALLED_INPUTS = ("RA2F_M1.MAP", "BATTLEMD.INI", "MAPSELMD.INI")

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
        p = L.screenshot(sink, TAG_SHOT(label), hwnd, bbox=bbox)
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(p), str(TRIP_OUT / p.name))
        return str(TRIP_OUT / p.name)
    except Exception as e:
        sink.step("screenshot_error", label=label, error=repr(e))
        return None


def TAG_SHOT(label):
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


# ---------------------------------------------------------------- D1 forensics
def wer_query_ps(since_local_iso: str) -> str:
    ps = (
        "$ErrorActionPreference='SilentlyContinue';"
        "$st=[datetime]'%s';"
        "$out=@();"
        "$out += '=== Application Error 1000 ===';"
        "$out += (Get-WinEvent -FilterHashtable @{LogName='Application';"
        "ProviderName='Application Error';Id=1000} -MaxEvents 10 | "
        "Where-Object { $_.TimeCreated -ge $st } | ForEach-Object { $_.ToXml() });"
        "$out += '=== Windows Error Reporting 1001 ===';"
        "$out += (Get-WinEvent -FilterHashtable @{LogName='Application';"
        "ProviderName='Windows Error Reporting';Id=1001} -MaxEvents 10 | "
        "Where-Object { $_.TimeCreated -ge $st } | ForEach-Object { $_.ToXml() });"
        "$out -join \"`n\"" % since_local_iso.replace("'", "''")
    )
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=90)
        return (r.stdout or "") + ("\n[stderr] " + r.stderr[:800] if r.stderr else "")
    except Exception as e:
        return "WER_QUERY_ERROR: %r" % (e,)


def capture_crash_forensics(sink, state, reason):
    """D1: run IMMEDIATELY on engine error / self-exit, BEFORE any cleanup."""
    if state.get("d1_done"):
        return state.get("d1_summary")
    state["d1_done"] = True
    TRIP_OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    # 1) except*.txt from the sandbox game root (engine writes it on the
    #    internal-error dialog path AND on the AV path).  Poll briefly: the
    #    write happens at dialog creation / before exit.
    #    NOTE: ra2youli ships a PRE-EXISTING except.txt (2026-11-13, 26,272 B)
    #    which robocopy copied into the sandbox baseline; every archived copy
    #    records mtime + sha + fresh/pre_existing classification vs trip start.
    t_start = state.get("t_start_dt")
    deadline = time.monotonic() + 12.0
    found = []
    while time.monotonic() < deadline:
        found = [p for p in sorted(C.GAME.glob("except*.txt"))
                 if (not t_start) or p.stat().st_mtime >= t_start.timestamp()]
        if found:
            break
        time.sleep(0.5)
    all_except = sorted(C.GAME.glob("except*.txt"))
    if found:
        sink.step("d1_except_fresh_found", n=len(found),
                  all_except_names=[p.name for p in all_except])
    for src in found:
        try:
            dst = TRIP_OUT / ("archived_" + src.name)
            dst.write_bytes(src.read_bytes())
            rows.append({"src": str(src), "dst": str(dst),
                         "size": dst.stat().st_size,
                         "mtime": L.local_iso(),
                         "sha256": L.sha256_file(dst)})
        except Exception as e:
            rows.append({"src": str(src), "error": repr(e)})
    baseline_note = {"pre_existing_except_in_baseline": [
        {"name": p.name, "size": p.stat().st_size,
         "mtime_epoch": p.stat().st_mtime} for p in all_except
        if (not t_start) or p.stat().st_mtime < t_start.timestamp()]}
    # 2) WER events since trip start
    wer = wer_query_ps(state.get("t_start_local") or "2000-01-01T00:00:00")
    wer_path = TRIP_OUT / "wer_events.txt"
    wer_path.write_text(wer, encoding="utf-8", errors="replace")
    # 3) ndjson tail snapshot
    nd_tail = None
    ndp = TRIP_OUT / "run.ndjson"
    if ndp.is_file():
        try:
            lines = ndp.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = lines[-120:]
            nd_tail = TRIP_OUT / "archived_ndjson_tail.ndjson"
            nd_tail.write_text("\n".join(tail) + "\n", encoding="utf-8")
        except Exception as e:
            nd_tail = "error: %r" % (e,)
    # 4) snapshot of the sandbox root listing (what else did the engine drop?)
    listing = sorted(p.name for p in C.GAME.glob("*") if p.is_file())[:80]
    state["d1_summary"] = {"reason": reason, "except_files": rows,
                           "baseline_note": baseline_note,
                           "wer_path": str(wer_path), "ndjson_tail": str(nd_tail),
                           "game_root_listing": listing}
    sink.step("d1_forensics_captured", **state["d1_summary"])
    return state["d1_summary"]


# ------------------------------------------------------------------ navigation
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


# ------------------------------------------------------------------ D4 inputs
def archive_installed_inputs(sink, state):
    d = TRIP_OUT / "installed_inputs"
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in INSTALLED_INPUTS:
        src = C.GAME / name
        if src.is_file():
            dst = d / name
            dst.write_bytes(src.read_bytes())
            rows.append({"file": name, "sha256": L.sha256_file(dst),
                         "size": dst.stat().st_size})
    dsn = C.design_path(STEP)
    if dsn.is_file():
        dst = d / dsn.name
        dst.write_text(dsn.read_text(encoding="utf-8"), encoding="utf-8")
        rows.append({"file": dsn.name, "sha256": L.sha256_file(dst)})
    state["inputs"] = rows
    sink.step("installed_inputs_archived", step=STEP, rows=rows)
    return rows


def config_pre_snapshot(sink):
    rows = []
    for name in C.PRISTINE:
        p = C.GAME / name
        rows.append({"file": name,
                     "present": p.is_file(),
                     "size": p.stat().st_size if p.is_file() else None,
                     "sha256": L.sha256_file(p) if p.is_file() else None})
    sink.step("config_pre_snapshot", rows=rows,
              note="pristine byte copies saved once at offline setup "
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
    state = {"pid": None, "hwnd": None, "hproc": None, "lock_taken": False,
             "d1_done": False, "d1_summary": None, "t_start_local": L.local_iso(),
             "t_start_dt": datetime.datetime.now(),
             "inputs": []}
    ok = False
    outcome = "unknown"
    result = {"step": STEP, "trip_dir": str(TRIP_OUT),
              "trip_suffix": _trip_suffix, "want_fn": WANT_FN,
              "sample_interval_ms_target": SAMPLE_INTERVAL_MS,
              "target_ingame_s": TARGET_INGAME_S, "min_valid_s": MIN_VALID_S,
              "hard_cap_s": HARD_CAP_S, "fps_assumed_nominal": FPS,
              "d1_forensics": None, "engagement": {}}
    RENDER = os.environ.get("W94_RENDER", "0") == "1"
    # render channel is opt-in per matrix cell (W94 generalized from W90:
    # no C6-only restriction; spawn/verify failure is recorded, trip continues)
    fb = {"enabled": RENDER, "proc": None, "console_path": None,
          "csv_path": None, "returncode": None, "killed_by_runner": None}
    result["render_channel"] = fb
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG, step=STEP,
                  t_start_local=state["t_start_local"],
                  note="add-back trip: one factor over the W84 df stable "
                       "baseline; D1/D2/D4 fixed this card")
        # ---- (0) installed-map identity check ------------------------------
        pkg_map = C.pkg_path(STEP) / "RA2F_M1.MAP"
        installed_map = C.GAME / "RA2F_M1.MAP"
        if not installed_map.is_file() or not pkg_map.is_file():
            raise TripError("installed/built RA2F_M1.MAP missing; run "
                            "w90_offline.py with W94_CELL=%s first" % STEP)
        map_match = (installed_map.read_bytes() == pkg_map.read_bytes())
        result["installed_map_matches_step_package"] = map_match
        sink.step("installed_map_identity", step=STEP, match=map_match,
                  installed_sha256=L.sha256_file(installed_map))
        if not map_match:
            raise TripError("sandbox installed map does not match step package %s"
                            % STEP)

        # ---- (0b) LOCK GATE (gate-only: session lock owner=w94 is held by
        #      the W90 orchestrator for the whole serial session; the runner
        #      never rewrites the lock) --------------------------------------
        pre = L.list_gamemd()
        lock_txt = C.lock_read()
        owner = C.lock_owner()
        sink.step("lock_gate", owner=owner, lock_content=lock_txt,
                  gamemd_processes=pre, n=len(pre))
        if not (owner.startswith("w94") or owner.startswith("w96")
                or owner.startswith("w98")):
            raise TripError("lock gate refused: session owner must be the "
                            "W98 batch runner (owner=w98-batchrun, got %r)"
                            % owner)
        if pre:
            raise TripError("residual gamemd before launch (not ours): %r"
                            % pre)

        # ---- (0c) D4 inputs + config pre-launch hash snapshot ---------------
        result["inputs_archive"] = archive_installed_inputs(sink, state)
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

        # ---- (4b) render channel attach (trip_C6_c only, W94 card §四) -----
        # W86 RPM framebeat: read-only, ~1kHz poll of draw.dll+0x5F120.
        # Measures 限帧放行间隔, NOT display frame time, NOT FPS (W86 wording
        # discipline).  A spawn/verify failure is recorded verbatim and the
        # main trip continues (card: 如实记录失败原因并继续).
        if RENDER:
            fbd = TRIP_OUT / "render_channel"
            fbd.mkdir(parents=True, exist_ok=True)
            cons_p = fbd / "framebeat_console.log"
            cons = cons_p.open("w", encoding="utf-8", errors="replace")
            argv = [sys.executable, "-B", str(C.TOOLS / "exp_rpm_framebeat.py"),
                    str(pid), "150", str(fbd)]
            try:
                fb["proc"] = subprocess.Popen(argv, stdout=cons,
                                              stderr=subprocess.STDOUT,
                                              cwd=str(fbd))
                fb["console_path"] = str(cons_p)
                fb["argv"] = argv
                fb["window_requested_s"] = 150
                sink.step("render_channel_started",
                          note="W86 RPM 只读通道：限帧放行间隔（非显示帧时间/"
                               "非 FPS）；失败如实记录且不中断主趟",
                          pid=pid, argv=argv)
            except Exception as e:
                fb["spawn_error"] = repr(e)
                sink.step("render_channel_spawn_failed", error=repr(e))
            finally:
                try:
                    cons.close()
                except Exception:
                    pass

        # ---- (5) sampling: 6 ms cadence, zero input ------------------------
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
        a8ed50_nonzero_n = 0
        a8ed50_n = 0
        x87_first = None
        x87_prev = None
        x87_changes = 0
        x87_first_change = None
        t_first_pos = None
        stop_reason = None
        term = None
        exit_code = None
        next_shot = 0
        last_ui_check = 0.0
        n_fg_loss = 0
        n_read_fail = 0
        n_winthread_fail = 0
        sg_t = time.perf_counter_ns()
        t_loop0 = time.perf_counter_ns()
        ec = wt.DWORD(0)
        STILL_ACTIVE = 259
        sink.step("sampling_begin", step=STEP, pid=pid,
                  note="zero input from here; 6 ms cadence; screenshots at "
                       "marks; UI/terminal check at 1 Hz; D1 armed")
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
            if vals is not None:
                a8ed50_n += 1
                if (vals.get("A8ED50") or 0) != 0:
                    a8ed50_nonzero_n += 1
                if a8ed50_first is None and (vals.get("A8ED50") or 0) != 0:
                    a8ed50_first = {"seq": seq, "t_perf_ns": t_ns,
                                    "value": vals["A8ED50"],
                                    "frame": vals.get("frame"),
                                    "ingame": t_first_pos is not None,
                                    "elapsed_ingame_s": (
                                        round((t_ns - t_first_pos) / 1e9, 4)
                                        if t_first_pos else None)}
                    sink.step("a8ed50_first_nonzero", **a8ed50_first)
                xv = vals.get("X87E8E0")
                if x87_first is None:
                    x87_first = xv
                    x87_prev = xv
                elif xv != x87_prev:
                    x87_changes += 1
                    if x87_first_change is None:
                        x87_first_change = {
                            "seq": seq, "from": x87_prev, "to": xv,
                            "frame": vals.get("frame"),
                            "elapsed_ingame_s": (
                                round((t_ns - t_first_pos) / 1e9, 4)
                                if t_first_pos else None),
                            "t_utc": L.utc_iso()}
                        sink.step("x87e8e0_first_change", **x87_first_change)
                    x87_prev = xv
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
            rec = {"kind": "sample", "seq": seq, "step": STEP,
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
                    sink.step("terminal_detected", **{k: v for k, v in
                                                      term.items() if k != "scen"})
                    if kind == "engine_internal_error_dialog":
                        # D1: capture BEFORE anything else touches the sandbox
                        result["d1_forensics"] = capture_crash_forensics(
                            sink, state, "engine_internal_error_dialog")
                while next_shot < len(SHOT_MARKS) and elapsed_ingame is not None \
                        and elapsed_ingame >= SHOT_MARKS[next_shot]:
                    shot(sink, hwnd, "combat_t%03d" % SHOT_MARKS[next_shot])
                    next_shot += 1
            # ---- stop rules ----
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            if not alive:
                exit_code = int(ec.value)
                stop_reason = "process_exited"
                sink.step("game_process_exited", t_ingame=elapsed_ingame,
                          exit_code=exit_code,
                          exit_code_hex="0x%08X" % (exit_code & 0xFFFFFFFF))
                # D1 immediately, BEFORE cleanup
                result["d1_forensics"] = capture_crash_forensics(
                    sink, state, "process_exited_0x%08X" % (exit_code & 0xFFFFFFFF))
                break
            if term is not None and term["kind"] == "engine_internal_error_dialog" \
                    and elapsed_ingame is not None \
                    and term.get("_d1_t") is None:
                term["_d1_t"] = elapsed_ingame
            if term is not None and term["kind"] == "engine_internal_error_dialog" \
                    and elapsed_ingame is not None \
                    and elapsed_ingame - term.get("_d1_t", 0) >= POST_ENGINE_ERROR_SAMPLE_S:
                stop_reason = "engine_error_terminal_confirmed"
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
            "a8ed50_samples_n": a8ed50_n,
            "a8ed50_nonzero_n": a8ed50_nonzero_n,
            "a8ed50_nonzero_ratio_full_window": (
                round(a8ed50_nonzero_n / a8ed50_n, 5) if a8ed50_n else None),
            "ndjson": str(nd_path),
            "loop_wall_s": round((time.perf_counter_ns() - t_loop0) / 1e9, 3)}
        sink.step("sampling_end", **result["sampling"])
        if term is not None:
            term.pop("_d1_t", None)
            result["terminal"] = term
        result["engagement"] = {
            "a8ed50_first_nonzero_seq": (a8ed50_first or {}).get("seq"),
            "a8ed50_first_nonzero_t_ingame_s": (a8ed50_first or {}).get(
                "elapsed_ingame_s"),
            "a8ed50_nonzero_n": a8ed50_nonzero_n,
            "a8ed50_n": a8ed50_n,
            "x87e8e0_first_value": x87_first,
            "x87e8e0_first_change_seq": (x87_first_change or {}).get("seq"),
            "x87e8e0_first_change_t_ingame_s": (x87_first_change or {}).get(
                "elapsed_ingame_s"),
            "x87e8e0_n_changes": x87_changes,
        }
        # ---- D2 outcome semantics (v2, per Lead correction 2026-11-14) -----
        # defeat_restart_dialog is NOT a success outcome for this card: it
        # means the player force died and the mission aborted early.
        # ok=True ONLY for: >=120 s window with NO terminal at all, or a
        # victory score screen.  ok=False for engine error, abnormal exit,
        # and defeat dialog.
        engine_error = (term is not None
                        and term["kind"] == "engine_internal_error_dialog")
        abnormal_exit = (stop_reason == "process_exited"
                         and (exit_code is None
                              or (exit_code & 0xC0000000)
                              or exit_code not in (0, 1)))
        defeat = (term is not None and term["kind"] == "defeat_restart_dialog")
        victory = (term is not None and term["kind"] == "victory_score_screen")
        if engine_error:
            outcome = ("VALID_WINDOW_WITH_ENGINE_ERROR" if valid
                       else "ABORTED_ENGINE_ERROR")
            ok = False
        elif abnormal_exit:
            outcome = ("ABORTED_CRASH_AV_0x%08X" % (exit_code & 0xFFFFFFFF)
                       if (exit_code is not None and (exit_code & 0xC0000000))
                       else "ABORTED_EXITED_%s" % exit_code)
            ok = False
        elif defeat:
            outcome = ("VALID_WINDOW_DEFEAT_DIALOG" if valid
                       else "DEFEAT_DIALOG_AT_%.0fs"
                       % (term["t_ingame_s"] or -1))
            ok = False
        elif valid:
            outcome = ("VALID_WINDOW_%s" % stop_reason) if not victory \
                else "VALID_WINDOW_VICTORY_%s" % stop_reason
            ok = True
        elif victory:
            outcome = "VICTORY_EARLY_AT_%.0fs" % (term["t_ingame_s"] or -1)
            ok = True
        else:
            outcome = "NO_RESULT_%s" % stop_reason
            ok = False
        sink.step("trip_result", ok=ok, outcome=outcome, step=STEP,
                  ingame_s=result["sampling"]["ingame_duration_s"],
                  min_valid_met=valid, terminal=(term or {}).get("kind"),
                  exit_code=exit_code,
                  d1_captured=bool(state["d1_done"]))
    except TripError as e:
        outcome = "BLOCKED: " + str(e)
        sink.step("trip_blocked", outcome=outcome, detail=e.detail)
        try:
            nd.close()
        except Exception:
            pass
        ok = False
    except Exception as e:
        outcome = "FATAL: " + repr(e)
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
        try:
            nd.close()
        except Exception:
            pass
        ok = False
    finally:
        pid, hwnd, hproc = state["pid"], state["hwnd"], state["hproc"]
        # D1 safety net: engine error or self-exit must ALWAYS have forensics
        # captured before any cleanup/close happens below.
        try:
            if not state["d1_done"] and (
                    (result.get("terminal") or {}).get("kind")
                    == "engine_internal_error_dialog"
                    or (result.get("sampling") or {}).get("stop_reason")
                    == "process_exited"):
                result["d1_forensics"] = capture_crash_forensics(
                    sink, state, "finally_safety_net")
        except Exception as e:
            sink.step("d1_safety_net_error", error=repr(e))
        try:
            winmm.timeEndPeriod(1)
        except Exception:
            pass
        # render channel: reap (it self-terminates at its 150 s window; if the
        # trip ended early we terminate it so no orphan poller survives)
        if fb.get("proc") is not None:
            try:
                p = fb["proc"]
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=10)
                        fb["killed_by_runner"] = "terminated_at_trip_end"
                    except Exception:
                        p.kill()
                        fb["killed_by_runner"] = "killed_after_terminate_timeout"
                fb["returncode"] = p.poll()
            except Exception as e:
                fb["kill_error"] = repr(e)
            try:
                fbd = TRIP_OUT / "render_channel"
                csvs = sorted(fbd.glob("framebeat_*.csv")) if fbd.is_dir() else []
                fb["csv_path"] = str(csvs[0]) if csvs else None
            except Exception:
                pass
            sink.step("render_channel_final", **{k: fb.get(k) for k in
                      ("enabled", "returncode", "killed_by_runner",
                       "csv_path", "console_path")})
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
        # unconditional except.txt presence check (archive FRESH rewrites only;
        # the baseline except.txt shipped from ra2youli stays untouched)
        late_rows = []
        try:
            t0dt = state.get("t_start_dt")
            for src in sorted(C.GAME.glob("except*.txt")):
                if t0dt and src.stat().st_mtime < t0dt.timestamp():
                    continue   # pre-existing baseline copy, not crash evidence
                dst = TRIP_OUT / ("archived_late_" + src.name)
                dst.write_bytes(src.read_bytes())
                late_rows.append({"src": str(src), "dst": str(dst),
                                  "sha256": L.sha256_file(dst),
                                  "mtime_epoch": src.stat().st_mtime})
        except Exception as e:
            late_rows.append({"error": repr(e)})
        if late_rows:
            sink.step("d1_late_except_archive", rows=late_rows)
        restore_rows = restore_per_trip_configs(sink)
        sink.step("trip_cleanup", close_steps=close_steps,
                  gamemd_residual=residual, residual_zero=(len(residual) == 0),
                  late_except_rows=late_rows)
        if state["lock_taken"]:
            C.lock_release("W94 trip step=%s FINISHED (outcome=%s): "
                           "self-launched gamemd (pid=%s) closed, residual=%d; "
                           "restored owner=lead."
                           % (STEP, outcome, pid, len(residual)))
        sink.step("lock_released", lock_content=C.lock_read())
        result["outcome"] = outcome
        result["ok"] = ok
        result["close_steps"] = close_steps
        result["gamemd_residual"] = residual
        result["config_restore_rows"] = restore_rows
        result["d1_forensics"] = state.get("d1_summary")
        result["w59_offsets"] = {"scen_ptr": "0x00A8B230", "filename": "+0x125C",
                                 "stage_idx": "+0x35A0", "end_of_game": "+0x34AC",
                                 "frame": "0x00A8ED84",
                                 "A8ED50": "0x00A8ED50", "B0CE88": "0x00B0CE88",
                                 "X87E8E0": "0x0087E8E0"}
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        (TRIP_OUT / "TRIP_RESULT.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        (C.OUT / ("TRIP_RESULT_%s%s.json" % (STEP, _trip_suffix))).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok, step=STEP,
                  outcome=outcome, gamemd_residual=residual,
                  lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

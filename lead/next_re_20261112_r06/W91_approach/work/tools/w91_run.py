#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W91 REAL-MACHINE trip - 长途接敌：趟内两阶段分离行军/寻路与交战.

Env:
  W91_TRIP = P1 | P2 ...   (REQUIRED; pre-registered unique trip dir
                            out/trip_<trip>/ ; never reused, fail if exists)

PURPOSE (card W91): same map/layout, enemy = British MTNK mission=Hunt only,
marching from rows 4-11 to player buildings rows 88-95.  In-trip phases:
  A phase = A8ED50==0 AND X87E8E0 changing      -> march/pathfinding only
  B phase = after first A8ED50 nonzero          -> march + combat + damage
Deliverables: per-phase window-thread CPU consumption rate
(Sigma GetThreadTimes kernel+user / wall, single-core %), A8ED50 first-nonzero
idx/time, X87E8E0 first-change idx + A-phase change count, per-phase wall time
and sample counts.  Reference anchors (quoted, not re-run): W88/W90 C6
1200-Hunt = 31.0-33.6 %, CTRL_C6 all-Guard = 17.75-18.10 %.

LEAD ADD-ON (zero-cost sub-step, trip P1 only, read-only): ddraw.dll globals
probe.  W90 U2 reported clamp=210 where the static disassembly says the
reference cap global (RVA 0x5EE48) is written to 60 exactly once
(0x10015E83).  Dump RVA 0x5EE30..0x5EE70 + the four known globals
(maxfps 0x594E8, vsync 0x594EC, last_t 0x5F120, interval 0x5F128) via
ReadProcessMemory from outside after mission entry -> <trip>/ddraw_globals_probe.json.
Failure is recorded verbatim and NEVER aborts the main trip.

D1 FORENSICS: same as W88/W90 (fresh except*.txt classified by mtime vs trip
  start; ra2youli ships a pre-existing 2026-11-13 except.txt) + WER + ndjson
  tail, captured IMMEDIATELY on engine-error terminal or process exit,
  BEFORE any cleanup.
D2 OUTCOME SEMANTICS (v2): defeat dialog is a NORMAL terminal for this card
  (player annihilation); ok=false, outcome VALID_WINDOW_DEFEAT_DIALOG /
  DEFEAT_DIALOG_AT_*.s.  Engine error / abnormal exit -> ok=false.
D4 INPUT ARCHIVE: installed RA2F_M1.MAP / BATTLEMD.INI / MAPSELMD.INI + design
  JSON into <trip>/installed_inputs/ + sha256.

REAL-MACHINE DISCIPLINE:
  * WMI Win32_Process.Create launches ONLY the sandbox gamemd.exe.
  * Read-only RPM + read-only thread time queries.  NO injection/debugger.
  * close_game only touches the pid WE launched.  No blanket taskkill.
  * Per-trip: RA2MD.INI / ddraw.ini byte-restored from pristine + hash proof.
  * Lock gate: owner must be w91 (session lock held by this card), zero
    gamemd before launch.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w91_lib as L
import w91_common as C

TRIP = os.environ.get("W91_TRIP", "").strip().upper()
if not TRIP:
    raise SystemExit("W91_TRIP must be an explicit trip name (P1, P2, ...)")
TRIP_OUT = C.OUT / ("trip_" + TRIP)
if TRIP_OUT.exists():
    raise SystemExit("trip dir already exists (never reuse): %s" % TRIP_OUT)
TAG = "run_" + TRIP
WANT_FN = "RA2F_M1.MAP"
FPS = 31.25                    # nominal: frame = *(DWORD*)0x00A8ED84, 32 ms timer
TARGET_INGAME_S = 260.0        # sampling target from first frame>0 (A>=40-60s + B)
MIN_VALID_S = 120.0            # W91 card: A-phase must be >=40 s (target 60) => total >=120
HARD_CAP_S = 320.0             # hard cap
SAMPLE_INTERVAL_MS = 6.0       # 6 ms cadence
SHOT_MARKS = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
APH_SHOT_MARKS = [2.0, 16.0, 32.0]   # A-phase elapsed marks -> aph_t002/016/032 (mid-A evidence)
POST_ENGINE_ERROR_SAMPLE_S = 5.0   # keep sampling briefly after the dialog
POST_DEFEAT_SAMPLE_S = 10.0        # defeat dialog: sample briefly, then stop

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

# ---- module enumeration (read-only) for the ddraw globals probe -------------
TH32CS_SNAPMODULE = 0x00000008
TH32CS_SNAPMODULE32 = 0x00000010


class MODULEENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD),
                ("th32ModuleID", wt.DWORD),
                ("GlblcntUsage", wt.DWORD),
                ("ProccntUsage", wt.DWORD),
                ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
                ("modBaseSize", wt.DWORD),
                ("hModule", ctypes.c_void_p),
                ("szModule", ctypes.c_wchar * 256),
                ("szExePath", ctypes.c_wchar * 260)]


k32.Module32FirstW.restype = wt.BOOL
k32.Module32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MODULEENTRY32W)]
k32.Module32NextW.restype = wt.BOOL
k32.Module32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MODULEENTRY32W)]

# psapi fallback: Toolhelp module snapshot from a 64-bit observer on a WOW64
# target returned an empty list on this host (trip_P1/P2 probe failed with
# "ddraw.dll not found in module list"), so enumerate 32-bit modules via
# EnumProcessModulesEx(LIST_MODULES_32BIT) as well.
psapi = ctypes.WinDLL("psapi")
LIST_MODULES_32BIT = 0x01
LIST_MODULES_ALL = 0x03
psapi.EnumProcessModulesEx.restype = wt.BOOL
psapi.EnumProcessModulesEx.argtypes = [wt.HANDLE, ctypes.POINTER(wt.HMODULE),
                                       wt.DWORD, ctypes.POINTER(wt.DWORD),
                                       wt.DWORD]
psapi.GetModuleBaseNameW.restype = wt.DWORD
psapi.GetModuleBaseNameW.argtypes = [wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]
psapi.GetModuleFileNameExW.restype = wt.DWORD
psapi.GetModuleFileNameExW.argtypes = [wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]


def enum_modules_psapi(hproc):
    rows = []
    n = 2048
    for _ in range(3):
        arr = (wt.HMODULE * n)()
        needed = wt.DWORD(0)
        ok = psapi.EnumProcessModulesEx(hproc, arr, ctypes.sizeof(arr),
                                        ctypes.byref(needed), LIST_MODULES_ALL)
        if not ok:
            return rows, "EnumProcessModulesEx_failed"
        cnt = min(needed.value // ctypes.sizeof(wt.HMODULE), n)
        for i in range(cnt):
            name = ctypes.create_unicode_buffer(260)
            path = ctypes.create_unicode_buffer(520)
            psapi.GetModuleBaseNameW(hproc, arr[i], name, 260)
            psapi.GetModuleFileNameExW(hproc, arr[i], path, 520)
            rows.append({"module": name.value, "base": int(arr[i] or 0),
                         "path": path.value})
        if cnt < n:
            return rows, None
        n *= 4
    return rows, "buffer_grew_thrice"


def find_module_base(hproc, module_name_lower: str):
    """Returns (base_or_None, modules_rows, error_or_None).  Toolhelp first,
    psapi EnumProcessModulesEx fallback (P1/P2 lesson)."""
    rows_toolhelp = []
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32,
                                        0)
    if snap and snap != ctypes.c_void_p(-1).value:
        me = MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(MODULEENTRY32W)
        ok = k32.Module32FirstW(snap, ctypes.byref(me))
        while ok:
            rows_toolhelp.append({"module": me.szModule,
                                  "base": int(me.modBaseAddr or 0),
                                  "size": int(me.modBaseSize)})
            if (me.szModule or "").lower() == module_name_lower:
                k32.CloseHandle(snap)
                return int(me.modBaseAddr or 0), rows_toolhelp, None
            ok = k32.Module32NextW(snap, ctypes.byref(me))
        k32.CloseHandle(snap)
    rows, err = enum_modules_psapi(hproc)
    for r in rows:
        if (r["module"] or "").lower() == module_name_lower:
            return r["base"], rows, None
    return None, (rows_toolhelp or rows), err or ("module %s not found"
                                                  % module_name_lower)


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
    wer = wer_query_ps(state.get("t_start_local") or "2000-01-01T00:00:00")
    wer_path = TRIP_OUT / "wer_events.txt"
    wer_path.write_text(wer, encoding="utf-8", errors="replace")
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
    listing = sorted(p.name for p in C.GAME.glob("*") if p.is_file())[:80]
    state["d1_summary"] = {"reason": reason, "except_files": rows,
                           "baseline_note": baseline_note,
                           "wer_path": str(wer_path), "ndjson_tail": str(nd_tail),
                           "game_root_listing": listing}
    sink.step("d1_forensics_captured", **state["d1_summary"])
    return state["d1_summary"]


# ------------------------------------------------- ddraw globals probe (W90 U2)
DDRAW_GLOBALS = [
    # (name, rva, expected_local_config, note)
    ("maxfps",       0x000594E8, "60",   "ddraw.ini maxfps"),
    ("vsync",        0x000594EC, "1",    "unset in ddraw.ini [gamemd] -> global default 1"),
    ("ref_cap",      0x0005EE48, "60",   "static: sole immediate write 0x10015E83 = 0x3C; W90 U2 read clamp=210"),
    ("last_t",       0x0005F120, "changing", "per-frame timestamp"),
    ("interval_ms",  0x0005F128, "16",   "int(1000/60)"),
]
DDRAW_DUMP_LO = 0x0005EE30
DDRAW_DUMP_HI = 0x0005EE70   # inclusive, 16 dwords


def find_module_base_pid(pid, module_name_lower: str):
    # Toolhelp path needs a pid (used by the old probe); psapi path uses the
    # opened process handle.  Kept for compatibility.
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32,
                                        pid)
    if not snap or snap == ctypes.c_void_p(-1).value:
        return None, "CreateToolhelp32Snapshot_failed"
    rows = []
    me = MODULEENTRY32W()
    me.dwSize = ctypes.sizeof(MODULEENTRY32W)
    ok = k32.Module32FirstW(snap, ctypes.byref(me))
    while ok:
        rows.append({"module": me.szModule, "base": int(me.modBaseAddr or 0),
                     "size": int(me.modBaseSize)})
        if (me.szModule or "").lower() == module_name_lower:
            k32.CloseHandle(snap)
            return int(me.modBaseAddr or 0), rows
        ok = k32.Module32NextW(snap, ctypes.byref(me))
    k32.CloseHandle(snap)
    return None, rows


def ddraw_globals_probe(sink, pid, state):
    """Read-only probe of cnc-ddraw globals.  NEVER aborts the trip."""
    res = {"enabled": True, "module": "ddraw.dll", "base": None,
           "modules_seen": None, "globals": [], "dump": [], "last_t_pair": None,
           "verdict": None, "error": None}
    try:
        TRIP_OUT.mkdir(parents=True, exist_ok=True)
        base, modinfo, moderr = find_module_base(state["hproc"], "ddraw.dll")
        res["modules_seen"] = modinfo
        if isinstance(moderr, str) and not base:
            res["error"] = "module_enum: %s" % moderr
            sink.step("ddraw_probe_failed", **{k: res[k] for k in ("error",)})
            return res
        if not base:
            res["error"] = "ddraw.dll not found in module list (%d modules seen)" % (
                len(modinfo) if modinfo else 0)
            sink.step("ddraw_probe_failed", error=res["error"])
            return res
        res["base"] = hex(base)
        image_base = base   # ASLR-relocated ImageBase (static ImageBase 0x10000000)
        globs = []
        for name, rva, expect, note in DDRAW_GLOBALS:
            b = L.rpm(state["hproc"], image_base + rva, 4)
            v = int.from_bytes(b, "little") if b else None
            globs.append({"name": name, "rva": hex(rva),
                          "va": hex(image_base + rva),
                          "value_dec": v, "value_hex": (hex(v) if v is not None
                                                        else None),
                          "expected": expect, "note": note})
        res["globals"] = globs
        # raw dump 0x5EE30..0x5EE70 (16 dwords)
        dump = []
        raw = L.rpm(state["hproc"], image_base + DDRAW_DUMP_LO,
                    DDRAW_DUMP_HI - DDRAW_DUMP_LO + 4)
        for i in range(16):
            rva = DDRAW_DUMP_LO + 4 * i
            if raw and 4 * i + 4 <= len(raw):
                v = int.from_bytes(raw[4 * i:4 * i + 4], "little")
            else:
                b1 = L.rpm(state["hproc"], image_base + rva, 4)
                v = int.from_bytes(b1, "little") if b1 else None
            dump.append({"rva": hex(rva), "va": hex(image_base + rva),
                         "value_dec": v, "value_hex": (hex(v) if v is not None
                                                       else None)})
        res["dump"] = dump
        res["dump_raw_hex"] = raw.hex() if raw else None
        # last_t twice, ~1.2 s apart, to demonstrate it is a moving timestamp
        def rd_last():
            b = L.rpm(state["hproc"], image_base + 0x0005F120, 4)
            return int.from_bytes(b, "little") if b else None
        v1 = rd_last()
        time.sleep(1.2)
        v2 = rd_last()
        res["last_t_pair"] = {"t0": v1, "t1_after_1p2s": v2,
                              "changed": (v1 is not None and v2 is not None
                                          and v1 != v2)}
        refcap = next((g for g in globs if g["name"] == "ref_cap"), None)
        if refcap and refcap["value_dec"] is not None:
            if refcap["value_dec"] == 60:
                res["verdict"] = ("0x5EE48 实测=60：W90 的 clamp=210 是读取口径"
                                  "问题（其脚本地址换算可疑，本卡不深挖）")
            elif refcap["value_dec"] == 210:
                res["verdict"] = ("0x5EE48 实测=210：存在静态扫描未覆盖的写入路径"
                                  "或配置覆盖，列入 UNKNOWNS")
            else:
                res["verdict"] = ("0x5EE48 实测=%d（既非 60 也非 210），列入 "
                                  "UNKNOWNS" % refcap["value_dec"])
        jp = TRIP_OUT / "ddraw_globals_probe.json"
        jp.write_text(json.dumps(res, ensure_ascii=False, indent=2,
                                 default=str), encoding="utf-8")
        lines = ["ddraw globals probe (READ-ONLY RPM) %s" % L.local_iso(),
                 "ddraw.dll base = %s" % res["base"], "",
                 "== known globals =="]
        for g in globs:
            lines.append("%-12s RVA=%-10s VA=%-12s value=%s (%s) expected=%s  # %s"
                         % (g["name"], g["rva"], g["va"], g["value_dec"],
                            g["value_hex"], g["expected"], g["note"]))
        lines += ["", "== dump RVA 0x5EE30..0x5EE70 (16 dwords) =="]
        for d in dump:
            lines.append("%-10s %-12s %s (%s)" % (d["rva"], d["va"],
                                                  d["value_dec"], d["value_hex"]))
        lines += ["", "last_t pair: %r" % (res["last_t_pair"],),
                  "VERDICT: %s" % res["verdict"], ""]
        (TRIP_OUT / "ddraw_globals_probe.txt").write_text(
            "\n".join(lines), encoding="utf-8")
        sink.step("ddraw_probe_done", base=res["base"],
                  ref_cap=refcap["value_dec"] if refcap else None,
                  maxfps=next((g["value_dec"] for g in globs
                               if g["name"] == "maxfps"), None),
                  last_t_changed=res["last_t_pair"]["changed"],
                  verdict=res["verdict"])
    except Exception as e:
        res["error"] = repr(e)
        sink.step("ddraw_probe_failed", error=res["error"],
                  traceback=traceback.format_exc()[-2000:])
    return res


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
    dsn = C.design_path(TRIP)
    if dsn.is_file():
        dst = d / dsn.name
        dst.write_text(dsn.read_text(encoding="utf-8"), encoding="utf-8")
        rows.append({"file": dsn.name, "sha256": L.sha256_file(dst)})
    state["inputs"] = rows
    sink.step("installed_inputs_archived", trip=TRIP, rows=rows)
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
             "inputs": [], "nd": None}
    ok = False
    outcome = "unknown"
    result = {"trip": TRIP, "trip_dir": str(TRIP_OUT), "want_fn": WANT_FN,
              "sample_interval_ms_target": SAMPLE_INTERVAL_MS,
              "target_ingame_s": TARGET_INGAME_S, "min_valid_s": MIN_VALID_S,
              "hard_cap_s": HARD_CAP_S, "fps_assumed_nominal": FPS,
              "d1_forensics": None, "engagement": {}}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG, trip=TRIP,
                  t_start_local=state["t_start_local"],
                  note="W91 long-approach trip: in-trip phase split "
                       "march(A: A8ED50==0 & X87E8E0 changing) vs "
                       "combat(B: after first A8ED50 nonzero); D1/D2/D4 fixed")
        # ---- (0) installed-map identity check ------------------------------
        pkg_map = C.pkg_path(TRIP) / "RA2F_M1.MAP"
        installed_map = C.GAME / "RA2F_M1.MAP"
        if not installed_map.is_file() or not pkg_map.is_file():
            raise TripError("installed/built RA2F_M1.MAP missing; run "
                            "w91_offline.py with W91_STEP=%s first" % TRIP)
        map_match = (installed_map.read_bytes() == pkg_map.read_bytes())
        result["installed_map_matches_step_package"] = map_match
        sink.step("installed_map_identity", trip=TRIP, match=map_match,
                  installed_sha256=L.sha256_file(installed_map))
        if not map_match:
            raise TripError("sandbox installed map does not match trip package %s"
                            % TRIP)

        # ---- (0b) LOCK GATE (owner must be w91; zero gamemd before launch) --
        pre = L.list_gamemd()
        lock_txt = C.lock_read()
        owner = C.lock_owner()
        sink.step("lock_gate", owner=owner, lock_content=lock_txt,
                  gamemd_processes=pre, n=len(pre))
        if owner != "w91":
            raise TripError("lock gate refused: session owner must be w91 "
                            "(got %r)" % owner)
        if pre:
            raise TripError("residual gamemd before launch (not ours): %r" % pre)

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

        # ---- (4b) ddraw globals probe (lead add-on, read-only, trip P1) ----
        result["ddraw_probe"] = ddraw_globals_probe(sink, pid, state)

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
        state["nd"] = nd

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
        x87_changes_in_A = 0          # X87E8E0 changes strictly inside phase A
        t_first_pos = None
        phase_a_start_ns = None       # first sample classified A
        aphase_shots_done = set()
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
        sink.step("sampling_begin", trip=TRIP, pid=pid,
                  note="zero input from here; 6 ms cadence; phase=A8ED50==0&"
                       "X87E8E0-changing -> A, after first nonzero -> B; "
                       "A-phase screenshots at +2/+16/+32 s; D1 armed")
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
            # ---- phase classification (pre-registered, mechanical) ----------
            phase = "pre"
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
                if a8ed50_first is not None:
                    phase = "B"
                elif x87_changes > 0:
                    phase = "A"
                    if phase_a_start_ns is None:
                        phase_a_start_ns = t_ns
                        sink.step("phase_A_start", seq=seq,
                                  elapsed_ingame_s=round(
                                      (t_ns - t_first_pos) / 1e9, 4)
                                  if t_first_pos else None)
                    x87_changes_in_A += 1
                # A-phase screenshots (mechanical marks on A-phase elapsed)
                if phase == "A" and phase_a_start_ns is not None:
                    a_el = (t_ns - phase_a_start_ns) / 1e9
                    for i, mk in enumerate(APH_SHOT_MARKS):
                        if i not in aphase_shots_done and a_el >= mk:
                            aphase_shots_done.add(i)
                            shot(sink, hwnd, "aph_t%03d" % int(mk))
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
            rec = {"kind": "sample", "seq": seq, "trip": TRIP,
                   "phase": phase,
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
            # defeat dialog: normal terminal for this card; sample briefly then stop
            if term is not None and term["kind"] == "defeat_restart_dialog" \
                    and elapsed_ingame is not None:
                if term.get("_def_t") is None:
                    term["_def_t"] = elapsed_ingame
                elif elapsed_ingame - term["_def_t"] >= POST_DEFEAT_SAMPLE_S:
                    stop_reason = "defeat_dialog_confirmed"
                    break
            if elapsed_ingame is not None:
                if elapsed_ingame >= TARGET_INGAME_S:
                    stop_reason = "target_reached"
                    break
                if elapsed_ingame >= HARD_CAP_S:
                    stop_reason = "hard_cap"
                    break
            elif (time.perf_counter_ns() - sg_t) / 1e9 > 480.0:
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
        phase_a_dur = ((a8ed50_first or {}).get("t_perf_ns")
                       if a8ed50_first else None)
        phase_a_wall_s = (round((phase_a_dur - phase_a_start_ns) / 1e9, 4)
                          if (phase_a_dur and phase_a_start_ns) else None)
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
            "phase_A_start_elapsed_ingame_s": (
                round((phase_a_start_ns - t_first_pos) / 1e9, 4)
                if (phase_a_start_ns and t_first_pos) else None),
            "phase_A_wall_s_until_B": phase_a_wall_s,
            "x87e8e0_changes_in_A": x87_changes_in_A,
            "aphase_shots": sorted(APH_SHOT_MARKS[i] for i in aphase_shots_done),
            "ndjson": str(nd_path),
            "loop_wall_s": round((time.perf_counter_ns() - t_loop0) / 1e9, 3)}
        sink.step("sampling_end", **result["sampling"])
        if term is not None:
            term.pop("_d1_t", None)
            term.pop("_def_t", None)
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
            "x87e8e0_n_changes_phase_A": x87_changes_in_A,
        }
        # ---- D2 outcome semantics (v2; defeat = normal terminal here) ------
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
        sink.step("trip_result", ok=ok, outcome=outcome, trip=TRIP,
                  ingame_s=result["sampling"]["ingame_duration_s"],
                  min_valid_met=valid, terminal=(term or {}).get("kind"),
                  exit_code=exit_code,
                  d1_captured=bool(state["d1_done"]))
    except TripError as e:
        outcome = "BLOCKED: " + str(e)
        sink.step("trip_blocked", outcome=outcome, detail=e.detail)
        ok = False
    except Exception as e:
        outcome = "FATAL: " + repr(e)
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
        ok = False
    finally:
        pid, hwnd, hproc = state["pid"], state["hwnd"], state["hproc"]
        try:
            if state.get("nd") is not None and not state["nd"].closed:
                state["nd"].close()
        except Exception:
            pass
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
            # trip_P1 lesson: gamemd may leave a CHILD gamemd alive after the
            # parent is closed (P1: pid 3516 ppid=40728).  Children of OUR pid
            # are part of this card's process tree; only they are touched.
            import time as _t
            for _ in range(5):
                kids = [r for r in L.list_gamemd() if r.get("ppid") == pid]
                if not kids:
                    break
                for r in kids:
                    rr = subprocess.run(["taskkill", "/F", "/PID", str(r["pid"])],
                                        capture_output=True, text=True, timeout=30)
                    close_steps.append("taskkill child /F /PID %s (ppid=%d, ours) rc=%s"
                                       % (r["pid"], pid, rr.returncode))
                    sink.step("close_child", pid=r["pid"], ppid=pid,
                               rc=rr.returncode)
                _t.sleep(1.0)
        residual = L.list_gamemd()
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
        sink.step("lock_note", note="session lock owner=w91 stays with this "
                                    "card until finalize; not released per-trip")
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
        (C.OUT / ("TRIP_RESULT_%s.json" % TRIP)).write_text(
            json.dumps(result, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok, trip=TRIP,
                  outcome=outcome, gamemd_residual=residual)
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

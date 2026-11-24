#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W45 / B-half - real-machine dual-track behaviour-equivalence harness.

SELF-CONTAINED: does NOT import W44's w44_lib (that library writes into W44's
out/ directory, which would violate this card's "only write inside
W45_b_line_equivalence/" rule).  Win32/RPM/UI primitives below are adapted
from W44 tools/w44_lib.py and tools/w44_phase_run.py (proven W27/W39/W44
sequence), with all paths redirected into this card.

DISCIPLINE (task card, copied):
  * desktop precheck within 30 s of launch: EnumWindows >=1 + screenshot OK;
    failure => STOP, judge "环境阻塞".
  * single instance: .game_instance.lock; finally restores owner=lead.
  * WMI Win32_Process.Create launch.
  * NO injection / attach-write / exe modification. Read-only
    PROCESS_VM_READ + ReadProcessMemory only.
  * finally: WM_CLOSE -> taskkill -> taskkill /F -> residual 0 -> byte-exact
    restore RA2MD.INI / ddraw.ini -> remove drops -> meta_end -> release lock.
  * restore set does NOT include ra2forge_install.json / .seal.
  * budget <=100 min; single trip <=10 min.

Usage:
  python w45_dual_track.py --phase all
  python w45_dual_track.py --phase prep
  python w45_dual_track.py --phase run --arms A1,A2,B1
  python w45_dual_track.py --phase finalize
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ------------------------------------------------------------------ paths
ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
CARD = RUN / "W45_b_line_equivalence"
OUT = CARD / "out"
TOOLS = CARD / "tools"
BASE = CARD / "sandbox_base"          # prepared, post-uninstall v0.3 clean base
PKG = OUT / "pkg_v13"                  # outer build dir
PKG_INNER = PKG / "W45 Equivalence Probe"   # --package must point HERE (holds BATTLEMD98.INI)
V13 = RUN / "W43_b_line_s3" / "ra2forge_patched_v13"
REAL = ROOT / "ra2youli"
LOCK = RUN / ".game_instance.lock"
PY = r"C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
DESIGN = CARD / "designs" / "w45_two_missions.json"

CONFIG_RESTORE = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak", "BATTLEMD.INI")
# deliberately NOT: ra2forge_install.json / ra2forge_install.json.seal
ESC_REQUIRED = ("GUI:AbortMission", "GUI:GameControls", "GUI:GameOptions",
                "GUI:LoadGame", "GUI:ResumeMission", "GUI:SaveGame")
K_EXPECTED_BATTLE_DELTA = 1   # pre-declared: BATTLEMD98.INI registers 1 battle

# ------------------------------------------------------------------ Win32
u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

for fn, rt, at in [
    ("PostMessageW", wt.BOOL, [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]),
    ("SendMessageTimeoutW", ctypes.c_void_p,
     [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM, wt.UINT, wt.UINT,
      ctypes.POINTER(ctypes.c_size_t)]),
    ("GetWindowThreadProcessId", wt.DWORD, [wt.HWND, ctypes.POINTER(wt.DWORD)]),
    ("GetWindowTextLengthW", ctypes.c_int, [wt.HWND]),
    ("GetWindowTextW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
    ("GetClassNameW", ctypes.c_int, [wt.HWND, wt.LPWSTR, ctypes.c_int]),
    ("EnumWindows", wt.BOOL, [ctypes.c_void_p, wt.LPARAM]),
    ("EnumChildWindows", wt.BOOL, [wt.HWND, ctypes.c_void_p, wt.LPARAM]),
    ("IsWindowVisible", wt.BOOL, [wt.HWND]),
    ("IsWindow", wt.BOOL, [wt.HWND]),
    ("GetWindowRect", wt.BOOL, [wt.HWND, ctypes.c_void_p]),
    ("GetDlgCtrlID", ctypes.c_int, [wt.HWND]),
    ("GetForegroundWindow", wt.HWND, []),
    ("SetForegroundWindow", wt.BOOL, [wt.HWND]),
    ("ShowWindow", wt.BOOL, [wt.HWND, ctypes.c_int]),
    ("BringWindowToTop", wt.BOOL, [wt.HWND]),
    ("AllowSetForegroundWindow", wt.BOOL, [wt.DWORD]),
    ("keybd_event", None, [ctypes.c_ubyte, ctypes.c_ubyte, wt.DWORD,
                           ctypes.c_size_t]),
    ("SetCursorPos", wt.BOOL, [ctypes.c_int, ctypes.c_int]),
    ("mouse_event", None, [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD,
                           ctypes.c_size_t]),
]:
    f = getattr(u, fn)
    f.restype = rt
    f.argtypes = at

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Process32FirstW.restype = wt.BOOL
k32.Process32NextW.restype = wt.BOOL

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

BM_CLICK = 0x00F5
WM_CLOSE = 0x0010
WM_SETTEXT = 0x000C
VK_ESCAPE = 0x1B
VK_MENU = 0x12
VK_RETURN = 0x0D
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
SMTO_ABORTIFHUNG = 0x0002
GAME_WND_CLASS = "Yuri's Revenge"
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
LB_GETCOUNT = 0x018B
LB_SETCURSEL = 0x0186

ADDR = {
    "frame": 0x00A8ED84,       # dword: 32 ms game timer (~31.25 counts/s) - NOT FPS
    "mode": 0x00A8B238,        # dword: DO NOT use as in-game gate
    "scen_ptr": 0x00A8B230,
    "battle_cnt": 0x00A83D08,
}


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


# ------------------------------------------------------------------ primitives
def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def local_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Sink:
    def __init__(self, tag: str):
        self.tag = tag
        OUT.mkdir(parents=True, exist_ok=True)
        self.nd = (OUT / ("%s.ndjson" % tag)).open("w", encoding="utf-8",
                                                    newline="\n")
        self.n = 0

    def step(self, step_name: str, kind: str = "event", **kw):
        rec = {"kind": kind, "step": step_name, "t_utc": utc_iso(),
               "t_local": local_iso(), "t_monotonic": time.monotonic(), **kw}
        self.nd.write(json.dumps(rec, ensure_ascii=False, sort_keys=True,
                                 default=str, separators=(",", ":")) + "\n")
        self.nd.flush()
        self.n += 1
        try:
            print("[%s] %s %s" % (local_iso(), step_name,
                                  json.dumps(kw, ensure_ascii=True,
                                             default=str)[:300]), flush=True)
        except Exception:
            try:
                sys.stdout.write("[%s] %s <print suppressed>\n"
                                 % (local_iso(), step_name))
                sys.stdout.flush()
            except Exception:
                pass
        return rec

    def close(self):
        self.nd.close()


def run_cmd(args, cwd, sink: Sink, label: str, timeout=300):
    p = OUT / ("cmd_%s.log" % label)
    try:
        r = subprocess.run(args, cwd=str(cwd), capture_output=True,
                           text=True, timeout=timeout)
        rc, so, se = r.returncode, r.stdout or "", r.stderr or ""
    except Exception as e:
        rc, so, se = -1, "", repr(e)
    p.write_text("CMD: %s\nCWD: %s\nEXIT: %d\n--- stdout ---\n%s\n"
                 "--- stderr ---\n%s\n"
                 % (" ".join('"%s"' % a if " " in a else a for a in args),
                    cwd, rc, so, se), encoding="utf-8")
    sink.step("cmd", label=label, rc=rc, out=so[-1500:], err=se[-800:],
              log=str(p))
    return rc, so, se


def list_gamemd():
    snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
    if not snap or snap == ctypes.c_void_p(-1).value:
        return []
    out = []
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            if (pe.szExeFile or "").lower() == "gamemd.exe":
                out.append({"pid": int(pe.th32ProcessID),
                            "ppid": int(pe.th32ParentProcessID)})
            ok = k32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        k32.CloseHandle(snap)
    return out


def launch_game(sandbox: Path, sink: Sink):
    cmdline = 'cmd.exe /c cd /d "%s" && start "" "gamemd.exe"' % str(sandbox)
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='%s'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % cmdline)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=90)
    txt = (r.stdout or "").strip()
    sink.step("launch_wmi", stdout=txt, stderr=(r.stderr or "")[:300])
    m = None
    for line in txt.splitlines():
        m = re.search(r"(\d+)\|(\d+)", line)
        if m:
            break
    launcher_pid = int(m.group(1)) if m else 0
    retval = int(m.group(2)) if m else -1
    if retval != 0:
        raise RuntimeError("WMI Win32_Process.Create failed retval=%d" % retval)
    return launcher_pid


def wait_for_pid(launcher_pid, sink: Sink, timeout_s=90):
    t0 = time.monotonic()
    fallback = None
    while time.monotonic() - t0 < timeout_s:
        rows = list_gamemd()
        for row in rows:
            if launcher_pid and row["ppid"] == launcher_pid:
                sink.step("pid_found", pid=row["pid"],
                          how="wmi_child_parent_pid",
                          elapsed_s=round(time.monotonic() - t0, 2))
                return row["pid"]
        if rows and fallback is None:
            fallback = rows[0]["pid"]
        time.sleep(1.0)
    if fallback:
        sink.step("pid_found", pid=fallback, how="fallback_only_gamemd_present")
        return fallback
    raise RuntimeError("no gamemd.exe within %ss" % timeout_s)


def process_alive(pid):
    return any(r["pid"] == pid for r in list_gamemd())


def close_game(pid, hwnd, sink: Sink):
    steps = []
    if not pid:
        sink.step("close_game", steps=["no_pid_no_launch"])
        return ["no_pid_no_launch"]
    if not process_alive(pid):
        sink.step("close_game", steps=["already_exited"], pid=pid)
        return ["already_exited"]
    if hwnd and u.IsWindow(hwnd):
        ok = u.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        steps.append("WM_CLOSE(hwnd=%s)->%s" % (hwnd, bool(ok)))
        time.sleep(2.0)
    if process_alive(pid):
        r = subprocess.run(["taskkill", "/PID", str(pid)],
                           capture_output=True, text=True, timeout=30)
        steps.append("taskkill /PID %s rc=%s" % (pid, r.returncode))
        time.sleep(2.0)
    if process_alive(pid):
        r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, text=True, timeout=30)
        steps.append("taskkill /F /PID %s rc=%s" % (pid, r.returncode))
        time.sleep(1.0)
    residual = [r for r in list_gamemd() if r["pid"] == pid]
    steps.append("residual_own_pid=%d" % len(residual))
    sink.step("close_game", pid=pid, steps=steps,
              all_gamemd_residual=list_gamemd())
    return steps


def wtxt(h):
    n = u.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(max(n + 1, 2))
    u.GetWindowTextW(h, b, n + 1)
    return b.value


def wcls(h):
    b = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(h, b, 256)
    return b.value


def rect(h):
    r = RECT()
    if u.GetWindowRect(h, ctypes.byref(r)):
        return [r.left, r.top, r.right, r.bottom]
    return None


def top_windows(pid):
    tops = []

    def cb(h, _l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append(h)
        return True
    u.EnumWindows(ENUM(cb), 0)
    return tops


def controls(pid):
    out, seen = [], set()

    def add(h):
        if h in seen:
            return
        seen.add(h)
        out.append({"hwnd": int(h), "cls": wcls(h), "text": wtxt(h),
                    "visible": bool(u.IsWindowVisible(h)), "rect": rect(h),
                    "ctrl_id": int(u.GetDlgCtrlID(h))})

    def walk(h):
        kids = []

        def ccb(kk, _l):
            kids.append(kk)
            return True
        u.EnumChildWindows(h, ENUM(ccb), 0)
        for kk in kids:
            add(kk)
            walk(kk)
    for t in top_windows(pid):
        add(t)
        walk(t)
    return out


def normalized(controls_list):
    return sorted([(c["text"] or "", c["cls"] or "",
                    bool(c["visible"]), int(c["ctrl_id"]))
                   for c in controls_list])


def find_btn(pid, name):
    for c in controls(pid):
        if c["cls"] == "Button" and name.lower() in (c["text"] or "").lower():
            return c["hwnd"]
    return None


def click(pid, name, sink: Sink, wait_s=0.8, label=None):
    h = find_btn(pid, name)
    rec = {"action": "click", "control_text": name, "hwnd": h,
           "label": label or name}
    if not h:
        rec["result"] = "not_found"
        sink.step("click", **rec)
        return False
    ok = bool(u.PostMessageW(h, BM_CLICK, 0, 0))
    rec["result"] = "posted" if ok else "post_failed"
    time.sleep(wait_s)
    sink.step("click", **rec)
    return ok


def click_hwnd(hwnd, sink: Sink, label, wait_s=0.8):
    ok = bool(u.PostMessageW(hwnd, BM_CLICK, 0, 0))
    sink.step("click_hwnd", label=label, hwnd=hwnd, result=bool(ok))
    time.sleep(wait_s)
    return ok


def key(vk, sink: Sink, label):
    u.keybd_event(vk, 0, 0, 0)
    u.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    sink.step("key", label=label, vk=vk)
    time.sleep(0.6)


def force_foreground(hwnd):
    if not hwnd or not u.IsWindow(hwnd):
        return False
    try:
        u.AllowSetForegroundWindow(0xFFFFFFFF)
    except Exception:
        pass
    u.keybd_event(VK_MENU, 0, 0, 0)
    try:
        u.ShowWindow(hwnd, SW_RESTORE)
        u.BringWindowToTop(hwnd)
        u.SetForegroundWindow(hwnd)
    finally:
        u.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)
    return int(u.GetForegroundWindow()) == int(hwnd)


def game_hwnd(pid):
    for h in top_windows(pid):
        if wcls(h) == GAME_WND_CLASS:
            return h
    return None


def real_mouse_click(sink: Sink, label: str, x: int, y: int, wait_s=1.0):
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    u.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    u.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    sink.step("real_mouse_click", label=label, x=x, y=y)
    time.sleep(wait_s)


def smt(h, msg, wp=0, lp=0, timeout=2500):
    r = ctypes.c_size_t(0)
    u.SendMessageTimeoutW(h, msg, wp, lp, SMTO_ABORTIFHUNG, timeout,
                          ctypes.byref(r))
    return r.value


def type_ascii(sink: Sink, label: str, text: str, wait_s=0.6):
    for ch in text:
        vk = ord(ch.upper())
        u.keybd_event(vk, 0, 0, 0)
        u.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.03)
    sink.step("type_ascii", label=label, text=text)
    time.sleep(wait_s)


def wm_settext(sink: Sink, label: str, hwnd, text: str, wait_s=0.5):
    b = ctypes.create_unicode_buffer(text)
    r = ctypes.c_size_t(0)
    u.SendMessageTimeoutW(hwnd, WM_SETTEXT, 0, ctypes.addressof(b),
                          SMTO_ABORTIFHUNG, 2000, ctypes.byref(r))
    sink.step("wm_settext", label=label, hwnd=hwnd, text=text,
              result=int(r.value))
    time.sleep(wait_s)


# ------------------------------------------------------------------ read-only RPM
def open_proc(pid):
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    return h if h else None


def rpm(hproc, addr, size):
    buf = (ctypes.c_char * size)()
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size,
                               ctypes.byref(got))
    if not ok or got.value != size:
        return None
    return bytes(buf.raw)


def rpm_partial(hproc, addr, size):
    buf = (ctypes.c_char * size)()
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size,
                               ctypes.byref(got))
    if not ok or got.value == 0:
        return None
    return bytes(buf.raw[:got.value])


def read_cstr(hproc, addr, max_len=260):
    b = rpm_partial(hproc, addr, max_len)
    if not b:
        return None
    z = b.find(b"\x00")
    if z >= 0:
        b = b[:z]
    return b.decode("latin-1", errors="replace")


def read_counters(hproc):
    out = {}
    for k, a in ADDR.items():
        b = rpm(hproc, a, 4)
        out[k] = int.from_bytes(b, "little") if b else None
    scen = out.get("scen_ptr")
    if scen and scen > 0x10000:
        out["scen_filename"] = read_cstr(hproc, scen + 0x125C, 128)
        out["scen_next"] = read_cstr(hproc, scen + 0x04, 128)
        b_skip = rpm(hproc, scen + 0x34B0, 1)
        out["scen_skip_mapsel"] = b_skip[0] if b_skip else None
        b_stg = rpm(hproc, scen + 0x35A0, 2)
        out["scen_stage_idx"] = int.from_bytes(b_stg, "little") if b_stg else None
        b_bat = rpm(hproc, scen + 0x34CC, 4)
        out["scen_battle_idx"] = int.from_bytes(b_bat, "little") if b_bat else None
    return out


# ------------------------------------------------------------------ screenshot / precheck
def screenshot(sink: Sink, label: str, hwnd=None):
    try:
        from PIL import ImageGrab
        bbox = rect(hwnd) if hwnd else None
        img = ImageGrab.grab(bbox=bbox)
        p = OUT / ("screen_%s.png" % label)
        img.save(p)
        sink.step("screenshot", label=label, path=str(p), bbox=bbox,
                  size=[img.width, img.height])
        return p
    except Exception as e:
        sink.step("screenshot", label=label, error=repr(e))
        return None


def desktop_precheck(sink: Sink):
    UOI_NAME = 2
    DESKTOP_READOBJECTS = 0x0001
    u.GetProcessWindowStation.restype = wt.HANDLE
    u.GetThreadDesktop.restype = wt.HANDLE
    u.GetThreadDesktop.argtypes = [wt.DWORD]
    u.OpenInputDesktop.restype = wt.HANDLE
    u.OpenInputDesktop.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    u.GetUserObjectInformationW.restype = wt.BOOL
    u.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int,
                                            ctypes.c_void_p, wt.DWORD,
                                            ctypes.POINTER(wt.DWORD)]
    u.CloseDesktop.restype = wt.BOOL
    u.CloseDesktop.argtypes = [wt.HANDLE]
    k32.GetCurrentThreadId.restype = wt.DWORD

    def obj_name(h):
        if not h:
            return None
        n = wt.DWORD(0)
        buf = ctypes.create_unicode_buffer(512)
        ok = u.GetUserObjectInformationW(h, UOI_NAME, buf,
                                         ctypes.sizeof(buf), ctypes.byref(n))
        return buf.value if ok else "<err=%d>" % ctypes.get_last_error()

    res = {"window_station": obj_name(u.GetProcessWindowStation()),
           "thread_desktop": obj_name(u.GetThreadDesktop(k32.GetCurrentThreadId()))}
    hin = u.OpenInputDesktop(0, False, DESKTOP_READOBJECTS)
    res["input_desktop"] = obj_name(hin) if hin else "<OpenInputDesktop NULL>"
    if hin:
        u.CloseDesktop(hin)
    tops = []

    def cb(h, _l):
        tops.append(h)
        return True
    u.EnumWindows(ENUM(cb), 0)
    res["enum_windows_total"] = len(tops)
    res["enum_windows_visible"] = sum(1 for h in tops if u.IsWindowVisible(h))
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        res["imagegrab"] = "OK"
        res["imagegrab_size"] = [img.width, img.height]
    except Exception as e:
        res["imagegrab"] = "FAILED: %r" % (e,)
    res["enum_ok"] = res["enum_windows_total"] >= 1
    res["grab_ok"] = res["imagegrab"] == "OK"
    res["pass"] = bool(res["enum_ok"] and res["grab_ok"])
    sink.step("step0_desktop_precheck", kind="meta", **res)
    if not res["pass"]:
        raise RuntimeError("STEP0_PRECHECK_FAILED: %s"
                           % json.dumps(res, ensure_ascii=False))
    return res


# ------------------------------------------------------------------ config / lock / inventory
def save_inventory(sandbox: Path, sink: Sink, label: str):
    rows = []
    for p in sorted(sandbox.glob("*"), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in (".sav", ".svg"):
            rows.append({"name": p.name, "size": p.stat().st_size,
                         "sha256": sha256_file(p),
                         "mtime_ns": p.stat().st_mtime_ns})
    sink.step("save_inventory", label=label, files=rows, n=len(rows))
    return rows


def restore_configs(sandbox: Path, sink: Sink):
    rows = []
    for n in CONFIG_RESTORE:
        src = OUT / ("pristine_" + n)
        dst = sandbox / n
        if src.is_file() and dst.is_file():
            shutil.copyfile(src, dst)
        rows.append({"file": n,
                     "sha256": sha256_file(dst) if dst.is_file() else None,
                     "expected": sha256_file(src) if src.is_file() else None,
                     "match": (dst.is_file() and src.is_file()
                               and sha256_file(dst) == sha256_file(src))})
    sink.step("restore_configs", rows=rows,
              all_match=all(r["match"] for r in rows))
    return rows


def lock_claim(owner: str, purpose: str):
    LOCK.write_text("run_id=NEXT_RE_20261112_R02\nowner=%s\ntime=%s\npurpose=%s\n"
                    % (owner, local_iso(), purpose), encoding="utf-8")


def lock_restore_lead():
    lock_claim("lead", "W45 B-line equivalence card finished: restored owner=lead "
               "(all game instances closed, configs byte-restored, drops removed)")


def robocopy(src: Path, dst: Path, sink: Sink, label: str):
    args = ["robocopy", str(src), str(dst), "/E", "/COPY:DAT", "/DCOPY:DAT",
            "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
    rc, so, se = run_cmd(args, ROOT, sink, label, timeout=600)
    ok = 0 <= rc < 8
    sink.step("robocopy", label=label, src=str(src), dst=str(dst), rc=rc,
              ok=ok)
    if not ok:
        raise RuntimeError("robocopy failed rc=%d %s" % (rc, se[-300:]))
    return ok


def tree_manifest(d: Path):
    rows = []
    for dirpath, _dirs, files in os.walk(d):
        for name in files:
            p = Path(dirpath) / name
            try:
                st = p.stat()
                rows.append({"rel": str(p.relative_to(d)).replace("\\", "/"),
                             "size": st.st_size, "sha256": sha256_file(p)})
            except OSError as e:
                rows.append({"rel": str(p.relative_to(d)).replace("\\", "/"),
                             "error": repr(e)})
    rows.sort(key=lambda r: r["rel"].lower())
    return {"file_count": len(rows),
            "total_bytes": sum(r.get("size", 0) for r in rows),
            "maplike_count": sum(1 for r in rows
                                 if Path(r["rel"]).suffix.lower()
                                 in {".yrm", ".mpr", ".map"}),
            "rows": rows}


# ------------------------------------------------------------------ phases
def phase_prep(sink: Sink):
    sink.step("phase_prep_start", real_dir=str(REAL), base=str(BASE))
    if BASE.exists():
        shutil.rmtree(BASE, ignore_errors=True)
    robocopy(REAL, BASE, sink, "prep_robocopy_base")
    m = tree_manifest(BASE)
    (OUT / "sandbox_base_pre.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    sink.step("base_pre_manifest", file_count=m["file_count"],
              total_bytes=m["total_bytes"], maplike_count=m["maplike_count"])

    # Snapshot pristine configs BEFORE any game launch (post-uninstall state).
    for n in CONFIG_RESTORE:
        p = BASE / n
        if p.is_file():
            shutil.copyfile(p, OUT / ("pristine_" + n))
    sink.step("pristine_captured", files=[n for n in CONFIG_RESTORE
                                          if (BASE / n).is_file()])

    # Both arms share the SAME prepared base: remove the pre-existing v0.3
    # package in-place (W44 S2), so neither arm carries it as a confounder.
    rc, so, se = run_cmd([PY, "-B", "-m", "ra2forge", "uninstall",
                          "--game", str(BASE), "--json"], V13, sink,
                         "prep_uninstall_v03")
    rc2, so2, se2 = run_cmd([PY, "-B", "-m", "ra2forge", "verify",
                            "--game", str(BASE), "--json"], V13, sink,
                           "prep_verify_after_uninstall")
    sink.step("prep_clean_base", uninstall_rc=rc, verify_rc=rc2,
              verify_json=so2[-1200:])

    # Build ONE v13 package from the SAME fixed design for every B run.
    DESIGN.parent.mkdir(parents=True, exist_ok=True)
    if PKG.exists():
        shutil.rmtree(PKG, ignore_errors=True)
    PKG.mkdir(parents=True, exist_ok=True)
    rc3, so3, se3 = run_cmd([PY, "-B", "-m", "ra2forge", "build",
                             "--design", str(DESIGN), "--out", str(PKG)],
                            V13, sink, "prep_build_v13")
    pkg_rows = []
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            pkg_rows.append({"rel": str(p.relative_to(PKG)).replace("\\", "/"),
                             "size": p.stat().st_size, "sha256": sha256_file(p)})
    sink.step("v13_package", build_rc=rc3, files=pkg_rows,
              package_inner=str(PKG_INNER),
              inner_has_battlemd98=(PKG_INNER / "BATTLEMD98.INI").is_file(),
              package_digest=hashlib.sha256(
                  "\n".join(sorted("%s %s" % (r["rel"], r["sha256"])
                                  for r in pkg_rows)).encode()).hexdigest())
    if not (PKG_INNER / "BATTLEMD98.INI").is_file():
        raise RuntimeError("built package inner dir lacks BATTLEMD98.INI: %s"
                           % PKG_INNER)
    sink.step("phase_prep_end", ok=(rc == 0 and rc2 == 0 and rc3 == 0))


def collect_one_arm(arm: str, tag: str, sink: Sink, sample_seconds: int):
    """One full trip. Returns a dict of collected comparables (never raises
    out without cleanup; errors are recorded and returned)."""
    sandbox = CARD / ("sandbox_" + tag)
    if sandbox.exists():
        shutil.rmtree(sandbox, ignore_errors=True)
    robocopy(BASE, sandbox, sink, tag + "_robocopy_run")

    rec = {"arm": arm, "tag": tag, "sandbox": str(sandbox),
           "errors": [], "phase_reached": False}

    # ---- install / verify state (B only) ----
    if arm.startswith("B"):
        # NOTE: `install` has NO --json flag (round-1 defect: exit 2).
        # Plain install first; only a definite content conflict (exit 1)
        # gets the explicit --allow-content-conflict release.
        rci, so_i, se_i = run_cmd(
            [PY, "-B", "-m", "ra2forge", "install", "--package",
             str(PKG_INNER), "--game", str(sandbox)], V13, sink,
            tag + "_install_v13")
        if rci == 1:
            rci, so_i, se_i = run_cmd(
                [PY, "-B", "-m", "ra2forge", "install", "--package",
                 str(PKG_INNER), "--game", str(sandbox),
                 "--allow-content-conflict"], V13, sink,
                tag + "_install_v13_allow")
        rec["install_rc"] = rci
        rec["install_stdout"] = so_i[-1200:]
        if rci != 0:
            rec["errors"].append("install rc=%d" % rci)
    rcv, so_v, se_v = run_cmd(
        [PY, "-B", "-m", "ra2forge", "verify", "--game", str(sandbox),
         "--json"], V13, sink, tag + "_verify_pre")
    rec["verify_pre_rc"] = rcv
    try:
        rec["verify_pre_json"] = json.loads(so_v)
    except Exception:
        rec["verify_pre_json"] = {"parse_error": so_v[-600:]}

    pid, hwnd, hproc = None, None, None
    try:
        # ---- pre-launch guard ----
        pre = list_gamemd()
        sink.step("pre_launch_guard", gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("gamemd residual before launch: %r" % pre)

        launcher = launch_game(sandbox, sink)
        # HARD GATE: desktop precheck within 30 s of WMI launch.
        desktop_precheck(sink)
        pid = wait_for_pid(launcher, sink)
        hproc = open_proc(pid)
        sink.step("proc_opened", pid=pid, hproc=bool(hproc))
        if not hproc:
            raise RuntimeError("OpenProcess(PROCESS_VM_READ) failed")

        # ---- main menu -> official campaign (NO D2 hijack) ----
        def wait_text(text, timeout_s, retry_click=None):
            t = time.monotonic()
            while time.monotonic() - t < timeout_s:
                cs = controls(pid)
                hits = [c for c in cs
                        if text.lower() in (c.get("text") or "").lower()]
                if hits:
                    sink.step("wait_text_found", text=text,
                              elapsed_s=round(time.monotonic() - t, 2),
                              hits=[(c["text"], c["cls"], c["visible"])
                                    for c in hits[:6]])
                    return hits
                if retry_click and (time.monotonic() - t) > 3.0:
                    click(pid, retry_click, sink, wait_s=0.6,
                          label=tag + "_retry_" + retry_click)
                    time.sleep(1.0)
                time.sleep(0.5)
            sink.step("wait_text_timeout", text=text,
                      controls=normalized(controls(pid))[:40])
            return None

        hwnd = None
        t0 = time.monotonic()
        while time.monotonic() - t0 < 90:
            hwnd = game_hwnd(pid)
            if hwnd and find_btn(pid, "GUI:SinglePlayer"):
                break
            time.sleep(0.5)
        if not hwnd or not find_btn(pid, "GUI:SinglePlayer"):
            raise RuntimeError("main menu not reached (GUI:SinglePlayer absent)")
        sink.step("main_menu_ready", hwnd=hwnd, rect=rect(hwnd),
                  elapsed_s=round(time.monotonic() - t0, 2))
        force_foreground(hwnd)
        click(pid, "GUI:SinglePlayer", sink, wait_s=1.2,
              label=tag + "_click_SinglePlayer")
        # BM_CLICK is async: POLL for the submenu instead of assuming a fixed
        # sleep was enough (A1test lesson: the click landed ~90 s later).
        if not wait_text("GUI:NewCampaign", 25, retry_click="GUI:SinglePlayer"):
            raise RuntimeError("single-player submenu not reached "
                               "(GUI:NewCampaign absent)")
        click(pid, "GUI:NewCampaign", sink, wait_s=2.0,
              label=tag + "_click_NewCampaign")
        if not wait_text("GUI:CampaignMenu", 25, retry_click="GUI:NewCampaign"):
            raise RuntimeError("campaign menu not reached "
                               "(GUI:CampaignMenu absent)")
        sink.step("campaign_menu_controls",
                  controls=normalized(controls(pid))[:40])
        screenshot(sink, tag + "_campaign_menu", hwnd)
        # Official Soviet badge (screen coords, W39/W44 proven).
        real_mouse_click(sink, tag + "_click_SOVIET_badge", 210, 285, wait_s=3.0)

        # ---- wait for scenario / skip movie / in-game ----
        cnt = read_counters(hproc)
        sink.step("after_badge_counters", counters=cnt)
        force_foreground(hwnd)
        for _ in range(2):
            key(VK_RETURN, sink, tag + "_skip_movie_RETURN")
        t1 = time.monotonic()
        ingame = False
        last_dump = -99.0
        while time.monotonic() - t1 < 120:
            # A briefing/play screen may appear (W44 clicks GUI:Play / StartGame).
            for btn in ("GUI:Play", "GUI:StartGame", "GUI:Continue"):
                if find_btn(pid, btn):
                    click(pid, btn, sink, wait_s=1.0,
                          label=tag + "_click_" + btn)
            cnt = read_counters(hproc)
            if cnt and (cnt.get("frame") or 0) > 30 and cnt.get("scen_filename"):
                ingame = True
                break
            # keybd_event goes to the FOREGROUND window; re-assert it, since
            # losing focus is the observed cause of flaky briefing dismissal.
            if int(time.monotonic() - t1) in (6, 14, 24):
                force_foreground(hwnd)
                key(VK_RETURN, sink, tag + "_retry_RETURN")
            if (time.monotonic() - t1) - last_dump >= 15:
                last_dump = time.monotonic() - t1
                sink.step("waiting_ingame_controls",
                          elapsed_s=round(last_dump, 1), counters=cnt,
                          controls=normalized(controls(pid))[:60])
            time.sleep(1.0)
        rec["ingame"] = ingame
        rec["counters_at_ingame"] = cnt
        if not ingame:
            raise RuntimeError("in-game phase not reached (frame>30 OR "
                               "scen_filename missing): %r" % (cnt,))
        rec["phase_reached"] = True
        force_foreground(hwnd)
        screenshot(sink, tag + "_ingame", hwnd)

        # ---- (1) timer series on the STABLE in-game segment ----
        samples = []
        read_fail = 0
        t2 = time.monotonic()
        # 6 ms cadence (HANDOFF §4.4 / W14): at 30 ms polling a Δframe==2 is
        # a sampling artefact, not a skipped tick. 6 ms makes the ≥64 ms and
        # Δframe>=2 criteria meaningful.
        while time.monotonic() - t2 < sample_seconds:
            c = read_counters(hproc)
            if not c or c.get("frame") is None:
                read_fail += 1
            else:
                samples.append((round(time.monotonic() - t2, 4),
                                c["frame"], c.get("mode")))
            time.sleep(0.006)
        # Trim any frame==0 loading remnants at either end.
        while samples and samples[0][1] == 0:
            samples.pop(0)
        while samples and samples[-1][1] == 0:
            samples.pop()
        frames = [s[1] for s in samples]
        wall = samples[-1][0] - samples[0][0] if len(samples) >= 2 else 0.0
        # Inter-tick intervals: wall gap between successive frame increments.
        inc_idx = [i for i in range(1, len(frames)) if frames[i] > frames[i - 1]]
        inc_times = [samples[i][0] for i in inc_idx]
        inc_jumps = [frames[i] - frames[i - 1] for i in inc_idx]
        intervals_ms = [round((inc_times[j] - inc_times[j - 1]) * 1000.0, 3)
                        for j in range(1, len(inc_times))]
        srt = sorted(intervals_ms)
        def pct(q):
            return srt[min(len(srt) - 1, int(q * len(srt)))] if srt else None
        rec["timer"] = {
            "cadence_s": 0.006,
            "n_samples": len(samples), "read_fail": read_fail,
            "wall_s": round(wall, 3),
            "frame_first": frames[0] if frames else None,
            "frame_last": frames[-1] if frames else None,
            "frame_delta": (frames[-1] - frames[0]) if frames else None,
            "rate_cps": (round((frames[-1] - frames[0]) / wall, 5)
                         if wall > 0 and frames else None),
            "n_increments": len(inc_idx),
            "interval_median_ms": pct(0.50), "interval_p95_ms": pct(0.95),
            "interval_p99_ms": pct(0.99),
            "interval_max_ms": max(intervals_ms) if intervals_ms else None,
            "intervals_ge64ms": sum(1 for x in intervals_ms if x >= 64),
            "delta_frame_ge2": sum(1 for d in inc_jumps if d >= 2),
            "series_head": samples[:5], "series_tail": samples[-5:],
        }
        sink.step("timer_series", **{k: v for k, v in rec["timer"].items()
                                     if k not in ("series_head", "series_tail")})
        rec["counters_after_timer"] = read_counters(hproc)

        # ---- (2)+(6) Esc menu control set / visibility, 3 stable polls ----
        # Round-1 lesson (A2): a single VK_ESCAPE can be lost, and blindly
        # pressing twice would CLOSE the menu.  Check first, press only if
        # the in-game menu is not already present.
        esc_open = False
        force_foreground(hwnd)
        for attempt in range(3):
            cs = controls(pid)
            if any("GUI:ResumeMission" in (c.get("text") or "") for c in cs):
                esc_open = True
                break
            key(VK_ESCAPE, sink, tag + "_Esc_open_attempt%d" % attempt)
            time.sleep(0.8)
        rec["esc_menu_opened"] = esc_open
        sink.step("esc_menu_open", opened=esc_open)
        polls = []
        for i in range(3):
            cs = controls(pid)
            polls.append(normalized(cs))
            time.sleep(0.8)
        rec["esc_polls"] = polls
        req_hit = sorted([t for t in ESC_REQUIRED
                          if any(any(t.lower() in (x[0] or "").lower()
                                     for x in p) for p in polls)])
        rec["esc_required_hits"] = req_hit
        rec["esc_stable"] = (polls[0] == polls[1] == polls[2])
        sink.step("esc_menu_controls", polls=[p[:40] for p in polls],
                  required_hits=req_hit, stable=rec["esc_stable"],
                  n_controls=[len(p) for p in polls])
        screenshot(sink, tag + "_esc_menu", hwnd)

        # ---- (4) save file bytes, using the already-open menu ----
        before = save_inventory(sandbox, sink, tag + "_before_save")
        try:
            click(pid, "GUI:SaveGame", sink, wait_s=2.0,
                  label=tag + "_click_SaveGame")
            cs = controls(pid)
            sv = [c for c in cs if c["cls"] == "Button" and c["visible"]
                  and (c["text"] or "") == "GUI:Save"]
            boxes = [c for c in cs if c["cls"] == "ListBox"
                     and int(smt(c["hwnd"], LB_GETCOUNT)) > 0]
            edits = [c for c in cs if c["cls"] == "Edit"]
            sink.step("save_dialog_plan", save_buttons=[c["text"] for c in sv],
                      n_boxes=len(boxes), n_edits=len(edits))
            if boxes:
                smt(boxes[0]["hwnd"], LB_SETCURSEL, 0)
                r = boxes[0]["rect"]
                real_mouse_click(sink, tag + "_click_first_slot",
                                 (r[0] + r[2]) // 2, r[1] + 10, wait_s=0.6)
            if edits:
                r = edits[0]["rect"]
                real_mouse_click(sink, tag + "_focus_name_field",
                                 (r[0] + r[2]) // 2, (r[1] + r[3]) // 2,
                                 wait_s=0.6)
                type_ascii(sink, tag + "_type_save_name", "W45SAVE")
                wm_settext(sink, tag + "_wm_settext", edits[0]["hwnd"],
                           "W45SAVE")
            screenshot(sink, tag + "_save_dialog", hwnd)
            if sv:
                click_hwnd(sv[0]["hwnd"], sink, tag + "_click_GUI_Save",
                           wait_s=3.0)
            after = save_inventory(sandbox, sink, tag + "_after_save")
            bmap = {x["name"]: x for x in before}
            added = [f for f in after if f["name"] not in bmap]
            changed = [f for f in after if f["name"] in bmap
                       and f["sha256"] != bmap[f["name"]]["sha256"]]
            rec["save_added"] = added
            rec["save_changed"] = changed
            saved = None
            for f in (added + changed):
                src = sandbox / f["name"]
                if src.is_file():
                    dst = OUT / ("save_%s_%s" % (tag, f["name"]))
                    dst.write_bytes(src.read_bytes())
                    saved = {"name": f["name"], "size": f["size"],
                             "sha256": f["sha256"], "copy": str(dst)}
                    sink.step("save_copied", **saved)
                    break
            rec["save"] = saved
            if saved is None and sv:
                click_hwnd(sv[0]["hwnd"], sink, tag + "_click_GUI_Save_retry",
                           wait_s=3.0)
                after2 = save_inventory(sandbox, sink, tag + "_after_save_retry")
                added2 = [f for f in after2 if f["name"] not in bmap]
                for f in added2:
                    src = sandbox / f["name"]
                    if src.is_file():
                        dst = OUT / ("save_%s_%s" % (tag, f["name"]))
                        dst.write_bytes(src.read_bytes())
                        rec["save"] = {"name": f["name"], "size": f["size"],
                                       "sha256": f["sha256"], "copy": str(dst)}
                        break
        except Exception as e:
            rec["errors"].append("save: %r" % (e,))
            sink.step("save_failed", error=repr(e))
        rec["counters_after_save"] = read_counters(hproc)

        # ---- verify post ----
        rcv2, so_v2, _ = run_cmd(
            [PY, "-B", "-m", "ra2forge", "verify", "--game", str(sandbox),
             "--json"], V13, sink, tag + "_verify_post")
        rec["verify_post_rc"] = rcv2
        try:
            rec["verify_post_json"] = json.loads(so_v2)
        except Exception:
            rec["verify_post_json"] = {"parse_error": so_v2[-600:]}

    except Exception as e:
        rec["errors"].append("run: %r" % (e,))
        sink.step("run_error", error=repr(e))
        try:
            screenshot(sink, tag + "_on_error", hwnd)
        except Exception:
            pass
    finally:
        # ---- HARD finally: close -> residual 0 -> restore -> remove drops ----
        try:
            steps = close_game(pid, hwnd, sink) if pid else ["no_pid"]
            rec["close_steps"] = steps
            rec["residual_after_close"] = list_gamemd()
        except Exception as e:
            rec["errors"].append("close: %r" % (e,))
        try:
            rec["restore_configs"] = restore_configs(sandbox, sink)
        except Exception as e:
            rec["errors"].append("restore: %r" % (e,))
        try:
            # remove drops: .sav files created by this run (not in pristine base)
            base_saves = {x["name"] for x in save_inventory(BASE, sink,
                                                            tag + "_base_saves")}
            removed = []
            for p in sandbox.glob("*"):
                if p.is_file() and p.suffix.lower() in (".sav", ".svg") \
                        and p.name not in base_saves:
                    p.unlink()
                    removed.append(p.name)
            rec["drops_removed"] = removed
            sink.step("drops_removed", files=removed)
        except Exception as e:
            rec["errors"].append("drops: %r" % (e,))
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
        sink.step("meta_end", kind="meta", arm=arm, tag=tag,
                  errors=rec["errors"], residual=rec.get("residual_after_close"),
                  restore_all_match=all(
                      r["match"] for r in rec.get("restore_configs", []))
                  if rec.get("restore_configs") else None)
    (OUT / ("%s_result.json" % tag)).write_text(
        json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True,
                   default=str), encoding="utf-8")
    return rec


def phase_run(arms, sink: Sink, sample_seconds: int):
    results = {}
    for tag in arms:
        arm = tag[0]
        sink.step("arm_start", kind="meta", arm=arm, tag=tag,
                  sample_seconds=sample_seconds)
        t0 = time.monotonic()
        results[tag] = collect_one_arm(arm, tag, sink, sample_seconds)
        sink.step("arm_end", kind="meta", arm=arm, tag=tag,
                  elapsed_s=round(time.monotonic() - t0, 2),
                  phase_reached=results[tag].get("phase_reached"),
                  errors=results[tag].get("errors"))
    (OUT / "dual_track_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1, sort_keys=True,
                   default=str), encoding="utf-8")
    return results


def phase_finalize(sink: Sink):
    # real-dir POST proof (real dir was only a robocopy source, never written)
    rc, so, se = run_cmd(
        [PY, str(TOOLS / "w45_real_dir_baseline.py"), "--phase", "post"],
        ROOT, sink, "finalize_real_dir_post")
    sink.step("finalize_real_dir_post", rc=rc, out=so[-800:])
    # remove run sandboxes (投放物) to reclaim disk; keep base + out evidence
    removed = []
    for p in CARD.glob("sandbox_A*"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            removed.append(p.name)
    for p in CARD.glob("sandbox_B*"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            removed.append(p.name)
    sink.step("run_sandboxes_removed", dirs=removed)
    sink.step("finalize_end", gamemd_residual=list_gamemd())
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("all", "prep", "run", "finalize"),
                    default="all")
    ap.add_argument("--arms", default="A1,A2,B1")
    ap.add_argument("--sample-seconds", type=int, default=75)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sink = Sink("w45_dual_track")
    claimed = False
    try:
        pre = LOCK.read_text(encoding="utf-8") if LOCK.is_file() else ""
        sink.step("lock_before", content=pre)
        if "owner=lead" not in pre:
            # still claim if no other active owner (honest guard)
            sink.step("lock_warning", note="owner is not lead; proceeding "
                      "because card is the designated single writer")
        lock_claim("w45", "W45 B-line equivalence dual-track (single "
                   "instance; restores owner=lead in finally)")
        claimed = True
        if a.phase in ("all", "prep"):
            phase_prep(sink)
        if a.phase in ("all", "run"):
            arms = [x.strip() for x in a.arms.split(",") if x.strip()]
            phase_run(arms, sink, a.sample_seconds)
        if a.phase in ("all", "finalize"):
            phase_finalize(sink)
        return 0
    except Exception as e:
        sink.step("FATAL", error=repr(e))
        return 2
    finally:
        # ALWAYS: make sure no game instance survives, then release the lock.
        try:
            for p in list_gamemd():
                subprocess.run(["taskkill", "/F", "/PID", str(p["pid"])],
                               capture_output=True, timeout=30)
            sink.step("final_sweep", residual=list_gamemd())
        except Exception as e:
            sink.step("final_sweep_error", error=repr(e))
        try:
            lock_restore_lead()
            sink.step("lock_restored", content=LOCK.read_text(encoding="utf-8"))
        except Exception as e:
            sink.step("lock_restore_error", error=repr(e))
        sink.close()


if __name__ == "__main__":
    raise SystemExit(main())

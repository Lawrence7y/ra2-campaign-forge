#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W65 / B-line NEW-CRITERIA real-machine live collector.

PROVENANCE
----------
This file is a **copy** of W45_b_line_equivalence/tools/w45_dual_track.py
(pristine unmodified copy kept at tools/w45_skeleton_copied.py) whose Win32 /
ReadProcessMemory / keypress / screenshot primitives are reused VERBATIM, with:

  * every output path redirected into W65_bline_live_collect/ (never imports
    another card's script -- HANDOFF discipline);
  * read-only RPM layer extended to the FULL FROZEN CRITERIA_SPEC.md §2.1
    schema (Scen+0x34AC end_of_game added; +0x125C read as 260-byte C string
    per W63/W59);
  * EnumWindows/EnumChildWindows visible-control-id capture for ui_controls;
  * NDJSON rows written to out/<TAG>.ndjson (one row per 6 ms sample);
  * per-trip lock claim owner=w65 -> release owner=lead in finally;
  * full-tree PRE/POST byte-exact restore + real-computed self-proof.

FROZEN thresholds (CRITERIA_SPEC.md §2.5) are NEVER touched here; this tool
only PRODUCES data.  The verdict is produced by W62's tool_b_stats.py.

DISCIPLINE (task card W65 red lines)
  * ReadProcessMemory only (PROCESS_VM_READ|PROCESS_QUERY_INFORMATION).
    NO write-memory / breakpoint / suspend-thread / injection / exe modification.
  * .game_instance.lock: read before EACH trip; wait if owner != lead or any
    live gamemd.exe; claim owner=w65; release owner=lead + status in FINALLY,
    regardless of success.  Never hold the lock across trips.
  * ra2youli is a READ-ONLY robocopy source + hash target.  Never written.
  * Only gamemd.exe pids launched by THIS trip are closed; residual=0 proven.
  * Sandbox writable configs: byte copies + hashes before launch; byte-exact
    restore after; full-tree hash equality re-computed as self-proof.
  * Only writes inside W65_bline_live_collect/; git untouched.

Usage:
  python w65_collect.py --phase prep
  python w65_collect.py --phase trip --tag A1|A2|B1|B2 [--sample-seconds 75]
  python w65_collect.py --phase audit
  python w65_collect.py --phase finalize
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
CARD = RUN / "W65_bline_live_collect"
OUT = CARD / "out"
TOOLS = CARD / "tools"
BASE = CARD / "sandbox_base"          # common clean sandbox start for BOTH arms
PKG = OUT / "pkg"                      # v15 build output dir
PKG_INNER = PKG / "W65Bline"           # inner package dir (campaign name)
V15 = RUN / "W60_battlemd_inplace" / "ra2forge_patched_v15"
REAL = ROOT / "ra2youli"
LOCK = RUN / ".game_instance.lock"
PY = r"C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
DESIGN = CARD / "designs" / "w65_design.json"
W62 = RUN / "W62_bline_new_criteria"
TOOL_C = W62 / "tool_c_writeaudit.py"
TOOL_B = W62 / "tool_b_stats.py"

# FROZEN spec constants -- mirrored here ONLY to emit cadence metadata.  The
# actual decision table lives exclusively in tool_b_stats.py (unmodified).
SPEC_FROZEN_AT = "2026-11-13T23:25:30+08:00"
CADENCE_S = 0.006                 # 6 ms; SAME for all 4 trips (SPEC §2.1 example t=0.006)
DEFAULT_SAMPLE_SECONDS = 75       # proven by W45/W55b; ~1-2 min per task card
NDJSON_FIELDS = ("t", "frame", "map_name", "stage_idx", "end_of_game",
                 "skip_map_select", "battle_idx", "ui_controls")

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
VK_ESCAPE = 0x1B
VK_MENU = 0x12
VK_RETURN = 0x0D
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
SMTO_ABORTIFHUNG = 0x0002
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

ADDR = {
    "frame": 0x00A8ED84,       # dword: 32 ms game timer (~31.25 counts/s) - NOT FPS
    "scen_ptr": 0x00A8B230,    # dword: ScenarioClass* singleton
}
# ScenarioClass offsets (W59 / LEAD_VERIFY_W59.md; W63 read_counters)
OFF_MAP_NAME = 0x125C          # char[0x104]
OFF_STAGE_IDX = 0x35A0         # WORD
OFF_END_OF_GAME = 0x34AC       # BYTE
OFF_SKIP_MAP_SELECT = 0x34B0   # BYTE
OFF_BATTLE_IDX = 0x34CC        # DWORD


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


def full_manifest(d: Path) -> dict:
    """{rel: {size, sha256}} for EVERY regular file under d (recursive)."""
    rows = {}
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(d).as_posix()
        st = p.stat()
        rows[rel] = {"size": st.st_size, "sha256": sha256_file(p)}
    return rows


def manifest_diff(pre: dict, post: dict) -> dict:
    kp, kk = set(pre), set(post)
    added = sorted(kk - kp)
    removed = sorted(kp - kk)
    modified = sorted(k for k in (kp & kk)
                      if pre[k]["size"] != post[k]["size"]
                      or pre[k]["sha256"] != post[k]["sha256"])
    return {"added": added, "removed": removed, "modified": modified}


class Sink:
    """Append-only event NDJSON (run log).  Distinct from the SPEC data NDJSON."""
    def __init__(self):
        OUT.mkdir(parents=True, exist_ok=True)
        self.path = OUT / "w65_run.ndjson"
        self.fd = self.path.open("a", encoding="utf-8", newline="\n")
        self.n = 0

    def step(self, step_name: str, kind: str = "event", **kw):
        rec = {"kind": kind, "step": step_name, "t_utc": utc_iso(),
               "t_local": local_iso(), "t_monotonic": time.monotonic(), **kw}
        self.fd.write(json.dumps(rec, ensure_ascii=False, sort_keys=True,
                                 default=str, separators=(",", ":")) + "\n")
        self.fd.flush()
        self.n += 1
        try:
            print("[%s] %s %s" % (local_iso(), step_name,
                                  json.dumps(kw, ensure_ascii=True,
                                             default=str)[:280]), flush=True)
        except Exception:
            pass
        return rec

    def close(self):
        self.fd.close()


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
    """Only accept a gamemd.exe that is a child of OUR WMI launcher.  The
    pre-launch guard guarantees 0 gamemd.exe existed, so any pid observed is
    ours; the parent check is belt-and-braces so we never close a user pid."""
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
        sink.step("pid_found", pid=fallback,
                  how="fallback_only_gamemd_present_after_prelaunch_guard_zero")
        return fallback
    raise RuntimeError("no gamemd.exe within %ss" % timeout_s)


def process_alive(pid):
    return any(r["pid"] == pid for r in list_gamemd())


def close_game(pid, hwnd, sink: Sink):
    """Close ONLY the pid this trip launched.  WM_CLOSE first, then taskkill
    /PID <own_pid>, then /F.  Never a blanket taskkill /IM."""
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
    """Full control census (used for menu navigation + screenshots)."""
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


def visible_ctrl_ids(pid):
    """CRITERIA_SPEC §2.1 ui_controls: visible control ids via
    EnumWindows/EnumChildWindows (read-only).  EnumChildWindows is recursive."""
    ids = set()

    def cb(h, _l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value != pid:
            return True
        if u.IsWindowVisible(h):
            ids.add(int(u.GetDlgCtrlID(h)))
        kids = []

        def ccb(kk, _l2):
            kids.append(kk)
            return True
        u.EnumChildWindows(h, ENUM(ccb), 0)
        for kk in kids:
            if u.IsWindowVisible(kk):
                ids.add(int(u.GetDlgCtrlID(kk)))
        return True
    u.EnumWindows(ENUM(cb), 0)
    return sorted(ids)


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
        if wcls(h) == "Yuri's Revenge":
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


def screenshot(sink: Sink, label: str, hwnd=None):
    try:
        from PIL import ImageGrab
        bbox = tuple(rect(hwnd)) if hwnd else None
        img = ImageGrab.grab(bbox=bbox)
        p = OUT / ("screen_%s.png" % label)
        img.save(p)
        sink.step("screenshot", label=label, path=str(p), bbox=bbox,
                  size=[img.width, img.height], sha256=sha256_file(p))
        return p
    except Exception as e:
        sink.step("screenshot", label=label, error=repr(e))
        return None


def desktop_precheck(sink: Sink):
    """W45 STEP0 precheck: EnumWindows >=1 and ImageGrab OK, within 30 s of
    WMI launch.  Failure => STOP, judge environment-blocked."""
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


def read_observables(hproc):
    """One SPEC §2.1 sample.  ALL reads are ReadProcessMemory (read-only).

    Returns dict with exactly the 7 scalar fields + ui_controls (=None here;
    the caller adds the EnumWindows result), or None on any hard read failure.
    """
    out = {}
    b_frame = rpm(hproc, ADDR["frame"], 4)
    if not b_frame:
        return None
    out["frame"] = int.from_bytes(b_frame, "little")
    b_ptr = rpm(hproc, ADDR["scen_ptr"], 4)
    if not b_ptr:
        return None
    scen = int.from_bytes(b_ptr, "little")
    if scen <= 0x10000:
        return None                       # not in a scenario yet
    out["map_name"] = read_cstr(hproc, scen + OFF_MAP_NAME, 260)
    b_stg = rpm(hproc, scen + OFF_STAGE_IDX, 2)
    b_eog = rpm(hproc, scen + OFF_END_OF_GAME, 1)
    b_skip = rpm(hproc, scen + OFF_SKIP_MAP_SELECT, 1)
    b_bat = rpm(hproc, scen + OFF_BATTLE_IDX, 4)
    if not all((b_stg, b_eog, b_skip, b_bat, out["map_name"] is not None)):
        return None
    out["stage_idx"] = int.from_bytes(b_stg, "little")
    out["end_of_game"] = b_eog[0]
    out["skip_map_select"] = b_skip[0]
    out["battle_idx"] = int.from_bytes(b_bat, "little")
    return out


# ------------------------------------------------------------------ lock (per trip)
def lock_text() -> str:
    return LOCK.read_text(encoding="utf-8") if LOCK.is_file() else ""


def lock_claim(owner: str, purpose: str):
    LOCK.write_text("run_id=NEXT_RE_20261112_R02\nowner=%s\ntime=%s\npurpose=%s\n"
                    % (owner, local_iso(), purpose), encoding="utf-8")


def lock_wait_and_claim(tag: str, sink: Sink, timeout_s=300):
    """Before EACH trip: owner must be lead AND no live gamemd.exe.  Wait
    otherwise.  Then claim owner=w65."""
    t0 = time.monotonic()
    while True:
        txt = lock_text()
        live = list_gamemd()
        owner_ok = ("owner=lead" in txt)
        sink.step("lock_before", tag=tag, content=txt,
                  owner_ok=owner_ok, live_gamemd=live)
        if owner_ok and not live:
            break
        if time.monotonic() - t0 > timeout_s:
            raise RuntimeError("lock wait timeout: owner_ok=%s live=%r text=%r"
                               % (owner_ok, live, txt))
        sink.step("lock_waiting", tag=tag, owner_ok=owner_ok, live_gamemd=live)
        time.sleep(3.0)
    lock_claim("w65", "W65 B-line new-criteria live collect TRIP=%s "
               "(single instance; restores owner=lead in finally)" % tag)
    sink.step("lock_claimed", tag=tag, content=lock_text())


def lock_release(tag: str, sink: Sink, ok: bool, status: str):
    """Every trip end (success OR failure) writes back owner=lead + status."""
    txt = ("run_id=NEXT_RE_20261112_R02\nowner=lead\ntime=%s\n"
           "purpose=W65 trip %s FINISHED (ok=%s, %s): self-launched gamemd "
           "closed, residual=0; restored owner=lead.\n"
           % (local_iso(), tag, str(ok).lower(), status))
    LOCK.write_text(txt, encoding="utf-8")
    sink.step("lock_released", tag=tag, content=txt)


# ------------------------------------------------------------------ robocopy / restore
def robocopy(src: Path, dst: Path, sink: Sink, label: str):
    args = ["robocopy", str(src), str(dst), "/E", "/COPY:DAT", "/DCOPY:DAT",
            "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NJS", "/NP"]
    rc, so, se = run_cmd(args, ROOT, sink, label, timeout=900)
    ok = 0 <= rc < 8
    sink.step("robocopy", label=label, src=str(src), dst=str(dst), rc=rc, ok=ok)
    if not ok:
        raise RuntimeError("robocopy failed rc=%d %s" % (rc, se[-300:]))
    return ok


def copy_root_pristine(sandbox: Path, dest: Path, sink: Sink, label: str):
    """Byte copy of EVERY root-level regular file (the game writes to root)."""
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted(sandbox.iterdir()):
        if p.is_file():
            q = dest / p.name
            shutil.copyfile(p, q)
            rows.append({"name": p.name, "size": p.stat().st_size,
                         "sha256": sha256_file(p)})
    sink.step("pristine_captured", label=label, n=len(rows),
              total_bytes=sum(r["size"] for r in rows))
    (OUT / ("pristine_manifest_%s.json" % label)).write_text(
        json.dumps(rows, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    return rows


def restore_and_prove(sandbox: Path, pre: dict, pristine: Path, sink: Sink,
                      label: str) -> dict:
    """Byte-exact restore of the trip sandbox to its PRE-launch state, then
    RE-COMPUTE the full-tree hash and prove equality (not an assertion)."""
    post = full_manifest(sandbox)
    diff = manifest_diff(pre, post)
    actions = []
    for rel in diff["modified"] + diff["removed"]:
        dst = sandbox / rel
        src = None
        if "/" not in rel and (pristine / rel).is_file():
            src = pristine / rel
        elif (BASE / rel).is_file():
            src = BASE / rel
        if src is not None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            actions.append({"rel": rel, "action": "restored_from",
                            "src": str(src)})
        else:
            actions.append({"rel": rel, "action": "NO_PRISTINE_SOURCE"})
    for rel in diff["added"]:
        p = sandbox / rel
        try:
            p.unlink()
            actions.append({"rel": rel, "action": "deleted_drop"})
        except OSError as e:
            actions.append({"rel": rel, "action": "delete_failed",
                            "error": repr(e)})
    post2 = full_manifest(sandbox)
    diff2 = manifest_diff(pre, post2)
    identical = not (diff2["added"] or diff2["removed"] or diff2["modified"])
    proof = {"label": label, "pre_file_count": len(pre),
             "post_file_count": len(post),
             "diff_game_run": diff, "restore_actions": actions,
             "post_restore_file_count": len(post2),
             "diff_after_restore": diff2,
             "IDENTICAL_TREE": identical}
    sink.step("restore_proof", **{k: v for k, v in proof.items()
                                  if k != "restore_actions"})
    sink.step("restore_actions_detail", label=label, actions=actions)
    (OUT / ("restore_proof_%s.json" % label)).write_text(
        json.dumps(proof, indent=1, ensure_ascii=False, sort_keys=True,
                   default=str), encoding="utf-8")
    return proof


# ------------------------------------------------------------------ PREP (offline, no lock)
def phase_prep(sink: Sink):
    sink.step("phase_prep_start", real_dir=str(REAL), base=str(BASE),
              v15=str(V15), frozen_spec_at=SPEC_FROZEN_AT)
    # (0) REAL-dir PRE manifest -- ra2youli is READ-ONLY source + hash target.
    real_pre = full_manifest(REAL)
    (OUT / "real_pre.json").write_text(
        json.dumps({"file_count": len(real_pre),
                    "total_bytes": sum(v["size"] for v in real_pre.values()),
                    "anchors": {k: real_pre.get(k) for k in
                                ("gamemd.exe", "ddraw.dll", "RA2MD.INI",
                                 "BATTLEMD.INI", "ra2md.mix")},
                    "rows": real_pre},
                   indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    sink.step("real_pre_manifest", file_count=len(real_pre),
              total_bytes=sum(v["size"] for v in real_pre.values()))

    # (1) ONE common base for BOTH arms: byte copy of the real dir, never
    #     writing back to it.
    if BASE.exists():
        shutil.rmtree(BASE, ignore_errors=True)
    robocopy(REAL, BASE, sink, "prep_robocopy_base")
    base_pre = full_manifest(BASE)
    (OUT / "sandbox_base_pre.json").write_text(
        json.dumps({"file_count": len(base_pre),
                    "total_bytes": sum(v["size"] for v in base_pre.values()),
                    "rows": base_pre},
                   indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    sink.step("base_pre_manifest", file_count=len(base_pre),
              total_bytes=sum(v["size"] for v in base_pre.values()))

    # (2) W45 C2: uniformly handle the pre-existing v0.3 package in the
    #     sandbox copy -- uninstall it with the v15 toolchain (W63 did this,
    #     exit 0).  Both arms then start from the SAME clean state.
    rc_u, so_u, se_u = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "uninstall",
         "--game", str(BASE), "--json"], V15, sink, "prep_uninstall_v03")
    rc_v, so_v, se_v = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "verify",
         "--game", str(BASE), "--json"], V15, sink,
        "prep_verify_after_uninstall")
    sink.step("prep_clean_base", uninstall_rc=rc_u, verify_rc=rc_v,
              verify_json=so_v[-1200:], uninstall_json=so_u[-1200:])

    # (3) Build ONE v15 package (append route: BATTLEMD98.INI, NO inplace
    #     rewrite of [SOV1]) from a FIXED design, reused for B1/B2.
    if PKG.exists():
        shutil.rmtree(PKG, ignore_errors=True)
    PKG.mkdir(parents=True, exist_ok=True)
    rc_b, so_b, se_b = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "build",
         "--design", str(DESIGN), "--out", str(PKG)], V15, sink,
        "prep_build_v15")
    pkg_rows = []
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            pkg_rows.append({"rel": p.relative_to(PKG).as_posix(),
                             "size": p.stat().st_size,
                             "sha256": sha256_file(p)})
    has_98 = (PKG_INNER / "BATTLEMD98.INI").is_file()
    has_inplace = (PKG_INNER / "BATTLEMD.INI").is_file()
    sink.step("v15_package", build_rc=rc_b, files=pkg_rows,
              package_inner=str(PKG_INNER),
              inner_has_battlemd98=has_98, inner_has_battlemd_ini=has_inplace,
              route="APPEND (no [SOV1] rewrite; both arms load the SAME "
                    "official Soviet mission -> comparable)",
              package_digest=hashlib.sha256(
                  "\n".join(sorted("%s %s" % (r["rel"], r["sha256"])
                                  for r in pkg_rows)).encode()).hexdigest())
    if rc_b != 0 or not PKG_INNER.is_dir() or not has_98 or has_inplace:
        raise RuntimeError("v15 append-route build failed or wrong shape: "
                           "rc=%d inner=%s has98=%s hasInplace=%s"
                           % (rc_b, PKG_INNER, has_98, has_inplace))
    (OUT / "cadence.json").write_text(json.dumps({
        "cadence_s": CADENCE_S,
        "sample_seconds_default": DEFAULT_SAMPLE_SECONDS,
        "same_cadence_all_four_trips": True,
        "spec_frozen_at": SPEC_FROZEN_AT,
        "note": "6 ms target cadence, identical loop for A1/A2/B1/B2. "
                "t in each NDJSON row is the ACTUAL monotonic elapsed time; "
                "tool_b_stats.py never uses t (only frame deltas).",
    }, indent=2), encoding="utf-8")
    sink.step("phase_prep_end", ok=True)


# ------------------------------------------------------------------ TRIP
def phase_trip(tag: str, sample_seconds: int, sink: Sink) -> int:
    arm = tag[0]
    sandbox = CARD / ("sandbox_" + tag)
    pristine = OUT / ("pristine_" + tag)
    rec = {"arm": arm, "tag": tag, "sandbox": str(sandbox),
           "cadence_s": CADENCE_S, "sample_seconds": sample_seconds,
           "errors": [], "phase_reached": False, "ndjson": str(OUT / (tag + ".ndjson"))}
    own_pid = None
    hwnd = None
    hproc = None
    claimed = False
    ok = False
    status = "not_started"
    try:
        # ---- LOCK: per trip, before ANY sandbox/game work -----------------
        lock_wait_and_claim(tag, sink)
        claimed = True

        # ---- fresh sandbox from the COMMON base --------------------------
        if sandbox.exists():
            shutil.rmtree(sandbox, ignore_errors=True)
        robocopy(BASE, sandbox, sink, tag + "_robocopy_run")

        # ---- B arm ONLY: install the v15 append package ------------------
        if arm == "B":
            rci, so_i, se_i = run_cmd(
                [PY, "-B", "-X", "utf8", "-m", "ra2forge", "install",
                 "--package", str(PKG_INNER), "--game", str(sandbox)],
                V15, sink, tag + "_install")
            if rci == 1:
                rci, so_i, se_i = run_cmd(
                    [PY, "-B", "-X", "utf8", "-m", "ra2forge", "install",
                     "--package", str(PKG_INNER), "--game", str(sandbox),
                     "--allow-content-conflict"], V15, sink,
                    tag + "_install_allow")
            rec["install_rc"] = rci
            rec["install_stdout"] = so_i[-1200:]
            if rci != 0:
                raise RuntimeError("v15 install rc=%d: %s" % (rci, se_i[-400:]))
        rcv, so_v, se_v = run_cmd(
            [PY, "-B", "-X", "utf8", "-m", "ra2forge", "verify",
             "--game", str(sandbox), "--json"], V15, sink, tag + "_verify_pre")
        rec["verify_pre_rc"] = rcv
        try:
            rec["verify_pre_json"] = json.loads(so_v)
        except Exception:
            rec["verify_pre_json"] = {"parse_error": so_v[-600:]}

        # ---- PRE-launch full-tree manifest + byte copies -----------------
        pre_manifest = full_manifest(sandbox)
        copy_root_pristine(sandbox, pristine, sink, tag)
        rec["pre_file_count"] = len(pre_manifest)
        rec["pre_total_bytes"] = sum(v["size"] for v in pre_manifest.values())
        sink.step("pre_launch_manifest", tag=tag,
                  file_count=len(pre_manifest),
                  total_bytes=rec["pre_total_bytes"])

        # ---- pre-launch guard: ZERO gamemd.exe before we start -----------
        pre = list_gamemd()
        sink.step("pre_launch_guard", tag=tag, gamemd_processes=pre, n=len(pre))
        if pre:
            raise RuntimeError("gamemd residual before launch: %r" % pre)

        # ---- launch + STEP0 desktop precheck -----------------------------
        launcher = launch_game(sandbox, sink)
        desktop_precheck(sink)
        own_pid = wait_for_pid(launcher, sink)
        rec["own_pid"] = own_pid
        hproc = open_proc(own_pid)
        sink.step("proc_opened", tag=tag, pid=own_pid, hproc=bool(hproc))
        if not hproc:
            raise RuntimeError("OpenProcess(PROCESS_VM_READ) failed")

        # ---- menu navigation (W45/W55b/W63 identical entry) -------------
        def wait_text(text, timeout_s, retry_click=None):
            t = time.monotonic()
            while time.monotonic() - t < timeout_s:
                cs = controls(own_pid)
                hits = [c for c in cs
                        if text.lower() in (c.get("text") or "").lower()]
                if hits:
                    sink.step("wait_text_found", tag=tag, text=text,
                              elapsed_s=round(time.monotonic() - t, 2),
                              hits=[(c["text"], c["cls"], c["visible"])
                                    for c in hits[:6]])
                    return hits
                if retry_click and (time.monotonic() - t) > 3.0:
                    click(own_pid, retry_click, sink, wait_s=0.6,
                          label=tag + "_retry_" + retry_click)
                    time.sleep(1.0)
                time.sleep(0.5)
            sink.step("wait_text_timeout", tag=tag, text=text,
                      controls=normalized(controls(own_pid))[:40])
            return None

        t0 = time.monotonic()
        while time.monotonic() - t0 < 90:
            hwnd = game_hwnd(own_pid)
            if hwnd and find_btn(own_pid, "GUI:SinglePlayer"):
                break
            time.sleep(0.5)
        if not hwnd or not find_btn(own_pid, "GUI:SinglePlayer"):
            raise RuntimeError("main menu not reached (GUI:SinglePlayer absent)")
        sink.step("main_menu_ready", tag=tag, hwnd=hwnd, rect=rect(hwnd),
                  elapsed_s=round(time.monotonic() - t0, 2))
        force_foreground(hwnd)
        click(own_pid, "GUI:SinglePlayer", sink, wait_s=1.2,
              label=tag + "_click_SinglePlayer")
        if not wait_text("GUI:NewCampaign", 25, retry_click="GUI:SinglePlayer"):
            raise RuntimeError("single-player submenu not reached "
                               "(GUI:NewCampaign absent)")
        click(own_pid, "GUI:NewCampaign", sink, wait_s=2.0,
              label=tag + "_click_NewCampaign")
        if not wait_text("GUI:CampaignMenu", 25, retry_click="GUI:NewCampaign"):
            raise RuntimeError("campaign menu not reached "
                               "(GUI:CampaignMenu absent)")
        sink.step("campaign_menu_controls", tag=tag,
                  controls=normalized(controls(own_pid))[:40])
        screenshot(sink, tag + "_campaign_menu", hwnd)
        # Soviet badge: SAME screen coords as W55b/W63 (210, 285).
        real_mouse_click(sink, tag + "_click_SOVIET_badge", 210, 285, wait_s=3.0)

        # ---- into first mission -----------------------------------------
        sink.step("after_badge_counters", tag=tag,
                  counters=read_observables(hproc))
        force_foreground(hwnd)
        for _ in range(2):
            key(VK_RETURN, sink, tag + "_skip_movie_RETURN")
        t1 = time.monotonic()
        ingame = False
        cnt = None
        last_dump = -99.0
        while time.monotonic() - t1 < 120:
            for btn in ("GUI:Play", "GUI:StartGame", "GUI:Continue"):
                if find_btn(own_pid, btn):
                    click(own_pid, btn, sink, wait_s=1.0,
                          label=tag + "_click_" + btn)
            cnt = read_observables(hproc)
            if cnt and (cnt.get("frame") or 0) > 30 and cnt.get("map_name"):
                ingame = True
                break
            if int(time.monotonic() - t1) in (6, 14, 24):
                force_foreground(hwnd)
                key(VK_RETURN, sink, tag + "_retry_RETURN")
            if (time.monotonic() - t1) - last_dump >= 15:
                last_dump = time.monotonic() - t1
                sink.step("waiting_ingame_controls", tag=tag,
                          elapsed_s=round(last_dump, 1), counters=cnt,
                          controls=normalized(controls(own_pid))[:60])
            time.sleep(1.0)
        rec["ingame"] = ingame
        rec["counters_at_ingame"] = cnt
        if not ingame:
            raise RuntimeError("in-game phase not reached (frame>30 OR "
                               "map_name missing): %r" % (cnt,))
        rec["phase_reached"] = True
        force_foreground(hwnd)
        screenshot(sink, tag + "_ingame", hwnd)

        # ---- SPEC §2.1 NDJSON sampling (6 ms, SAME for all 4 trips) ------
        ndpath = OUT / (tag + ".ndjson")
        rows_written = 0
        read_fail = 0
        consec_fail = 0
        t2 = time.monotonic()
        with ndpath.open("w", encoding="utf-8", newline="\n") as fd:
            while time.monotonic() - t2 < sample_seconds:
                t_elapsed = round(time.monotonic() - t2, 6)
                obs = read_observables(hproc)
                ids = visible_ctrl_ids(own_pid)
                if obs is None:
                    read_fail += 1
                    consec_fail += 1
                    if consec_fail >= 50:
                        raise RuntimeError("50 consecutive RPM read failures; "
                                           "game likely exited mid-sample")
                else:
                    consec_fail = 0
                    row = {"t": t_elapsed,
                           "frame": obs["frame"],
                           "map_name": obs["map_name"],
                           "stage_idx": obs["stage_idx"],
                           "end_of_game": obs["end_of_game"],
                           "skip_map_select": obs["skip_map_select"],
                           "battle_idx": obs["battle_idx"],
                           "ui_controls": ids}
                    fd.write(json.dumps(row, ensure_ascii=False,
                                        sort_keys=True, separators=(",", ":")) + "\n")
                    rows_written += 1
                time.sleep(CADENCE_S)
        rec["rows_written"] = rows_written
        rec["dframe_points"] = max(0, rows_written - 1)
        rec["read_fail"] = read_fail
        rec["ndjson_sha256"] = sha256_file(ndpath)
        rec["ndjson_bytes"] = ndpath.stat().st_size
        sink.step("ndjson_sampling", tag=tag, rows_written=rows_written,
                  dframe_points=rec["dframe_points"], read_fail=read_fail,
                  cadence_s=CADENCE_S, sample_seconds=sample_seconds,
                  sha256=rec["ndjson_sha256"], bytes=rec["ndjson_bytes"])
        if rows_written < 31:
            raise RuntimeError("insufficient dframe points: rows=%d (<31)"
                               % rows_written)
        rec["counters_after_sampling"] = read_observables(hproc)
        ok = True
        status = ("ok=True phase_reached=True rows=%d dframe_points=%d "
                  "read_fail=%d" % (rows_written, rec["dframe_points"], read_fail))
    except Exception as e:
        rec["errors"].append("run: %r" % (e,))
        sink.step("run_error", tag=tag, error=repr(e))
        try:
            screenshot(sink, tag + "_on_error", hwnd)
        except Exception:
            pass
        status = "ok=False error=%r" % (e,)
    finally:
        # ---- HARD finally: close OWN pid -> residual 0 -> restore -> prove
        try:
            steps = close_game(own_pid, hwnd, sink) if own_pid else ["no_pid"]
            rec["close_steps"] = steps
        except Exception as e:
            rec["errors"].append("close: %r" % (e,))
        rec["residual_after_close"] = list_gamemd()
        rec["residual_own_pid"] = [r for r in rec["residual_after_close"]
                                   if r["pid"] == own_pid]
        try:
            if "pre_manifest" in locals():
                rec["restore_proof"] = restore_and_prove(
                    sandbox, pre_manifest, pristine, sink, tag)
            else:
                rec["restore_proof"] = {"IDENTICAL_TREE": None,
                                        "note": "no PRE manifest (failed early)"}
        except Exception as e:
            rec["errors"].append("restore: %r" % (e,))
            rec["restore_proof"] = {"IDENTICAL_TREE": False, "error": repr(e)}
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
        ok = bool(ok and not rec["errors"]
                  and not rec["residual_own_pid"]
                  and rec.get("restore_proof", {}).get("IDENTICAL_TREE") is True)
        rec["ok"] = ok
        rec["status"] = status
        sink.step("meta_end", kind="meta", tag=tag, arm=arm, ok=ok,
                  status=status, errors=rec["errors"],
                  residual=rec["residual_after_close"],
                  identical_tree=rec.get("restore_proof", {}).get("IDENTICAL_TREE"))
        # ---- release lock REGARDLESS of outcome --------------------------
        if claimed:
            try:
                lock_release(tag, sink, ok, status)
            except Exception as e:
                sink.step("lock_release_error", tag=tag, error=repr(e))
    (OUT / ("%s_result.json" % tag)).write_text(
        json.dumps(rec, ensure_ascii=False, indent=1, sort_keys=True,
                   default=str), encoding="utf-8")
    # remove the (now restored) trip sandbox to reclaim disk; evidence stays
    try:
        if sandbox.exists():
            shutil.rmtree(sandbox, ignore_errors=True)
            sink.step("trip_sandbox_removed", tag=tag, path=str(sandbox))
    except Exception as e:
        sink.step("trip_sandbox_remove_error", tag=tag, error=repr(e))
    return 0 if ok else 1


# ------------------------------------------------------------------ C AUDIT (offline, no lock/game)
def phase_audit(sink: Sink) -> int:
    """Run tool_c_writeaudit.py --audit on REAL snapshots of the B-arm install
    process (same v15 install/uninstall commands, same BASE state), on a
    dedicated inert sandbox.  No game launched, no lock taken."""
    sb = CARD / "sandbox_audit"
    if sb.exists():
        shutil.rmtree(sb, ignore_errors=True)
    robocopy(BASE, sb, sink, "audit_robocopy")
    pre = full_manifest(sb)
    rci, so_i, se_i = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "install",
         "--package", str(PKG_INNER), "--game", str(sb)],
        V15, sink, "audit_install")
    post = full_manifest(sb)
    rcu, so_u, se_u = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "uninstall",
         "--game", str(sb), "--json"], V15, sink, "audit_uninstall")
    uninst = full_manifest(sb)

    # Declared write set D (CRITERIA_SPEC §1.2), built UP FRONT from PACKAGE
    # CONTENTS + fixed engine whitelist -- NOT from the observed write set.
    members = []
    for cand in ("BATTLEMD.INI", "BATTLEMD98.INI"):
        if (PKG_INNER / cand).is_file():
            members.append(cand)
            break
    for cand in ("MAPSELMD.INI", "ra2md.csf"):
        if (PKG_INNER / cand).is_file():
            members.append(cand)
    members += sorted(p.name for p in PKG_INNER.glob("*.MAP") if p.is_file())
    if (PKG_INNER / "expandmd98.mix").is_file():
        members.append("expandmd98.mix")
    D = set(members) | {"ra2forge_install.json", "ra2forge_install.json.seal"}
    for n in members:
        if n in pre:
            D.add(n + ".ra2forge.bak")
    declared = {"D": sorted(D), "members": members,
                "inplace": False, "declared_rewrite": [],
                "engine_derived": ["ra2forge_install.json",
                                   "ra2forge_install.json.seal"]}
    (OUT / "c_audit_before.json").write_text(
        json.dumps(pre, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (OUT / "c_audit_after.json").write_text(
        json.dumps(post, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (OUT / "c_audit_uninst.json").write_text(
        json.dumps(uninst, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    (OUT / "c_audit_declared.json").write_text(
        json.dumps(declared, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    sink.step("c_audit_snapshots", install_rc=rci, uninstall_rc=rcu,
              pre=len(pre), post=len(post), uninst=len(uninst),
              declared=sorted(D), members=members)

    rc, so, se = run_cmd(
        [PY, "-B", "-X", "utf8", str(TOOL_C), "--audit",
         "--before", str(OUT / "c_audit_before.json"),
         "--after", str(OUT / "c_audit_after.json"),
         "--uninst", str(OUT / "c_audit_uninst.json"),
         "--declared", str(OUT / "c_audit_declared.json"),
         "--out", str(OUT / "c_audit_B_arm.json")],
        CARD, sink, "tool_c_writeaudit_audit")
    sink.step("c_audit_tool_exit", rc=rc, out=so[-1500:], err=se[-800:])
    try:
        rep = json.loads((OUT / "c_audit_B_arm.json").read_text(encoding="utf-8"))
        sink.step("c_audit_verdict", verdict=rep.get("verdict"),
                  out_of_scope=rep.get("out_of_scope_writes"),
                  protected_all_equal=rep.get("protected_hash_check", {}).get("all_equal"),
                  failed_checks=rep.get("failed_checks"))
    except Exception as e:
        sink.step("c_audit_report_parse_error", error=repr(e))
    shutil.rmtree(sb, ignore_errors=True)
    return 0 if rc == 0 else 1


# ------------------------------------------------------------------ FINALIZE (real-dir proof)
def phase_finalize(sink: Sink) -> int:
    real_post = full_manifest(REAL)
    pre_raw = (OUT / "real_pre.json").read_text(encoding="utf-8")
    pre = json.loads(pre_raw)["rows"]
    d = manifest_diff(pre, real_post)
    identical = not (d["added"] or d["removed"] or d["modified"])
    anchors = ("gamemd.exe", "ddraw.dll", "RA2MD.INI", "BATTLEMD.INI",
               "ra2md.mix")
    anchor_rows = [{"name": n,
                    "pre_sha256": pre.get(n, {}).get("sha256"),
                    "post_sha256": real_post.get(n, {}).get("sha256"),
                    "equal": pre.get(n, {}).get("sha256") ==
                             real_post.get(n, {}).get("sha256")} for n in anchors]
    proof = {
        "card": "W65_bline_live_collect",
        "IDENTICAL_TREE": identical,
        "real_dir": str(REAL),
        "pre_file_count": len(pre), "post_file_count": len(real_post),
        "pre_total_bytes": sum(v["size"] for v in pre.values()),
        "post_total_bytes": sum(v["size"] for v in real_post.values()),
        "added": d["added"], "removed": d["removed"], "modified": d["modified"],
        "anchors": anchor_rows,
        "all_anchors_equal": all(r["equal"] for r in anchor_rows),
        "method": "full-tree SHA-256 of every regular file under ra2youli, "
                  "PRE (before any sandbox/launch) vs POST (after all trips). "
                  "ra2youli was ONLY a robocopy source and hash target.",
        "generated_utc": utc_iso(),
        "gamemd_residual": list_gamemd(),
        "lock_content": lock_text(),
    }
    (OUT / "REAL_DIR_PROOF.json").write_text(
        json.dumps(proof, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    txt = ["REAL_DIR_PROOF.txt -- W65 B-line live collect",
           "IDENTICAL_TREE=%s" % identical,
           "real_dir=%s" % REAL,
           "PRE  file_count=%d total_bytes=%d" %
           (len(pre), sum(v["size"] for v in pre.values())),
           "POST file_count=%d total_bytes=%d" %
           (len(real_post), sum(v["size"] for v in real_post.values())),
           "added=%d removed=%d modified=%d" %
           (len(d["added"]), len(d["removed"]), len(d["modified"])),
           "all_anchors_equal=%s" % all(r["equal"] for r in anchor_rows),
           ""]
    for r in anchor_rows:
        txt.append("%-20s pre=%s post=%s equal=%s" %
                   (r["name"], r["pre_sha256"], r["post_sha256"], r["equal"]))
    txt += ["", "gamemd residual=%r" % (list_gamemd(),),
            "lock=%r" % (lock_text(),),
            "", "[本次实测] full-tree hash equality re-computed, not asserted."]
    (CARD / "REAL_DIR_PROOF.txt").write_text("\n".join(txt) + "\n",
                                             encoding="utf-8")
    sink.step("finalize_real_dir_post", IDENTICAL_TREE=identical,
              added=len(d["added"]), removed=len(d["removed"]),
              modified=len(d["modified"]), gamemd_residual=list_gamemd(),
              lock=lock_text())
    return 0 if identical else 1


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="W65 live collector")
    ap.add_argument("--phase", choices=("prep", "trip", "audit", "finalize"),
                    required=True)
    ap.add_argument("--tag", choices=("A1", "A2", "B1", "B2"))
    ap.add_argument("--sample-seconds", type=int, default=DEFAULT_SAMPLE_SECONDS)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sink = Sink()
    try:
        if a.phase == "prep":
            phase_prep(sink)
            return 0
        if a.phase == "trip":
            if not a.tag:
                print("ERROR --phase trip needs --tag", file=sys.stderr)
                return 2
            return phase_trip(a.tag, a.sample_seconds, sink)
        if a.phase == "audit":
            return phase_audit(sink)
        if a.phase == "finalize":
            return phase_finalize(sink)
        return 2
    except Exception as e:
        sink.step("FATAL", phase=a.phase, tag=a.tag, error=repr(e))
        # last-resort lock safety: never leave owner=w65 behind
        try:
            if "owner=w65" in lock_text():
                lock_claim("lead", "W65 FATAL fallback: restored owner=lead")
                sink.step("fatal_lock_restored", content=lock_text())
        except Exception as ee:
            sink.step("fatal_lock_restore_error", error=repr(ee))
        return 2
    finally:
        sink.close()


if __name__ == "__main__":
    raise SystemExit(main())

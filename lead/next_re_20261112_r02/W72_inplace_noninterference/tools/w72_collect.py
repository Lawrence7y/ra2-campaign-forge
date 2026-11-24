#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W72 / inplace non-interference -- real-machine live collector.

PROVENANCE
----------
This file is a **copy** of W69_bline_v2_collect/tools/w69_collect.py
(itself a copy of W65/w45 primitives) with:

  * every output path redirected into W72_inplace_noninterference/ (never
    imports another card's script -- HANDOFF red line 5);
  * OWNER = "w72" (w72 -> lead, lock per trip);
  * PREP builds a v15 **battlemd:inplace** package (NOT append): the bundled
    official BATTLEMD.INI is rewritten in [SOV1] to Scenario=SOV01UMD.MAP,
    the OFFICIAL Soviet first mission.  Byte-exact diff is ASSERTED == 1 line;
  * PREP uniformly uninstalls the pre-existing v0.3 package and removes the
    unowned orphan BATTLEMD.INI.ra2forge.bak from the SANDBOX COPY ONLY
    (W63 step 7b; inplace_preflight exit 34 otherwise).  REAL is NEVER written;
  * B-arm install passes --feature-set (inplace plan) and asserts .bak in
    place + manifest original_sha256 + post_install_sha256;
  * EVERY trip asserts Scen+0x125C == "SOV01UMD.MAP" at ingame AND in EVERY
    NDJSON row (both arms must play the SAME official map -- success premise);
  * AUDIT constructs the declared write set with inplace=True /
    declared_rewrite=["BATTLEMD.INI"] and runs the card-local FROZEN
    tool_c_writeaudit.py --audit (DECLARED-REWRITE, not out-of-scope);
  * COMPARE merges A1+A2 / B1+B2 and runs the card-local FROZEN W68b
    tool_b_stats_v2.py --compare (byte-identical, sha-verified in
    work/criteria_frozen/SHA256_PROOF.json);
  * FINALIZE proves ra2youli PRE/POST full-tree IDENTICAL_TREE=True.

DISCIPLINE (W72 red lines)
  * ReadProcessMemory only (PROCESS_VM_READ|PROCESS_QUERY_INFORMATION).
    NO write-memory / breakpoint / suspend-thread / injection / exe change.
  * .game_instance.lock: read before EACH trip; wait if owner != lead or any
    live gamemd.exe; claim owner=w72; release owner=lead + status in FINALLY.
    NEVER hold the lock across trips.
  * ra2youli is a READ-ONLY robocopy source + hash target. Never written.
  * Only gamemd.exe pids launched by THIS trip are closed; residual=0 proven.
  * Sandbox writable configs: byte copies + hashes before launch; byte-exact
    restore after; full-tree hash equality RE-COMPUTED as self-proof.
  * Only writes inside W72_inplace_noninterference/; git untouched.

Usage:
  python w72_collect.py --phase prep
  python w72_collect.py --phase trip --tag A1|A2|B1|B2 [--sample-seconds 75]
  python w72_collect.py --phase audit
  python w72_collect.py --phase compare
  python w72_collect.py --phase finalize
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
CARD = RUN / "W72_inplace_noninterference"
OUT = CARD / "out"
TOOLS = CARD / "tools"
WORK = CARD / "work"
FROZEN = WORK / "criteria_frozen"
BASE = CARD / "sandbox_base"          # common clean sandbox start for BOTH arms
PKG = OUT / "pkg"                      # v15 build output dir
PKG_INNER = PKG / "W72Inplace"         # inner package dir (campaign name)
V15 = RUN / "W60_battlemd_inplace" / "ra2forge_patched_v15"
OFFICIAL_BATTLEMD = V15 / "ra2forge" / "data" / "BATTLEMD.OFFICIAL.INI"
REAL = ROOT / "ra2youli"
LOCK = RUN / ".game_instance.lock"
PY = r"C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
DESIGN = CARD / "designs" / "w72_design.json"
FEATURE_SET = CARD / "designs" / "w72_feature_set.json"
TOOL_C = FROZEN / "tool_c_writeaudit.py"
TOOL_B = FROZEN / "tool_b_stats_v2.py"
REPORT_TOOL = TOOLS / "w72_report.py"

OWNER = "w72"
EXPECTED_MAP = "SOV01UMD.MAP"
OFFICIAL_SCENARIO = "SOV01umd.MAP"
REWRITE_SCENARIO = "SOV01UMD.MAP"

SPEC_FROZEN_AT = "2026-11-14T00:33:05.3748807+08:00"
CADENCE_S = 0.006                 # 6 ms; SAME for all 4 trips
DEFAULT_SAMPLE_SECONDS = 75       # W45/W55b/W69 proven; ~1-2 min per trip
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
    return {
        "added": sorted(kk - kp),
        "removed": sorted(kp - kk),
        "modified": sorted(k for k in (kp & kk)
                           if pre[k]["size"] != post[k]["size"]
                           or pre[k]["sha256"] != post[k]["sha256"]),
    }


class Sink:
    """Append-only event NDJSON (run log). Distinct from the SPEC data NDJSON."""
    def __init__(self):
        OUT.mkdir(parents=True, exist_ok=True)
        self.path = OUT / "w72_run.ndjson"
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
    """Close ONLY the pid this trip launched. WM_CLOSE -> taskkill /PID <own>
    -> /F. Never a blanket taskkill /IM."""
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


def visible_ctrl_ids(pid):
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
    """W45 STEP0 precheck: EnumWindows >=1 and ImageGrab OK."""
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
    """One SPEC §2.1 sample. ALL reads ReadProcessMemory (read-only)."""
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
        return None
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
    lock_claim(OWNER, "W72 inplace non-interference live collect TRIP=%s "
               "(single instance; restores owner=lead in finally)" % tag)
    sink.step("lock_claimed", tag=tag, content=lock_text())


def lock_release(tag: str, sink: Sink, ok: bool, status: str):
    txt = ("run_id=NEXT_RE_20261112_R02\nowner=lead\ntime=%s\n"
           "purpose=W72 trip %s FINISHED (ok=%s, %s): self-launched gamemd "
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


# ------------------------------------------------------------------ INI diff helper
def ini_diff_lines(before: bytes, after: bytes) -> list[dict]:
    la = re.split(b"(?<=\n)", before)
    lb = re.split(b"(?<=\n)", after)
    out = []
    for i in range(max(len(la), len(lb))):
        x = la[i] if i < len(la) else b"<absent>"
        y = lb[i] if i < len(lb) else b"<absent>"
        if x != y:
            out.append({"line": i + 1,
                        "before": x.decode("latin-1").rstrip("\r\n"),
                        "after": y.decode("latin-1").rstrip("\r\n")})
    return out


# ------------------------------------------------------------------ PREP (offline, no lock)
def phase_prep(sink: Sink):
    sink.step("phase_prep_start", real_dir=str(REAL), base=str(BASE),
              v15=str(V15), design=str(DESIGN), feature_set=str(FEATURE_SET),
              frozen_spec_at=SPEC_FROZEN_AT,
              note="OFFLINE: no lock claimed, no gamemd.exe launched")
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

    # (1) ONE common base for BOTH arms: byte copy of the real dir.
    if BASE.exists():
        shutil.rmtree(BASE, ignore_errors=True)
    robocopy(REAL, BASE, sink, "prep_robocopy_base")

    # (2) Uniformly handle the pre-existing v0.3 package (W63/W69 flow).
    rc_u, so_u, se_u = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "uninstall",
         "--game", str(BASE), "--json"], V15, sink, "prep_uninstall_v03")
    rc_v, so_v, se_v = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "verify",
         "--game", str(BASE), "--json"], V15, sink,
        "prep_verify_after_uninstall")
    sink.step("prep_clean_base", uninstall_rc=rc_u, verify_rc=rc_v,
              verify_json=so_v[-1200:], uninstall_json=so_u[-1200:])
    if rc_u != 0:
        raise RuntimeError("v0.3 uninstall rc=%d: %s" % (rc_u, se_u[-400:]))

    # (3) Remove the UNOWNED orphan BATTLEMD.INI.ra2forge.bak from the
    #     SANDBOX COPY ONLY (W63 step 7b -> inplace_preflight exit 34).
    #     REAL is NEVER touched; a byte copy is kept in work/ for the record.
    orphan = BASE / "BATTLEMD.INI.ra2forge.bak"
    orphan_info = {"present_before": orphan.is_file(),
                   "sha256": sha256_file(orphan) if orphan.is_file() else None,
                   "size": orphan.stat().st_size if orphan.is_file() else None,
                   "real_dir_untouched": True}
    if orphan.is_file():
        shutil.copyfile(orphan, WORK / "orphan_bak_backup" /
                        "BATTLEMD.INI.ra2forge.bak")
        orphan.unlink()
    orphan_info["removed_from_sandbox_only"] = not orphan.exists()
    sink.step("prep_orphan_bak", **orphan_info)
    (OUT / "orphan_bak_handling.json").write_text(
        json.dumps(orphan_info, indent=1, ensure_ascii=False), encoding="utf-8")

    # (4) The inplace target MUST be the official 2733 B baseline.
    official = OFFICIAL_BATTLEMD.read_bytes()
    official_sha = hashlib.sha256(official).hexdigest()
    cur = (BASE / "BATTLEMD.INI").read_bytes()
    sink.step("prep_inplace_target_precheck", size=len(cur),
              sha256=hashlib.sha256(cur).hexdigest(),
              expected_sha256=official_sha,
              official_match=(hashlib.sha256(cur).hexdigest() == official_sha))
    if hashlib.sha256(cur).hexdigest() != official_sha:
        raise RuntimeError("BASE BATTLEMD.INI != official baseline; "
                           "inplace_preflight would refuse (exit 33)")

    # (5) Build ONE v15 INPLACE package (BATTLEMD.INI, NO BATTLEMD98.INI).
    if PKG.exists():
        shutil.rmtree(PKG, ignore_errors=True)
    PKG.mkdir(parents=True, exist_ok=True)
    rc_b, so_b, se_b = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "build",
         "--design", str(DESIGN), "--out", str(PKG),
         "--feature-set", str(FEATURE_SET)], V15, sink, "prep_build_v15_inplace")
    pkg_rows = []
    for p in sorted(PKG.rglob("*")):
        if p.is_file():
            pkg_rows.append({"rel": p.relative_to(PKG).as_posix(),
                             "size": p.stat().st_size,
                             "sha256": sha256_file(p)})
    has_inplace = (PKG_INNER / "BATTLEMD.INI").is_file()
    has_98 = (PKG_INNER / "BATTLEMD98.INI").is_file()
    if rc_b != 0 or not PKG_INNER.is_dir() or not has_inplace or has_98:
        raise RuntimeError("v15 inplace build failed/wrong shape: "
                           "rc=%d inner=%s hasInplace=%s has98=%s "
                           "stderr=%s" % (rc_b, PKG_INNER, has_inplace,
                                          has_98, se_b[-500:]))

    # (6) BYTE-EXACT INI diff: official -> inplace-rewritten package member.
    rewritten = (PKG_INNER / "BATTLEMD.INI").read_bytes()
    diff = ini_diff_lines(official, rewritten)
    ini_report = {
        "card": "W72_inplace_noninterference",
        "route": "battlemd:inplace (v15 W60 implementation)",
        "feature_set": str(FEATURE_SET),
        "battlemd_mode": "inplace",
        "scenario_requested": REWRITE_SCENARIO,
        "official_scenario": OFFICIAL_SCENARIO,
        "note": ("Equivalent-but-different spelling: Windows/engine matches the "
                 "map filename case-insensitively; Scen+0x125C is uppercased "
                 "to SOV01UMD.MAP in BOTH arms. Bytes differ in exactly 1 "
                 "line so the installer takes the REPLACE path (creates "
                 "BATTLEMD.INI.ra2forge.bak + records original_sha256)."),
        "before_bytes": len(official), "after_bytes": len(rewritten),
        "before_sha256": hashlib.sha256(official).hexdigest(),
        "after_sha256": hashlib.sha256(rewritten).hexdigest(),
        "before_lines": len(re.split(b"(?<=\n)", official)),
        "after_lines": len(re.split(b"(?<=\n)", rewritten)),
        "crlf_lines_after": rewritten.count(b"\r\n"),
        "bare_lf_after": rewritten.count(b"\n") - rewritten.count(b"\r\n"),
        "diff_line_count": len(diff), "diff": diff,
        "after_values_equal_official": (rewritten == official),
    }
    (OUT / "ini_diff.json").write_text(
        json.dumps(ini_report, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    (OUT / "BATTLEMD.INI.before").write_bytes(official)
    (OUT / "BATTLEMD.INI.after").write_bytes(rewritten)
    sink.step("ini_diff", **ini_report)
    if len(diff) != 1:
        raise RuntimeError("expected exactly 1 INI diff line, got %d: %r"
                           % (len(diff), diff))
    if rewritten == official:
        raise RuntimeError("inplace rewrite is byte-identical to official: "
                           "installer would ADOPT/REPLAY, no .bak would exist")
    if b"Scenario=" + REWRITE_SCENARIO.encode() + b"\r\n" not in rewritten:
        raise RuntimeError("package BATTLEMD.INI lacks Scenario=%s"
                           % REWRITE_SCENARIO)

    sink.step("v15_package", build_rc=rc_b, files=pkg_rows,
              package_inner=str(PKG_INNER),
              inner_has_battlemd_ini=has_inplace,
              inner_has_battlemd98=has_98,
              route="INPLACE (official BATTLEMD.INI rewritten 1 line; "
                    "Scenario=SOV01UMD.MAP == official map -> both arms "
                    "play the SAME map)",
              package_digest=hashlib.sha256(
                  "\n".join(sorted("%s %s" % (r["rel"], r["sha256"])
                                  for r in pkg_rows)).encode()).hexdigest())
    (OUT / "cadence.json").write_text(json.dumps({
        "cadence_s": CADENCE_S,
        "sample_seconds_default": DEFAULT_SAMPLE_SECONDS,
        "same_cadence_all_four_trips": True,
        "spec_frozen_at": SPEC_FROZEN_AT,
        "note": "6 ms target cadence, identical loop for A1/A2/B1/B2. "
                "t in each NDJSON row is ACTUAL monotonic elapsed time; "
                "tool_b_stats_v2.py never uses t (only frame deltas).",
    }, indent=2), encoding="utf-8")
    sink.step("phase_prep_end", ok=True)


# ------------------------------------------------------------------ TRIP
def phase_trip(tag: str, sample_seconds: int, sink: Sink) -> int:
    arm = tag[0]
    sandbox = CARD / ("sandbox_" + tag)
    pristine = OUT / ("pristine_" + tag)
    rec = {"arm": arm, "tag": tag, "sandbox": str(sandbox),
           "cadence_s": CADENCE_S, "sample_seconds": sample_seconds,
           "expected_map": EXPECTED_MAP,
           "errors": [], "phase_reached": False,
           "ndjson": str(OUT / (tag + ".ndjson"))}
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

        # ---- B arm ONLY: install the v15 INPLACE package -----------------
        if arm == "B":
            inst_args = [PY, "-B", "-X", "utf8", "-m", "ra2forge", "install",
                         "--package", str(PKG_INNER), "--game", str(sandbox),
                         "--feature-set", str(FEATURE_SET)]
            rci, so_i, se_i = run_cmd(inst_args, V15, sink, tag + "_install")
            if rci != 0:
                rci, so_i, se_i = run_cmd(
                    inst_args + ["--allow-content-conflict"], V15, sink,
                    tag + "_install_allow")
            rec["install_rc"] = rci
            rec["install_stdout"] = so_i[-1500:]
            rec["install_stderr"] = se_i[-800:]
            if rci != 0:
                raise RuntimeError("v15 inplace install rc=%d: %s"
                                   % (rci, se_i[-400:]))
            # ---- B-arm inplace proof: .bak + manifest original_sha256 ----
            man_path = sandbox / "ra2forge_install.json"
            man = json.loads(man_path.read_text(encoding="utf-8"))
            entries = [e for e in man.get("files", [])
                       if e.get("name") == "BATTLEMD.INI"]
            bak = sandbox / "BATTLEMD.INI.ra2forge.bak"
            official_sha = hashlib.sha256(
                OFFICIAL_BATTLEMD.read_bytes()).hexdigest()
            ip = {
                "tag": tag,
                "manifest_path": str(man_path),
                "manifest_sha256": sha256_file(man_path),
                "battlemd_entries": entries,
                "entry_count": len(entries),
                "bak_present": bak.is_file(),
                "bak_size": bak.stat().st_size if bak.is_file() else None,
                "bak_sha256": sha256_file(bak) if bak.is_file() else None,
                "official_baseline_sha256": official_sha,
                "bak_equals_official": (bak.is_file()
                                        and sha256_file(bak) == official_sha),
                "inplace_rewrite_block": man.get("inplace_rewrite"),
                "on_disk_battlemd_sha256": sha256_file(sandbox / "BATTLEMD.INI"),
                "package_battlemd_sha256": sha256_file(
                    PKG_INNER / "BATTLEMD.INI"),
            }
            ip["on_disk_equals_package"] = (
                ip["on_disk_battlemd_sha256"] ==
                ip["package_battlemd_sha256"])
            if len(entries) == 1:
                e = entries[0]
                ip["original_sha256_recorded"] = e.get("original_sha256")
                ip["original_sha256_matches_official"] = (
                    e.get("original_sha256") == official_sha)
                ip["post_install_sha256_recorded"] = e.get("post_install_sha256")
                ip["post_install_sha_matches_disk"] = (
                    e.get("post_install_sha256") ==
                    ip["on_disk_battlemd_sha256"])
            else:
                ip["original_sha256_matches_official"] = False
                ip["post_install_sha_matches_disk"] = False
            (OUT / ("%s_inplace_proof.json" % tag)).write_text(
                json.dumps(ip, indent=1, ensure_ascii=False, sort_keys=True,
                           default=str), encoding="utf-8")
            sink.step("inplace_proof", **{k: v for k, v in ip.items()
                                          if k != "battlemd_entries"})
            if not (ip["bak_present"] and ip["bak_equals_official"]
                    and ip["original_sha256_matches_official"]
                    and ip["on_disk_equals_package"]):
                raise RuntimeError("inplace proof failed: %r" % ip)
        else:
            # A arm: no package. Record that BATTLEMD.INI is the untouched
            # official baseline and no .bak / manifest exists.
            rec["a_arm_state"] = {
                "install": "NONE",
                "battlemd_sha256": sha256_file(sandbox / "BATTLEMD.INI"),
                "battlemd_is_official": (
                    sha256_file(sandbox / "BATTLEMD.INI") ==
                    hashlib.sha256(OFFICIAL_BATTLEMD.read_bytes()).hexdigest()),
                "bak_present": (sandbox / "BATTLEMD.INI.ra2forge.bak").is_file(),
                "manifest_present": (sandbox / "ra2forge_install.json").is_file(),
            }
            sink.step("a_arm_state", **rec["a_arm_state"])

        rcv, so_v, se_v = run_cmd(
            [PY, "-B", "-X", "utf8", "-m", "ra2forge", "verify",
             "--game", str(sandbox), "--json"], V15, sink, tag + "_verify_pre")
        rec["verify_pre_rc"] = rcv
        try:
            rec["verify_pre_json"] = json.loads(so_v)
        except Exception:
            rec["verify_pre_json"] = {"parse_error": so_v[-600:]}
        if rcv != 0:
            raise RuntimeError("verify_pre rc=%d: %s" % (rcv, se_v[-400:]))

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

        # ---- menu navigation (W45/W55b/W63/W69 identical entry) ---------
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
        # Soviet badge: SAME screen coords as W55b/W63/W65/W69 (210, 285).
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
        # SUCCESS PREMISE: both arms must play the SAME official map.
        rec["map_at_ingame"] = cnt.get("map_name")
        if rec["map_at_ingame"] != EXPECTED_MAP:
            raise RuntimeError("MAP_MISMATCH at ingame: 0x125C=%r != %r "
                               "-- arms would not be comparable"
                               % (rec["map_at_ingame"], EXPECTED_MAP))
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

        # ---- post-hoc: EVERY row must carry the SAME map ------------------
        distinct = {}
        with ndpath.open("r", encoding="utf-8") as fd:
            for line in fd:
                line = line.strip()
                if not line:
                    continue
                m = json.loads(line)["map_name"]
                distinct[m] = distinct.get(m, 0) + 1
        map_check = {"tag": tag, "expected_map": EXPECTED_MAP,
                     "distinct_map_names": distinct,
                     "all_rows_expected": set(distinct) == {EXPECTED_MAP},
                     "rows_checked": sum(distinct.values())}
        (OUT / ("%s_map_check.json" % tag)).write_text(
            json.dumps(map_check, indent=1, ensure_ascii=False, sort_keys=True),
            encoding="utf-8")
        rec["map_check"] = map_check
        sink.step("map_check", **map_check)
        if not map_check["all_rows_expected"]:
            raise RuntimeError("MAP_MISMATCH in NDJSON rows: %r" % distinct)
        rec["counters_after_sampling"] = read_observables(hproc)
        if (rec["counters_after_sampling"] or {}).get("map_name") != EXPECTED_MAP:
            raise RuntimeError("MAP_MISMATCH after sampling: %r"
                               % (rec["counters_after_sampling"],))
        ok = True
        status = ("ok=True phase_reached=True rows=%d dframe_points=%d "
                  "read_fail=%d map=%s" %
                  (rows_written, rec["dframe_points"], read_fail, EXPECTED_MAP))
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
    try:
        if sandbox.exists():
            shutil.rmtree(sandbox, ignore_errors=True)
            sink.step("trip_sandbox_removed", tag=tag, path=str(sandbox))
    except Exception as e:
        sink.step("trip_sandbox_remove_error", tag=tag, error=repr(e))
    return 0 if ok else 1


# ------------------------------------------------------------------ C AUDIT (offline, no lock/game)
def build_declared(pre: dict) -> dict:
    """Mirror of FROZEN tool_c_writeaudit.declared_write_set (W62 §1.2):
    D = package members U engine-derived U per-member .bak (if pre-existing).
    inplace iff BATTLEMD.INI in pkg and no BATTLEMD98.INI."""
    members = []
    ini = None
    for cand in ("BATTLEMD.INI", "BATTLEMD98.INI"):
        if (PKG_INNER / cand).is_file():
            ini = cand
            break
    if ini is None:
        raise FileNotFoundError("no BATTLEMD*.INI in package %s" % PKG_INNER)
    members.append(ini)
    for cand in ("MAPSELMD.INI", "ra2md.csf"):
        if (PKG_INNER / cand).is_file():
            members.append(cand)
    members += sorted(p.name for p in PKG_INNER.glob("*.MAP") if p.is_file())
    if (PKG_INNER / "expandmd98.mix").is_file():
        members.append("expandmd98.mix")
    engine = ["ra2forge_install.json", "ra2forge_install.json.seal"]
    d = set(members) | set(engine)
    bak = []
    for n in members:
        if n in pre:
            slot = n + ".ra2forge.bak"
            d.add(slot)
            bak.append(slot)
    inplace = ("BATTLEMD.INI" in members) and ("BATTLEMD98.INI" not in members)
    return {"D": sorted(d), "members": members,
            "declared_rewrite": ["BATTLEMD.INI"] if inplace else [],
            "inplace": inplace, "bak_slots": sorted(bak),
            "engine_derived": engine,
            "note": "Constructed UP FRONT from PACKAGE CONTENTS + fixed "
                    "engine whitelist, NOT from the observed write set."}


def phase_audit(sink: Sink) -> int:
    """tool_c_writeaudit.py --audit on REAL snapshots of the B-arm inplace
    install lifecycle, on a dedicated inert sandbox. No game, no lock."""
    sb = CARD / "sandbox_audit"
    if sb.exists():
        shutil.rmtree(sb, ignore_errors=True)
    robocopy(BASE, sb, sink, "audit_robocopy")
    pre = full_manifest(sb)
    inst_args = [PY, "-B", "-X", "utf8", "-m", "ra2forge", "install",
                 "--package", str(PKG_INNER), "--game", str(sb),
                 "--feature-set", str(FEATURE_SET)]
    rci, so_i, se_i = run_cmd(inst_args, V15, sink, "audit_install")
    if rci != 0:
        rci, so_i, se_i = run_cmd(inst_args + ["--allow-content-conflict"],
                                  V15, sink, "audit_install_allow")
    post = full_manifest(sb)
    # extra C-6 byte proof BEFORE uninstall consumes the .bak
    bak = sb / "BATTLEMD.INI.ra2forge.bak"
    official = OFFICIAL_BATTLEMD.read_bytes()
    bak_proof = {"bak_present_post_install": bak.is_file(),
                 "bak_sha256": sha256_file(bak) if bak.is_file() else None,
                 "official_sha256": hashlib.sha256(official).hexdigest(),
                 "bak_byte_equal_to_official": (
                     bak.is_file() and
                     sha256_file(bak) == hashlib.sha256(official).hexdigest())}
    (OUT / "c_audit_bak_proof.json").write_text(
        json.dumps(bak_proof, indent=1, ensure_ascii=False), encoding="utf-8")
    sink.step("c_audit_bak_proof", **bak_proof)
    if rci != 0:
        raise RuntimeError("audit install rc=%d: %s" % (rci, se_i[-400:]))

    rcu, so_u, se_u = run_cmd(
        [PY, "-B", "-X", "utf8", "-m", "ra2forge", "uninstall",
         "--game", str(sb), "--json"], V15, sink, "audit_uninstall")
    uninst = full_manifest(sb)

    declared = build_declared(pre)
    (OUT / "c_audit_before.json").write_text(
        json.dumps(pre, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    (OUT / "c_audit_after.json").write_text(
        json.dumps(post, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    (OUT / "c_audit_uninst.json").write_text(
        json.dumps(uninst, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    (OUT / "c_audit_declared.json").write_text(
        json.dumps(declared, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    sink.step("c_audit_snapshots", install_rc=rci, uninstall_rc=rcu,
              pre=len(pre), post=len(post), uninst=len(uninst),
              declared=sorted(declared["D"]), members=declared["members"],
              inplace=declared["inplace"],
              declared_rewrite=declared["declared_rewrite"])

    rc, so, se = run_cmd(
        [PY, "-B", "-X", "utf8", str(TOOL_C), "--audit",
         "--before", str(OUT / "c_audit_before.json"),
         "--after", str(OUT / "c_audit_after.json"),
         "--uninst", str(OUT / "c_audit_uninst.json"),
         "--declared", str(OUT / "c_audit_declared.json"),
         "--out", str(OUT / "c_audit_B_arm.json")],
        CARD, sink, "tool_c_writeaudit_audit")
    sink.step("c_audit_tool_exit", rc=rc, out=so[-1500:], err=se[-800:])
    summary = {"tool_exit": rc, "install_rc": rci, "uninstall_rc": rcu,
               "declared": declared}
    try:
        rep = json.loads((OUT / "c_audit_B_arm.json").read_text(encoding="utf-8"))
        summary["verdict"] = rep.get("verdict")
        summary["out_of_scope_writes"] = rep.get("out_of_scope_writes")
        summary["write_set"] = rep.get("write_set")
        summary["write_set_flat"] = rep.get("write_set_flat")
        summary["W_subset_D"] = (len(rep.get("out_of_scope_writes") or []) == 0)
        summary["protected_all_equal"] = rep.get(
            "protected_hash_check", {}).get("all_equal")
        summary["protected_touched"] = rep.get("protected_touched")
        summary["restore"] = rep.get("restore")
        summary["checks"] = rep.get("checks")
        summary["failed_checks"] = rep.get("failed_checks")
        summary["inplace_proof"] = rep.get("inplace_proof")
        summary["battlemd_classified_as_declared_rewrite"] = (
            "BATTLEMD.INI" in (declared.get("declared_rewrite") or [])
            and (rep.get("inplace_proof", {}).get("classified_as")
                 == "DECLARED-REWRITE (not out-of-scope)"))
        summary["bak_in_place_post_install"] = (
            rep.get("inplace_proof", {}).get("bak_present_post_install"))
        sink.step("c_audit_verdict", verdict=summary.get("verdict"),
                  out_of_scope=summary.get("out_of_scope_writes"),
                  protected_all_equal=summary.get("protected_all_equal"),
                  failed_checks=summary.get("failed_checks"),
                  classified=summary.get(
                      "battlemd_classified_as_declared_rewrite"))
    except Exception as e:
        summary["report_parse_error"] = repr(e)
        sink.step("c_audit_report_parse_error", error=repr(e))
    (OUT / "c_audit_verdict.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True,
                   default=str), encoding="utf-8")
    shutil.rmtree(sb, ignore_errors=True)
    return 0 if (rc == 0 and summary.get("verdict") == "PASS") else 1


# ------------------------------------------------------------------ COMPARE (offline, no lock/game)
def phase_compare(sink: Sink) -> int:
    # (1) merge arms + descriptive stats (card-local copy of W69 report tool)
    rc_r, so_r, se_r = run_cmd([PY, "-B", "-X", "utf8", str(REPORT_TOOL)],
                               CARD, sink, "w72_report", timeout=300)
    # (2) FROZEN W68b V2 tool --compare (byte-identical card-local copy)
    rc_c, so_c, se_c = run_cmd(
        [PY, "-B", "-X", "utf8", str(TOOL_B), "--compare",
         "--arm-a", str(OUT / "A_merged.ndjson"),
         "--arm-b", str(OUT / "B_merged.ndjson"),
         "--noise-a1", str(OUT / "A1.ndjson"),
         "--noise-a2", str(OUT / "A2.ndjson"),
         "--noise-b1", str(OUT / "B1.ndjson"),
         "--noise-b2", str(OUT / "B2.ndjson"),
         "--out", str(OUT / "b_compare_v2.json")],
        CARD, sink, "tool_b_stats_v2_compare", timeout=600)
    (OUT / "b_compare_v2.exit.txt").write_text(str(rc_c), encoding="utf-8")
    (OUT / "b_compare_v2.stdout.txt").write_text(so_c + "\n--- stderr ---\n" + se_c,
                                                 encoding="utf-8")
    # (3) FROZEN V2 tool selftest (synthetic, NOT a real-machine result)
    rc_s, so_s, se_s = run_cmd(
        [PY, "-B", "-X", "utf8", str(TOOL_B), "--selftest",
         "--out", str(OUT / "v2_selftest.json")],
        CARD, sink, "tool_b_stats_v2_selftest", timeout=600)
    summary = {"report_exit": rc_r, "compare_exit": rc_c,
               "selftest_exit": rc_s,
               "tool": str(TOOL_B),
               "tool_sha256": sha256_file(TOOL_B)}
    try:
        rep = json.loads((OUT / "b_compare_v2.json").read_text(encoding="utf-8"))
        summary["schema_version"] = rep.get("schema_version")
        summary["verdict"] = rep.get("verdict")
        summary["reason"] = rep.get("reason")
        summary["detail"] = rep.get("detail")
        summary["n_a"] = rep.get("n_a")
        summary["n_b"] = rep.get("n_b")
        summary["N_ks"] = rep.get("N_ks")
        summary["D_ks"] = rep.get("D_ks")
        summary["p_value"] = rep.get("p_value")
        summary["J_ui"] = rep.get("J_ui")
        summary["max_N_disc"] = rep.get("max_N_disc")
        summary["discrete_shifted_fields"] = rep.get("discrete_shifted_fields")
        summary["discrete_unstable_fields"] = rep.get("discrete_unstable_fields")
        summary["discrete_fields"] = {
            k: {"p_value": v.get("p_value"), "T_f_tvd": v.get("T_f_tvd"),
                "D_disc": v.get("D_disc"), "N_disc": v.get("N_disc"),
                "p_method": v.get("p_method"), "verdict": v.get("verdict"),
                "value_set_A": v.get("value_set_A"),
                "value_set_B": v.get("value_set_B")}
            for k, v in (rep.get("discrete_fields") or {}).items()}
        sink.step("compare_verdict", verdict=summary["verdict"],
                  reason=summary["reason"], detail=summary["detail"],
                  n_a=summary["n_a"], n_b=summary["n_b"],
                  N_ks=summary["N_ks"], D_ks=summary["D_ks"],
                  p_value=summary["p_value"])
    except Exception as e:
        summary["report_parse_error"] = repr(e)
        sink.step("compare_report_parse_error", error=repr(e))
    (OUT / "compare_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True,
                   default=str), encoding="utf-8")
    return 0 if (rc_r == 0 and rc_c == 0) else 1


# ------------------------------------------------------------------ FINALIZE (real-dir proof)
def phase_finalize(sink: Sink) -> int:
    real_post = full_manifest(REAL)
    pre = json.loads((OUT / "real_pre.json").read_text(encoding="utf-8"))["rows"]
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
        "card": "W72_inplace_noninterference",
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
                  "ra2youli was ONLY a read-only robocopy source + hash target.",
        "lock_final": lock_text(),
        "gamemd_residual": list_gamemd(),
    }
    (OUT / "finalize.json").write_text(
        json.dumps(proof, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8")
    lines = [
        "W72_inplace_noninterference / REAL_DIR_PROOF.txt",
        "Method: full-tree SHA-256 of EVERY regular file under ra2youli, "
        "PRE (before any sandbox/launch) vs POST (after all 4 trips).",
        "ra2youli was ONLY a read-only robocopy source + hash target; "
        "NEVER written by this card.",
        "",
        "IDENTICAL_TREE = %s" % identical,
        "pre_file_count  = %d" % len(pre),
        "post_file_count = %d" % len(real_post),
        "pre_total_bytes  = %d" % sum(v["size"] for v in pre.values()),
        "post_total_bytes = %d" % sum(v["size"] for v in real_post.values()),
        "added    = %r" % d["added"],
        "removed  = %r" % d["removed"],
        "modified = %r" % d["modified"],
        "",
        "Anchor hashes (PRE == POST):",
    ]
    for r in anchor_rows:
        lines.append("  %-16s equal=%s  %s" %
                     (r["name"], r["equal"], r["pre_sha256"]))
    lines += ["", "all_anchors_equal = %s" % proof["all_anchors_equal"],
              "gamemd_residual = %r" % proof["gamemd_residual"],
              "lock_final owner = %r" % ("owner=lead" in proof["lock_final"]),
              "", "generated = %s" % local_iso()]
    (CARD / "REAL_DIR_PROOF.txt").write_text("\n".join(lines) + "\n",
                                             encoding="utf-8")
    sink.step("finalize", IDENTICAL_TREE=identical,
              pre_file_count=len(pre), post_file_count=len(real_post),
              added=d["added"], removed=d["removed"], modified=d["modified"],
              all_anchors_equal=proof["all_anchors_equal"],
              gamemd_residual=proof["gamemd_residual"],
              lock_owner_is_lead=("owner=lead" in proof["lock_final"]))
    return 0 if identical else 1


# ------------------------------------------------------------------ main
def main(argv=None):
    p = argparse.ArgumentParser(description="W72 inplace non-interference collector")
    p.add_argument("--phase", required=True,
                   choices=("prep", "trip", "audit", "compare", "finalize"))
    p.add_argument("--tag", choices=("A1", "A2", "B1", "B2"))
    p.add_argument("--sample-seconds", type=int, default=DEFAULT_SAMPLE_SECONDS)
    a = p.parse_args(argv)
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
        if a.phase == "compare":
            return phase_compare(sink)
        if a.phase == "finalize":
            return phase_finalize(sink)
    except Exception as e:
        sink.step("phase_fatal", phase=a.phase, error=repr(e))
        print("FATAL: %r" % (e,), file=sys.stderr)
        return 1
    finally:
        sink.close()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

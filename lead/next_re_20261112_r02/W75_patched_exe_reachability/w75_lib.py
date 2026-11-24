#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W75 · live-probe library (COPIED/ADAPTED from W74 w74_lib.py, W27 live_lib.py,
then RE-POINTED to THIS card).  Never import another card's script: its output
paths are hardcoded.  All W75 writes land inside W75_patched_exe_reachability.

Proven techniques (read-only w.r.t. the game process):
  * WMI Win32_Process.Create launch, detached from this agent's process tree
  * EnumWindows / EnumChildWindows + GetWindowTextW / GetClassNameW / GetDlgCtrlID
  * PostMessageW(BM_CLICK) navigation by CONTROL TEXT (never by index)
  * OpenProcess(PROCESS_VM_READ|PROCESS_QUERY_INFORMATION) + ReadProcessMemory
  * PIL ImageGrab screenshots
  * real mouse move / click via SetCursorPos + mouse_event
  * close_game: WM_CLOSE -> taskkill -> taskkill /F, ONLY our own pid
  * byte-exact config restore from out/pristine_* + sha256 self-proof

FORBIDDEN & NOT USED: SuspendThread, StackWalk64, MiniDumpWriteDump,
DebugActiveProcess, breakpoints, DLL injection, CreateRemoteThread,
WriteProcessMemory, any write into the game process or its exe/dll, hooks.

Extra W75 measurement points:
  [0xA8F7A8]      DWORD  "currently selected control id" (0x6EB=1771 per W61 Q1)
  Scen+0x34CC     DWORD  BattleIdx (signed -1 on failed 0x46CC90 lookup)
  Scen+0x125C     char[0x104] current scenario filename
  [0x825C20]      DWORD  hover sound index (context only)
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ------------------------------------------------------------------ paths
ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W75 = RUN / "W75_patched_exe_reachability"
OUT = W75 / "out"
GAME = W75 / "sandbox_game"                    # robocopy of read-only real dir
REAL = ROOT / "ra2youli"                       # READ-ONLY SOURCE, NEVER WRITTEN
LOCK = RUN / ".game_instance.lock"
W61_PATCHED = RUN / "W61_third_badge_route" / "work" / "gamemd_v14r.exe"

# ------------------------------------------------------------------ constants
BM_CLICK = 0x00F5
WM_CLOSE = 0x0010
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
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

EXPECTED = {
    "real_gamemd_sha":   "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "patch_gamemd_sha":  "b9021544a369fc8db77b1d0500de335e703886c5633dadc73c836dee9f891287",
    "gamemd_len":        4825360,
    "real_file_count":   647,
    "real_total_bytes":  1989215270,
}

ADDR = {
    "frame":       0x00A8ED84,   # dword 32 ms counter
    "mode":        0x00A8B238,   # dword
    "scen_ptr":    0x00A8B230,   # dword ScenarioClass* singleton
    "battle_cnt":  0x00A83D08,   # dword Battles.Count
    "sel_ctrl_id": 0x00A8F7A8,   # dword currently selected control id (W61 Q1)
    "hover_sound": 0x00825C20,   # dword hover sound index (context only)
}

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
    ("ClientToScreen", wt.BOOL, [wt.HWND, ctypes.c_void_p]),
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
k32.GetExitCodeProcess.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Process32FirstW.restype = wt.BOOL
k32.Process32NextW.restype = wt.BOOL

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD), ("szExeFile", wt.WCHAR * 260),
    ]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# ------------------------------------------------------------------ helpers
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


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class Sink:
    """Per-step NDJSON recorder; every record flushed immediately."""

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
                                             default=str)[:420]), flush=True)
        except Exception:
            try:
                sys.stdout.write("[%s] %s <console print suppressed>\n"
                                 % (local_iso(), step_name))
                sys.stdout.flush()
            except Exception:
                pass
        return rec

    def close(self):
        self.nd.close()


# ------------------------------------------------------------------ process
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


def launch_game(sink: Sink):
    cmdline = 'cmd.exe /c cd /d "%s" && start "" "gamemd.exe"' % str(GAME)
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='%s'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % cmdline)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, errors="replace", timeout=90)
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
        sink.step("pid_found", pid=fallback, how="fallback_only_gamemd_present",
                  elapsed_s=round(time.monotonic() - t0, 2))
        return fallback
    raise RuntimeError("no gamemd.exe within %ss" % timeout_s)


def process_alive(pid) -> bool:
    return any(r["pid"] == pid for r in list_gamemd())


def exit_code(pid):
    h = k32.OpenProcess(0x0400, False, pid)   # QUERY_INFORMATION only
    if not h:
        return None
    try:
        c = wt.DWORD(0)
        ok = k32.GetExitCodeProcess(h, ctypes.byref(c))
        return int(c.value) if ok else None
    finally:
        k32.CloseHandle(h)


def close_game(pid, hwnd, sink: Sink):
    """Only our own pid; WM_CLOSE -> taskkill -> taskkill /F."""
    steps = []
    if not pid:
        sink.step("close_game", steps=["no_pid_no_launch"])
        return ["no_pid_no_launch"]
    if not process_alive(pid):
        sink.step("close_game", steps=["already_exited"], pid=pid,
                  exit_code=exit_code(pid))
        return ["already_exited"]
    if hwnd and u.IsWindow(hwnd):
        ok = u.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        steps.append("WM_CLOSE(hwnd=%s)->%s" % (hwnd, bool(ok)))
        time.sleep(2.0)
    if process_alive(pid):
        r = subprocess.run(["taskkill", "/PID", str(pid)],
                           capture_output=True, text=True, errors="replace", timeout=30)
        steps.append("taskkill /PID %s rc=%s out=%r" %
                     (pid, r.returncode, (r.stdout or r.stderr).strip()[:200]))
        time.sleep(2.0)
    if process_alive(pid):
        r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, text=True, errors="replace", timeout=30)
        steps.append("taskkill /F /PID %s rc=%s out=%r" %
                     (pid, r.returncode, (r.stdout or r.stderr).strip()[:200]))
        time.sleep(1.0)
    residual = [r for r in list_gamemd() if r["pid"] == pid]
    steps.append("residual_own_pid=%d" % len(residual))
    sink.step("close_game", pid=pid, steps=steps,
              all_gamemd_residual=list_gamemd(),
              own_pid_alive=process_alive(pid))
    return steps


# ------------------------------------------------------------------ windows
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
    """All child windows of this pid, with ctrl_id (GetDlgCtrlID)."""
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
    t0 = time.monotonic()
    time.sleep(wait_s)
    rec["wait_s"] = round(time.monotonic() - t0, 3)
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
        if wcls(h) == GAME_WND_CLASS:
            return h
    return None


# ------------------------------------------------------------------ RPM
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


def as_i32(b):
    if not b:
        return None
    x = int.from_bytes(b, "little")
    return x - (1 << 32) if x >= (1 << 31) else x


def read_w75_point(hproc, label=None):
    """One W75 sample. ALL reads ReadProcessMemory (read-only)."""
    out = {"label": label}
    for k, a in ADDR.items():
        b = rpm(hproc, a, 4)
        out[k] = int.from_bytes(b, "little") if b else None
    out["sel_ctrl_id_hex"] = (hex(out["sel_ctrl_id"])
                              if out["sel_ctrl_id"] is not None else None)
    scen = out.get("scen_ptr")
    if scen and scen > 0x10000:
        out["scen_filename"] = read_cstr(hproc, scen + 0x125C, 260)
        out["scen_next"] = read_cstr(hproc, scen + 0x04, 128)
        b = rpm(hproc, scen + 0x34CC, 4)
        out["scen_battle_idx_u32"] = int.from_bytes(b, "little") if b else None
        out["scen_battle_idx_i32"] = as_i32(b)
        out["scen_battle_idx_hex"] = (hex(int.from_bytes(b, "little"))
                                      if b else None)
        b = rpm(hproc, scen + 0x34AC, 1)
        out["scen_end_of_game"] = b[0] if b else None
        b = rpm(hproc, scen + 0x34B0, 1)
        out["scen_skip_mapsel"] = b[0] if b else None
        b = rpm(hproc, scen + 0x35A0, 2)
        out["scen_stage_idx"] = int.from_bytes(b, "little") if b else None
    else:
        for k in ("scen_filename", "scen_next", "scen_battle_idx_u32",
                  "scen_battle_idx_i32", "scen_battle_idx_hex",
                  "scen_end_of_game", "scen_skip_mapsel", "scen_stage_idx"):
            out[k] = None
    return out


# ------------------------------------------------------------------ screen
def screenshot(sink: Sink, label: str, hwnd=None, bbox=None):
    from PIL import ImageGrab
    if bbox is None and hwnd:
        bbox = rect(hwnd)
    img = ImageGrab.grab(bbox=bbox)
    p = OUT / ("screen_%s.png" % label)
    img.save(p)
    sink.step("screenshot", label=label, path=str(p), bbox=bbox,
              size=[img.width, img.height])
    return p


def move_mouse(sink: Sink, label: str, x: int, y: int, wait_s=1.0):
    u.SetCursorPos(int(x), int(y))
    sink.step("move_mouse", label=label, x=x, y=y, wait_s=wait_s)
    time.sleep(wait_s)


def real_mouse_click(sink: Sink, label: str, x: int, y: int, wait_s=1.0):
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    u.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    u.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    sink.step("real_mouse_click", label=label, x=x, y=y, wait_s=wait_s)
    time.sleep(wait_s)


def post_mouse_click(sink: Sink, label: str, hwnd, x: int, y: int,
                     wait_s=1.0):
    """WM_LBUTTONDOWN/UP to a window at CLIENT coordinates (secondary path)."""
    lp = (int(y) << 16) | (int(x) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    sink.step("post_mouse_click", label=label, hwnd=hwnd, x=x, y=y,
              wait_s=wait_s)
    time.sleep(wait_s)


# ------------------------------------------------------------------ config
# Byte copies are made in w75_prep.py into out/pristine/. This list is the
# "writable config" set (small files the game can rewrite). The full 647-file
# tree inventory is the stronger superset proof.
CONFIG_FILES = [
    "RA2MD.INI", "RA2MD.INI.benchbak", "ddraw.ini", "ddraw.ini.benchbak",
    "ra2.ini", "Ra2.lcf", "ra2md.lcf", "yuri.lcf",
    "BATTLEMD.INI", "BATTLEMD98.INI", "BATTLEMD.INI.ra2forge.bak",
    "expandmd98.mix", "expandmd98.mix.old-pre-migrate",
    "expandmd98.mix.ra2forge.bak",
    "ra2forge_install.json", "ra2forge_uninstall.txt.pre-migrate.bak",
    "ECH01.MAP", "ECH02.MAP", "ECH03.MAP",
    "ECH01.MAP.ra2forge.bak", "ECH02.MAP.ra2forge.bak",
    "ECH03.MAP.ra2forge.bak",
    "except.txt", "ra2render.log", "ra2render.ini", "launcher.txt",
    "subtitle.txt", "subtitlemd.txt",
]


def restore_configs(sink: Sink):
    """Byte-exact restore of writable configs from out/pristine/<name>."""
    rows = []
    for n in CONFIG_FILES:
        src = OUT / "pristine" / n
        dst = GAME / n
        if src.is_file():
            shutil.copyfile(src, dst)
            rows.append({"file": n, "sha256": sha256_file(dst),
                         "expected": sha256_file(src),
                         "match": sha256_file(dst) == sha256_file(src),
                         "restored": True})
        elif dst.is_file():
            # baseline absent -> remove anything the game created
            dst.unlink()
            rows.append({"file": n, "removed_created_file": True,
                         "match": True})
        else:
            rows.append({"file": n, "absent_baseline": True, "match": True})
    sink.step("restore_configs", rows=rows,
              all_match=all(r["match"] for r in rows))
    return rows


# ------------------------------------------------------------------ lock
def lock_read():
    if not LOCK.is_file():
        return None
    d = {}
    for line in LOCK.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def lock_claim(owner: str, purpose: str):
    LOCK.write_text(
        "run_id=NEXT_RE_20261112_R02\nowner=%s\ntime=%s\npurpose=%s\n"
        % (owner, local_iso(), purpose), encoding="utf-8")


def lock_release(owner: str, purpose: str):
    lock_claim(owner, purpose)


# ------------------------------------------------------------------ tree inventory
def inventory_tree(root: Path):
    """Full rel-path inventory with size + sha256 + mtime_ns."""
    rows = []
    for p in sorted(root.rglob("*"), key=lambda x: str(x).lower()):
        if p.is_file():
            st = p.stat()
            rows.append({"rel": str(p.relative_to(root)).replace("\\", "/"),
                         "size": st.st_size,
                         "sha256": sha256_file(p),
                         "mtime_ns": st.st_mtime_ns})
    return {"root": str(root), "file_count": len(rows),
            "total_bytes": sum(r["size"] for r in rows), "files": rows}


def diff_trees(pre, post, compare_mtime=True):
    a = {r["rel"]: r for r in pre["files"]}
    b = {r["rel"]: r for r in post["files"]}
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    changed = []
    mtime_diff = []
    for k in sorted(set(a) & set(b)):
        if (a[k]["size"] != b[k]["size"]
                or a[k]["sha256"] != b[k]["sha256"]):
            changed.append(k)
        elif compare_mtime and a[k]["mtime_ns"] != b[k]["mtime_ns"]:
            mtime_diff.append(k)
    return {"added": added, "removed": removed, "changed": changed,
            "mtime_diff": mtime_diff,
            "identical_tree": not (added or removed or changed or mtime_diff),
            "pre_count": pre["file_count"], "post_count": post["file_count"],
            "pre_bytes": pre["total_bytes"], "post_bytes": post["total_bytes"]}


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

    res = {}
    res["window_station"] = obj_name(u.GetProcessWindowStation())
    res["thread_desktop"] = obj_name(u.GetThreadDesktop(k32.GetCurrentThreadId()))
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
    child_total = 0
    for h in [x for x in tops if u.IsWindowVisible(x)][:8]:
        kids = []

        def ccb(kk, _l):
            kids.append(kk)
            return True
        u.EnumChildWindows(h, ENUM(ccb), 0)
        child_total += len(kids)
    res["enum_child_windows_total_first8"] = child_total
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

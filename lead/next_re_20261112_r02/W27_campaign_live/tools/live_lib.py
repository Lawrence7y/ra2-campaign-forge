#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W27 · live probe library — read-only Win32 observation of a sandbox gamemd.exe.

Reuses the techniques proven in W1/W4/W7/W20 (same run id), verbatim semantics:
  * WMI Win32_Process.Create launch (detached from the agent process tree)
  * EnumWindows / EnumChildWindows + GetWindowTextW / GetClassNameW
  * PostMessageW(..., BM_CLICK, ...) navigation by CONTROL TEXT (never by index)
  * SendMessageTimeoutW for LB_* reads; LB_GETITEMDATA -> pointer -> UTF-16LE via RPM
  * OpenProcess(VM_READ|QUERY_INFORMATION) + ReadProcessMemory (READ ONLY)
  * VirtualQueryEx + chunked RPM for a bounded read-only memory string search
  * close_game: WM_CLOSE -> taskkill (no /F) -> taskkill /F, only our own pid
  * restore_configs: byte-exact restore from pristine copies + sha256 self-proof

FORBIDDEN and NOT used: SuspendThread, StackWalk64, MiniDumpWriteDump,
DebugActiveProcess, breakpoints, DLL injection / CreateRemoteThread,
WriteProcessMemory, any write to the game process or its exe/dll, hooks.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

# ------------------------------------------------------------------ paths
ROOT = Path(r"D:\Project\ra2-campaign-forge")
RUN = ROOT / "lead" / "next_re_20261112_r02"
W27 = RUN / "W27_campaign_live"
OUT = W27 / "out"
GAME = W27 / "sandbox_game"
LOCK = RUN / ".game_instance.lock"

# ------------------------------------------------------------------ constants
BM_CLICK = 0x00F5
WM_CLOSE = 0x0010
WM_SETTEXT = 0x000C
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
LB_GETCOUNT = 0x018B
LB_GETITEMDATA = 0x0199
LB_SETCURSEL = 0x0186
LB_GETCURSEL = 0x0188
LB_GETTEXTLEN = 0x018A
LB_GETTEXT = 0x0189
VK_ESCAPE = 0x1B
VK_MENU = 0x12
VK_RETURN = 0x0D
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
STILL_ACTIVE = 259
SMTO_ABORTIFHUNG = 0x0002
GAME_WND_CLASS = "Yuri's Revenge"
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01

READABLE_PROTECT = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}

# known engine counters (read-only, proven in W1..W20)
ADDR = {
    "frame": 0x00A8ED84,   # dword
    "mode": 0x00A8B238,    # dword (0 = intro/main menu, 5 = everything else)
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
k32.VirtualQueryEx.restype = ctypes.c_size_t
k32.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                               ctypes.c_size_t]

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_wchar * 260),
    ]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class MBI(ctypes.Structure):
    """MEMORY_BASIC_INFORMATION, x64 layout (48 bytes)."""
    _fields_ = [("BaseAddress", ctypes.c_void_p),
                ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wt.DWORD),
                ("__alignment1", wt.DWORD),
                ("RegionSize", ctypes.c_size_t),
                ("State", wt.DWORD),
                ("Protect", wt.DWORD),
                ("Type", wt.DWORD),
                ("__alignment2", wt.DWORD)]


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
    """Per-step JSON + NDJSON recorder; every record is flushed immediately."""

    def __init__(self, tag: str):
        self.tag = tag
        self.nd = (OUT / ("%s.ndjson" % tag)).open("w", encoding="utf-8",
                                                    newline="\n")
        self.n = 0

    def step(self, step_name: str, **kw):
        rec = {"step": step_name, "t_utc": utc_iso(), "t_local": local_iso(),
               "t_monotonic": time.monotonic(), **kw}
        self.nd.write(json.dumps(rec, ensure_ascii=False, sort_keys=True,
                                 default=str, separators=(",", ":")) + "\n")
        self.nd.flush()
        self.n += 1
        print("[%s] %s %s" % (local_iso(), step_name,
                              json.dumps(kw, ensure_ascii=False, default=str)[:400]),
              flush=True)
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
                       capture_output=True, text=True, timeout=90)
    txt = (r.stdout or "").strip()
    sink.step("launch_wmi", stdout=txt, stderr=(r.stderr or "")[:300])
    import re
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
                sink.step("pid_found", pid=row["pid"], how="wmi_child_parent_pid",
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


def close_game(pid, hwnd, sink: Sink):
    """Only our own pid; WM_CLOSE -> taskkill -> taskkill /F."""
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
        steps.append("taskkill /PID %s rc=%s out=%r" %
                     (pid, r.returncode, (r.stdout or r.stderr).strip()[:200]))
        time.sleep(2.0)
    if process_alive(pid):
        r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, text=True, timeout=30)
        steps.append("taskkill /F /PID %s rc=%s out=%r" %
                     (pid, r.returncode, (r.stdout or r.stderr).strip()[:200]))
        time.sleep(1.0)
    residual = [r for r in list_gamemd() if r["pid"] == pid]
    steps.append("residual_own_pid=%d" % len(residual))
    sink.step("close_game", pid=pid, steps=steps,
              all_gamemd_residual=list_gamemd())
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


def smt(h, msg, wp=0, lp=0, timeout=2500):
    r = ctypes.c_size_t(0)
    u.SendMessageTimeoutW(h, msg, wp, lp, SMTO_ABORTIFHUNG, timeout,
                          ctypes.byref(r))
    return r.value


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
    """All controls of pid: hwnd, class, text, visible, rect, ctrl_id."""
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


def snap(pid, sink: Sink, name: str, note: str = ""):
    cs = controls(pid)
    sink.step("snap", name=name, note=note, pid=pid,
              n_controls=len(cs),
              controls=[c for c in cs if c["text"] or c["cls"] in
                        ("ListBox", "ComboBox", "Edit", "Button", "Static")])
    return cs


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


def click_hwnd(hwnd, sink: Sink, label, wait_s=0.8):
    ok = bool(u.PostMessageW(hwnd, BM_CLICK, 0, 0))
    sink.step("click_hwnd", label=label, hwnd=hwnd, result=bool(ok),
              wait_s=wait_s)
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


def read_counters(hproc):
    out = {}
    for k, a in ADDR.items():
        b = rpm(hproc, a, 4)
        out[k] = int.from_bytes(b, "little") if b else None
    return out


def read_utf16_ptr(hproc, ptr, max_bytes=480):
    if not ptr:
        return None
    b = rpm_partial(hproc, ptr, max_bytes)
    if not b:
        return None
    out = bytearray()
    for j in range(0, len(b) - 1, 2):
        if b[j] == 0 and b[j + 1] == 0:
            break
        out += b[j:j + 2]
    try:
        return bytes(out).decode("utf-16-le", errors="replace")
    except Exception:
        return None


def read_listbox(hproc, hwnd, sink: Sink, label, max_items=400):
    """LB_GETCOUNT + LB_GETITEMDATA -> pointer -> UTF-16LE (W7 technique)."""
    n = int(smt(hwnd, LB_GETCOUNT))
    cur = int(smt(hwnd, LB_GETCURSEL))
    items = []
    for i in range(min(n, max_items)):
        d = int(smt(hwnd, LB_GETITEMDATA, i)) & 0xFFFFFFFF
        items.append({"index": i, "itemdata": d,
                      "name": read_utf16_ptr(hproc, d)})
    sink.step("listbox", label=label, hwnd=hwnd, n_items=n, cur_sel=cur,
              items=items)
    return {"hwnd": hwnd, "n": n, "cur": cur, "items": items}


def all_listboxes(pid, hproc, sink: Sink, label):
    out = []
    for c in controls(pid):
        if c["cls"] in ("ListBox", "ComboBox") and c["visible"]:
            try:
                n = int(smt(c["hwnd"], LB_GETCOUNT)) if c["cls"] == "ListBox" else -1
            except Exception:
                n = -1
            out.append({"hwnd": c["hwnd"], "cls": c["cls"], "text": c["text"],
                        "rect": c["rect"], "ctrl_id": c["ctrl_id"], "n_guess": n})
    sink.step("listboxes", label=label, boxes=out)
    return out


def memory_search(hproc, needles, sink: Sink, label, cap_bytes=512 << 20,
                  max_regions=4096):
    """Read-only VirtualQueryEx + chunked ReadProcessMemory string search.

    No dump file, no suspend, no write. Returns per-needle hit counts and
    up to 3 context snippets per encoding.
    """
    enc = []
    for s in needles:
        enc.append((s, "ascii", s.encode("ascii", errors="ignore")))
        enc.append((s, "utf16le", s.encode("utf-16-le", errors="ignore")))
    hits = {("%s|%s" % (s, e)): {"count": 0, "samples": []} for s, e, _ in enc}
    regions = 0
    bytes_read = 0
    addr = 0
    mbi = MBI()
    chunk = 1 << 20
    max_addr = 0x7FFFFFFF  # 32-bit target
    while addr < max_addr and regions < max_regions and bytes_read < cap_bytes:
        got = k32.VirtualQueryEx(hproc, ctypes.c_void_p(addr),
                                 ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not got:
            break
        base = int(mbi.BaseAddress or 0)
        size = int(mbi.RegionSize or 0)
        if size <= 0:
            break
        regions += 1
        end = base + size
        if (int(mbi.State) == MEM_COMMIT
                and not (int(mbi.Protect) & (PAGE_GUARD | PAGE_NOACCESS))
                and int(mbi.Protect) in READABLE_PROTECT):
            off = base
            while off < end and bytes_read < cap_bytes:
                want = min(chunk, end - off)
                b = rpm_partial(hproc, off, want)
                if not b:
                    off += want
                    continue
                bytes_read += len(b)
                for s, e, nb in enc:
                    if not nb:
                        continue
                    key = "%s|%s" % (s, e)
                    start = 0
                    while True:
                        p = b.find(nb, start)
                        if p < 0:
                            break
                        hits[key]["count"] += 1
                        if len(hits[key]["samples"]) < 3:
                            lo = max(0, p - 48)
                            hi = min(len(b), p + len(nb) + 48)
                            ctx = b[lo:hi]
                            try:
                                txt = ctx.decode("utf-16-le" if e == "utf16le"
                                                 else "latin-1", errors="replace")
                            except Exception:
                                txt = repr(ctx)
                            hits[key]["samples"].append({
                                "addr": hex(off + p),
                                "context": txt.replace("\x00", ".")[:180]})
                        start = p + 1
                off += want
        addr = end
        if end <= base:
            break
    sink.step("memory_search", label=label, regions_scanned=regions,
              bytes_read=bytes_read, cap_bytes=cap_bytes, hits=hits)
    return {"regions": regions, "bytes_read": bytes_read, "hits": hits}


# ------------------------------------------------------------------ screen
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001


def screenshot(sink: Sink, label: str, hwnd=None, bbox=None):
    """Passive screen capture for click TARGETING / supplementary visual
    evidence. Never modifies the game or its data. Not used as control text."""
    from PIL import ImageGrab
    if bbox is None and hwnd:
        bbox = rect(hwnd)
    if bbox is None:
        bbox = None  # full virtual screen; window already gone
    img = ImageGrab.grab(bbox=bbox)
    p = OUT / ("screen_%s.png" % label)
    img.save(p)
    sink.step("screenshot", label=label, path=str(p), bbox=bbox,
              size=[img.width, img.height],
              note="passive screen capture (targeting/supplementary evidence; "
                   "NOT control text)")
    return p


def real_mouse_click(sink: Sink, label: str, x: int, y: int, wait_s=1.0):
    """Physical mouse click at SCREEN coordinates (SetCursorPos+mouse_event)."""
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    u.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    u.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    sink.step("real_mouse_click", label=label, x=x, y=y, wait_s=wait_s)
    time.sleep(wait_s)


def type_ascii(sink: Sink, label: str, text: str, wait_s=0.6):
    """Type plain ASCII via keybd_event (VK code == ASCII for A-Z, 0-9)."""
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


def save_inventory(sink: Sink, label: str):
    rows = []
    for p in sorted(GAME.glob("*"), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in (".sav", ".svg"):
            rows.append({"name": p.name, "size": p.stat().st_size,
                         "sha256": sha256_file(p),
                         "mtime_ns": p.stat().st_mtime_ns})
    sink.step("save_inventory", label=label, files=rows, n=len(rows))
    return rows


def post_mouse_click(sink: Sink, label: str, hwnd, x: int, y: int, wait_s=1.0):
    """Send WM_LBUTTONDOWN/UP to a window at CLIENT coordinates."""
    lp = (int(y) << 16) | (int(x) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    sink.step("post_mouse_click", label=label, hwnd=hwnd, x=x, y=y,
              wait_s=wait_s)
    time.sleep(wait_s)


# ------------------------------------------------------------------ config
RESTORE_FILES = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak")
VERIFY_ONLY_FILES = ("gamemd.exe", "ddraw.dll")


def restore_configs(sink: Sink):
    rows = []
    for n in RESTORE_FILES:
        src = OUT / ("pristine_" + n)
        dst = GAME / n
        if src.is_file():
            shutil.copyfile(src, dst)
        rows.append({"file": n, "sha256": sha256_file(dst) if dst.is_file() else None,
                     "expected": sha256_file(src) if src.is_file() else None,
                     "match": (dst.is_file() and src.is_file()
                               and sha256_file(dst) == sha256_file(src))})
    for n in VERIFY_ONLY_FILES:
        dst = GAME / n
        src = OUT / ("pristine_" + n)
        rows.append({"file": n, "sha256": sha256_file(dst) if dst.is_file() else None,
                     "expected": sha256_file(src) if src.is_file() else None,
                     "match": (dst.is_file() and src.is_file()
                               and sha256_file(dst) == sha256_file(src)),
                     "verify_only": True})
    sink.step("restore_configs", rows=rows,
              all_match=all(r["match"] for r in rows))
    return rows


def lock_claim(owner: str, purpose: str):
    LOCK.write_text(
        "run_id=NEXT_RE_20261112_R02\nowner=%s\ntime=%s\npurpose=%s\n"
        % (owner, local_iso(), purpose), encoding="utf-8")


def lock_restore_lead():
    lock_claim("lead", "W27 C-line live card finished: restored owner=lead")

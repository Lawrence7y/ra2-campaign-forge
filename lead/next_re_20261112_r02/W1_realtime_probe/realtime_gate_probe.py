# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W1 —— 真机只读门控观测探针。

目标：用一次真实遭遇战判定「帧计数停推」是 *门控跳过* 还是 *真的卡顿*。

授权边界（本批）：
  * 允许：WMI 分离启动 gamemd.exe、对本进程 ReadProcessMemory、
          枚举窗口/线程、BM_CLICK 导航、LB_* 读地图列表、窗口消息/输入。
  * 禁止：SuspendThread / ResumeThread / StackWalk64 / MiniDump / 断点 /
          注入 / 写目标进程内存 / 改 exe 或 dll。
  * 只处理自己启动的那个实例；不 taskkill 别人的进程。
  * 本批只做只读轮询，不抓栈。

P0：脚本一启动就开 NDJSON sink 并写 meta 行，此后每行 flush。
P1：finally 中关闭自己启动的实例、核对残留、逐字节还原配置并自证哈希。
P2：正常结束后调用 analyze_probe.py 离线重算（只从 ndjson）。

用法：
  python -X utf8 realtime_gate_probe.py --seconds 300 --interval 0.05 \
      --map-pattern "Proving Grounds" --out out/gate_probe_xxx.ndjson
"""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
BASE = ROOT / "lead" / "next_re_20261112_r02" / "W1_realtime_probe"
OUT = BASE / "out"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"

EXPECTED_RA2MD = "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d"
# 与 baseline_pre_launch/PRE_LAUNCH_BASELINE.tsv 一致（只读常量，不自行改动地址）
BASELINE_HASHES = {
    "RA2MD.INI": EXPECTED_RA2MD,
    "ddraw.ini": "c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52",
    "RA2MD.INI.benchbak": EXPECTED_RA2MD,
    "gamemd.exe": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll": "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
}
RESTORE_FILES = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak")
VERIFY_ONLY_FILES = ("gamemd.exe", "ddraw.dll")

# ★ 由 Lead 三起点交叉解码确认，禁止改动
ADDR = {
    "frame":     0x00A8ED84,   # dword 帧计数（0x55DE81 处 inc）
    "g1":        0x00A83D49,   # byte 门控1
    "g2":        0x00A8ECD0,   # byte 门控2
    "g3":        0x008B41C0,   # byte 门控3（是 0x8B41C0，不是 0x41C0）
    "g4":        0x00A83D48,   # byte 门控4
    "exitstate": 0x00A8EDD8,   # dword 既有登记的退出态（辅助）
    "b07784":    0x00B07784,   # dword 推进函数里与 edi 比较的字段（辅助）
}
CODE_SIG_ADDR = 0x0055DE4F
CODE_SIG_EXPECT = bytes.fromhex("a0493da800")   # mov al, [0xa83d49]

BM_CLICK = 0x00F5
LB_GETCOUNT = 0x018B
LB_GETITEMDATA = 0x0199
LB_SETCURSEL = 0x0186
WM_CLOSE = 0x0010
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_ESCAPE = 0x1B
VK_MENU = 0x12
KEYEVENTF_KEYUP = 0x0002
SW_RESTORE = 9
STILL_ACTIVE = 259
GAME_WND_CLASS = "Yuri's Revenge"
MAX_INVENTORY_FILES = 6000
SMALL_HASH_LIMIT = 2 * 1024 * 1024

LOG_LINES = []


def utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def log(msg):
    line = "%s %s" % (utc_iso(), msg)
    LOG_LINES.append(line)
    try:
        print(line, flush=True)
    except Exception:
        pass
    return line


# ------------------------------------------------------------------ Win32 绑定
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
    ("GetForegroundWindow", wt.HWND, []),
    ("SetForegroundWindow", wt.BOOL, [wt.HWND]),
    ("ShowWindow", wt.BOOL, [wt.HWND, ctypes.c_int]),
    ("BringWindowToTop", wt.BOOL, [wt.HWND]),
    ("AllowSetForegroundWindow", wt.BOOL, [wt.DWORD]),
    ("keybd_event", None,
     [ctypes.c_ubyte, ctypes.c_ubyte, wt.DWORD, ctypes.c_size_t]),
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
k32.IsWow64Process.restype = wt.BOOL
k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]
k32.GetExitCodeProcess.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.GetConsoleWindow.restype = wt.HWND
k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Process32FirstW.restype = wt.BOOL
k32.Process32NextW.restype = wt.BOOL
# 不设 argtypes：直接传 ctypes.byref(PROCESSENTRY32W)，避免 c_void_p 转换差异

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD), ("th32ProcessID", wt.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", wt.DWORD),
        ("cntThreads", wt.DWORD), ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


def list_gamemd():
    """Toolhelp32 快照枚举 gamemd（只读，不涉及任何别的进程的操作）。"""
    snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)   # TH32CS_SNAPPROCESS
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


def wtxt(h):
    n = u.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(max(n + 1, 2))
    u.GetWindowTextW(h, b, n + 1)
    return b.value


def wcls(h):
    b = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(h, b, 256)
    return b.value


def smt(h, msg, wp=0, lp=0, timeout=2500):
    r = ctypes.c_size_t(0)
    u.SendMessageTimeoutW(h, msg, wp, lp, 0x0002, timeout, ctypes.byref(r))
    return r.value


def controls(pid):
    tops = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            tops.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    out, seen = [], set()

    def walk(h):
        kids = []

        def ccb(kk, l):
            kids.append(kk)
            return True

        u.EnumChildWindows(h, ENUM(ccb), 0)
        for kk in kids:
            if kk not in seen:
                seen.add(kk)
                out.append((kk, wcls(kk), wtxt(kk), bool(u.IsWindowVisible(kk))))
            walk(kk)

    for t in tops:
        walk(t)
    return out


def find_btn(pid, name):
    for h, c, t, v in controls(pid):
        if c == "Button" and name.lower() in (t or "").lower():
            return h
    return None


def click(pid, name, wait):
    h = find_btn(pid, name)
    if not h:
        log("    !! 未找到按钮 %s" % name)
        return False
    ok = u.PostMessageW(h, BM_CLICK, 0, 0)
    log("    click %-22s hwnd=%-10d -> %s" % (name, h, bool(ok)))
    time.sleep(wait)
    return True


def find_maplist(pid, minitems=50):
    for h, c, t, v in controls(pid):
        if c == "ListBox" and v:
            n = int(smt(h, LB_GETCOUNT))
            if n >= minitems:
                return h, n
    return None, 0


def game_top_windows(pid):
    out = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid and wcls(h) == GAME_WND_CLASS:
            out.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    return out


def any_other_window(pid):
    cand = []

    def cb(h, l):
        if not u.IsWindowVisible(h):
            return True
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid:
            return True
        t = wtxt(h)
        if t:
            cand.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    return cand[0] if cand else 0


def force_foreground(hwnd):
    """尽力把某窗口置前（ALT 技巧）；返回是否真的成为前台。"""
    if not hwnd or not u.IsWindow(hwnd):
        return False
    try:
        u.AllowSetForegroundWindow(0xFFFFFFFF)   # ASFW_ANY
    except Exception:
        pass
    u.keybd_event(VK_MENU, 0, 0, 0)
    try:
        u.ShowWindow(hwnd, SW_RESTORE)
        u.BringWindowToTop(hwnd)
        u.SetForegroundWindow(hwnd)
    finally:
        u.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.15)
    fg = u.GetForegroundWindow()
    p = wt.DWORD(0)
    u.GetWindowThreadProcessId(fg, ctypes.byref(p))
    return int(fg) == int(hwnd)


def send_esc():
    """真实键盘事件发 Esc（不写目标进程内存，不做注入）。"""
    u.keybd_event(VK_ESCAPE, 0, 0, 0)
    time.sleep(0.06)
    u.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.06)


def button_texts(pid, limit=40):
    """只读枚举本 pid 的按钮文字，作为「菜单是否真的弹出」的证据。"""
    out = []
    for h, c, t, v in controls(pid):
        if c == "Button" and t:
            out.append((h, t))
    return out[:limit]


def click_resume_button(pid, prefer=("return", "resume", "back", "cancel", "continue")):
    """按控件文字找「返回对局」按钮并 BM_CLICK；找不到才退回 Esc×2。

    禁止固定索引：完全按名称子串匹配，并记录实际点到的 hwnd 与文字。
    """
    btns = button_texts(pid, limit=200)
    for key in prefer:
        for h, t in btns:
            if key in (t or "").lower():
                ok = u.PostMessageW(h, BM_CLICK, 0, 0)
                return {"method": "button", "hwnd": int(h), "text": t,
                        "clicked": bool(ok)}
    send_esc()
    time.sleep(0.4)
    send_esc()
    return {"method": "esc_x2_fallback", "n_buttons": len(btns),
            "buttons": [t for _, t in btns[:25]]}


# ------------------------------------------------------------------ 工具
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root, cap=MAX_INVENTORY_FILES):
    """有上限的目录清单（只用于比对「游戏写回了哪些文件」）。"""
    out = {}
    n = 0
    for dirpath, dirnames, filenames in os.walk(str(root)):
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                st = p.stat()
            except OSError:
                continue
            try:
                rel = str(p.relative_to(root))
            except ValueError:
                continue
            h = None
            if st.st_size <= SMALL_HASH_LIMIT:
                try:
                    h = sha256_file(p)
                except OSError:
                    h = None
            out[rel] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns,
                        "sha256": h}
            n += 1
            if n >= cap:
                return out
    return out


def diff_inventory(before, after):
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = []
    for k in sorted(set(before) & set(after)):
        b, a = before[k], after[k]
        if (b["size"] != a["size"] or b["mtime_ns"] != a["mtime_ns"]
                or b["sha256"] != a["sha256"]):
            changed.append(k)
    return {"added": added, "removed": removed, "changed": changed}


class GuardStop(Exception):
    pass


class NDJSONSink(object):
    """逐条写 NDJSON；每行 flush（对齐 re_n01_monitor.NDJSONSink）。"""

    def __init__(self, path, fsync=False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fsync = bool(fsync)
        self.f = self.path.open("w", encoding="utf-8", newline="\n")
        self.n_lines = 0

    def write(self, rec):
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), default=str)
        self.f.write(line + "\n")
        self.f.flush()
        if self.fsync:
            os.fsync(self.f.fileno())
        self.n_lines += 1
        return rec

    def close(self):
        if not self.f.closed:
            self.f.flush()
            self.f.close()


def rpm(hproc, addr, size):
    buf = (ctypes.c_char * size)()
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size,
                               ctypes.byref(got))
    if not ok or got.value != size:
        return None
    return bytes(buf.raw)


def rpm_partial(hproc, addr, size):
    """允许部分读取（地图名指针可能靠近不可读页边界，与 _run_hl_match.py 的 rw 一致）。"""
    buf = (ctypes.c_char * size)()
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size,
                               ctypes.byref(got))
    if not ok or got.value == 0:
        return None
    return bytes(buf.raw[:got.value])


def read_all(hproc):
    """一次采样读 7 个地址。任一失败 ⇒ read_status=fail，全部测量字段置 None。"""
    vals, failed = {}, []
    for k, a in ADDR.items():
        b = rpm(hproc, a, 1 if k.startswith("g") else 4)
        if b is None:
            failed.append(k)
            continue
        vals[k] = b[0] if k.startswith("g") else int.from_bytes(b, "little")
    if failed:
        return None, failed
    return vals, []


def state_stamp(seq, t_ns):
    return {"seq": seq, "t_mono_ns": int(t_ns), "t_utc_iso": utc_iso(),
            "kind": "sample"}


# ------------------------------------------------------------------ 启动 / 导航
def launch_game():
    cmdline = 'cmd.exe /c cd /d "%s" && start "" "gamemd.exe"' % str(GAME_DIR)
    ps = ("$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='%s'}; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)" % cmdline)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=60)
    txt = (r.stdout or "").strip()
    log("    WMI Create 返回 %r (stderr=%r)" % (txt, (r.stderr or "")[:200]))
    m = None
    for line in txt.splitlines():
        mm = __import__("re").search(r"(\d+)\|(\d+)", line)
        if mm:
            m = mm
            break
    launcher_pid = int(m.group(1)) if m else 0
    retval = int(m.group(2)) if m else -1
    if retval != 0:
        raise RuntimeError("WMI Win32_Process.Create 失败 retval=%d" % retval)
    return launcher_pid


def wait_for_pid(launcher_pid, timeout_s=90):
    t0 = time.monotonic()
    fallback = None
    while time.monotonic() - t0 < timeout_s:
        rows = list_gamemd()
        for row in rows:
            if launcher_pid and row["ppid"] == launcher_pid:
                return row["pid"], "wmi_child_parent_pid"
        if rows and fallback is None:
            fallback = rows[0]["pid"]
        time.sleep(1.0)
    if fallback:
        return fallback, "fallback_only_gamemd_present"
    raise RuntimeError("启动后 %ss 未发现 gamemd.exe" % timeout_s)


def wait_main_menu(pid, timeout_s=90):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if find_btn(pid, "GUI:SinglePlayer"):
            log("    主菜单就绪（%.1fs）" % (time.monotonic() - t0))
            return True
        time.sleep(2.0)
    raise RuntimeError("主菜单超时 %ss（未找到 GUI:SinglePlayer）" % timeout_s)


def read_map_names(hproc, lb, n):
    names = []
    for i in range(n):
        d = int(smt(lb, LB_GETITEMDATA, i)) & 0xFFFFFFFF
        s = None
        if d:
            b = None
            for sz in (240 * 2, 128, 64, 32):
                b = rpm_partial(hproc, d, sz)
                if b is not None:
                    break
            if b is not None:
                out = bytearray()
                for j in range(0, len(b) - 1, 2):
                    if b[j] == 0 and b[j + 1] == 0:
                        break
                    out += b[j:j + 2]
                try:
                    s = bytes(out).decode("utf-16-le")
                except Exception:
                    s = None
        names.append((i, s))
    return names


def select_map_by_name(hproc, pid, pattern):
    click(pid, "GUI:ChooseMap", 3.0)
    lb, n = find_maplist(pid)
    log("    地图 ListBox=%s 条目=%d" % (lb, n))
    if not lb:
        raise RuntimeError("未拿到地图列表")
    names = read_map_names(hproc, lb, n)
    pat = pattern.lower()
    hits = [(i, s) for i, s in names if s and pat in s.lower()]
    for i, s in hits[:20]:
        log("    命中 [%3d] %r" % (i, s))
    log("    含 %r 的条目共 %d 个" % (pattern, len(hits)))
    if not hits:
        raise RuntimeError("地图列表中没有名称含 %r 的条目" % pattern)
    idx, disp = hits[0]
    log("    LB_SETCURSEL(%d) -> %s  显示名=%r" %
        (idx, smt(lb, LB_SETCURSEL, idx), disp))
    time.sleep(0.6)
    if not click(pid, "GUI:UseMap", 3.0):
        raise RuntimeError("GUI:UseMap 未点击成功")
    return {"index": idx, "display_name": disp, "n_items": n,
            "n_hits": len(hits), "pattern": pattern}


# ------------------------------------------------------------------ 收尾 P1
def close_game(pid, hwnd):
    """优雅优先；只处理自己启动的 pid。"""
    steps = []

    def alive():
        return any(r["pid"] == pid for r in list_gamemd())

    if not pid:
        steps.append("no_pid_no_launch: 未启动实例，无需关闭")
        return steps
    if not alive():
        steps.append("already_exited: 轮询期间进程已自然退出，不重启补测")
        return steps

    if hwnd and u.IsWindow(hwnd):
        ok = u.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        steps.append("WM_CLOSE(hwnd=%d) -> %s" % (hwnd, bool(ok)))
    else:
        steps.append("WM_CLOSE skipped: 无有效主窗口句柄")
    for _ in range(12):
        time.sleep(0.5)
        if not alive():
            steps.append("进程在 WM_CLOSE 后 6s 内自行退出")
            return steps

    # 只对自己记录的 pid 发 taskkill（不带 /F 先试优雅）
    if alive():
        r = subprocess.run(["taskkill", "/PID", str(pid)],
                           capture_output=True, text=True, timeout=30)
        steps.append("taskkill /PID %d (无 /F) rc=%d out=%r" %
                     (pid, r.returncode, (r.stdout or "").strip()[:200]))
    for _ in range(10):
        time.sleep(0.5)
        if not alive():
            steps.append("进程在 taskkill(无 /F) 后退出")
            return steps

    if alive():
        r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, text=True, timeout=30)
        steps.append("taskkill /F /PID %d rc=%d out=%r" %
                     (pid, r.returncode, (r.stdout or "").strip()[:200]))
    time.sleep(1.0)
    steps.append("最终存活=%s" % alive())
    return steps


def restore_configs():
    rows = []
    for name in RESTORE_FILES:
        src, dst = BASELINE_DIR / name, GAME_DIR / name
        if not src.exists():
            rows.append({"file": name, "error": "基线副本缺失，未还原"})
            continue
        pre = sha256_file(dst) if dst.exists() else None
        base_hash = sha256_file(src)
        shutil.copyfile(src, dst)                  # 逐字节拷贝
        post = sha256_file(dst)
        byte_same = (dst.read_bytes() == src.read_bytes())
        rows.append({
            "file": name, "baseline_copy_sha256": base_hash,
            "baseline_tsv_sha256": BASELINE_HASHES.get(name),
            "tsv_matches_copy": base_hash == BASELINE_HASHES.get(name),
            "pre_restore_sha256": pre, "post_restore_sha256": post,
            "byte_identical_to_baseline": bool(byte_same),
            "sha_match": post == base_hash == BASELINE_HASHES.get(name),
        })
    for name in VERIFY_ONLY_FILES:
        p = GAME_DIR / name
        h = sha256_file(p) if p.exists() else None
        rows.append({"file": name, "verify_only": True,
                     "baseline_tsv_sha256": BASELINE_HASHES.get(name),
                     "post_sha256": h,
                     "unchanged": h == BASELINE_HASHES.get(name)})
    return rows


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join(["---"] * len(headers)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def write_config_restore(residual_before, residual_after, rows, diff, close_steps,
                         ndjson_path, inventory_counts):
    t = []
    t.append("# CONFIG_RESTORE.md —— 配置还原与残留进程核对")
    t.append("")
    t.append("- run_id: `%s`" % RUN_ID)
    t.append("- 生成时刻(UTC): `%s`" % utc_iso())
    t.append("- NDJSON: `%s`" % ndjson_path)
    t.append("")
    t.append("## 1. 残留进程核对")
    t.append("")
    t.append("- 启动前 `gamemd.exe` 残留：**%d** 个 %s" %
             (len(residual_before), residual_before))
    t.append("- 收尾后 `gamemd.exe` 残留：**%d** 个 %s" %
             (len(residual_after), residual_after))
    t.append("- 关闭步骤（只针对自己启动的 pid）：")
    for s in close_steps:
        t.append("  - %s" % s)
    t.append("")
    t.append("## 2. 配置逐字节还原（基线 → 还原后）")
    t.append("")
    rr = []
    for r in rows:
        if r.get("verify_only"):
            rr.append([r["file"], "(无字节副本，仅校验)",
                       r["baseline_tsv_sha256"], r["post_sha256"],
                       "未改动=%s" % r["unchanged"]])
        elif "error" in r:
            rr.append([r["file"], "-", "-", "-", r["error"]])
        else:
            rr.append([r["file"], r["pre_restore_sha256"],
                       r["baseline_tsv_sha256"], r["post_restore_sha256"],
                       "逐字节一致=%s / 哈希一致=%s" %
                       (r["byte_identical_to_baseline"], r["sha_match"])])
    t.append(md_table(["文件", "收尾时(还原前) SHA-256", "基线 SHA-256",
                       "还原后 SHA-256", "结论"], rr))
    t.append("")
    ok = all(r.get("byte_identical_to_baseline") and r.get("sha_match")
             for r in rows if r.get("file") in RESTORE_FILES and "error" not in r)
    t.append("**结论：`RA2MD.INI` / `ddraw.ini` 是否逐字节还原 = %s**" % ok)
    t.append("")
    t.append("## 3. 游戏写回了哪些文件（与启动前清单比对）")
    t.append("")
    t.append("- 清单范围：`ra2youli\\` 有上限递归扫描（上限 %d 文件）；"
             "启动前 %d 个，收尾 %d 个。" %
             (MAX_INVENTORY_FILES, inventory_counts[0], inventory_counts[1]))
    t.append("- 新增 %d / 删除 %d / 变化 %d" %
             (len(diff["added"]), len(diff["removed"]), len(diff["changed"])))
    for k in ("added", "removed", "changed"):
        vals = diff[k]
        t.append("- %s (%d): %s" %
                 (k, len(vals), "、".join("`%s`" % x for x in vals[:60])
                  if vals else "（无）"))
        if len(vals) > 60:
            t.append("  - …还有 %d 项，见 `out/run_meta.json`" % (len(vals) - 60))
    t.append("")
    t.append("> 注：配置还原发生在清单比对 **之后**，因此上表记录的是游戏真实写回结果；"
             "还原本身会再次改写 `RA2MD.INI` / `ddraw.ini`。")
    p = BASE / "CONFIG_RESTORE.md"
    p.write_text("\n".join(t) + "\n", encoding="utf-8")
    return p


def write_runlog(a, ndjson_path, sink, exit_code, meta, close_steps, residual_after,
                 started_utc, ended_utc):
    cmd = "%s -X utf8 %s %s" % (
        sys.executable, str(BASE / "realtime_gate_probe.py"),
        " ".join('"%s"' % x if " " in x else x for x in sys.argv[1:]))
    t = []
    t.append("# RUNLOG.md —— 真机只读观测执行日志")
    t.append("")
    t.append("- run_id: `%s`" % RUN_ID)
    t.append("- 开始(UTC): `%s`" % started_utc)
    t.append("- 结束(UTC): `%s`" % ended_utc)
    t.append("- 退出码: **%d**" % exit_code)
    t.append("- 精确命令（脚本自身视角）: `%s`" % cmd)
    t.append("- 外层启动器命令: 由 `pwsh` 后台作业执行，见本文件末尾补充。")
    t.append("- NDJSON: `%s`（%d 行，每行 flush）" % (ndjson_path, sink.n_lines))
    t.append("- 参数: seconds=%s interval=%s map_pattern=%r menu_timeout=%s load_wait=%s" %
             (a.seconds, a.interval, a.map_pattern, a.menu_timeout, a.load_wait))
    t.append("- pid=%s is32=%s map=%s" %
             (meta.get("pid"), meta.get("is32"), meta.get("map")))
    t.append("")
    t.append("## stdout 关键片段（完整输出见 `out/probe_stdout.txt`）")
    t.append("")
    t.append("```text")
    for line in LOG_LINES:
        t.append(line)
    t.append("```")
    t.append("")
    t.append("## 收尾")
    t.append("")
    for s in close_steps:
        t.append("- %s" % s)
    t.append("- 收尾后 gamemd 残留: %d %s" % (len(residual_after), residual_after))
    t.append("")
    p = BASE / "RUNLOG.md"
    p.write_text("\n".join(t) + "\n", encoding="utf-8")
    return p


# ------------------------------------------------------------------ 主流程
def build_schedule(seconds):
    return [
        (0.00 * seconds, "phase_game_start", "game_start"),
        (0.08 * seconds, "phase_stable_ingame", "stable_ingame"),
        (0.20 * seconds, "event_esc_open_menu", "menu_open_attempt"),
        (0.27 * seconds, "event_esc_return_game", "return_to_game"),
        (0.34 * seconds, "event_verify_resume", "stable_ingame"),
        (0.46 * seconds, "event_focus_lost", "focus_lost_window"),
        (0.55 * seconds, "event_focus_regained", "focus_regained_window"),
        (0.62 * seconds, "phase_stable_ingame_3", "stable_ingame"),
    ]


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=300.0)
    ap.add_argument("--interval", type=float, default=0.05)
    ap.add_argument("--map-pattern", default="Proving Grounds")
    ap.add_argument("--out", default="")
    ap.add_argument("--menu-timeout", type=float, default=90.0)
    ap.add_argument("--load-wait", type=float, default=15.0)
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ndjson_path = Path(a.out) if a.out else OUT / ("gate_probe_%s.ndjson" % ts)
    if not ndjson_path.is_absolute():
        # 相对路径以 BASE 为根；若已含 out/ 前缀则不再叠加，避免 out\out\
        ndjson_path = (BASE / ndjson_path
                       if str(ndjson_path).replace("\\", "/").startswith("out/")
                       else OUT / ndjson_path)
    ndjson_path.parent.mkdir(parents=True, exist_ok=True)

    sink = NDJSONSink(ndjson_path)          # ★ P0：最先开文件
    started_utc = utc_iso()
    exit_code = 0
    pid, launcher_pid, own = 0, 0, ""
    hproc = None
    game_hwnd = 0
    is32 = None
    map_info = None
    prelaunch_hashes = {}
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    meta = {"run_id": RUN_ID, "ndjson": str(ndjson_path),
            "started_utc": started_utc, "args": vars(a),
            "addresses": {k: hex(v) for k, v in ADDR.items()},
            "baseline_hashes": BASELINE_HASHES, "pid": None, "is32": None,
            "map": None, "code_signature_ok": None,
            "prelaunch_hashes": {}, "error": None,
            "schedule": build_schedule(a.seconds)}

    log("[P0] NDJSON sink 已打开: %s" % ndjson_path)

    try:
        # ---------- 步骤 1：启动前检查 ----------
        log("[S1] 启动前：残留进程 + 实算 SHA-256")
        residual_before = list_gamemd()
        log("    gamemd 残留 = %d %s" % (len(residual_before), residual_before))
        if residual_before:
            raise GuardStop("启动前已存在 gamemd 残留，拒绝启动：%r" % residual_before)
        for name in ("RA2MD.INI", "ddraw.ini", "gamemd.exe", "ddraw.dll"):
            p = GAME_DIR / name
            if not p.exists():
                raise GuardStop("缺少文件 %s" % p)
            prelaunch_hashes[name] = {"bytes": p.stat().st_size,
                                      "sha256": sha256_file(p)}
            log("    %-14s %8d  %s" %
                (name, prelaunch_hashes[name]["bytes"],
                 prelaunch_hashes[name]["sha256"]))
        meta["prelaunch_hashes"] = prelaunch_hashes
        meta["residual_before"] = residual_before
        if prelaunch_hashes["RA2MD.INI"]["sha256"] != EXPECTED_RA2MD:
            raise GuardStop(
                "RA2MD.INI 哈希 != %s（实测 %s），按任务卡要求停止并报告" %
                (EXPECTED_RA2MD, prelaunch_hashes["RA2MD.INI"]["sha256"]))
        inventory_before = inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                    "prelaunch_hashes": prelaunch_hashes,
                    "residual_before": residual_before,
                    "note": "meta: 此后每行均为独立 NDJSON；异常退出此前各行仍可解析"})

        # ---------- 步骤 2：启动 + 等主菜单 ----------
        log("[S2] WMI 分离启动 gamemd.exe")
        launcher_pid = launch_game()
        pid, own = wait_for_pid(launcher_pid, a.menu_timeout)
        log("    pid=%d 归属判定=%s (launcher_pid=%d)" % (pid, own, launcher_pid))
        meta["pid"], meta["launcher_pid"], meta["ownership"] = pid, launcher_pid, own
        hproc = k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not hproc:
            raise RuntimeError("OpenProcess(PROCESS_VM_READ|QUERY_INFORMATION) 失败")
        flag = wt.BOOL(0)
        k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        meta["is32"] = is32
        log("    IsWow64Process -> is32=%s" % is32)
        sig = rpm(hproc, CODE_SIG_ADDR, len(CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == CODE_SIG_EXPECT)
        log("    代码签名@0x55DE4F = %r 期望 %r -> ok=%s" %
            (sig.hex() if sig else None, CODE_SIG_EXPECT.hex(),
             meta["code_signature_ok"]))
        wait_main_menu(pid, a.menu_timeout)

        # ---------- 步骤 3：导航 + 按名称选图 ----------
        log("[S3] 导航 SinglePlayer -> Skirmish")
        if not click(pid, "GUI:SinglePlayer", 3.0):
            raise RuntimeError("GUI:SinglePlayer 点击失败")
        if not click(pid, "GUI:Skirmish", 3.5):
            raise RuntimeError("GUI:Skirmish 点击失败")
        map_info = select_map_by_name(hproc, pid, a.map_pattern)
        meta["map"] = map_info
        hwnds = game_top_windows(pid)
        game_hwnd = hwnds[0] if hwnds else 0
        log("    游戏主窗口 hwnd=%s" % game_hwnd)
        if not click(pid, "GUI:StartGame", 1.0):
            raise RuntimeError("GUI:StartGame 点击失败")
        log("    等待加载 %.1fs" % a.load_wait)
        time.sleep(a.load_wait)

        # ---------- 步骤 4/5：只读轮询 ----------
        log("[S4] 开始只读轮询 %.1fs @ %.3fs" % (a.seconds, a.interval))
        sched = build_schedule(a.seconds)
        sched_i = 0
        current_remark = "game_start"
        # 尽量让游戏成为前台（供 Esc / 焦点实验使用），仅做状态标注
        if game_hwnd:
            ok = force_foreground(game_hwnd)
            log("    初始置前游戏窗口 -> %s" % ok)
        sink.write({"kind": "event", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "event": "run_start_polling",
                    "remark": current_remark, "pid": pid,
                    "detail": {"map": map_info, "is32": is32,
                               "code_signature_ok": meta["code_signature_ok"]}})

        t0_ns = time.perf_counter_ns()
        seq = 0
        prev_sample = None
        n_fail = 0
        n_exited = 0
        frame_at_menu = None
        menu_buttons = []
        resume_action = None
        pause_unrecovered = False
        next_tick = time.perf_counter()
        while True:
            t_ns = time.perf_counter_ns()
            elapsed = (t_ns - t0_ns) / 1e9
            if elapsed >= a.seconds:
                break

            # 事件调度（只触发一次）
            while sched_i < len(sched) and elapsed >= sched[sched_i][0]:
                ev_time, ev_name, new_remark = sched[sched_i]
                detail = {}
                if ev_name == "event_esc_open_menu":
                    cur_frame = None
                    v0, _ = read_all(hproc)
                    if v0:
                        cur_frame = v0["frame"]
                        frame_at_menu = cur_frame
                    send_esc()
                    time.sleep(1.0)
                    menu_buttons = button_texts(pid)
                    detail = {"action": "keybd_event(VK_ESCAPE)",
                              "frame_at_menu": cur_frame,
                              "menu_button_texts": [t for _, t in menu_buttons],
                              "intent": "打开局内菜单（是否真的暂停以帧/门控读数为准）"}
                    log("    菜单按钮文字(前 25): %s" %
                        [t for _, t in menu_buttons[:25]])
                elif ev_name == "event_esc_return_game":
                    resume_action = click_resume_button(pid)
                    detail = {"action": "click_resume_button",
                              "result": resume_action,
                              "intent": "从菜单返回对局"}
                    log("    返回对局动作: %s" % resume_action)
                elif ev_name == "event_verify_resume":
                    vv, _ = read_all(hproc)
                    d = (vv["frame"] - frame_at_menu
                         if vv and frame_at_menu is not None else None)
                    ok = bool(d is not None and d > 0)
                    pause_unrecovered = not ok
                    detail = {"frame_at_menu": frame_at_menu,
                              "frame_now": vv["frame"] if vv else None,
                              "delta_since_menu": d, "resumed": ok,
                              "resume_action": resume_action}
                    log("    ★ 恢复校验: 菜单后 Δframe=%s resumed=%s" % (d, ok))
                    if not ok:
                        log("    !! 菜单暂停未被解除，后续 remark 标为 pause_unrecovered")
                elif ev_name == "event_focus_lost":
                    other = any_other_window(pid)
                    ok = force_foreground(other) if other else False
                    detail = {"action": "SetForegroundWindow(other_hwnd)",
                              "other_hwnd": int(other or 0), "success": ok,
                              "intent": "窗口失焦"}
                elif ev_name == "event_focus_regained":
                    ok = force_foreground(game_hwnd)
                    detail = {"action": "SetForegroundWindow(game_hwnd)",
                              "success": ok, "intent": "切回游戏"}
                current_remark = new_remark
                if ev_name == "event_verify_resume" and pause_unrecovered:
                    current_remark = "pause_unrecovered"
                if pause_unrecovered and ev_name != "event_verify_resume":
                    current_remark = new_remark + "|pause_unrecovered"
                sink.write({"kind": "event", "seq": seq,
                            "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                            "event": ev_name, "remark": current_remark,
                            "elapsed_s": round(elapsed, 3), "pid": pid,
                            "detail": detail})
                log("    [event] t=%.2fs %s -> %s %s" %
                    (elapsed, ev_name, current_remark, detail))
                sched_i += 1

            # 前台窗口是否属于本 pid
            fg = u.GetForegroundWindow()
            fgpid = wt.DWORD(0)
            u.GetWindowThreadProcessId(fg, ctypes.byref(fgpid))
            win_foreground = (fgpid.value == pid)

            vals, failed = read_all(hproc)
            seq += 1
            rec = state_stamp(seq, t_ns)
            rec.update({"pid": pid, "elapsed_s": round(elapsed, 6),
                        "remark": current_remark,
                        "win_foreground": bool(win_foreground),
                        "frame": None, "g1": None, "g2": None, "g3": None,
                        "g4": None, "exitstate": None, "b07784": None,
                        "any_gate_nonzero": None, "frame_advanced": None,
                        "frame_delta": None, "frame_regression": False,
                        "read_status": "ok", "read_fail_detail": []})
            if vals is None:
                rec["read_status"] = "fail"
                rec["read_fail_detail"] = failed
                rec["remark"] = current_remark + "|read_fail"
                n_fail += 1
                if n_fail <= 5:
                    log("    !! read_status=fail @ seq=%d detail=%s" % (seq, failed))
            else:
                rec.update({k: vals[k] for k in
                            ("frame", "g1", "g2", "g3", "g4",
                             "exitstate", "b07784")})
                rec["any_gate_nonzero"] = bool(vals["g1"] or vals["g2"] or
                                               vals["g3"] or vals["g4"])
                if prev_sample is not None and prev_sample["read_status"] == "ok":
                    d = vals["frame"] - prev_sample["frame"]
                    rec["frame_delta"] = d
                    rec["frame_advanced"] = bool(d > 0)
                    if d < 0:
                        rec["frame_regression"] = True
                        rec["remark"] = current_remark + "|frame_regression"
                        sink.write({"kind": "event", "seq": seq,
                                    "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                                    "event": "frame_regression",
                                    "remark": rec["remark"], "pid": pid,
                                    "detail": {"from": prev_sample["frame"],
                                               "to": vals["frame"]}})
            sink.write(rec)                      # ★ 每拍一行，flush
            prev_sample = rec if rec["read_status"] == "ok" else {
                "read_status": "fail", "frame": None}

            # 进程自然退出/崩溃：如实记录，不重启补测
            ec = wt.DWORD(0)
            if k32.GetExitCodeProcess(hproc, ctypes.byref(ec)) and ec.value != STILL_ACTIVE:
                n_exited += 1
                sink.write({"kind": "event", "seq": seq,
                            "t_mono_ns": time.perf_counter_ns(),
                            "t_utc_iso": utc_iso(),
                            "event": "game_process_exited",
                            "remark": "game_process_exited",
                            "pid": pid, "elapsed_s": round(elapsed, 3),
                            "detail": {"exit_code": ec.value,
                                       "last_read_status": rec["read_status"],
                                       "last_frame": rec["frame"]}})
                log("    !! 进程自然退出 t=%.2fs exit=%d 最后读数 frame=%s "
                    "read_status=%s；不重启补测" %
                    (elapsed, ec.value, rec["frame"], rec["read_status"]))
                break

            next_tick += a.interval
            now = time.perf_counter()
            if next_tick < now:
                next_tick = now + a.interval
            time.sleep(max(0.0, next_tick - now))

        ended_elapsed = (time.perf_counter_ns() - t0_ns) / 1e9
        meta["observed_seconds"] = ended_elapsed
        meta["n_samples"] = seq
        meta["n_read_fail"] = n_fail
        meta["n_exit_events"] = n_exited
        meta["frame_at_menu"] = frame_at_menu
        meta["menu_buttons"] = [t for _, t in menu_buttons]
        meta["resume_action"] = resume_action
        meta["pause_unrecovered"] = pause_unrecovered
        log("[S4] 轮询结束：实际 %.3fs，采样 %d 拍，读失败 %d，退出事件 %d" %
            (ended_elapsed, seq, n_fail, n_exited))
        sink.write({"kind": "event", "seq": seq,
                    "t_mono_ns": time.perf_counter_ns(), "t_utc_iso": utc_iso(),
                    "event": "polling_end", "remark": "polling_end",
                    "pid": pid, "detail": {"observed_seconds": ended_elapsed,
                                           "n_samples": seq, "n_read_fail": n_fail}})

    except GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
        sink.write({"kind": "event", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "event": "guard_stop",
                    "remark": "guard_stop", "detail": str(e)})
    except Exception as e:
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())
        try:
            sink.write({"kind": "event", "seq": 0,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "event": "exception",
                        "remark": "exception", "detail": meta["error"]})
        except Exception:
            pass

    # ---------------- ★ P1：无论如何都要还原 ----------------
    finally:
        ended_utc = utc_iso()
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
        try:
            log("[P1] 收尾：关闭自启动实例")
            close_steps = close_game(pid, game_hwnd)
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:
            close_steps.append("close_game 异常: %r" % e)
            log("    close_game 异常 %r" % e)
        residual_after = list_gamemd()
        log("    收尾后 gamemd 残留 = %d %s" %
            (len(residual_after), residual_after))
        try:
            inventory_after = inventory(GAME_DIR)
            log("    收尾后文件清单 %d 项" % len(inventory_after))
        except Exception as e:
            log("    inventory_after 异常 %r" % e)
        diff = diff_inventory(inventory_before, inventory_after)
        try:
            rows = restore_configs()
            for r in rows:
                log("    还原 %s -> %s" % (r.get("file"),
                                          r.get("post_restore_sha256")
                                          or r.get("post_sha256")))
        except Exception as e:
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)

        try:
            (OUT / "probe_stdout.txt").write_text(
                "\n".join(LOG_LINES) + "\n", encoding="utf-8")
        except Exception:
            pass
        try:
            write_config_restore(residual_before, residual_after, rows, diff,
                                 close_steps, ndjson_path,
                                 (len(inventory_before), len(inventory_after)))
        except Exception as e:
            log("    write_config_restore 异常 %r" % e)
        meta["ended_utc"] = ended_utc
        meta["residual_after"] = residual_after
        meta["close_steps"] = close_steps
        meta["restore_rows"] = rows
        meta["written_back"] = diff
        meta["n_ndjson_lines"] = sink.n_lines
        try:
            (OUT / "run_meta.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True,
                           default=str), encoding="utf-8")
        except Exception as e:
            log("    写 run_meta.json 异常 %r" % e)
        try:
            write_runlog(a, ndjson_path, sink, exit_code, meta, close_steps,
                         residual_after, started_utc, ended_utc)
        except Exception as e:
            log("    write_runlog 异常 %r" % e)
        try:
            sink.write({"kind": "meta_end", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                        "exit_code": exit_code,
                        "residual_after": residual_after,
                        "n_ndjson_lines": sink.n_lines + 1})
        except Exception:
            pass
        sink.close()
        log("[P1] 收尾完成（配置已还原，NDJSON=%d 行）" % sink.n_lines)

    # ---------------- P2：离线重算（只从 ndjson） ----------------
    if exit_code == 0:
        try:
            ana = BASE / "analyze_probe.py"
            if ana.exists():
                r = subprocess.run(
                    [sys.executable, str(ana), "--ndjson", str(ndjson_path),
                     "--md", str(BASE / "ANALYSIS.md"),
                     "--uncovered", str(BASE / "UNCOVERED.md")],
                    cwd=str(BASE), capture_output=True, text=True, timeout=180)
                log("[P2] analyze_probe rc=%d out=%r err=%r" %
                    (r.returncode, (r.stdout or "")[-800:],
                     (r.stderr or "")[-800:]))
            else:
                log("[P2] analyze_probe.py 不存在，跳过")
        except Exception as e:
            log("[P2] analyze_probe 异常 %r（不影响 P1）" % e)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

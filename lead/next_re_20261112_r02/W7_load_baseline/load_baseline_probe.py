#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W7 —— RE-N03 真实负载与地图身份基线（真机单实例，3 次独立启动）。

任务（RE-N03，按序）：
  T1 载体稳定性：3 次独立启动，按名称子串选中 Proving Grounds（索引不稳定 ⇒ 禁固定索引），
     UseMap → StartGame → 等加载完成（mode!=5 门控）→ 局内连续采样 >=60 s @30ms。
  T2 候选代理量：0xA8ED50 / 0xB0CE88 / 0x87E8E0 在「进图前 / 加载中 / 局内稳定」三阶段的
     取值特征。★ 三者为既有登记的**候选代理字段**，语义未证；严禁写成「单位数/负载」。
  T3 H1 分层：另行判定（H1_LAYERING.md），本脚本输出里附带地图列表空名条目审计，
     供 T3 类 2（进列表但名称为空）的现状检测。

复用（已验证实现，零语义改动）：
  * W1_realtime_probe/realtime_gate_probe.py —— WMI 分离启动 / wait_for_pid /
    wait_main_menu / LB_* 读地图名（ITEMDATA→指针→UTF-16LE） / BM_CLICK 导航 /
    close_game / restore_configs / inventory / NDJSONSink / rpm(_partial)。
  * W6_transition/transition_probe.py —— 已修的 tid 语义：
    GetWindowThreadProcessId 的 tid 取**返回值**（第二参数写回的是 pid）。

授权：启动 ra2youli/gamemd.exe、只读 ReadProcessMemory、枚举窗口/线程、
      发送窗口消息/点击控件。禁止：SuspendThread/StackWalk64/MiniDump/断点/注入/
      写目标进程内存/改 exe/dll/hook。只处理自己启动的 pid；不杀别人进程。
写域：仅 lead/next_re_20261112_r02/W7_load_baseline/（本文件与 out/）。
实例锁：lead/next_re_20261112_r02/.game_instance.lock（开工 owner=本代理，
        收尾由外层在全部趟次结束后恢复 owner=lead）。

采样字段（每拍只读，任一失败 ⇒ read_status=fail，全部测量字段置 None，保留该拍）：
  t_mono_ns, frame(0xA8ED84,4B), mode(0xA8B238,4B),
  g1(0xA83D49,1B) g2(0xA8ECD0,1B) g3(0x8B41C0,1B) g4(0xA83D48,1B),
  A8E9A0(1B), ABCD58(0x00ABCD58,1B), exitstate(0xA8EDD8,4B),
  A8ED50(0x00A8ED50,4B) [候选代理], B0CE88(0x00B0CE88,4B) [候选代理],
  87E8E0(0x0087E8E0,4B) [候选代理，可回绕], read_status

区间推进速率 = Δframe / Δt（区间口径），**不是逐帧 FPS**；不给逐帧 P95/P99。

用法：
  python -X utf8 load_baseline_probe.py --run 1
  python -X utf8 load_baseline_probe.py --run 2
  python -X utf8 load_baseline_probe.py --run 3
  python -X utf8 load_baseline_probe.py --analyze        # 三趟后离线汇总 LOAD_BASELINE.md
"""
from __future__ import annotations

import argparse
import collections
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
W7 = ROOT / "lead" / "next_re_20261112_r02" / "W7_load_baseline"
OUT = W7 / "out"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"
LOCK_PATH = ROOT / "lead" / "next_re_20261112_r02" / ".game_instance.lock"
SELF_OWNER = "W7-load-baseline-subagent"
LEAD_OWNER = "lead"

EXPECTED_RA2MD = "c91c6a475b816fab8f4ab45b567c162f6b4ece9cc45d90abd69edab8dcd3c27d"
BASELINE_HASHES = {                     # 与 baseline_pre_launch/PRE_LAUNCH_BASELINE.tsv 一致
    "RA2MD.INI": EXPECTED_RA2MD,
    "ddraw.ini": "c983abadc1162a2606243e097719aab557ce6381c040776336d0c746d6df9d52",
    "RA2MD.INI.benchbak": EXPECTED_RA2MD,
    "gamemd.exe": "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476",
    "ddraw.dll": "85e0f7d530dfda134793a57cb3e76b0287dcc96892ee57162dd68f47283b03a9",
}
VERIFY_FILES = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak", "gamemd.exe", "ddraw.dll")
RESTORE_FILES = ("RA2MD.INI", "ddraw.ini", "RA2MD.INI.benchbak")
VERIFY_ONLY_FILES = ("gamemd.exe", "ddraw.dll")

# ★ Lead 三起点交叉解码确认的地址（只读；禁止改动）
ADDR = {
    "frame":        (0x00A8ED84, 4),   # dword 帧计数（0x55DE81 处 inc）
    "mode_A8B238":  (0x00A8B238, 4),   # dword 模式枚举（菜单/加载/设置=5，局内非5）
    "g1":           (0x00A83D49, 1),   # byte 门控1
    "g2":           (0x00A8ECD0, 1),   # byte 门控2
    "g3":           (0x008B41C0, 1),   # byte 门控3（是 0x8B41C0，不是 0x41C0）
    "g4":           (0x00A83D48, 1),   # byte 门控4
    "A8E9A0":       (0x00A8E9A0, 1),   # byte 循环活动/局内标志（候选读数）
    "ABCD58":       (0x00ABCD58, 1),   # byte 帧处理闩（候选读数）
    "exitstate":    (0x00A8EDD8, 4),   # dword 既有登记的退出态（辅助）
    "A8ED50":       (0x00A8ED50, 4),   # ★候选代理：既有登记「注册 Bullet 对象 Count」语义未证
    "B0CE88":       (0x00B0CE88, 4),   # ★候选代理：既有登记「脏矩形向量当前 Count」语义未证
    "87E8E0":       (0x0087E8E0, 4),   # ★候选代理：既有登记「工作区代际尝试代理」，可回绕，语义未证
}
CODE_SIG_ADDR = 0x0055DE4F
CODE_SIG_EXPECT = bytes.fromhex("a0493da800")   # mov al, [0xa83d49]

BM_CLICK = 0x00F5
LB_GETCOUNT = 0x018B
LB_GETITEMDATA = 0x0199
LB_SETCURSEL = 0x0186
WM_CLOSE = 0x0010
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
        ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_wchar * 260),
    ]


def list_gamemd():
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


def game_window_tid(w1_pid):
    """W6 已修语义：游戏窗口 tid = GetWindowThreadProcessId 的**返回值**。"""
    hwnds = game_top_windows(w1_pid)
    if not hwnds:
        return 0, None
    q = wt.DWORD(0)
    ret = u.GetWindowThreadProcessId(hwnds[0], ctypes.byref(q))
    return hwnds[0], (int(ret) or None)


def force_foreground(hwnd):
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


# ------------------------------------------------------------------ 工具
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root, cap=MAX_INVENTORY_FILES):
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
    """逐条写 NDJSON；每行 flush。"""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = self.path.open("w", encoding="utf-8", newline="\n")
        self.n_lines = 0

    def write(self, rec):
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), default=str)
        self.f.write(line + "\n")
        self.f.flush()
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
    """允许部分读取（地图名指针可能靠近不可读页边界，与 W1/_run_hl_match.py 的 rw 一致）。"""
    buf = (ctypes.c_char * size)()
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size,
                               ctypes.byref(got))
    if not ok or got.value == 0:
        return None
    return bytes(buf.raw[:got.value])


def read_all(hproc):
    """一次采样读 12 个地址。任一失败 ⇒ (None, failed)，保留该拍 read_status=fail。"""
    vals, failed = {}, []
    for k, (a, sz) in ADDR.items():
        b = rpm(hproc, a, sz)
        if b is None:
            failed.append(k)
            continue
        vals[k] = b[0] if sz == 1 else int.from_bytes(b, "little")
    if failed:
        return None, failed
    return vals, []


# ------------------------------------------------------------------ 启动 / 导航（W1 已验证实现）
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
    """按名称子串选中（禁固定索引）。记录条目总数 / 命中明细 / 空名条目审计。"""
    if not click(pid, "GUI:ChooseMap", 3.0):
        raise RuntimeError("GUI:ChooseMap 点击失败")
    lb, n = find_maplist(pid)
    log("    地图 ListBox=%s 条目=%d" % (lb, n))
    if not lb:
        raise RuntimeError("未拿到地图列表")
    names = read_map_names(hproc, lb, n)
    noname = [i for i, s in names if not s]
    pat = pattern.lower()
    hits = [(i, s) for i, s in names if s and pat in s.lower()]
    for i, s in hits[:20]:
        log("    命中 [%3d] %r" % (i, s))
    log("    含 %r 的条目共 %d 个；空名/乱码条目 %d 个（索引 %s）" %
        (pattern, len(hits), len(noname), noname[:20]))
    if not hits:
        raise RuntimeError("地图列表中没有名称含 %r 的条目" % pattern)
    idx, disp = hits[0]
    log("    LB_SETCURSEL(%d) -> %s  显示名=%r" %
        (idx, smt(lb, LB_SETCURSEL, idx), disp))
    time.sleep(0.6)
    if not click(pid, "GUI:UseMap", 3.0):
        raise RuntimeError("GUI:UseMap 未点击成功")
    return {"index": idx, "display_name": disp, "n_items": n,
            "n_hits": len(hits), "hits": [{"index": i, "name": s} for i, s in hits],
            "noname_indices": noname, "pattern": pattern}


# ------------------------------------------------------------------ 收尾（W1 已验证实现）
def close_game(pid, hwnd):
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


def check_lock():
    """实例锁守卫：owner 必须是 lead（允许接管）或自己（已持有）。其它 ⇒ 停手。"""
    try:
        txt = LOCK_PATH.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError("实例锁不可读 %s: %r" % (LOCK_PATH, e))
    owner = None
    for line in txt.splitlines():
        if line.startswith("owner="):
            owner = line.split("=", 1)[1].strip()
    if owner == LEAD_OWNER:
        return "lead_free"
    if owner == SELF_OWNER:
        return "self_held"
    raise RuntimeError("实例锁 owner=%r 不是 lead 也不是本代理 ⇒ 停手" % owner)


def write_lock(purpose):
    LOCK_PATH.write_text(
        "run_id=%s\nowner=%s\ntime=%s\npurpose=%s\n"
        % (RUN_ID, SELF_OWNER, datetime.datetime.now().astimezone().isoformat(),
           purpose),
        encoding="utf-8")


# ------------------------------------------------------------------ 单趟主流程
def run_one(a):
    run_no = a.run
    ndjson_path = OUT / ("run%d.ndjson" % run_no)
    meta_path = OUT / ("run%d_meta.json" % run_no)
    sink = NDJSONSink(ndjson_path)
    started_utc = utc_iso()
    exit_code = 0
    pid, launcher_pid, own = 0, 0, ""
    hproc = None
    game_hwnd, game_tid = 0, None
    is32 = None
    map_info = None
    prelaunch_hashes = {}
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    meta = {
        "run_id": RUN_ID, "card": "RE-N03 W7 load baseline", "run": run_no,
        "ndjson": str(ndjson_path), "started_utc": started_utc,
        "args": {k: getattr(a, k) for k in vars(a)},
        "addresses": {k: [hex(ad), sz] for k, (ad, sz) in ADDR.items()},
        "baseline_hashes": BASELINE_HASHES,
        "pid": None, "is32": None, "game_hwnd": None, "game_tid": None,
        "map": None, "code_signature_ok": None, "prelaunch_hashes": {},
        "residual_before": [], "residual_after": [], "close_steps": [],
        "error": None, "n_samples": 0, "n_read_fail": 0,
        "phase_stop": None, "battle_gate": None,
    }

    def ev(name, detail=None):
        try:
            sink.write({"kind": "event", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "event": name,
                        "detail": detail or {}})
        except Exception:
            pass

    try:
        # ---------- S0 守卫：锁 + 残留 + 哈希 ----------
        log("[S0] run%d 实例锁 + 残留进程 + 哈希守卫" % run_no)
        lock_state = check_lock()
        log("    实例锁 owner 状态 = %s（接管/持有）" % lock_state)
        write_lock("W7 RE-N03 run%d 真实负载与地图身份基线" % run_no)
        ev("lock_claimed", {"owner": SELF_OWNER, "state": lock_state})

        residual_before = list_gamemd()
        meta["residual_before"] = residual_before
        log("    gamemd 残留 = %d %s" % (len(residual_before), residual_before))
        if residual_before:
            raise GuardStop("启动前已存在 gamemd 残留，停手不杀：%r" % residual_before)
        for name in VERIFY_FILES:
            p = GAME_DIR / name
            if not p.exists():
                raise GuardStop("缺少文件 %s" % p)
            h = sha256_file(p)
            prelaunch_hashes[name] = {"bytes": p.stat().st_size, "sha256": h,
                                      "expected": BASELINE_HASHES[name],
                                      "match": h == BASELINE_HASHES[name]}
            log("    %-20s %8d %s match=%s" %
                (name, prelaunch_hashes[name]["bytes"], h,
                 prelaunch_hashes[name]["match"]))
        meta["prelaunch_hashes"] = prelaunch_hashes
        if not all(v["match"] for v in prelaunch_hashes.values()):
            bad = [n for n, v in prelaunch_hashes.items() if not v["match"]]
            raise GuardStop("启动前哈希与基线不一致，停手：%s" % bad)
        inventory_before = inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID, "run": run_no,
                    "prelaunch_hashes": prelaunch_hashes,
                    "residual_before": residual_before,
                    "note": "meta：此后每行独立 NDJSON；异常退出此前各行仍可解析"})

        # ---------- S1 启动 + 主菜单 ----------
        log("[S1] WMI 分离启动 gamemd.exe")
        ev("launching", {})
        launcher_pid = launch_game()
        pid, own = wait_for_pid(launcher_pid, a.menu_timeout)
        meta["pid"], meta["launcher_pid"], meta["ownership"] = pid, launcher_pid, own
        log("    pid=%d 归属=%s (launcher_pid=%d)" % (pid, own, launcher_pid))
        ev("pid_found", {"pid": pid, "ownership": own})
        hproc = k32.OpenProcess(0x0010 | 0x0400, False, pid)
        if not hproc:
            raise RuntimeError("OpenProcess(VM_READ|QUERY_INFORMATION) 失败")
        flag = wt.BOOL(0)
        k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        meta["is32"] = is32
        sig = rpm(hproc, CODE_SIG_ADDR, len(CODE_SIG_EXPECT))
        meta["code_signature_ok"] = (sig == CODE_SIG_EXPECT)
        log("    is32=%s 代码签名@0x55DE4F ok=%s" %
            (is32, meta["code_signature_ok"]))
        if not meta["code_signature_ok"]:
            raise GuardStop("代码签名不匹配，地址基线失效，停手")
        wait_main_menu(pid, a.menu_timeout)
        ev("main_menu_ready", {})

        # 游戏窗口 + tid（W6 已修语义）
        hwnds = game_top_windows(pid)
        game_hwnd = hwnds[0] if hwnds else 0
        game_hwnd2, game_tid = game_window_tid(pid)
        meta["game_hwnd"] = int(game_hwnd or game_hwnd2 or 0)
        meta["game_tid"] = game_tid
        log("    游戏窗口 hwnd=%s tid=%s" % (meta["game_hwnd"], game_tid))
        ev("game_window", {"hwnd": meta["game_hwnd"], "tid": game_tid})

        # ---------- S2 导航 + 按名称选图（pre_map 相位采样同步进行） ----------
        log("[S2] 导航 SinglePlayer -> Skirmish（pre_map 相位 @%.0fms）" %
            (a.pre_interval_ms))
        stop_flag = {"stop": False}

        def pre_sampler():
            seq = 0
            t0 = time.perf_counter_ns()
            while not stop_flag["stop"]:
                vals, failed = read_all(hproc)
                seq += 1
                rec = {"seq": seq, "kind": "sample", "phase": "pre_map",
                       "t_mono_ns": time.perf_counter_ns(),
                       "t_utc_iso": utc_iso(),
                       "elapsed_s": round((time.perf_counter_ns() - t0) / 1e9, 6),
                       "read_status": "ok" if vals is not None else "fail",
                       "read_fail_detail": failed,
                       "win_foreground": fg_is(pid)}
                for k in ADDR:
                    rec[k] = vals.get(k) if vals is not None else None
                sink.write(rec)
                time.sleep(a.pre_interval_ms / 1000.0)
            return seq

        import threading
        th = threading.Thread(target=pre_sampler, daemon=True)
        th.start()
        try:
            if not click(pid, "GUI:SinglePlayer", 3.0):
                raise RuntimeError("GUI:SinglePlayer 点击失败")
            if not click(pid, "GUI:Skirmish", 3.5):
                raise RuntimeError("GUI:Skirmish 点击失败")
            map_info = select_map_by_name(hproc, pid, a.map_pattern)
        finally:
            stop_flag["stop"] = True
            th.join(timeout=5.0)
        meta["map"] = map_info
        ev("map_selected", {"index": map_info["index"],
                            "display_name": map_info["display_name"],
                            "n_items": map_info["n_items"],
                            "n_hits": map_info["n_hits"],
                            "noname_indices": map_info["noname_indices"],
                            "pattern": map_info["pattern"]})

        # ---------- S3 StartGame + 加载（速率门控） ----------
        # ★ 门控修正（run1 被误杀后的定性，两份证据）：
        #   (a) W6 存档 samples.ndjson：W_A_load 与 W_A_ingame 的 mode 全部 = 5 且 frame
        #       都在推进 —— mode[0xA8B238] 在加载与局内**都是 5**，区分不了；
        #       任务卡「正常局内非 5」与 W6 自身数据不符，如实记录修正。
        #   (b) W6 数据可用判别器：加载段速率 ~21–25 计数/s，局内 ~31 计数/s。
        #   ⇒ 进图门控改为：StartGame 后 elapsed ≥ min_load_s 且 2s 窗速率 ≥ battle_rate
        #     持续 rate_high_s ⇒ 判定进入局内稳定段。mode 只记录、不当门控。
        log("[S3] StartGame → 等加载（速率门控 ≥%.0f/s 持续 %.0fs，elapsed≥%.0fs）" %
            (a.battle_rate, a.rate_high_s, a.min_load_s))
        if not click(pid, "GUI:StartGame", 1.0):
            raise RuntimeError("GUI:StartGame 点击失败")
        ev("startgame_clicked", {})
        ok = force_foreground(meta["game_hwnd"])
        log("    置前游戏窗口 -> %s" % ok)

        phase_stop, mode_hist, battle_at = None, [], None
        seq = 0
        t_load0 = time.perf_counter_ns()
        win = collections.deque()            # (t_ns, frame) 最近 ~2s 窗
        rate_high_since = None
        load_rate_samples = []
        while True:
            vals, failed = read_all(hproc)
            seq += 1
            t_ns = time.perf_counter_ns()
            elapsed = (t_ns - t_load0) / 1e9
            rec = {"seq": seq, "kind": "sample", "phase": "loading",
                   "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "elapsed_s": round(elapsed, 6),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed, "win_foreground": fg_is(pid)}
            for k in ADDR:
                rec[k] = vals.get(k) if vals is not None else None
            sink.write(rec)
            ec = wt.DWORD(0)
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            if not alive:
                phase_stop = "process_exited_during_loading"
                ev("process_exited", {"phase": "loading",
                                      "exit_code": ec.value})
                break
            if vals is not None:
                mode_hist.append(vals["mode_A8B238"])
                f = vals["frame"]
                win.append((t_ns, f))
                while len(win) > 1 and t_ns - win[0][0] > 2.0e9:
                    win.popleft()
                if len(win) >= 2 and t_ns - win[0][0] >= 1.8e9:
                    r = (f - win[0][1]) / ((t_ns - win[0][0]) / 1e9)
                    load_rate_samples.append(round(r, 3))
                    if r >= a.battle_rate and elapsed >= a.min_load_s:
                        if rate_high_since is None:
                            rate_high_since = t_ns
                        if (t_ns - rate_high_since) / 1e9 >= a.rate_high_s:
                            battle_at = t_ns
                            phase_stop = "battle_rate_detected"
                            ev("battle_detected", {
                                "after_s": round(elapsed, 3),
                                "rate_2s": round(r, 3),
                                "mode": vals["mode_A8B238"],
                                "n_mode_samples": len(mode_hist)})
                            break
                    else:
                        rate_high_since = None
            if (t_ns - t_load0) / 1e9 >= a.load_timeout:
                phase_stop = "load_timeout_no_battle_rate"
                ev("load_timeout", {"last_modes_tail": mode_hist[-40:],
                                    "n_mode_samples": len(mode_hist)})
                break
            time.sleep(a.ingame_interval_ms / 1000.0)
        meta["phase_stop"] = phase_stop
        meta["battle_gate"] = {
            "detected": battle_at is not None,
            "after_s": (round((battle_at - t_load0) / 1e9, 3)
                        if battle_at is not None else None),
            "min_load_s": a.min_load_s, "battle_rate": a.battle_rate,
            "rate_high_s": a.rate_high_s,
            "loading_rate_samples_tail": load_rate_samples[-20:],
            "loading_n_mode_samples": len(mode_hist),
            "mode_note": "mode[0xA8B238] 在加载与局内均为 5（run1 误杀 + W6 存档互证），"
                         "只记录不作为门控",
        }
        if battle_at is None:
            raise RuntimeError("未检测到局内速率签名（%s），本趟按失败收尾" % phase_stop)

        # ---------- S4 局内稳定相位采样 >=ingame_seconds @30ms ----------
        log("[S4] 局内采样 %.1fs @ %.0fms" % (a.ingame_seconds, a.ingame_interval_ms))
        ev("ingame_sampling_start", {"target_seconds": a.ingame_seconds})
        t_in0 = time.perf_counter_ns()
        seq_in = 0
        while True:
            vals, failed = read_all(hproc)
            seq_in += 1
            t_ns = time.perf_counter_ns()
            elapsed = (t_ns - t_in0) / 1e9
            rec = {"seq": seq_in, "kind": "sample", "phase": "ingame",
                   "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "elapsed_s": round(elapsed, 6),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed, "win_foreground": fg_is(pid)}
            for k in ADDR:
                rec[k] = vals.get(k) if vals is not None else None
            sink.write(rec)
            ec = wt.DWORD(0)
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            if not alive:
                ev("process_exited", {"phase": "ingame",
                                      "exit_code": ec.value,
                                      "elapsed_s": round(elapsed, 3)})
                log("    !! 局内采样 %.1fs 时进程退出（exit=%d），如实记录，不重启补测"
                    % (elapsed, ec.value))
                meta["phase_stop"] = "process_exited_during_ingame"
                break
            if elapsed >= a.ingame_seconds:
                break
            time.sleep(a.ingame_interval_ms / 1000.0)
        log("[S4] 局内采样结束：seq_in=%d" % seq_in)
        ev("ingame_sampling_end", {"n_samples": seq_in})

    except GuardStop as e:
        meta["error"] = "GuardStop: %s" % e
        exit_code = 2
        log("!! GuardStop: %s" % e)
        ev("guard_stop", {"detail": str(e)})
    except Exception as e:
        meta["error"] = "%s: %s" % (type(e).__name__, e)
        exit_code = 1
        log("!! 异常 %s: %s" % (type(e).__name__, e))
        log(traceback.format_exc())
        ev("exception", {"detail": meta["error"]})

    # ---------- P1 收尾（无论如何执行） ----------
    finally:
        ended_utc = utc_iso()
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
        try:
            log("[P1] run%d 收尾：关闭自启动实例" % run_no)
            close_steps = close_game(pid, meta.get("game_hwnd") or 0)
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:
            close_steps.append("close_game 异常: %r" % e)
            log("    close_game 异常 %r" % e)
        residual_after = list_gamemd()
        log("    收尾后 gamemd 残留 = %d %s" % (len(residual_after), residual_after))
        try:
            inventory_after = inventory(GAME_DIR)
            log("    收尾后文件清单 %d 项" % len(inventory_after))
        except Exception as e:
            log("    inventory_after 异常 %r" % e)
        diff = diff_inventory(inventory_before, inventory_after)
        try:
            rows = restore_configs()
            for r in rows:
                log("    还原 %s -> %s" %
                    (r.get("file"), r.get("post_restore_sha256")
                     or r.get("post_sha256")))
        except Exception as e:
            rows = [{"file": "?", "error": "restore_configs 异常 %r" % e}]
            log("    restore_configs 异常 %r" % e)

        try:
            (OUT / ("run%d_stdout.txt" % run_no)).write_text(
                "\n".join(LOG_LINES) + "\n", encoding="utf-8")
        except Exception:
            pass
        meta["ended_utc"] = ended_utc
        meta["residual_after"] = residual_after
        meta["close_steps"] = close_steps
        meta["restore_rows"] = rows
        meta["written_back"] = diff
        meta["inventory_counts"] = [len(inventory_before), len(inventory_after)]
        try:
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True,
                           default=str), encoding="utf-8")
        except Exception as e:
            log("    写 %s 异常 %r" % (meta_path.name, e))
        try:
            sink.write({"kind": "meta_end", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "run_id": RUN_ID, "run": run_no,
                        "exit_code": exit_code, "error": meta["error"],
                        "residual_after": residual_after})
        except Exception:
            pass
        sink.close()
        log("[P1] run%d 收尾完成（配置已还原，NDJSON=%d 行）" % (run_no, sink.n_lines))
        meta["n_ndjson_lines"] = sink.n_lines
        try:
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True,
                           default=str), encoding="utf-8")
        except Exception:
            pass
    return exit_code, meta


def fg_is(pid):
    fg = u.GetForegroundWindow()
    p = wt.DWORD(0)
    u.GetWindowThreadProcessId(fg, ctypes.byref(p))
    return p.value == pid


# ------------------------------------------------------------------ 离线分析
PHASE_ORDER = ("pre_map", "loading", "ingame")


def load_ndjson(path):
    samples, events = [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            k = rec.get("kind")
            if k == "sample":
                samples.append(rec)
            elif k == "event":
                events.append(rec)
    return samples, events


def phase_stats(samples, phase):
    mine = [s for s in samples if s.get("phase") == phase]
    ok = [s for s in mine if s.get("read_status") == "ok"]
    fv = [s["frame"] for s in ok if s.get("frame") is not None]
    ts = [s["t_mono_ns"] for s in ok]
    dur = ((ts[-1] - ts[0]) / 1e9) if len(ts) >= 2 else 0.0
    rate = ((fv[-1] - fv[0]) / dur) if (len(fv) >= 2 and dur > 0) else None
    # 1s 窗推进健康度（区间口径，非逐帧 FPS）
    adv = tot = 0
    for i in range(len(ok)):
        t = ok[i]["t_mono_ns"]
        j = i
        while j > 0 and t - ok[j - 1]["t_mono_ns"] < int(1.0e9):
            j -= 1
        if ok[i].get("frame") is not None and ok[j].get("frame") is not None \
                and t - ok[j]["t_mono_ns"] >= int(0.9e9):
            tot += 1
            if ok[i]["frame"] - ok[j]["frame"] > 0:
                adv += 1
    def dist(key):
        c = collections.Counter(s.get(key) for s in ok)
        return dict(sorted(((str(k), v) for k, v in c.items()),
                           key=lambda x: -x[1]))
    def uniq(key):
        return sorted({str(s.get(key)) for s in ok})
    gates0 = sum(1 for s in ok
                 if all(s.get(k) == 0 for k in ("g1", "g2", "g3", "g4")))
    p = {
        "phase": phase, "n_samples": len(mine), "n_ok": len(ok),
        "n_read_fail": len(mine) - len(ok),
        "duration_s": round(dur, 3),
        "frame_first": fv[0] if fv else None,
        "frame_last": fv[-1] if fv else None,
        "frame_net_delta": (fv[-1] - fv[0]) if len(fv) >= 2 else None,
        "advance_rate_counts_per_s": (round(rate, 3) if rate is not None else None),
        "advancing_1s_windows": adv, "total_1s_windows": tot,
        "advancing_ratio": (round(adv / tot, 4) if tot else None),
        "mean_interval_ms": (round(1000.0 * dur / (len(ts) - 1), 2)
                             if len(ts) >= 2 else None),
        "gates_all_zero_n": gates0,
        "gates_all_zero_ratio": (round(gates0 / len(ok), 4) if ok else None),
        "mode_dist": dist("mode_A8B238"),
        "A8E9A0_uniq": uniq("A8E9A0"),
        "ABCD58_uniq": uniq("ABCD58"),
        "exitstate_uniq": uniq("exitstate"),
    }
    for key in ("A8ED50", "B0CE88", "87E8E0"):
        vals = [s.get(key) for s in ok if s.get(key) is not None]
        p[key] = {
            "n": len(vals),
            "first": vals[0] if vals else None,
            "last": vals[-1] if vals else None,
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "n_distinct": len(set(vals)),
        }
    return p


def analyze(a):
    runs = []
    for run_no in (1, 2, 3):
        nd = OUT / ("run%d.ndjson" % run_no)
        mp = OUT / ("run%d_meta.json" % run_no)
        if not nd.exists() or not mp.exists():
            runs.append({"run": run_no, "missing": True})
            continue
        meta = json.loads(mp.read_text(encoding="utf-8"))
        samples, events = load_ndjson(str(nd))
        phases = {ph: phase_stats(samples, ph) for ph in PHASE_ORDER}
        mapinfo = meta.get("map") or {}
        ev_map = next((e for e in events if e.get("event") == "map_selected"), None)
        runs.append({
            "run": run_no, "meta": meta, "phases": phases,
            "pid": meta.get("pid"), "is32": meta.get("is32"),
            "game_tid": meta.get("game_tid"),
            "map_index": mapinfo.get("index"),
            "display_name": mapinfo.get("display_name"),
            "n_items": mapinfo.get("n_items"),
            "n_hits": mapinfo.get("n_hits"),
            "noname_indices": mapinfo.get("noname_indices"),
            "ingame_detected": (meta.get("battle_gate") or {}).get("detected"),
            "phase_stop": meta.get("phase_stop"),
            "residual_after": meta.get("residual_after"),
            "restore_ok": all(
                r.get("sha_match") and r.get("byte_identical_to_baseline")
                for r in (meta.get("restore_rows") or [])
                if r.get("file") in RESTORE_FILES),
            "prelaunch_match": all(
                v.get("match") for v in (meta.get("prelaunch_hashes") or {}).values()),
        })
    summary = {"generated_utc": utc_iso(), "run_id": RUN_ID, "runs": runs}
    (OUT / "analyze_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True,
                   default=str), encoding="utf-8")
    log("[A] analyze_summary.json 已写出")
    return summary


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, default=0,
                    help="1..3 执行单趟；0 = 不执行")
    ap.add_argument("--map-pattern", default="Proving Grounds")
    ap.add_argument("--ingame-seconds", type=float, default=75.0)
    ap.add_argument("--ingame-interval-ms", type=float, default=30.0)
    ap.add_argument("--pre-interval-ms", type=float, default=250.0)
    ap.add_argument("--menu-timeout", type=float, default=120.0)
    ap.add_argument("--load-timeout", type=float, default=180.0)
    ap.add_argument("--min-load-s", type=float, default=15.0,
                    help="StartGame 后最短加载时间（秒），速率门控在此之后才生效")
    ap.add_argument("--battle-rate", type=float, default=28.0,
                    help="局内速率签名阈值（计数/s，2s 窗）；加载段实测 ~21–25")
    ap.add_argument("--rate-high-s", type=float, default=5.0,
                    help="速率持续超过阈值多少秒判定进入局内")
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.analyze:
        analyze(a)
        return 0
    if not a.run:
        print("usage: --run 1..3 或 --analyze")
        return 3
    exit_code, meta = run_one(a)
    log("[MAIN] run%d exit_code=%d pid=%s map_index=%s phase_stop=%s" %
        (a.run, exit_code, meta.get("pid"),
         (meta.get("map") or {}).get("index"), meta.get("phase_stop")))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

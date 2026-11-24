#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W13 —— RE-N04b 长时漂移测试（单趟，目标 600 s）。

任务（RE-N04b）：
  载体 [8]试验地_Pro_ProvingGrounds.yrm（钉定哈希 3e3c8745…bfd5b19，按名称子串
  "Proving Grounds" 选图，禁固定索引）。从「开局后首个 frame>0」起连续采样 ≥600 s，
  30 ms/拍，检验 0xA8ED84 帧计数的「区间推进速率」是否随对局推进而向下漂移。

★ 固定口径（必须写进报告 §0）：
  1. [0xA8ED84] 的速率是「计数/s」，不是帧率/FPS；「变慢」只能表述为
     「区间推进速率下降 x%」。
  2. 30 ms 轮询非逐帧采样 ⇒ 不算逐帧 P95/P99 / 帧时间 / 1% low。
  3. 无经校验的单位计数 ⇒ 不用文件名宣称负载；A8ED50/B0CE88/87E8E0 语义未定，
     不写成「单位数」。
  4. 无干净零售 1.001 对照臂 ⇒ 单臂；不出现「原版对比」「优化收益」。
  5. 停推 ≠ 卡顿；frame 长时间不变先看闲置态线索（win_foreground / 输入证据）。
     mode[0xA8B238] 区分不了 加载/局内/退出后闲置（全 5），只记录不当门控。
  6. ra2youli 文件名含 [ ] ⇒ PowerShell 用 -LiteralPath；Python glob 用 glob.escape
     （本脚本全部用 Path 直拼字面名，不经 glob）。

★ 本卡预设（开工前固定，不得事后改）：
  * 采样段 = StartGame 后首个 frame>0 起至 自然结束/600s 目标；段内零按键、零切窗、
    零干预。置前动作（Alt+SetForegroundWindow）在 StartGame 点击**之前**完成，
    其后本进程零输入；GetLastInputInfo 每秒留痕作为零输入证据。
  * 有效局内段（主判据段）= 上述采样段（含加载尾；W7 已证加载段速率≈局内 ~31.2/s，
    20s/600s 的尾部不足以制造伪漂移，如实披露）。另设敏感性段 = W12 同口径门
    （首帧>0 后 elapsed≥15s 且 2s 窗速率≥28/s 持续 5s）至段末。
  * 漂移判据：10 s 窗速率（真实 t_mono_ns Δframe/Δt），有效窗（真实 Δt≥8.0s）按序取
    n3=N//3，首 1/3 vs 末 1/3 中位；降幅 >0.5% ⇒ 候选下行漂移；≤0.5%（含上升）⇒
    未观测到漂移。斜率 = 全有效窗 rate~窗序号最小二乘（计数/s per 10 s）。
  * 拐点（若判漂移）= 首个 rate < 0.995×median(首 1/3) 的有效窗；只给相关不归因。
  * 自然结束判定：UI 巡检（1s 周期）连续 2 次发现 text 含 "continue"（不分大小写）
    的可见 Button ⇒ 自然结束；或进程退出。结束后继续采样 20 s（phase=post_end，
    不计入有效局内段），不重启补测。
  * 停推段 = 连续 ok 拍 frame 相同且真实跨度 ≥1.0s；逐段标 win_foreground 与输入证据；
    无输入下的停推记「未知原因的停推」，不得归因卡顿。
  * read_status=fail 拍保留、不填补。
  * 重试规则：仅当失败严格发生在首个 frame>0 之前（启动/导航基础设施问题）允许 1 次
    重试；采样开始后任何终止均为最终。

授权：启动 ra2youli/gamemd.exe、只读 ReadProcessMemory、枚举窗口、发消息/点控件
（仅导航/选图/开局阶段）。禁止：SuspendThread/StackWalk64/MiniDump/断点/注入/写目标
进程内存/改 exe/dll/hook；禁止增删改 ra2youli 文件（配置还原除外，为卡面要求）。
只处理自己启动的 pid；启动前有 gamemd 残留 ⇒ 停手报告。

写域：仅 lead/next_re_20261112_r02/W13_longrun_drift/（本文件与 out/）+ 实例锁
（授权例外：开工 owner=本代理，收尾恢复 owner=lead）。

用法：
  python -X utf8 longrun_probe.py                    # 单趟 600 s
  python -X utf8 longrun_probe.py --target-seconds 600 --interval-ms 30
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
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
W13 = ROOT / "lead" / "next_re_20261112_r02" / "W13_longrun_drift"
OUT = W13 / "out"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"
LOCK_PATH = ROOT / "lead" / "next_re_20261112_r02" / ".game_instance.lock"
SELF_OWNER = "W13-longrun-drift-subagent"
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

# 载体钉定（卡面口径 3e3c8745…bfd5b19 / 175,361 B，开工前实算一致）
PG_FILENAME = "[8]试验地_Pro_ProvingGrounds.yrm"
PG_SHA256 = "3e3c874572bc02199cddce05b3633888caf968e6fbb457e763fb70b9fbfd5b19"
PG_BYTES = 175361

# ★ Lead 三起点交叉解码确认的地址（只读；禁止改动）——与 W7/W12 完全一致
ADDR = {
    "frame":        (0x00A8ED84, 4),   # dword 帧计数（0x55DE81 处 inc）；速率=计数/s，非 FPS
    "mode_A8B238":  (0x00A8B238, 4),   # dword 模式枚举（intro/主菜单=0，会话启动后=5）
    "g1":           (0x00A83D49, 1),   # byte 门控1
    "g2":           (0x00A8ECD0, 1),   # byte 门控2
    "g3":           (0x008B41C0, 1),   # byte 门控3（是 0x8B41C0，不是 0x41C0）
    "g4":           (0x00A83D48, 1),   # byte 门控4
    "A8E9A0":       (0x00A8E9A0, 1),   # byte 循环活动/局内标志（候选读数）
    "ABCD58":       (0x00ABCD58, 1),   # byte 帧处理闩（候选读数）
    "exitstate":    (0x00A8EDD8, 4),   # dword 既有登记的退出态（辅助）
    "A8ED50":       (0x00A8ED50, 4),   # ★候选代理（语义未定；W7 实测恒 0）
    "B0CE88":       (0x00B0CE88, 4),   # ★候选代理（语义未定）
    "87E8E0":       (0x0087E8E0, 4),   # ★候选代理（语义未定，可回绕）
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
GRACE_S = 20.0            # 自然结束后的补采时长（phase=post_end，不计入有效局内段）
GATE_RATE = 28.0          # W12 同口径敏感性门：2s 窗速率阈值（计数/s）
GATE_MIN_S = 15.0         # W12 同口径敏感性门：最短 elapsed
GATE_HOLD_S = 5.0         # W12 同口径敏感性门：速率持续时长

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


# ------------------------------------------------------------------ Win32 绑定（W7/W12 同）
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
    ("GetLastInputInfo", wt.BOOL, [ctypes.c_void_p]),
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


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


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


def fg_is(pid):
    fg = u.GetForegroundWindow()
    p = wt.DWORD(0)
    u.GetWindowThreadProcessId(fg, ctypes.byref(p))
    return p.value == pid


def last_input_dwtime():
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if u.GetLastInputInfo(ctypes.byref(lii)):
        return int(lii.dwTime)
    return None


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
    """逐条写 NDJSON；每行 flush。线程安全（W13 双线程写，外加锁）。"""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.f = self.path.open("w", encoding="utf-8", newline="\n")
        self.n_lines = 0
        self.lock = threading.RLock()   # 可重入：ui_watcher 在持锁段内也要写事件

    def write(self, rec):
        line = json.dumps(rec, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), default=str)
        with self.lock:
            self.f.write(line + "\n")
            self.f.flush()
            self.n_lines += 1
        return rec

    def close(self):
        with self.lock:
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


def parse_ini_sections(path, sections):
    """逐字抓取指定节的 key=value（不做语义解读；找不到的节/键记 null）。"""
    out = {}
    try:
        cur = None
        for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith(";"):
                continue
            m = re.match(r"^\[(.+)\]$", line)
            if m:
                cur = m.group(1)
                continue
            if cur in sections and "=" in line:
                k, v = line.split("=", 1)
                out.setdefault(cur, {})[k.strip()] = v.strip()
    except Exception as e:
        out["_error"] = repr(e)
    return {s: out.get(s) for s in sections}


def capture_conditions():
    """统一条件逐字记录（开工前哈希守卫已保证 live==baseline 逐字节一致，此处读 live 自证）。"""
    ra2 = parse_ini_sections(GAME_DIR / "RA2MD.INI",
                             ["Intro", "MultiPlayer", "Skirmish", "Options",
                              "Video", "Audio"])
    ddr = parse_ini_sections(GAME_DIR / "ddraw.ini", ["ddraw", "gamemd", "ra2md"])
    note = ("难度/速度键的段位语义未解码，仅逐字记录；[Skirmish] 节为遭遇战局设置来源；"
            "skirmish 对话框内难度/席位等 UI 态不在本 INI 键集内（见 UNCOVERED）。"
            "窗口模式：ddraw windowed=false+fullscreen=false+width/height=0 ⇒ 全屏路径，"
            "游戏内部分辨率由 RA2MD [Video] 决定。")
    return {"RA2MD.INI": ra2, "ddraw.ini": ddr, "note": note}


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
        mm = re.search(r"(\d+)\|(\d+)", line)
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


def select_map_by_name(hproc, pid, patterns):
    """按名称子串选中（禁固定索引）。patterns 依次尝试，取第一个有命中的模式；
    多命中时优先名称里含所有模式词的条目。记录条目总数 / 命中明细 / 空名条目审计。"""
    if not click(pid, "GUI:ChooseMap", 3.0):
        raise RuntimeError("GUI:ChooseMap 点击失败")
    lb, n = find_maplist(pid)
    log("    地图 ListBox=%s 条目=%d" % (lb, n))
    if not lb:
        raise RuntimeError("未拿到地图列表")
    names = read_map_names(hproc, lb, n)
    noname = [i for i, s in names if not s]
    chosen = None
    used_pattern = None
    all_hits = {}
    for pat in patterns:
        p = pat.lower()
        hits = [(i, s) for i, s in names if s and p in s.lower()]
        all_hits[pat] = len(hits)
        if hits:
            words = p.split()
            best = [hs for hs in hits
                    if all(w in (hs[1] or "").lower() for w in words)]
            pick = (best or hits)[0]
            chosen, used_pattern = pick, pat
            log("    模式 %r 命中 %d 个，取 [%d] %r" % (pat, len(hits), pick[0], pick[1]))
            for i, s in hits[:20]:
                log("      命中明细 [%3d] %r" % (i, s))
            break
    log("    含模式命中统计=%s；空名/乱码条目 %d 个（索引 %s）" %
        (all_hits, len(noname), noname[:20]))
    if chosen is None:
        raise RuntimeError("地图列表中没有名称命中任何模式 %r" % (patterns,))
    idx, disp = chosen
    log("    LB_SETCURSEL(%d) -> %s  显示名=%r" %
        (idx, smt(lb, LB_SETCURSEL, idx), disp))
    time.sleep(0.6)
    if not click(pid, "GUI:UseMap", 3.0):
        raise RuntimeError("GUI:UseMap 未点击成功")
    return {"index": idx, "display_name": disp, "n_items": n,
            "pattern_used": used_pattern, "pattern_hits": all_hits,
            "hits": [{"index": i, "name": s} for i, s in
                     ([(j, s2) for j, s2 in names
                       if s2 and used_pattern.lower() in s2.lower()])][:20],
            "noname_indices": noname, "patterns": list(patterns)}


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


# ------------------------------------------------------------------ UI 巡检线程（1s 周期，只读）
def ui_watcher(pid, hproc, sink, stop_flag, state):
    """每秒：按钮扫描（自然结束判定）、前台、进程存活、GetLastInputInfo 零输入留痕。
    只读操作；采样段内本线程不做任何输入。"""
    while not stop_flag["stop"]:
        try:
            t_ns = time.perf_counter_ns()
            btns = [(t, bool(v)) for (h, c, t, v) in controls(pid) if c == "Button"]
            vis_texts = [t for (t, v) in btns if v]
            cont = [t for t in vis_texts if "continue" in (t or "").lower()]
            fg = fg_is(pid)
            li = last_input_dwtime()
            ec = wt.DWORD(0)
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            rec = {"kind": "ui_watch", "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "win_foreground": fg, "alive": alive,
                   "button_texts_visible": vis_texts,
                   "continue_hits": cont,
                   "last_input_dwtime": li}
            sink.write(rec)
            prev = state.get("prev_cont_hits")
            with sink.lock:
                if cont and prev and state.get("natural_end_t") is None:
                    state["natural_end_t"] = t_ns
                    state["natural_end_buttons"] = cont
                    sink.write({"kind": "event", "seq": -1, "t_mono_ns": t_ns,
                                "t_utc_iso": utc_iso(), "event": "natural_end",
                                "detail": {"buttons": cont,
                                           "rule": "连续 2 次 ui_watch（间隔≈1s）"
                                                   "发现可见 continue 类 Button"}})
                if not alive and state.get("proc_exit_t") is None:
                    state["proc_exit_t"] = t_ns
                    sink.write({"kind": "event", "seq": -1, "t_mono_ns": t_ns,
                                "t_utc_iso": utc_iso(), "event": "process_exited_watch",
                                "detail": {"exit_code": ec.value}})
                state["prev_cont_hits"] = cont
            if state.get("proc_exit_t") is not None:
                break
        except Exception as e:
            sink.write({"kind": "event", "seq": -1,
                        "t_mono_ns": time.perf_counter_ns(),
                        "t_utc_iso": utc_iso(), "event": "watcher_error",
                        "detail": repr(e)})
        time.sleep(1.0)


# ------------------------------------------------------------------ 单趟主流程
def run_one(a, attempt):
    ndjson_path = OUT / "run.ndjson"
    meta_path = OUT / "meta.json"
    sink = NDJSONSink(ndjson_path)
    started_utc = utc_iso()
    exit_code = 0
    pid, launcher_pid, own = 0, 0, ""
    hproc = None
    game_hwnd, game_tid = 0, None
    is32 = None
    map_info = None
    prelaunch_hashes = {}
    conditions = {}
    stop_flag2 = {"stop": True}          # 先置停；S4 起跑时重开，finally 兜底再停
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    meta = {
        "run_id": RUN_ID, "card": "RE-N04b W13 longrun drift (single run)",
        "attempt": attempt,
        "ndjson": str(ndjson_path), "started_utc": started_utc,
        "args": {k: getattr(a, k) for k in vars(a)},
        "addresses": {k: [hex(ad), sz] for k, (ad, sz) in ADDR.items()},
        "baseline_hashes": BASELINE_HASHES,
        "carrier": {"expected_filename": PG_FILENAME, "expected_bytes": PG_BYTES,
                    "expected_sha256": PG_SHA256,
                    "sha256": None, "bytes": None},
        "pid": None, "is32": None, "game_hwnd": None, "game_tid": None,
        "map": None, "code_signature_ok": None, "prelaunch_hashes": {},
        "conditions": {}, "residual_before": [], "residual_after": [],
        "close_steps": [], "error": None, "n_samples": 0, "n_read_fail": 0,
        "phase_stop": None,
        "predeclared_analysis_plan": {
            "primary_segment": "有效局内段=phase=ingame（开局后首个 frame>0 起）至"
                               "自然结束或 600s 目标；含加载尾（W7: 加载速率≈局内 "
                               "~31.2/s，尾部占比 ~3%，如实披露，不作为门控）",
            "secondary_segment": "敏感性段=W12 同口径门（首帧>0 后 elapsed≥15s 且 "
                                 "2s 窗速率≥28/s 持续 5s，即 gate_marker 事件）至段末；"
                                 "同一预设阈值 0.5% 重算一遍作对照，不改变分档判据",
            "window_s": 10.0,
            "window_anchor": "段内首个 ok 拍 t_mono_ns，固定 10s 网格；窗边界参考拍="
                             "边界时刻前最后一个 ok 拍（窗与窗共享边界，无缝拼合）",
            "valid_window_rule": "窗内参考两拍真实 Δt ≥ 8.0s 才计入中位/斜率；"
                                 "残窗仍列出标注 partial",
            "third_rule": "有效窗数 N 取 n3=N//3；首 1/3=前 n3 窗，末 1/3=后 n3 窗",
            "drift_threshold_pct": 0.5,
            "drift_def": "drop_pct=(median(首1/3)-median(末1/3))/median(首1/3)*100；"
                         ">0.5 ⇒ 候选下行漂移；≤0.5（含上升）⇒ 未观测到漂移",
            "slope_def": "全有效窗 rate~窗序号 最小二乘斜率（计数/s per 10 s 窗）",
            "knee_def": "判漂移时：首个 rate < 0.995*median(首1/3) 的有效窗；"
                        "只给相关字段变化，不归因",
            "w12_reference_counts_per_s_card": 31.25,
            "w12_reference_counts_per_s_r1r3_median": 31.2484,
            "natural_end_rule": "ui_watch（1s 周期）连续 2 次发现可见 Button text 含 "
                                "'continue'（不分大小写）⇒ 自然结束；或进程退出；"
                                "结束后 grace 20s（phase=post_end）继续采样，不重启",
            "grace_after_end_s": GRACE_S,
            "no_first_frame_timeout_s": 300.0,
            "stall_rule": "连续 ok 拍 frame 相同且真实跨度 ≥1.0s；逐段标 foreground/"
                          "输入证据；无输入下记「未知原因的停推」，不归因卡顿",
            "fail_rule": "read_status=fail 拍保留、不填补",
            "retry_rule": "仅当失败严格发生在首个 frame>0 之前允许 1 次重试；"
                          "采样开始后任何终止均为最终",
            "unit_note": "[0xA8ED84] 速率单位=计数/s，非 FPS；30ms 轮询非逐帧采样",
        },
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
        # ---------- S0 守卫：锁 + 残留 + 哈希 + 载体钉定 ----------
        log("[S0] W13 实例锁 + 残留进程 + 哈希守卫（attempt=%d）" % attempt)
        lock_state = check_lock()
        log("    实例锁 owner 状态 = %s（接管/持有）" % lock_state)
        write_lock("W13 RE-N04b 长时漂移测试 进行中 (attempt %d)" % attempt)
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
        conditions = capture_conditions()
        meta["conditions"] = conditions
        log("    统一条件已记录：Video=%s Skirmish.GameSpeed=%s Options.GameSpeed=%s "
            "Options.Difficulty=%s ddraw.windowed=%s renderer=%s maxfps=%s" %
            (conditions["RA2MD.INI"].get("Video"),
             (conditions["RA2MD.INI"].get("Skirmish") or {}).get("GameSpeed"),
             (conditions["RA2MD.INI"].get("Options") or {}).get("GameSpeed"),
             (conditions["RA2MD.INI"].get("Options") or {}).get("Difficulty"),
             (conditions["ddraw.ini"].get("ddraw") or {}).get("windowed"),
             (conditions["ddraw.ini"].get("ddraw") or {}).get("renderer"),
             (conditions["ddraw.ini"].get("gamemd") or {}).get("maxfps")))

        # 载体钉定：必须是钉定哈希/字节数的 Proving Grounds
        carrier_path = GAME_DIR / PG_FILENAME
        if not carrier_path.exists():
            raise GuardStop("载体文件缺失 %s" % carrier_path)
        csha = sha256_file(carrier_path)
        cbytes = carrier_path.stat().st_size
        meta["carrier"] = {"expected_filename": PG_FILENAME,
                           "expected_bytes": PG_BYTES, "expected_sha256": PG_SHA256,
                           "sha256": csha, "bytes": cbytes}
        log("    载体 %s %d B sha=%s" % (PG_FILENAME, cbytes, csha))
        if csha != PG_SHA256 or cbytes != PG_BYTES:
            raise GuardStop("载体哈希/字节数与钉定值不一致，停手")

        inventory_before = inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                    "predeclared_analysis_plan": meta["predeclared_analysis_plan"],
                    "prelaunch_hashes": prelaunch_hashes, "carrier": meta["carrier"],
                    "residual_before": residual_before, "conditions": conditions,
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

        th = threading.Thread(target=pre_sampler, daemon=True)
        th.start()
        try:
            if not click(pid, "GUI:SinglePlayer", 3.0):
                raise RuntimeError("GUI:SinglePlayer 点击失败")
            if not click(pid, "GUI:Skirmish", 3.5):
                raise RuntimeError("GUI:Skirmish 点击失败")
            map_info = select_map_by_name(hproc, pid, a.map_patterns)
        finally:
            stop_flag["stop"] = True
            th.join(timeout=5.0)
        meta["map"] = map_info
        ev("map_selected", {"index": map_info["index"],
                            "display_name": map_info["display_name"],
                            "n_items": map_info["n_items"],
                            "pattern_used": map_info["pattern_used"],
                            "pattern_hits": map_info["pattern_hits"],
                            "noname_indices": map_info["noname_indices"],
                            "patterns": map_info["patterns"]})

        # ---------- S3 置前（开局阶段允许的最后输入）→ StartGame ----------
        ok = force_foreground(meta["game_hwnd"])
        ff_t = time.perf_counter_ns()
        li_after_ff = last_input_dwtime()
        log("[S3] 置前游戏窗口 -> %s（此后本进程零输入，StartGame 待发）" % ok)
        ev("foreground_forced", {"ok": ok, "last_input_dwtime_after": li_after_ff,
                                 "note": "置前=开局阶段允许输入的最后一次；"
                                         "其后采样段零按键/零切窗/零干预"})
        if not click(pid, "GUI:StartGame", 0.0):
            raise RuntimeError("GUI:StartGame 点击失败")
        sg_t = time.perf_counter_ns()
        ev("startgame_clicked", {"t_mono_ns": sg_t})
        log("    StartGame 已点击；等待首个 frame>0")

        # ---------- S4 采样段：首个 frame>0 起，≥600s @30ms，零干预 ----------
        stop_flag2 = {"stop": False}
        state = {"prev_cont_hits": [], "natural_end_t": None,
                 "natural_end_buttons": None, "proc_exit_t": None}
        watcher = threading.Thread(target=ui_watcher,
                                   args=(pid, hproc, sink, stop_flag2, state),
                                   daemon=True)
        watcher.start()
        ev("sampling_watch_started", {"cadence_s": 1.0,
                                      "zero_input_from": utc_iso()})
        seq = 0
        t_first_pos = None
        t_gate = None
        win = collections.deque()            # (t_ns, frame) 最近 ~2s 窗（gate 标记用）
        rate_high_since = None
        stop_reason = None
        last_prog = -1
        post_end_until = None
        while True:
            vals, failed = read_all(hproc)
            seq += 1
            t_ns = time.perf_counter_ns()
            ec = wt.DWORD(0)
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            if not alive:
                stop_reason = "process_exited_during_sampling"
                ev("process_exited", {"phase": "sampling", "exit_code": ec.value})
                break
            with sink.lock:
                net_end_t = state.get("natural_end_t")
            phase = "post_start"
            if t_first_pos is None and vals is not None \
                    and vals.get("frame", 0) > 0 and t_ns > sg_t:
                t_first_pos = t_ns
                ev("first_frame_positive",
                   {"frame": vals["frame"], "after_startgame_s":
                       round((t_ns - sg_t) / 1e9, 6)})
                log("    首个 frame>0（frame=%d，StartGame 后 %.3fs）⇒ 采样计时起点"
                    % (vals["frame"], (t_ns - sg_t) / 1e9))
            if t_first_pos is not None:
                if net_end_t is not None and t_ns >= net_end_t:
                    phase = "post_end"
                    if post_end_until is None:
                        post_end_until = net_end_t + int(GRACE_S * 1e9)
                else:
                    phase = "ingame"
            elapsed = ((t_ns - t_first_pos) / 1e9) if t_first_pos is not None \
                else round((t_ns - sg_t) / 1e9, 6)
            rec = {"seq": seq, "kind": "sample", "phase": phase,
                   "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "elapsed_s": round(elapsed, 6),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed, "win_foreground": fg_is(pid)}
            for k in ADDR:
                rec[k] = vals.get(k) if vals is not None else None
            sink.write(rec)
            # gate 标记（W12 同口径，敏感性段起点；不作采样门控）
            if t_first_pos is not None and t_gate is None and vals is not None:
                f = vals["frame"]
                win.append((t_ns, f))
                while len(win) > 1 and t_ns - win[0][0] > 2.0e9:
                    win.popleft()
                if len(win) >= 2 and t_ns - win[0][0] >= 1.8e9:
                    r = (f - win[0][1]) / ((t_ns - win[0][0]) / 1e9)
                    el = (t_ns - t_first_pos) / 1e9
                    if r >= GATE_RATE and el >= GATE_MIN_S:
                        if rate_high_since is None:
                            rate_high_since = t_ns
                        if (t_ns - rate_high_since) / 1e9 >= GATE_HOLD_S:
                            t_gate = t_ns
                            ev("gate_marker_w12_style",
                               {"after_first_frame_s": round(el, 3),
                                "rate_2s": round(r, 3),
                                "note": "敏感性段起点标记；不影响采样"})
                    else:
                        rate_high_since = None
            # 终止条件
            if t_first_pos is None and (t_ns - sg_t) / 1e9 >= 300.0:
                stop_reason = "no_first_frame_positive_timeout"
                ev("no_first_frame_timeout", {"after_startgame_s":
                                              round((t_ns - sg_t) / 1e9, 3)})
                break
            if t_first_pos is not None:
                if elapsed >= a.target_seconds:
                    stop_reason = "target_reached"
                    break
                if post_end_until is not None and t_ns >= post_end_until:
                    stop_reason = "natural_end_grace_done"
                    break
            prog = int(elapsed // 30)
            if t_first_pos is not None and prog != last_prog:
                last_prog = prog
                log("    [采样] t=%.0fs frame=%s fg=%s gate=%s" %
                    (elapsed, vals.get("frame") if vals else None,
                     rec["win_foreground"], t_gate is not None))
            time.sleep(a.interval_ms / 1000.0)
        stop_flag2["stop"] = True
        dur_sampling = ((time.perf_counter_ns() - t_first_pos) / 1e9
                        if t_first_pos is not None else 0.0)
        log("[S4] 采样段结束：reason=%s 有效局内段=%.1fs seq=%d gate=%s "
            "natural_end=%s" % (stop_reason, dur_sampling, seq,
                                t_gate is not None,
                                state.get("natural_end_t") is not None))
        ev("sampling_end", {"reason": stop_reason,
                            "ingame_duration_s": round(dur_sampling, 3),
                            "n_samples": seq,
                            "gate_marker_set": t_gate is not None,
                            "natural_end": state.get("natural_end_t") is not None,
                            "natural_end_buttons":
                                state.get("natural_end_buttons")})
        meta["phase_stop"] = stop_reason
        meta["sampling"] = {
            "first_frame_positive_t_mono_ns": t_first_pos,
            "startgame_clicked_t_mono_ns": sg_t,
            "foreground_forced_t_mono_ns": ff_t,
            "gate_marker_t_mono_ns": t_gate,
            "natural_end_t_mono_ns": state.get("natural_end_t"),
            "natural_end_buttons": state.get("natural_end_buttons"),
            "proc_exit_t_mono_ns": state.get("proc_exit_t"),
            "stop_reason": stop_reason,
            "ingame_duration_s": round(dur_sampling, 3),
            "target_seconds": a.target_seconds,
            "interval_ms": a.interval_ms,
            "grace_after_end_s": GRACE_S,
            "n_samples_total": seq,
        }
        if t_first_pos is None:
            raise RuntimeError("StartGame 后 %ss 内未出现 frame>0，本趟按失败收尾"
                               % a.target_seconds)

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
        try:
            stop_flag2["stop"] = True          # 兜底停 UI 巡检线程
        except Exception:
            pass
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
        try:
            log("[P1] W13 收尾：关闭自启动实例")
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
            (OUT / "probe_stdout.txt").write_text(
                "\n".join(LOG_LINES) + "\n", encoding="utf-8")
        except Exception:
            pass

        # ---- 恢复实例锁 owner=lead（卡面硬要求；探针 self-heal 链最后一环） ----
        try:
            lock_owner_now = None
            try:
                for line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
                    if line.startswith("owner="):
                        lock_owner_now = line.split("=", 1)[1].strip()
            except Exception:
                pass
            if lock_owner_now == SELF_OWNER:
                LOCK_PATH.write_text(
                    "run_id=%s\nowner=%s\ntime=%s\npurpose=%s\n"
                    % (RUN_ID, LEAD_OWNER,
                       datetime.datetime.now().astimezone().isoformat(),
                       "W13 RE-N04b 探针收尾自愈：恢复 owner=lead"),
                    encoding="utf-8")
                meta["lock_restored"] = True
                log("    实例锁已恢复 owner=lead")
            else:
                meta["lock_restored"] = False
                meta["lock_owner_at_cleanup"] = lock_owner_now
                log("    实例锁 owner=%r 非本代理持有，不动（如实记录）" % lock_owner_now)
        except Exception as e:
            meta["lock_restored"] = False
            meta["lock_restore_error"] = repr(e)
            log("    恢复锁异常 %r" % e)

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
                        "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                        "exit_code": exit_code, "error": meta["error"],
                        "residual_after": residual_after})
        except Exception:
            pass
        sink.close()
        log("[P1] W13 收尾完成（配置已还原，NDJSON=%d 行）" % sink.n_lines)
        meta["n_ndjson_lines"] = sink.n_lines
        try:
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True,
                           default=str), encoding="utf-8")
        except Exception:
            pass
    return exit_code, meta


# ------------------------------------------------------------------ main
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--map-patterns", nargs="+",
                    default=["Proving Grounds"],
                    help="按名称子串选图的模式序列（依次尝试，禁固定索引）")
    ap.add_argument("--target-seconds", type=float, default=600.0,
                    help="采样段目标时长（卡要求 ≥600s，从首个 frame>0 起算）")
    ap.add_argument("--interval-ms", type=float, default=30.0)
    ap.add_argument("--pre-interval-ms", type=float, default=250.0)
    ap.add_argument("--menu-timeout", type=float, default=120.0)
    ap.add_argument("--attempt", type=int, default=1,
                    help="尝试序号（基础设施失败重试时递增，写进 meta）")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    exit_code, meta = run_one(a, attempt=a.attempt)
    log("[MAIN] W13 exit_code=%d pid=%s map_index=%s display=%r phase_stop=%s "
        "ingame_s=%s" %
        (exit_code, meta.get("pid"),
         (meta.get("map") or {}).get("index"),
         (meta.get("map") or {}).get("display_name"),
         meta.get("phase_stop"),
         (meta.get("sampling") or {}).get("ingame_duration_s")))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

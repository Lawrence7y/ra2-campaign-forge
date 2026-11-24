#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""NEXT_RE_20261112_R02 / W19 —— RE-N04h 高「单位/步兵」载体（LoadBench U800）CPU 负载对照。

★ B″ 臂载体（开工前钉定，开工实算核对）：[2]0LoadBench_U0800.yrm，48,745 B，
  sha256 ac0881fdaf16767d053ef8e6f704fd2303f2dd67c5ce8846fb6881e740f421e0。
  离线实读 [Basic]：Name="[2] 0LoadBench U800"（Official=no / MaxPlayer=2 /
  MinPlayer=2 / MultiplayerOnly=1 / GameMode=standard / Player=Russians）。
  离线逐段计数：[Units, 480]=480 条、[Infantry, 320]=320 条、无 [Structures] 段
  （=0）⇒ 声明合计 800（全库最高）。探针 S0 再次实读并核对，Name 不一致 ⇒ 停手。
  ★ 选图纪律：地图列表按显示名（=[Basic].Name）匹配，禁文件名匹配（文件名含
  [ ]，PowerShell 需 -LiteralPath）。W17 白名单实测该显示名在 268 条 skirmish
  列表条目中唯一命中（索引 96；W12 R4 以此索引成功进图，速率 31.2498 计数/s
  ⇒ 可达）。本卡仍实测确认，命中数 >1 时如实记录并说明取舍，无法区分则停手。

★ 缺口（本卡动机）：W12 R4 只测过 U800 的帧速率（31.2498，对负载不敏感的无效
  仪器），从未测过 CPU；「单位/步兵数量」维度从未被 CPU 通道测过。本卡补洞：
  问题 = 480 车 + 320 步兵的声明量是否转化为运行对象并压出 CPU？

★ 单变量纪律：与 A 臂（W15，[8] Proving Grounds，52 建筑）/ B′ 臂（W18，HexBay，
  144 建筑）仅地图不同；配置基线 baseline_pre_launch/ 逐字节一致；启动/导航/
  采样协议与 W15/W18 相同。
  A 臂基线（W15 实测，对照锚点）：cycle 每拍中位 1.691 ms；占用率 5.39% 单核；
  拍率 31.2492 计数/s；拍间隔均值 32.000 ms、≥64 ms 间隔 0；有效段 240.006 s。
  HexBay 臂（W18 实测，并列锚点）：cycle 每拍中位 1.767 ms（+4.5% vs A）；占用率
  5.67%；cyc_per_ms 自标定 3,311,138；A8ED50 全程 0。
  ★ 判据（预设，不得事后改）：[成功造出压力] = U800 每拍 CPU 中位 > 2.54 ms
  （A×1.5）或占用率 > 10%；[无显著差异] = 相对 A 差 < 20%；[中间地带] =
  20%–50%；[U800 不可用] = 未进图或有效段 < 90 s（如实记录，不重启凑时长）。

★ 必须避开的坑（Lead 卡面 + 本会话实测教训，已内建）：
  1) mode[0xA8B238] 不能判进图（加载/局内/退出后闲置全为 5）⇒ 进图判据 =
     frame 以 ≈29–32 计数/s 持续 ≥60 s。
  2) GetThreadTimes 记账量子 15.625 ms（本机 828 个非零 Δ 全为该值）⇒ FILETIME
     通道只作交叉核对；主判读通道 = cycle（QueryThreadCycleTime）。
  3) ★ 周期系数单位勘误（Lead 已在 W15 卡面写错）：3.104e9 是 cyc/s（≈3.104 GHz
     时钟频率），不是 cyc/ms；cyc/ms ≈ 3.1e6（W18 实测自标定 3,311,138）。
     本探针不硬编码任何 cyc/ms 判读常数：逐拍只记 win_cyc_delta 原始值，
     cyc_est_ms_Acorr_provisional = Δ/3.104e6 仅作进度显示旁证（明确标注
     provisional）；全部判读 ms 由 analyze_u800.py 用本趟全段自标定重算
     （cyc_per_ms = Σ逐拍 cycΔ / Σ逐拍 FILETIME CPU ms，量子抵消）。
  4) 文件名含 [ ]：PowerShell 用 -LiteralPath；Python glob 用 glob.escape。
  5) 选图按 [Basic].Name（"[2] 0LoadBench U800"），不用文件名。
  6) 声明量 ≠ 运行实例数 ⇒ 负载只以实测 CPU 为准；不得用声明量推断负载。

★ 关键旁证（必须记录，不得当已证单位数）：0xA8ED50 是既有登记的「注册 Bullet
  对象 Count」候选（语义未证）。W7/W15/W18 三卡它全程为 0。本卡逐拍记录，
  首次 0→非零记事件（a8ed50_first_nonzero）⇒ 单位实例化旁证；若仍全程 0，
  则连"对象存在"都无旁证（如实报告）。

★ 本卡能测 / 测不到（必须写进报告 §0）：
  能测：U800 臂每拍 CPU 消耗分布、占用率、趋势；与 A / HexBay 臂的单变量对照。
  测不到：阻塞类等待（Sleep/Present/vsync/等消息）——CPU 时间不含等待，
          「一拍 CPU 很低」≠「这一拍很快」；「一拍 CPU 很高」才是可靠的重活信号。
  也测不到：GPU 侧耗时、画面掉帧；单位运行实例数无已解码地址（0xA8ED50 语义
          未证，只作旁证描述，不当单位数）。

★ 仪器通道（开工前固定，与 W15/W18 完全一致）：
  主判读：窗口线程 QueryThreadCycleTime 累计，每拍采样取 Δ（周期计数，上下文
          切换粒度，细于时钟节拍记账）。
  交叉核对：窗口线程 GetThreadTimes kernel/user（FILETIME→ms，记账量子
          15.625 ms，只作交叉核对，不得把 0 读作「拍快」）。
  进程级：全线程扫放观察者进程 1Hz（OpenThread+GetThreadTimes 求和+CycleTime；
          NtQuerySystemInformation 另给 ContextSwitches）。不留在采样循环内的
          原因：本机 Toolhelp 全系统线程迭代 ~7600 条 ≈5ms，会周期性污染 6ms
          采样间隔。线程退出时其最后累计值并入 retired，避免漏计。

★ 归属方式（predeclared）：每拍成本 = 相邻两次 frame 递增采样之间
  Δ(win_kernel+win_user) 与 Δ(win_cycle)。递增事件只能以采样粒度观测 ⇒ 归属窗口
  = 1 拍 ± 采样量化（±~6 ms），且窗口线程 CPU 含渲染+消息泵+逻辑（非纯逻辑）。

★ 预设判据（开工前固定，不得事后改）：
  * 采样 6 ms 目标间隔，实测间隔如实报告。
  * 分布主表用 df=1（Δframe=1）的递增事件；df≥2 的全额记单行并标注，不摊分。
  * 热点候选：每拍 CPU ≥ 3×中位 且 ≥ 1.0 ms ⇒ 列前 20。
  * 趋势：10 s 窗 median(每拍CPU)；末 1/3 窗中位 > 首 1/3 窗中位 × 1.2 ⇒ 上升候选。
  * CPU 占用率 = ΔCPU/有效墙钟（窗口线程与进程级各一）；单位=单核百分比。
  * read_status=fail 拍保留不填补；跨 fail 拍的递增不计算（如实计数）。
  * 采样段零输入、零切窗、不进菜单；对局自然结束如实记录、不重启补测；
    有效段 <90 s 判 [U800 不可用]。
  * 不得把 CPU 时间当帧时间/耗时；不得由「CPU 低」推断「拍快」。

★ 结构（attempt2/W14 教训）：本探针由代理经 WMI Win32_Process.Create 独立启动
  （脱离代理进程树）；观察者另起独立 WMI 进程（load_u800_ui_watch.py）。本探针
  finally 自愈收尾：停观察者 → 关游戏 → 核对残留 → 逐字节还原
  RA2MD.INI/ddraw.ini/benchbak 并实算自证 → 写 kind=meta_end → 恢复锁 owner=lead。

授权：启动 ra2youli/gamemd.exe、只读 ReadProcessMemory、OpenThread+GetThreadTimes、
枚举窗口/线程、发消息/点控件（仅导航/选图/开局阶段）。禁止：SuspendThread/
StackWalk64/MiniDump/断点/注入/写目标进程内存/改 exe/dll/hook；禁止增删改
ra2youli 文件（配置还原除外，为卡面要求）。只处理自己启动的 pid；启动前有
gamemd 残留 ⇒ 停手报告。

写域：仅 lead/next_re_20261112_r02/W19_load_U800/（本文件、load_u800_ui_watch.py、
analyze_u800.py、out/）+ 实例锁（授权例外：开工 owner=本代理，收尾恢复 owner=lead）。
源：W15_tick_cpu/tick_cpu_probe.py → W18_load_HexBay/load_hexbay_probe.py 同链
仪器，复制+定向替换生成，逐项核对。

用法：
  python -X utf8 load_u800_probe.py                       # 单趟 240 s @ 6 ms
  python -X utf8 load_u800_probe.py --interval-ms 6 --target-seconds 240
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
import threading
import time
import traceback
from pathlib import Path

RUN_ID = "NEXT_RE_20261112_R02"
ROOT = Path(r"D:\Project\ra2-campaign-forge")
W19 = ROOT / "lead" / "next_re_20261112_r02" / "W19_load_U800"
OUT = W19 / "out"
GAME_DIR = ROOT / "ra2youli"
BASELINE_DIR = ROOT / "lead" / "next_re_20261112_r02" / "baseline_pre_launch"
LOCK_PATH = ROOT / "lead" / "next_re_20261112_r02" / ".game_instance.lock"
SELF_OWNER = "W19-load-U800-subagent"
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

# B″ 臂载体钉定（开工实算 ac0881fd…f421e0 / 48,745 B；离线实读 [Basic].Name="[2] 0LoadBench U800"，
# Official=no / MaxPlayer=2；W17 白名单实测列表索引 96 唯一命中；W12 R4 已以此进图 ⇒ 可达）
BG_FILENAME = "[2]0LoadBench_U0800.yrm"
BG_SHA256 = "ac0881fdaf16767d053ef8e6f704fd2303f2dd67c5ce8846fb6881e740f421e0"
BG_BYTES = 48745
BG_EXPECTED_NAME = "[2] 0LoadBench U800"          # 离线实读的权威 [Basic].Name；S0 再读核对，不一致 ⇒ 停手
BG_DECLARED = {"units": 480, "infantry": 320, "structures": 0}   # 离线逐段计数；S0 再读核对

# ★ Lead 三起点交叉解码确认的地址（只读；禁止改动）——与 W7/W12/W13/W14 完全一致
ADDR = {
    "frame":        (0x00A8ED84, 4),   # dword 帧计数（0x55DE81 处 inc）；32ms 定拍
    "mode_A8B238":  (0x00A8B238, 4),   # dword 模式枚举（intro/主菜单=0，会话启动后=5）
    "g1":           (0x00A83D49, 1),   # byte 门控1
    "g2":           (0x00A8ECD0, 1),   # byte 门控2
    "g3":           (0x008B41C0, 1),   # byte 门控3
    "g4":           (0x00A83D48, 1),   # byte 门控4
    "A8E9A0":       (0x00A8E9A0, 1),   # byte 循环活动/局内标志（候选读数）
    "ABCD58":       (0x00ABCD58, 1),   # byte 帧处理闩（候选读数）
    "exitstate":    (0x00A8EDD8, 4),   # dword 既有登记的退出态（辅助）
    "A8ED50":       (0x00A8ED50, 4),   # ★候选 BulletCnt（卡面口径；首次 0→非零记事件）
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
SWEEP_MS = 320.0          # 全线程扫周期 ≈ 10 逻辑拍（卡面允许的低频方案）
THREAD_QUERY_INFORMATION = 0x0040
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

WATCHER_STOP_FILE = OUT / "watcher_stop.json"
WATCHER_STATE_FILE = OUT / "state.json"
WATCHER_SCRIPT = W19 / "load_u800_ui_watch.py"

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


# ------------------------------------------------------------------ Win32 绑定（W7/W12/W13/W14 同）
u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
winmm = ctypes.WinDLL("winmm")

PF = ctypes.POINTER(wt.FILETIME)

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
k32.GetCurrentProcess.restype = wt.HANDLE
k32.SetPriorityClass.argtypes = [wt.HANDLE, wt.DWORD]

# ---- 自 W15 沿用：线程 CPU 仪器（外部只读） ----
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
# GetThreadTimes 实签名：4 出参 = creation / exit / kernel / user（无 ctx switches）
k32.GetThreadTimes.restype = wt.BOOL
k32.GetThreadTimes.argtypes = [wt.HANDLE, PF, PF, PF, PF]
k32.QueryThreadCycleTime.restype = wt.BOOL
k32.QueryThreadCycleTime.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_ulonglong)]
k32.GetProcessTimes.restype = wt.BOOL
k32.GetProcessTimes.argtypes = [wt.HANDLE, PF, PF, PF, PF]
k32.Thread32First.restype = wt.BOOL
k32.Thread32First.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
k32.Thread32Next.restype = wt.BOOL
k32.Thread32Next.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD), ("szExeFile", ctypes.c_wchar * 260),
    ]


class THREADENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
        ("th32ThreadID", wt.DWORD), ("th32OwnerProcessID", wt.DWORD),
        ("tpDeltaPri", ctypes.c_long), ("dwFlags", wt.DWORD),
        # 本机实测系统要求 dwSize=28（SDK 文档为 24）：补尾随 4 字节
        ("_pad_dwSize28", wt.DWORD),
    ]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("dwTime", wt.DWORD)]


def ft_ms(f):
    """FILETIME(100ns) -> ms。kernel/user 计时即此通道。"""
    return (((int(f.dwHighDateTime) & 0xFFFFFFFF) << 32)
            | (int(f.dwLowDateTime) & 0xFFFFFFFF)) / 1e4


def process_exists(pid):
    snap = k32.CreateToolhelp32Snapshot(0x00000002, 0)
    if not snap or snap == ctypes.c_void_p(-1).value:
        return False
    found = False
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            if int(pe.th32ProcessID) == int(pid):
                found = True
                break
            ok = k32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        k32.CloseHandle(snap)
    return found


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


def list_thread_ids(pid):
    """Toolhelp 全系统线程快照，过滤出 pid 的 tid 列表（失败返回 None）。"""
    snap = k32.CreateToolhelp32Snapshot(0x00000004, 0)   # TH32CS_SNAPTHREAD
    if not snap or snap == ctypes.c_void_p(-1).value:
        return None
    tids = []
    try:
        te = THREADENTRY32W()
        te.dwSize = ctypes.sizeof(THREADENTRY32W)
        ok = k32.Thread32First(snap, ctypes.byref(te))
        while ok:
            if int(te.th32OwnerProcessID) == int(pid):
                tids.append(int(te.th32ThreadID))
            ok = k32.Thread32Next(snap, ctypes.byref(te))
    finally:
        k32.CloseHandle(snap)
    return tids


class ThreadTable(object):
    """pid 全线程 CPU 累计表（外部只读）。

    OpenThread(THREAD_QUERY_INFORMATION) + GetThreadTimes(creation/exit/kernel/user)
    + QueryThreadCycleTime。线程从枚举消失 ⇒ 最后累计值并入 retired 后关闭句柄。
    求和 = 当前线程累计 + retired，覆盖「采样窗内退出」的线程，不漏计。
    """

    def __init__(self, pid):
        self.pid = pid
        self.h = {}                    # tid -> HANDLE
        self.cur = {}                  # tid -> (k_ms, u_ms, cycles)
        self.retired = [0.0, 0.0, 0]   # kernel_ms, user_ms, cycles（已退出线程）
        self.n_open_fail = 0
        self.n_gettimes_fail = 0

    def ensure(self, tid):
        hh = self.h.get(tid)
        if hh:
            return hh
        hh = k32.OpenThread(THREAD_QUERY_INFORMATION, False, tid)
        if hh:
            self.h[tid] = hh
        return hh

    def query_one(self, hh):
        """单个句柄：返回 (kernel_ms, user_ms, cycles) 或 None。"""
        c = wt.FILETIME(); e = wt.FILETIME(); k = wt.FILETIME(); uu = wt.FILETIME()
        if not k32.GetThreadTimes(hh, ctypes.byref(c), ctypes.byref(e),
                                  ctypes.byref(k), ctypes.byref(uu)):
            return None
        cyc = ctypes.c_ulonglong(0)
        okc = k32.QueryThreadCycleTime(hh, ctypes.byref(cyc))
        return (ft_ms(k), ft_ms(uu), (int(cyc.value) if okc else None))

    def sweep(self):
        """全线程扫：返回 dict（None=快照失败）。"""
        tids = list_thread_ids(self.pid)
        if tids is None:
            return None
        tset = set(tids)
        for tid in tids:
            if tid not in self.h:
                hh = k32.OpenThread(THREAD_QUERY_INFORMATION, False, tid)
                if hh:
                    self.h[tid] = hh
                else:
                    self.n_open_fail += 1
        rows = {}
        for tid, hh in list(self.h.items()):
            q = self.query_one(hh)
            if q is None:
                self.n_gettimes_fail += 1
                continue
            rows[tid] = q
        # 枚举中消失的线程：并入 retired 后关闭句柄
        for tid in [t for t in list(self.h.keys()) if t not in tset]:
            last = self.cur.get(tid)
            if last:
                self.retired[0] += last[0]
                self.retired[1] += last[1]
                if last[2]:
                    self.retired[2] += last[2]
            try:
                k32.CloseHandle(self.h.pop(tid))
            except Exception:
                pass
        # GetThreadTimes 仍失败的句柄：保留（可能是瞬时失败），下次重试
        self.cur = {t: rows[t] for t in self.h if t in rows}
        sk = sum(r[0] for r in self.cur.values()) + self.retired[0]
        su = sum(r[1] for r in self.cur.values()) + self.retired[1]
        sc = sum((r[2] or 0) for r in self.cur.values()) + self.retired[2]
        return {
            "t_mono_ns": time.perf_counter_ns(), "t_utc_iso": utc_iso(),
            "n_threads_enum": len(tids), "n_threads": len(self.cur),
            "n_handles": len(self.h),
            "sum_kernel_ms": round(sk, 6), "sum_user_ms": round(su, 6),
            "sum_cpu_ms": round(sk + su, 6), "sum_cycles": int(sc),
            "retired_cpu_ms": round(self.retired[0] + self.retired[1], 6),
            "retired_cycles": int(self.retired[2]),
            "n_open_fail_cum": self.n_open_fail,
            "n_gettimes_fail_cum": self.n_gettimes_fail,
            "threads": {str(t): {"kernel_ms": round(r[0], 6),
                                 "user_ms": round(r[1], 6),
                                 "cpu_ms": round(r[0] + r[1], 6),
                                 "cycles": r[2]}
                        for t, r in sorted(self.cur.items())},
        }

    def close_all(self):
        for hh in self.h.values():
            try:
                k32.CloseHandle(hh)
            except Exception:
                pass
        self.h = {}


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


def win_tid_of(hwnd):
    """★ 用 GetWindowThreadProcessId 的返回值（=tid），不是 lpdwProcessId。"""
    q = wt.DWORD(0)
    ret = u.GetWindowThreadProcessId(hwnd, ctypes.byref(q))
    return int(ret) or None


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
        self.lock = threading.RLock()

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


def read_yrm_carrier(path):
    """★ W19 新增：实读载体 yrm 的 [Basic] 关键键与 [Units]/[Infantry]/[Structures]
    声明计数（GBK 解码；yrm 为 INI 族文本）。Name 为选图权威依据。"""
    try:
        text = Path(path).read_bytes().decode("gbk", errors="replace")
    except Exception as e:
        return {"_error": repr(e)}
    basic, decl, cur = {}, {}, None
    decl_sections = ("Units", "Infantry", "Structures")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            cur = m.group(1)
            if any(cur == s or cur.startswith(s + ",") for s in decl_sections):
                decl.setdefault(cur.split(",")[0].lower(), 0)
            continue
        if cur == "Basic" and "=" in line:
            k, v = line.split("=", 1)
            basic[k.strip()] = v.strip()
        elif cur and "=" in line and any(
                cur == s or cur.startswith(s + ",") for s in decl_sections):
            decl[cur.split(",")[0].lower()] = \
                decl.get(cur.split(",")[0].lower(), 0) + 1
    return {"basic": basic, "declared_counts": decl}


def capture_conditions():
    ra2 = parse_ini_sections(GAME_DIR / "RA2MD.INI",
                             ["Intro", "MultiPlayer", "Skirmish", "Options",
                              "Video", "Audio"])
    ddr = parse_ini_sections(GAME_DIR / "ddraw.ini", ["ddraw", "gamemd", "ra2md"])
    note = ("难度/速度键的段位语义未解码，仅逐字记录；窗口模式：ddraw windowed=false+"
            "fullscreen=false+width/height=0 ⇒ 全屏路径，游戏内部分辨率由 RA2MD [Video] 决定。")
    return {"RA2MD.INI": ra2, "ddraw.ini": ddr, "note": note}


# ------------------------------------------------------------------ 启动 / 导航（W13/W14 已验证实现）
def spawn_wmi_hidden(cmdline, cwd):
    """WMI Win32_Process.Create 启动（隐藏控制台），返回 (cmd_pid, retval)。
    创建的进程父为 WmiPrvSE，脱离本进程树 —— attempt2 教训的硬要求。"""
    esc = cmdline.replace("'", "''")
    ps = ("$su = $null; "
          "try { $su = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly "
          "-Property @{ShowWindow=[uint16]0} } catch { $su = $null }; "
          "if ($su -ne $null) { "
          "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='%s'; CurrentDirectory='%s'; "
          "ProcessStartupInformation=$su} } else { "
          "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{CommandLine='%s'; CurrentDirectory='%s'} }; "
          "Write-Output ('{0}|{1}' -f $r.ProcessId, $r.ReturnValue)"
          % (esc, str(cwd), esc, str(cwd)))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=60)
    # powershell 输出可能是 GBK（本地化错误文本）；utf-8 严格解码会崩读线程
    txt = ((r.stdout or b"") + b"\n--STDERR--\n" + (r.stderr or b"")
           ).decode("utf-8", "replace").strip()
    log("    WMI Create 返回 %r" % txt[:200])
    m = None
    for line in txt.splitlines():
        mm = re.search(r"(\d+)\|(\d+)", line)
        if mm:
            m = mm
            break
    if not m:
        raise RuntimeError("WMI Win32_Process.Create 未返回 pid|retval: %r" % txt[:200])
    return int(m.group(1)), int(m.group(2))


def launch_game():
    cmdline = ('cmd.exe /c cd /d "%s" && start "" "gamemd.exe"' % str(GAME_DIR))
    cmd_pid, retval = spawn_wmi_hidden(cmdline, str(W19))
    if retval != 0:
        raise RuntimeError("WMI Win32_Process.Create 失败 retval=%d" % retval)
    return cmd_pid


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
    """按名称子串选中（禁固定索引）。"""
    if not click(pid, "GUI:ChooseMap", 3.0):
        raise RuntimeError("GUI:ChooseMap 点击失败")
    lb, n = find_maplist(pid)
    log("    地图 ListBox=%s 条目=%d" % (lb, n))
    if not lb:
        raise RuntimeError("未拿到地图列表")
    names = read_map_names(hproc, lb, n)
    noname = [i for i, s in names if not s]
    # W19 (attempt2 教训)：全列表名称落盘 —— 显示名来源必须以实测为准
    try:
        (OUT / "maplist_names.json").write_text(
            json.dumps([{"index": i, "name": s} for i, s in names],
                       ensure_ascii=False, indent=1),
            encoding="utf-8")
        log("    全列表名称已落盘 maplist_names.json（%d 条，空名 %d 个）"
            % (len(names), len(noname)))
        probe_hits = [(i, s) for i, s in names
                      if s and any(k in s.lower() for k in
                                   ("loadbench", "u800", "u0800"))]
        for i, s in probe_hits[:20]:
            log("      探针关键词命中 [%3d] %r" % (i, s))
    except Exception as e:
        log("    maplist_names.json 落盘异常 %r" % e)
    chosen = None
    used_pattern = None
    all_hits = {}
    for pat in patterns:
        p = pat.lower()
        exact = [(i, s) for i, s in names if s and s.lower() == p]
        hits = [(i, s) for i, s in names if s and p in s.lower()]
        all_hits[pat] = len(hits)
        if not hits:
            continue
        if exact:
            pick = exact[0]
            log("    模式 %r 精确命中 %d 个，取 [%d] %r" %
                (pat, len(exact), pick[0], pick[1]))
        else:
            words = p.split()
            best = [hs for hs in hits
                    if all(w in (hs[1] or "").lower() for w in words)]
            pick = (best or hits)[0]
            log("    模式 %r 子串命中 %d 个（无精确命中），取 [%d] %r" %
                (pat, len(hits), pick[0], pick[1]))
        chosen, used_pattern = pick, pat
        for i, s in hits[:20]:
            log("      命中明细 [%3d] %r" % (i, s))
        break
    log("    含模式命中统计=%s；空名/乱码条目 %d 个（索引 %s）" %
        (all_hits, len(noname), noname[:20]))
    if chosen is None:
        for i, s in names[:80]:
            log("      [dump %3d] %r" % (i, s))
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


# ------------------------------------------------------------------ 收尾
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
                           capture_output=True, timeout=30)
        steps.append("taskkill /PID %d (无 /F) rc=%d out=%r" %
                     (pid, r.returncode,
                      ((r.stdout or b"") + (r.stderr or b"")).decode(
                          "utf-8", "replace")[:200]))
    for _ in range(10):
        time.sleep(0.5)
        if not alive():
            steps.append("进程在 taskkill(无 /F) 后退出")
            return steps

    if alive():
        r = subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, timeout=30)
        steps.append("taskkill /F /PID %d rc=%d out=%r" %
                     (pid, r.returncode,
                      ((r.stdout or b"") + (r.stderr or b"")).decode(
                          "utf-8", "replace")[:200]))
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


# ------------------------------------------------------------------ 观察者进程管理
def spawn_watcher(pid):
    cmdline = ('cmd.exe /c python -X utf8 "%s" --pid %d --interval-ms 1000 '
               '--outdir "%s" > watcher_live_stdout.txt 2>&1'
               % (str(WATCHER_SCRIPT), pid, str(OUT)))
    cmd_pid, retval = spawn_wmi_hidden(cmdline, str(W19))
    if retval != 0:
        raise RuntimeError("观察者 WMI Create 失败 retval=%d" % retval)
    return cmd_pid


def stop_watcher():
    """写停机文件，观察者最迟下个周期退出。"""
    try:
        WATCHER_STOP_FILE.write_text(
            json.dumps({"stop": True, "t_utc_iso": utc_iso()}, ensure_ascii=False),
            encoding="utf-8")
        return True
    except Exception as e:
        log("    写观察者停机文件异常 %r" % e)
        return False


def wait_watcher_exit(cmd_pid, timeout_s=25.0):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if not process_exists(cmd_pid):
            return True, round(time.monotonic() - t0, 2)
        time.sleep(0.5)
    return False, timeout_s


def read_watcher_state():
    try:
        st = WATCHER_STATE_FILE.stat()
        with WATCHER_STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.loads(f.read())
        data["_mtime_t_mono_ns"] = time.perf_counter_ns()
        return data
    except Exception:
        return None


def probe_getprocesstimes(pid):
    """卡面：Lead 自测 GetProcessTimes 同权限返回 False（原因未明）。
    本探针只做一次性探测并如实记录结果；进程级 CPU 不依赖它。
    ① 用既有 RPM 句柄权限 (VM_READ|QUERY_INFORMATION)；② 用 0x1000 新句柄。"""
    out = {}
    h1 = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    if h1:
        c, e, k, uu = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
        ok = k32.GetProcessTimes(h1, ctypes.byref(c), ctypes.byref(e),
                                 ctypes.byref(k), ctypes.byref(uu))
        out["with_vmread_query_handle"] = {
            "ok": bool(ok),
            "kernel_ms": round(ft_ms(k), 4) if ok else None,
            "user_ms": round(ft_ms(uu), 4) if ok else None,
            "last_error": ctypes.get_last_error() if not ok else 0,
        }
        k32.CloseHandle(h1)
    else:
        out["with_vmread_query_handle"] = {"ok": False, "open_failed": True}
    h2 = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if h2:
        c, e, k, uu = wt.FILETIME(), wt.FILETIME(), wt.FILETIME(), wt.FILETIME()
        ok = k32.GetProcessTimes(h2, ctypes.byref(c), ctypes.byref(e),
                                 ctypes.byref(k), ctypes.byref(uu))
        out["with_limited_query_handle"] = {
            "ok": bool(ok),
            "kernel_ms": round(ft_ms(k), 4) if ok else None,
            "user_ms": round(ft_ms(uu), 4) if ok else None,
            "last_error": ctypes.get_last_error() if not ok else 0,
        }
        k32.CloseHandle(h2)
    else:
        out["with_limited_query_handle"] = {"ok": False, "open_failed": True}
    return out


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
    stop_flag2 = {"stop": True}
    inventory_before, inventory_after = {}, {}
    residual_before, residual_after = [], []
    close_steps = []
    watcher_cmd_pid = None
    watcher_wait = None
    priority_set = False
    ttable = None
    gpt_probe = None
    meta = {
        "run_id": RUN_ID,
        "card": "RE-N04h W19 load-B-double-prime arm (LoadBench U800, 480 vehicles + 320 infantry): unit/infantry dimension CPU-pressure test (external read-only, single run)",
        "attempt": attempt,
        "ndjson": str(ndjson_path), "started_utc": started_utc,
        "args": {k: getattr(a, k) for k in vars(a)},
        "addresses": {k: [hex(ad), sz] for k, (ad, sz) in ADDR.items()},
        "baseline_hashes": BASELINE_HASHES,
        "carrier": {"expected_filename": BG_FILENAME, "expected_bytes": BG_BYTES,
                    "expected_sha256": BG_SHA256,
                    "sha256": None, "bytes": None},
        "pid": None, "is32": None, "game_hwnd": None, "game_tid": None,
        "map": None, "code_signature_ok": None, "prelaunch_hashes": {},
        "conditions": {}, "residual_before": [], "residual_after": [],
        "close_steps": [], "error": None, "n_samples": 0, "n_read_fail": 0,
        "n_winthread_fail": 0, "n_sweeps": 0,
        "phase_stop": None,
        "timebeginperiod_ret": None,
        "priority_class": None,
        "getprocesstimes_probe": None,
        "watcher": {"cmd_pid": None, "spawned_utc": None,
                    "state_reads_ok": 0, "state_reads_fail": 0,
                    "natural_end_from_state": None, "stop_written": None,
                    "wait_exit": None},
        "predeclared_analysis_plan": {
            "unit_note": "CPU 时间 ≠ 帧时间/耗时。CPU 时间不含阻塞等待"
                         "（Sleep/Present/vsync/等消息）⇒ 「一拍 CPU 低」"
                         "≠「这一拍快」；「一拍 CPU 高」才是可靠的重活信号。"
                         "GPU 侧耗时、画面掉帧本卡测不到（需注入，禁止）。",
            "channel_note": "主通道=窗口线程 GetThreadTimes kernel/user（累计，"
                            "FILETIME→ms），每拍采样。GetThreadTimes 实签名 4 出参="
                            "creation/exit/kernel/user，无 ctx switches 出参；"
                            "win_ctx_switches 与全线程求和由观察者进程 1Hz 只读采集"
                            "（NtQuerySystemInformation tid 校验 + OpenThread/"
                            "GetThreadTimes 求和，失败=沿用上次值/null）。"
                            "辅通道=QueryThreadCycleTime（周期计数，粒度细于"
                            "时钟节拍记账）。",
            "attribution": "每拍成本 = 相邻两次 frame 递增采样之间 "
                           "Δ(win_kernel+win_user)。递增事件只能以采样粒度观测 ⇒ "
                           "归属窗口 = 1 拍 ± 采样量化（±~6 ms）；窗口含渲染+消息泵+"
                           "逻辑，非纯逻辑 CPU。",
            "quantization_note": "GetThreadTimes 记账受系统时钟节拍粒度约束 ⇒ "
                                 "累计值呈台阶；每拍值可能出现量子。本次实测的量子"
                                 "在分析中如实报告，不预设。",
            "hotspot_rule": "每拍 CPU ≥ 3×中位 且 ≥ 1.0 ms ⇒ 热点候选；前 20 名"
                            "（t_rel、CPU ms、frame、mode、fg）。cycle 通道同判据"
                            "表仅作旁证（标注辅助）。",
            "trend_rule": "10 s 窗 median(每拍CPU)；末 1/3 窗中位 > 首 1/3 窗中位"
                          "× 1.2 ⇒ 上升候选。",
            "occupancy_rule": "ΔCPU/有效墙钟（窗口线程与进程级各一）；单位=单核百分比。",
            "df_rule": "分布主表用 df=1（Δframe=1）事件；df≥2 全额记单行并标注，"
                       "不摊分（真实拍内分布未知，摊分会伪造数据）。",
            "hiccup_rule": "括号采样间隔 > max(3×中位采样间隔, 24 ms) 的递增事件标 "
                           "hiccup，如实保留并标注。",
            "fail_rule": "read_status=fail 拍保留不填补；跨 fail 拍的递增不计算。",
            "a_arm_baseline_w15": {
                "carrier": "[8]试验地_Pro_ProvingGrounds.yrm",
                "cycle_median_ms_per_tick": 1.691,
                "filetime_mean_ms_per_tick": 1.725,
                "occupancy_pct_singlecore_window_thread": 5.39,
                "tick_rate_counts_per_s": 31.2492,
                "tick_interval_mean_ms": 32.000,
                "tick_interval_ge64ms": 0,
                "ingame_s": 240.006,
            },
            "hexbay_arm_w18": {
                "carrier": "[8]黑心湾_HexBay.yrm (144 建筑)",
                "cycle_median_ms_per_tick": 1.767189,
                "occupancy_pct_singlecore_window_thread": 5.670446,
                "cyc_per_ms_selfcalibrated": 3311138,
                "rel_change_vs_a_median_pct": 4.506,
                "a8ed50": "全程 0",
                "tier": "[无显著差异]",
            },
            "verdict_rule": "预设（不得事后改）：[成功造出压力]=U800 cycle 每拍中位 "
                            ">2.54 ms（=A 1.691×1.5）或窗口线程占用率 >10%；"
                            "[无显著差异]=相对 A 差 <20%；[中间地带]=20%–50%（如实"
                            "报告）；[U800 不可用]=未进图或有效段 <90 s（不重启凑时长）",
            "map_entry_rule": "进图成功 = frame 以 ≈29–32 计数/s 持续 ≥60 s；"
                              "mode[0xA8B238] 仅作旁证，不作进图判据",
            "combat_witness_rule": "A8ED50（候选 BulletCnt，语义未证）逐拍记录；"
                                   "W7/W15/W18 三卡全程 0。本卡只问：U800 上是否"
                                   "变为非零（单位实例化旁证）。不得把它当已证"
                                   "单位数，只作旁证描述",
            "declared_vs_runtime_rule": "声明 480 车 + 320 步兵 ≠ 运行实例数；"
                                        "负载只以实测 CPU 为准，不得用声明量"
                                        "推断负载",
            "segment_rule": "有效局内段 = phase=ingame（首个 frame>0 起）至自然结束"
                            "(+grace 20s 为 post_end) 或 240s 目标（卡面 ≥180s）；"
                            "<90s 判[U800 不可用]。",
            "natural_end_rule": "观察者进程 1s 周期 ui_watch 连续 2 次发现可见 Button "
                                "text 含 'continue' ⇒ 自然结束；或进程退出",
            "retry_rule": "仅当失败严格发生在首个 frame>0 之前允许 1 次重试；"
                          "采样开始后任何终止均为最终",
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
        log("[S0] W19 实例锁 + 残留进程 + 哈希守卫（attempt=%d）" % attempt)
        lock_state = check_lock()
        log("    实例锁 owner 状态 = %s" % lock_state)
        write_lock("W19 RE-N04h U800 单位/步兵维度 CPU 负载对照 进行中 (attempt %d)" % attempt)
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
        log("    统一条件已记录：Video=%s Skirmish.GameSpeed=%s ddraw.windowed=%s "
            "renderer=%s maxfps=%s" %
            (conditions["RA2MD.INI"].get("Video"),
             (conditions["RA2MD.INI"].get("Skirmish") or {}).get("GameSpeed"),
             (conditions["ddraw.ini"].get("ddraw") or {}).get("windowed"),
             (conditions["ddraw.ini"].get("ddraw") or {}).get("renderer"),
             (conditions["ddraw.ini"].get("gamemd") or {}).get("maxfps")))

        carrier_path = GAME_DIR / BG_FILENAME
        if not carrier_path.exists():
            raise GuardStop("载体文件缺失 %s" % carrier_path)
        csha = sha256_file(carrier_path)
        cbytes = carrier_path.stat().st_size
        meta["carrier"] = {"expected_filename": BG_FILENAME,
                           "expected_bytes": BG_BYTES, "expected_sha256": BG_SHA256,
                           "sha256": csha, "bytes": cbytes}
        log("    载体 %s %d B sha=%s" % (BG_FILENAME, cbytes, csha))
        if csha != BG_SHA256 or cbytes != BG_BYTES:
            raise GuardStop("载体哈希/字节数与钉定值不一致，停手")
        # ★ W19 新增：实读 [Basic].Name / Official / MaxPlayer 与声明计数，
        #   与钉定值核对（不一致 ⇒ 停手）；声明量只作载体身份，不作负载推断。
        carrier_ini = read_yrm_carrier(carrier_path)
        cname = (carrier_ini.get("basic") or {}).get("Name")
        coff = (carrier_ini.get("basic") or {}).get("Official")
        cmp_ = (carrier_ini.get("basic") or {}).get("MaxPlayer")
        cmin = (carrier_ini.get("basic") or {}).get("MinPlayer")
        cmode = (carrier_ini.get("basic") or {}).get("GameMode")
        cdecl = carrier_ini.get("declared_counts") or {}
        meta["carrier_ini"] = carrier_ini
        log("    载体实读 [Basic]: Name=%r Official=%r MaxPlayer=%r MinPlayer=%r "
            "GameMode=%r declared=%s" % (cname, coff, cmp_, cmin, cmode, cdecl))
        if cname != BG_EXPECTED_NAME:
            raise GuardStop("载体 [Basic].Name=%r 与钉定 %r 不一致，停手"
                            % (cname, BG_EXPECTED_NAME))
        for k in ("units", "infantry", "structures"):
            got = cdecl.get(k)
            want = BG_DECLARED[k]
            if got is None and k == "structures":
                got = 0                      # 无 [Structures] 段 ⇒ 0
            if got != want:
                raise GuardStop("载体声明计数 %s=%r 与钉定 %r 不一致，停手"
                                % (k, got, want))

        inventory_before = inventory(GAME_DIR)
        log("    启动前文件清单 %d 项" % len(inventory_before))
        sink.write({"kind": "meta", "seq": 0, "t_mono_ns": time.perf_counter_ns(),
                    "t_utc_iso": utc_iso(), "run_id": RUN_ID,
                    "predeclared_analysis_plan": meta["predeclared_analysis_plan"],
                    "prelaunch_hashes": prelaunch_hashes, "carrier": meta["carrier"],
                    "residual_before": residual_before, "conditions": conditions,
                    "sweep_note": "全线程扫在观察者进程 1Hz",
                    "note": "meta：此后每行独立 NDJSON；异常退出此前各行仍可解析"})

        # 进程优先级：低于正常，绝不与游戏抢 CPU
        try:
            priority_set = bool(k32.SetPriorityClass(
                k32.GetCurrentProcess(), 0x00004000))  # BELOW_NORMAL_PRIORITY_CLASS
            meta["priority_class"] = "BELOW_NORMAL" if priority_set else "set_failed"
        except Exception as e:
            meta["priority_class"] = "set_error:%r" % e

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

        hwnds = game_top_windows(pid)
        game_hwnd = hwnds[0] if hwnds else 0
        meta["game_hwnd"] = int(game_hwnd or 0)
        if game_hwnd:
            game_tid = win_tid_of(game_hwnd)
        meta["game_tid"] = game_tid
        log("    游戏窗口 hwnd=%s tid=%s（GetWindowThreadProcessId 返回值）" %
            (meta["game_hwnd"], game_tid))
        ev("game_window", {"hwnd": meta["game_hwnd"], "tid": game_tid})

        # 线程 CPU 仪器：初始全线程扫（主菜单相位）+ GetProcessTimes 一次性探测
        ttable = ThreadTable(pid)
        sw0 = ttable.sweep()
        meta["n_sweeps"] = 1
        if sw0:
            sink.write({"kind": "thread_sweep", "phase": "menu", **sw0})
            log("    初始线程扫：n_threads=%s sum_cpu=%.3f ms（主菜单相位）" %
                (sw0["n_threads"], sw0["sum_cpu_ms"]))
        else:
            log("    !! 初始线程扫快照失败")
        gpt_probe = probe_getprocesstimes(pid)
        meta["getprocesstimes_probe"] = gpt_probe
        log("    GetProcessTimes 一次性探测：%s" %
            json.dumps(gpt_probe, ensure_ascii=False))
        if game_tid:
            hh = ttable.ensure(game_tid)
            log("    窗口线程 tid=%s 句柄=%s" % (game_tid, bool(hh)))
        ev("thread_instrument_ready", {"game_tid": game_tid,
                                       "n_threads": (sw0 or {}).get("n_threads"),
                                       "getprocesstimes": gpt_probe})

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
        log("[S3] 置前游戏窗口 -> %s（此后本进程零输入，StartGame 待发）" % ok)
        ev("foreground_forced", {"ok": ok,
                                 "note": "置前=开局阶段允许输入的最后一次；"
                                         "其后采样段零按键/零切窗/零干预"})
        if not click(pid, "GUI:StartGame", 0.0):
            raise RuntimeError("GUI:StartGame 点击失败")
        sg_t = time.perf_counter_ns()
        ev("startgame_clicked", {"t_mono_ns": sg_t})
        log("    StartGame 已点击；等待首个 frame>0")

        # ---------- S4 采样段：6 ms 目标间隔，零干预，每拍记线程 CPU ----------
        watcher_cmd_pid = spawn_watcher(pid)
        meta["watcher"]["cmd_pid"] = watcher_cmd_pid
        meta["watcher"]["spawned_utc"] = utc_iso()
        ev("watcher_spawned", {"cmd_pid": watcher_cmd_pid})
        log("[S4] 观察者已独立启动 (cmd_pid=%d)；timeBeginPeriod(1)…"
            % watcher_cmd_pid)
        try:
            tbp_ret = int(winmm.timeBeginPeriod(1))
        except Exception as e:
            tbp_ret = "error:%r" % e
        meta["timebeginperiod_ret"] = tbp_ret
        log("    timeBeginPeriod(1) -> %s（提升本进程 sleep 粒度；不触碰游戏进程）"
            % tbp_ret)

        interval_ns = int(round(a.interval_ms * 1e6))
        seq = 0
        t_first_pos = None
        prev_t_ns = None
        sched_anchor = None
        n_resync = 0
        stop_reason = None
        last_prog = -1
        post_end_until = None
        natural_end_t = None
        proc_exit_t = None
        state_cache = None
        wthreads = {}                 # 观察者 NtQuery+GetThreadTimes 线程表（1Hz 辅助）
        last_state_check = 0
        n_state_ok = 0
        n_state_fail = 0
        qd = wt.DWORD(0)
        prev_cyc = None              # W19 新增：上一采样窗口线程 cycle 累计
        bullet_first = None          # W19 新增：A8ED50 首次非零（交战旁证）
        t_loop0 = time.perf_counter_ns()
        while True:
            t_ns = time.perf_counter_ns()
            vals, failed = read_all(hproc)
            # ---- 窗口线程 CPU（每拍主通道） ----
            wt_err = None
            wtid = None
            wk = wu = wcyc = None
            if game_hwnd and u.IsWindow(game_hwnd):
                wtid = win_tid_of(game_hwnd)
            if wtid is None:
                hwnds2 = game_top_windows(pid)
                if hwnds2:
                    game_hwnd = hwnds2[0]
                    meta["game_hwnd"] = int(game_hwnd)
                    wtid = win_tid_of(game_hwnd)
            if wtid:
                hh = ttable.ensure(wtid)
                if hh:
                    q1 = ttable.query_one(hh)
                    if q1 is not None:
                        wk, wu, wcyc = q1
                    else:
                        wt_err = "GetThreadTimes_fail"
                else:
                    wt_err = "OpenThread_fail"
            else:
                wt_err = "window_gone"
            if wt_err:
                meta["n_winthread_fail"] = meta.get("n_winthread_fail", 0) + 1
            # ---- W19 新增：cycle Δ（相邻采样）与 A8ED50 首次非零事件 ----
            cyc_d = None
            if wcyc is not None and prev_cyc is not None:
                cyc_d = wcyc - prev_cyc
            if wcyc is not None:
                prev_cyc = wcyc
            if vals is not None and bullet_first is None \
                    and (vals.get("A8ED50") or 0) != 0:
                bullet_first = {"t_mono_ns": t_ns, "value": vals["A8ED50"],
                                "frame": vals.get("frame"),
                                "phase": ("ingame" if t_first_pos is not None
                                          else "pre_startgame")}
                ev("a8ed50_first_nonzero", bullet_first)
                log("    ★ A8ED50 首次非零=%s（frame=%s，phase=%s）" %
                    (vals["A8ED50"], vals.get("frame"),
                     bullet_first["phase"]))
            # 全线程扫已移至观察者进程（1Hz；本机 Toolhelp 全系统线程迭代 ~5ms，
            # 留在 6ms 采样循环内会周期性污染采样间隔——bindtest 实测 7639 线程）。
            # n_threads/sum_all_threads_cpu_ms 由观察者 state.json 低频供给。
            seq += 1
            ec = wt.DWORD(0)
            alive = bool(k32.GetExitCodeProcess(hproc, ctypes.byref(ec))
                         and ec.value == STILL_ACTIVE)
            fg = fg_is(pid)
            interval_ms = ((t_ns - prev_t_ns) / 1e6) if prev_t_ns is not None else None
            if sched_anchor is None:
                sched_anchor = t_ns
            sched_late_ms = (t_ns - sched_anchor) / 1e6
            sched_anchor += interval_ns
            if (t_ns - sched_anchor) > 4 * interval_ns:
                # 严重滞后（系统停顿）：重锚，避免无界追平爆发；如实记录
                sched_anchor = t_ns
                n_resync += 1
                ev("cadence_resync", {"seq": seq, "sched_late_ms":
                                      round(sched_late_ms, 3)})
            if not alive:
                proc_exit_t = t_ns
                stop_reason = "process_exited_during_sampling"
                ev("process_exited", {"phase": "sampling", "exit_code": ec.value})
            if t_first_pos is None and vals is not None \
                    and vals.get("frame", 0) > 0 and t_ns > sg_t:
                t_first_pos = t_ns
                ev("first_frame_positive",
                   {"frame": vals["frame"],
                    "after_startgame_s": round((t_ns - sg_t) / 1e9, 6)})
                log("    首个 frame>0（frame=%d，StartGame 后 %.3fs）⇒ 采样计时起点"
                    % (vals["frame"], (t_ns - sg_t) / 1e9))
            phase = "post_start"
            if t_first_pos is not None:
                if natural_end_t is not None and t_ns >= natural_end_t:
                    phase = "post_end"
                    if post_end_until is None:
                        post_end_until = natural_end_t + int(GRACE_S * 1e9)
                else:
                    phase = "ingame"
            elapsed = ((t_ns - t_first_pos) / 1e9) if t_first_pos is not None \
                else round((t_ns - sg_t) / 1e9, 6)
            rec = {"seq": seq, "kind": "sample", "phase": phase,
                   "t_mono_ns": t_ns, "t_utc_iso": utc_iso(),
                   "elapsed_s": round(elapsed, 6),
                   "interval_ms_actual": (round(interval_ms, 4)
                                          if interval_ms is not None else None),
                   "sched_late_ms": round(sched_late_ms, 4),
                   "read_status": "ok" if vals is not None else "fail",
                   "read_fail_detail": failed, "win_foreground": fg,
                   "win_tid": wtid, "win_kernel_ms": wk, "win_user_ms": wu,
                   "win_cpu_ms": (round(wk + wu, 6)
                                  if (wk is not None and wu is not None) else None),
                   "win_cycle": wcyc, "win_cyc_delta": cyc_d,
                   "cyc_est_ms_Acorr_provisional": (
                       round(cyc_d / 3.104e6, 6) if cyc_d is not None else None),
                   "win_thread_err": wt_err,
                   "n_threads": (state_cache or {}).get("n_threads"),
                   "sum_all_threads_cpu_ms":
                       (state_cache or {}).get("sum_all_threads_cpu_ms"),
                   "threads_sweep_age_ms":
                       (round((t_ns - (state_cache or {}).get(
                           "threads_sweep_t_mono_ns", t_ns)) / 1e6, 3)
                        if state_cache else None)}
            if wthreads and wtid is not None:
                row = wthreads.get(str(wtid))
                if row:
                    rec["win_ctx_switches"] = row.get("ctx")
                    rec["ctx"] = row.get("ctx")
                    rec["win_ctx_src_age_ms"] = round(
                        (t_ns - (state_cache or {}).get("_mtime_t_mono_ns", t_ns)) / 1e6,
                        3)
            for k in ADDR:
                rec[k] = vals.get(k) if vals is not None else None
            sink.write(rec)
            prev_t_ns = t_ns
            if failed:
                meta["n_read_fail"] = meta.get("n_read_fail", 0) + 1
            # 观察者状态：~1s 读一次 state.json（原子替换写入，无半读）
            if t_ns - last_state_check > 0.9e9:
                last_state_check = t_ns
                st = read_watcher_state()
                if st is None:
                    n_state_fail += 1
                else:
                    n_state_ok += 1
                    state_cache = st
                    wthreads = st.get("thread_rows") or {}
                    if st.get("natural_end") and natural_end_t is None \
                            and st.get("natural_end_t_mono_ns"):
                        natural_end_t = st["natural_end_t_mono_ns"]
                        ev("natural_end_detected", {
                            "t_mono_ns": natural_end_t,
                            "buttons": st.get("natural_end_buttons"),
                            "rule": "观察者连续 2 次发现可见 continue 类 Button"})
                        log("    自然结束（观察者 %s）⇒ post_end grace %.0fs" %
                            (st.get("natural_end_buttons"), GRACE_S))
                    if st.get("alive") is False and proc_exit_t is None \
                            and t_first_pos is not None:
                        proc_exit_t = st.get("t_mono_ns")
                        stop_reason = "process_exited_via_watcher"
                        ev("process_exited", {"phase": "via_watcher"})
            if proc_exit_t is not None:
                break
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
                log("    [采样] t=%.0fs frame=%s fg=%s n_resync=%d "
                    "win_cpu=%.1fms sum_all=%.1fms n_th=%s" %
                    (elapsed, vals.get("frame") if vals else None, fg, n_resync,
                     (wk or 0) + (wu or 0),
                     (state_cache or {}).get("sum_all_threads_cpu_ms") or -1,
                     (state_cache or {}).get("n_threads")))
            # 睡到下一个节拍（deadline 制：平均间隔=目标值，抖动如实记录）
            now = time.perf_counter_ns()
            d = (sched_anchor - now) / 1e9
            if d > 0:
                time.sleep(d)
        stop_flag2["stop"] = True
        dur_sampling = ((time.perf_counter_ns() - t_first_pos) / 1e9
                        if t_first_pos is not None else 0.0)
        if ttable is not None:
            sw_end = ttable.sweep()
            if sw_end:
                meta["n_sweeps"] = meta.get("n_sweeps", 0) + 1
                sink.write({"kind": "thread_sweep", "phase": "end", **sw_end})
        log("[S4] 采样段结束：reason=%s 有效局内段=%.1fs seq=%d n_resync=%d "
            "natural_end=%s" % (stop_reason, dur_sampling, seq, n_resync,
                                natural_end_t is not None))
        ev("sampling_end", {"reason": stop_reason,
                            "ingame_duration_s": round(dur_sampling, 3),
                            "n_samples": seq, "n_resync": n_resync,
                            "interval_ms_target": a.interval_ms})
        meta["phase_stop"] = stop_reason
        meta["n_samples"] = seq
        meta["sampling"] = {
            "first_frame_positive_t_mono_ns": t_first_pos,
            "startgame_clicked_t_mono_ns": sg_t,
            "foreground_forced_t_mono_ns": ff_t,
            "natural_end_t_mono_ns": natural_end_t,
            "proc_exit_t_mono_ns": proc_exit_t,
            "stop_reason": stop_reason,
            "ingame_duration_s": round(dur_sampling, 3),
            "target_seconds": a.target_seconds,
            "interval_ms_target": a.interval_ms,
            "interval_ms_actual_note": "实测间隔分布见 analyze_u800.py 输出"
                                       "（不得把目标值当实测值）",
            "grace_after_end_s": GRACE_S,
            "sweep_note": "全线程扫在观察者进程 1Hz（kind=thread_sweep 写入 "
                          "ui_watch.ndjson，state.json 供值）；探针自身仅"
                          "菜单前初始扫与结束扫两次",
            "sweep_period_ms": 1000.0,
            "n_samples_total": seq,
            "n_resync": n_resync,
            "n_sweeps": meta.get("n_sweeps", 0),
            "a8ed50_first_nonzero": bullet_first,
            "watcher_state_reads_ok": n_state_ok,
            "watcher_state_reads_fail": n_state_fail,
            "loop_overhead_t_mono_ns": time.perf_counter_ns() - t_loop0,
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
            stop_flag2["stop"] = True
        except Exception:
            pass
        # 1) 停观察者（写停机文件；观察者最迟下个周期退出）
        meta["watcher"]["stop_written"] = stop_watcher()
        # 2) 关线程 CPU 仪器句柄
        if ttable is not None:
            try:
                ttable.close_all()
            except Exception:
                pass
        if hproc:
            try:
                k32.CloseHandle(hproc)
            except Exception:
                pass
        # 3) 关闭自启动实例
        try:
            log("[P1] W19 收尾：关闭自启动实例")
            close_steps = close_game(pid, meta.get("game_hwnd") or 0)
            for s in close_steps:
                log("    %s" % s)
        except Exception as e:
            close_steps.append("close_game 异常: %r" % e)
            log("    close_game 异常 %r" % e)
        # 4) 等观察者退出（非孤儿证据）
        if watcher_cmd_pid:
            try:
                okw, took = wait_watcher_exit(watcher_cmd_pid)
                watcher_wait = {"cmd_pid": watcher_cmd_pid, "exited": okw,
                                "wait_s": took}
                log("    观察者退出=%s（等待 %.1fs）" % (okw, took))
            except Exception as e:
                watcher_wait = {"cmd_pid": watcher_cmd_pid, "error": repr(e)}
        meta["watcher"]["wait_exit"] = watcher_wait
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
            winmm.timeEndPeriod(1)
        except Exception:
            pass
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
                       "W19 RE-N04h 探针收尾自愈：恢复 owner=lead"),
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
                        "residual_after": residual_after,
                        "lock_restored": meta.get("lock_restored")})
        except Exception:
            pass
        sink.close()
        log("[P1] W19 收尾完成（配置已还原，NDJSON=%d 行）" % sink.n_lines)
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
                    default=["[2] 0LoadBench U800", "0LoadBench U800",
                             "LoadBench U800", "U800"],
                    help="按显示名选图的模式序列（依次尝试，禁固定索引/文件名）。"
                         "W17 白名单实测：'[2] 0LoadBench U800' 在 268 条列表中"
                         "唯一命中（索引 96，W12 R4 以此进图）；本卡仍实测确认，"
                         "命中 >1 时说明取舍")
    ap.add_argument("--target-seconds", type=float, default=240.0,
                    help="采样段目标时长（卡要求 ≥180s，从首个 frame>0 起算）")
    ap.add_argument("--interval-ms", type=float, default=6.0,
                    help="目标采样间隔 ms（实测值必须如实报告）")
    ap.add_argument("--pre-interval-ms", type=float, default=250.0)
    ap.add_argument("--menu-timeout", type=float, default=120.0)
    ap.add_argument("--attempt", type=int, default=1)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    exit_code, meta = run_one(a, attempt=a.attempt)
    log("[MAIN] W19 exit_code=%d pid=%s map_index=%s display=%r phase_stop=%s "
        "ingame_s=%s" %
        (exit_code, meta.get("pid"),
         (meta.get("map") or {}).get("index"),
         (meta.get("map") or {}).get("display_name"),
         meta.get("phase_stop"),
         (meta.get("sampling") or {}).get("ingame_duration_s")))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

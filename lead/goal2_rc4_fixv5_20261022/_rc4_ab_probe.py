#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RC-4 A/B 探针（待办 9 / 裁决 6）。

★ 基底
  `lead/goal2_rc4_trigger_20261022/_rc4_debugdump_probe.py`（Arm A + DebugActiveProcess
  + 首次异常即时 dump）。本件**不 import 母本**，是独立副本，只沿用其方法学。

★ 与基底的四处增量（裁决 6 逐条）
  1. **loader 启动（U8 授权语义）**：`--arm B --dll <name>` 走副本 `rc4_loader.exe`
     （CREATE_SUSPENDED + 远程 LoadLibraryA）；`--arm A` 直启 gamemd（零注入）。
     ★ loader 必须放在载体目录里跑，DLL 也必须在载体目录里。
  2. **A8 收尾清扫**：按载体目录精确清扫 gamemd/ra2loader（不按名全杀），
     并带**枚举器正控**（查本进程自己的 exe 名）——枚举失败 ⇒ 判 V-fail，
     绝不把「查不到」当「零残留」。
  3. **正控探针**：`--positive-control` 时主动构造一个**必然命中**的判据
     （读 [0x887368] 并断言读到的是一个 u32），用于证明 RPM 通道本身能工作。
     ★ 只证「通道能读」，不证「崩溃会发生」。
  4. **守卫命中计数**：从载体里的 `ra2render.log` 抽 `[ra2rc4guard]` 行，
     取「守卫命中计数合计 N」。这是 B 臂的核心判据。

★ 判据（写进 JSON，供后续裁决）
  - `rc4_hit`：是否在首次异常事件里看到 (Eip=0x00724737, Access=0x250)
  - `guard_hits`：守卫计数合计（B 臂要求 >= 1）
  - `clean_exit`：关窗后 <= 20 s 进程正常退出（不是被 TerminateProcess）
  - `except_changed`：except.txt 是否新增（★ 零新增不单独当未崩判据，铁律 7）
  - `a8.remaining`：载体下残留进程（必须为空）

★ 纪律
  - 只调试**本趟自己启动**的 pid；`DebugActiveProcess` 前先核对 pid 身份。
  - 载体每趟排他新建、趟后精确终止 + 删除 + 复测残留。
  - dump 落 `D:\\ra2dumps`（仓外），不上公开仓。
  - 本件**不在无人授权时自行发射**：默认 `--dry-run`，必须显式 `--live` 才真跑。

★ 用法
  python _rc4_ab_probe.py --arm A --trips 3 --live
  python _rc4_ab_probe.py --arm B --dll ra2rc4guard.dll --trips 3 --live
  python _rc4_ab_probe.py --arm A --dry-run          # 只做预检与计划打印
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge").resolve()
CARD = (ROOT / "lead" / "goal2_rc4_fixv5_20261022").resolve()
SRC = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/"
       "qc161_u0400_trip/_src_L1_sf8_20261020").resolve()
DUMP_DIR = Path(r"D:\ra2dumps").resolve()

GAMEMD_SHA16 = "73201cc021497c95"
SRC_FILE_COUNT = 88
WINDOW_CLASS = "Yuri's Revenge"
CARRIER_PATH_MAX = 130          # ★ 载体**目录**门禁（≥131 触发次生崩溃）
CLOSE_WAIT_S = 20.0             # 关窗后允许的正常退出时限

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
WM_CLOSE = 0x0010

RC4_EIP = 0x00724737
RC4_ACCESS = 0x00000250

GUARD_LOG_TAG = "[ra2rc4guard]"

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)

k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenProcess.restype = wt.HANDLE
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.CloseHandle.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.restype = wt.BOOL
k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR,
                                           ctypes.POINTER(wt.DWORD)]
k32.QueryFullProcessImageNameW.restype = wt.BOOL
k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
k32.TerminateProcess.restype = wt.BOOL
k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
k32.WaitForSingleObject.restype = wt.DWORD
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.GetExitCodeProcess.restype = wt.BOOL
k32.DebugActiveProcess.argtypes = [wt.DWORD]
k32.DebugActiveProcess.restype = wt.BOOL
k32.DebugActiveProcessStop.argtypes = [wt.DWORD]
k32.DebugActiveProcessStop.restype = wt.BOOL
k32.ContinueDebugEvent.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD]
k32.ContinueDebugEvent.restype = wt.BOOL
k32.WaitForDebugEvent.argtypes = [ctypes.c_void_p, wt.DWORD]
k32.WaitForDebugEvent.restype = wt.BOOL
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.CreateToolhelp32Snapshot.restype = wt.HANDLE

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [ENUMPROC, wt.LPARAM]
u32.EnumWindows.restype = wt.BOOL
u32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u32.GetClassNameW.restype = ctypes.c_int
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.PostMessageW.restype = wt.BOOL

dbg.MiniDumpWriteDump.argtypes = [wt.HANDLE, wt.DWORD, wt.HANDLE, ctypes.c_int,
                                  ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_void_p]
dbg.MiniDumpWriteDump.restype = wt.BOOL

MINIDUMP_WITH_DATA_SEGS = 0x00000001
MINIDUMP_WITH_FULL_MEMORY = 0x00000002
MINIDUMP_WITH_HANDLE_DATA = 0x00000004
MINIDUMP_WITH_UNLOADED_MODULES = 0x00000020
MINIDUMP_WITH_PRIVATE = 0x00080000
DUMP_TYPE_FULL = (MINIDUMP_WITH_DATA_SEGS | MINIDUMP_WITH_FULL_MEMORY
                  | MINIDUMP_WITH_HANDLE_DATA | MINIDUMP_WITH_UNLOADED_MODULES
                  | MINIDUMP_WITH_PRIVATE)
DUMP_RIGHTS = 0x0400 | 0x0010

EXCEPTION_DEBUG_EVENT = 1
EXIT_PROCESS_DEBUG_EVENT = 5
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_ACCESS_VIOLATION = 0xC0000005
EXCEPTION_BREAKPOINT = 0x80000003


class EXCEPTION_RECORD(ctypes.Structure):
    pass


EXCEPTION_RECORD._fields_ = [
    ("ExceptionCode", wt.DWORD),
    ("ExceptionFlags", wt.DWORD),
    ("ExceptionRecord", ctypes.POINTER(EXCEPTION_RECORD)),
    ("ExceptionAddress", ctypes.c_void_p),
    ("NumberParameters", wt.DWORD),
    ("ExceptionInformation", ctypes.c_void_p * 15),
]


class EXCEPTION_DEBUG_INFO(ctypes.Structure):
    _fields_ = [("ExceptionRecord", EXCEPTION_RECORD),
                ("dwFirstChance", wt.DWORD)]


class _DEU(ctypes.Union):
    _fields_ = [("Exception", EXCEPTION_DEBUG_INFO),
                ("pad", ctypes.c_ubyte * 160)]


class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wt.DWORD),
                ("dwProcessId", wt.DWORD),
                ("dwThreadId", wt.DWORD),
                ("u", _DEU)]


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name: str) -> str:
    """落盘名必须是单层、无分隔符、无 `..`。"""
    if not name or name in (".", ".."):
        raise ValueError("illegal name: %r" % (name,))
    if "/" in name or "\\" in name:
        raise ValueError("name contains separator: %r" % (name,))
    if Path(name).name != name:
        raise ValueError("name not single-level: %r" % (name,))
    return name


def list_procs() -> dict:
    h = k32.CreateToolhelp32Snapshot(2, 0)
    if not h or h == ctypes.c_void_p(-1).value:
        return {}
    out = {}
    e = PE32()
    e.dwSize = ctypes.sizeof(PE32)
    k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.POINTER(PE32)]
    ok = k32.Process32FirstW(h, ctypes.byref(e))
    while ok:
        out[e.th32ProcessID] = e.szExeFile
        ok = k32.Process32NextW(h, ctypes.byref(e))
    k32.CloseHandle(h)
    return out


def game_procs() -> list:
    return [n for n in list_procs().values()
            if n.lower() in ("gamemd.exe", "ra2loader.exe", "rc4_loader.exe",
                             "game.exe")]


def query_image(pid: int):
    h = k32.OpenProcess(0x1000, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wt.DWORD(1024)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value
    finally:
        k32.CloseHandle(h)
    return None


def under_carrier(img: str, cdir: Path) -> bool:
    """★ 用 relative_to，不用 startswith（`C:\\a` 与 `C:\\ab` 会误配）。"""
    try:
        Path(img).resolve().relative_to(cdir.resolve())
        return True
    except ValueError:
        return False


def rpm_u32(h, addr: int):
    buf = ctypes.create_string_buffer(4)
    n = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr),
                               ctypes.cast(buf, ctypes.c_void_p), 4,
                               ctypes.byref(n))
    if not ok or n.value != 4:
        return None
    return int.from_bytes(buf.raw, "little")


def find_main_window(pid: int):
    found = []

    def _cb(hwnd, _lp):
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, cls, 256)
        if cls.value != WINDOW_CLASS:
            return True
        w = wt.DWORD(0)
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(w))
        if w.value == pid:
            found.append(hwnd)
            return False
        return True

    u32.EnumWindows(ENUMPROC(_cb), 0)
    return found[0] if found else None


# ---------------------------------------------------------------------------
# A8 收尾清扫 + 枚举器正控
# ---------------------------------------------------------------------------
def enum_probe(where: str) -> dict:
    """★★ 枚举器正控：查本进程自己的 exe 名。查不到 ⇒ 枚举器坏了。

    ★ 为什么：`list_procs` 在 CreateToolhelp32Snapshot 失败时返回空 dict，
      与「确实没有该进程」不可区分 ⇒ 会把枚举失败误判成零残留。
    """
    self_pid = os.getpid()
    self_name = Path(sys.executable).name
    procs = list_procs()
    found = [p for p, n in procs.items() if n.lower() == self_name.lower()]
    ok = self_pid in found
    return {"where": where, "self_name": self_name, "self_pid": self_pid,
            "n_procs": len(procs), "found": found[:8], "ok": ok}


def a8_sweep(cdir: Path, own_pid) -> dict:
    """按载体目录精确清扫；带前后两次枚举器正控。"""
    before = enum_probe("before_sweep")
    if not before["ok"]:
        return {"swept": [], "remaining": [{"pid": None,
                                            "image": "<ENUM_FAILED_BEFORE>"}],
                "rounds": 0, "enum_probe_before": before,
                "enum_probe_after": None, "verdict": "V_FAIL_ENUM"}

    targets = ("gamemd.exe", "ra2loader.exe", "rc4_loader.exe")
    swept, rounds = [], 0
    for r in range(3):
        rounds = r + 1
        killed = 0
        for pid, nm in list(list_procs().items()):
            if nm.lower() not in targets:
                continue
            if own_pid is not None and pid == own_pid:
                continue
            img = query_image(pid)
            if img is None or not under_carrier(img, cdir):
                continue
            h = k32.OpenProcess(0x0001 | 0x00100000, False, pid)
            if not h:
                continue
            try:
                if k32.TerminateProcess(h, 1):
                    k32.WaitForSingleObject(h, 5000)
                    killed += 1
                    swept.append({"pid": pid, "image": img})
            finally:
                k32.CloseHandle(h)
        if killed == 0:
            break
        time.sleep(0.8)

    after = enum_probe("before_remaining")
    if not after["ok"]:
        return {"swept": swept,
                "remaining": [{"pid": None, "image": "<ENUM_FAILED_AFTER>"}],
                "rounds": rounds, "enum_probe_before": before,
                "enum_probe_after": after, "verdict": "V_FAIL_ENUM"}

    remaining = []
    for pid, nm in list(list_procs().items()):
        if nm.lower() not in targets:
            continue
        if own_pid is not None and pid == own_pid:
            continue
        img = query_image(pid)
        if img is not None and under_carrier(img, cdir):
            remaining.append({"pid": pid, "image": img})

    return {"swept": swept, "remaining": remaining, "rounds": rounds,
            "enum_probe_before": before, "enum_probe_after": after,
            "verdict": "PASS" if not remaining else "V_FAIL_REMAINING"}


# ---------------------------------------------------------------------------
# dump
# ---------------------------------------------------------------------------
def write_minidump(pid: int, name: str) -> dict:
    try:
        name = safe_name(name)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    DUMP_DIR.mkdir(parents=True, exist_ok=True)
    dest = DUMP_DIR / name
    if dest.parent.resolve() != DUMP_DIR.resolve():
        return {"ok": False, "error": "dest parent mismatch"}

    k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p,
                                wt.DWORD, wt.DWORD, wt.HANDLE]
    k32.CreateFileW.restype = wt.HANDLE
    fh = k32.CreateFileW(str(dest), 0x40000000, 0, None, 2, 0x80, None)
    if not fh or fh == ctypes.c_void_p(-1).value:
        return {"ok": False, "error": "CreateFileW", "winerr": ctypes.get_last_error()}

    hp = k32.OpenProcess(DUMP_RIGHTS, False, pid)
    if not hp:
        k32.CloseHandle(fh)
        return {"ok": False, "error": "OpenProcess", "winerr": ctypes.get_last_error()}
    try:
        ok = dbg.MiniDumpWriteDump(hp, pid, fh, DUMP_TYPE_FULL, None, None, None)
        err = ctypes.get_last_error()
    finally:
        k32.CloseHandle(hp)
        k32.CloseHandle(fh)
    if not ok:
        return {"ok": False, "error": "MiniDumpWriteDump", "winerr": err}
    return {"ok": True, "path": str(dest), "size": dest.stat().st_size,
            "sha256": sha256_file(dest)}


# ---------------------------------------------------------------------------
# 守卫日志解析
# ---------------------------------------------------------------------------
def parse_guard_log(log_path: Path) -> dict:
    """从 ra2render.log 抽 [ra2rc4guard] 行，取命中计数与安装/恢复结论。"""
    out = {"present": False, "lines": [], "hits_total": None,
           "install_ok": None, "restore_memcmp": None, "restore_fnv_equal": None,
           "enabled": None, "dry_run": None}
    if not log_path.exists():
        return out
    out["present"] = True
    txt = log_path.read_text(encoding="utf-8", errors="replace")
    for ln in txt.splitlines():
        if GUARD_LOG_TAG not in ln:
            continue
        out["lines"].append(ln)
        if "EnableRC4Guard=" in ln:
            out["enabled"] = ("=1" in ln)
        if "干跑" in ln:
            out["dry_run"] = True
        if "守卫已装 8/8" in ln:
            out["install_ok"] = True
        if "原字节比对失败" in ln or "安装未完成" in ln:
            out["install_ok"] = False
        if "守卫命中计数合计" in ln:
            try:
                out["hits_total"] = int(ln.split("守卫命中计数合计")[1].split("（")[0].strip())
            except Exception:
                pass
        if "memcmp" in ln and "FNV-1a-64" in ln:
            out["restore_memcmp"] = "不等 FAIL" not in ln
            out["restore_fnv_equal"] = "相等 PASS" in ln
    return out


# ---------------------------------------------------------------------------
# 载体
# ---------------------------------------------------------------------------
def create_carrier(dst: Path, extra_files: list[Path]) -> dict:
    dst.mkdir(parents=True, exist_ok=False)
    copied = {}
    for f in sorted(SRC.iterdir()):
        if not f.is_file():
            continue
        tgt = dst / safe_name(f.name)
        shutil.copy2(f, tgt)
        copied[f.name] = tgt.stat().st_size
    for f in extra_files:
        if not f.is_file():
            raise FileNotFoundError(str(f))
        tgt = dst / safe_name(f.name)
        shutil.copy2(f, tgt)
        copied[f.name] = tgt.stat().st_size
    return copied


def rm_carrier(cdir: Path) -> tuple:
    target = cdir.resolve()
    if not target.is_relative_to(CARD) or target == CARD:
        return False, "refused: outside card root"
    last = None
    for i in range(8):
        time.sleep(1.0 + i * 0.5)
        try:
            shutil.rmtree(target)
            return True, None
        except Exception as e:      # noqa: BLE001
            last = repr(e)
    return False, last


# ---------------------------------------------------------------------------
# 单趟
# ---------------------------------------------------------------------------
def _exc_fields(de: DEBUG_EVENT) -> dict:
    er = de.u.Exception.ExceptionRecord
    n = int(er.NumberParameters)
    info = [int(er.ExceptionInformation[i] or 0) for i in range(min(n, 15))]
    return {"code": int(er.ExceptionCode),
            "address": int(er.ExceptionAddress or 0),
            "first_chance": int(de.u.Exception.dwFirstChance),
            "nparams": n, "info": info, "thread": int(de.dwThreadId)}


def one_trip(idx: int, arm: str, dll_name, hold_s: float,
             debug_timeout: float, keep_dump: bool) -> dict:
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = CARD / ("ab_%s_%s_t%d" % (stamp, arm, idx))
    # ★ 载体目录名尽量短：门禁卡的是**目录**长度（≥131 触发次生崩溃）
    carrier = out_dir / "ct" / ("c" + "0" * 10)

    rec = {"trip": idx, "arm": arm, "dll": dll_name,
           "carrier": str(carrier), "carrier_len": len(str(carrier)),
           "out_dir": str(out_dir)}
    if rec["carrier_len"] > CARRIER_PATH_MAX:
        rec["abort"] = "carrier_path_too_long"
        return rec

    out_dir.mkdir(parents=True, exist_ok=True)

    extra = []
    if arm == "B":
        if not dll_name:
            rec["abort"] = "arm_B_requires_dll"
            return rec
        extra = [CARD / "src" / "rc4_loader.exe", CARD / "src" / dll_name]
    try:
        files = create_carrier(carrier, extra)
    except Exception as e:      # noqa: BLE001
        rec["abort"] = "carrier_create_failed: %r" % (e,)
        return rec

    rec["carrier_files"] = len(files)
    rec["gamemd_sha16"] = sha256_file(carrier / "gamemd.exe")[:16]
    if rec["gamemd_sha16"] != GAMEMD_SHA16:
        rec["abort"] = "gamemd_sha_mismatch"
        _cleanup(None, carrier, rec, attached=False)
        return rec

    ex_path = carrier / "except.txt"
    ex_before = ex_path.read_bytes() if ex_path.exists() else b""
    rec["except_sha16_before"] = hashlib.sha256(ex_before).hexdigest()[:16]

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    t_launch = time.time()
    if arm == "A":
        proc = subprocess.Popen([str(carrier / "gamemd.exe")],
                                cwd=str(carrier), env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        pid = proc.pid
    else:
        proc = subprocess.Popen([str(carrier / "rc4_loader.exe"), dll_name],
                                cwd=str(carrier), env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        # ★ loader 派生 gamemd：按**载体目录**找出那个 gamemd 的 pid，
        #   绝不把 loader 自己的 pid 当游戏。
        pid = None
        for _ in range(100):
            time.sleep(0.1)
            for p, nm in list_procs().items():
                if nm.lower() != "gamemd.exe":
                    continue
                img = query_image(p)
                if img and under_carrier(img, carrier):
                    pid = p
                    break
            if pid:
                break
        if pid is None:
            rec["abort"] = "gamemd_not_found_under_carrier"
            _cleanup(proc, carrier, rec, attached=False)
            return rec
        rec["loader_pid"] = proc.pid

    rec["pid"] = pid
    rec["launch_s"] = round(time.time() - t_launch, 2)

    if not k32.DebugActiveProcess(pid):
        rec["abort"] = "DebugActiveProcess_failed"
        rec["winerr"] = ctypes.get_last_error()
        _cleanup(proc, carrier, rec, attached=False)
        return rec
    rec["debugger_attached"] = True
    t_attach = time.time()

    events, hit, dump_rec = [], None, None
    n_events = 0
    closed_at = t_close = None
    exit_seen = False

    de = DEBUG_EVENT()
    while time.time() - t_attach < debug_timeout:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 200):
            if ctypes.get_last_error() == 121:
                if closed_at is None and (time.time() - t_attach) >= hold_s:
                    hwnd = find_main_window(pid)
                    if hwnd:
                        # ★★ §374 待办 7 定谳：单例创建的唯一入口是 WM_CREATE，
                        #   而 WM_CLOSE 本身不创建也不销毁单例 ⇒ 命中与否取决于
                        #   「关窗**之前**单例是否已创建」。故关窗前必须先读一次，
                        #   否则三种退出方式很可能给出同一个答案、无法解释。
                        hp0 = k32.OpenProcess(0x0400 | 0x0010, False, pid)
                        if hp0:
                            rec["singleton_before_close"] = rpm_u32(hp0, G_SINGLETON)
                            rec["hwnd_before_close"] = rpm_u32(hp0, G_HWND)
                            k32.CloseHandle(hp0)
                        u32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                        t_close = time.time()
                        closed_at = round(time.time() - t_attach, 3)
                continue
            rec["wait_error"] = ctypes.get_last_error()
            break

        n_events += 1
        code = de.dwDebugEventCode

        if code == EXCEPTION_DEBUG_EVENT:
            ef = _exc_fields(de)
            if ef["code"] in (EXCEPTION_ACCESS_VIOLATION, EXCEPTION_BREAKPOINT):
                events.append(ef)
            if ef["code"] == EXCEPTION_ACCESS_VIOLATION:
                access = ef["info"][1] if len(ef["info"]) > 1 else None
                if ef["address"] == RC4_EIP and access == RC4_ACCESS:
                    hit = dict(ef)
                    hit["since_attach_s"] = round(time.time() - t_attach, 3)
                    hit["since_close_s"] = (round(time.time() - t_close, 3)
                                            if t_close else None)
                    dump_rec = write_minidump(pid, "rc4ab_%s_%s_t%d.dmp"
                                              % (stamp, arm, idx))
                    hp = k32.OpenProcess(0x0400 | 0x0010, False, pid)
                    if hp:
                        hit["singleton_at_hit"] = rpm_u32(hp, G_SINGLETON)
                        hit["hwnd_at_hit"] = rpm_u32(hp, G_HWND)
                        hit["exitstate_at_hit"] = rpm_u32(hp, G_EXITSTATE)
                        k32.CloseHandle(hp)
                    k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId,
                                           DBG_EXCEPTION_NOT_HANDLED)
                    break
            k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId,
                                   DBG_EXCEPTION_NOT_HANDLED)
            continue

        if code == EXIT_PROCESS_DEBUG_EVENT:
            exit_seen = True
            events.append({"code": "EXIT_PROCESS",
                           "since_attach_s": round(time.time() - t_attach, 3)})
            k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, DBG_CONTINUE)
            break

        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, DBG_CONTINUE)

    t_end = time.time()
    rec["n_debug_events"] = n_events
    rec["notable_events"] = events[-20:]
    rec["closed_at_s"] = closed_at
    rec["rc4_hit"] = hit
    rec["minidump"] = dump_rec if keep_dump else (
        {"ok": bool((dump_rec or {}).get("ok")), "suppressed": True})

    # 关窗后 ≤20 s 正常退出：用「进程已退出」+ 时延判，不看 except.txt
    # ★★ B 臂的 proc 是 **loader**，不是 gamemd。`proc.poll()` 只能说明 loader 退没退。
    #   若 loader 因自身异常先退（CreateRemoteThread 失败、WaitForSingleObject 被
    #   外部杀掉等），而 gamemd 仍在跑，用 proc.poll() 会**误判 clean_exit=True**
    #   ⇒ 假绿通道。故：B 臂一律只以 gamemd 的 pid 存活为准，不采信 proc.poll()。
    if arm == "A":
        exited = exit_seen or (proc.poll() is not None)
    else:
        # ★ 只认 gamemd（pid）已从进程表消失；loader 死活不参与判定
        exited = not any(p == pid for p in list_procs())
    rec["exit_judged_by"] = "exit_event|proc.poll" if arm == "A" else "gamemd_pid_only"
    rec["loader_alive_at_judge"] = (proc.poll() is None) if arm == "B" else None
    rec["clean_exit"] = bool(exited and closed_at is not None
                             and (t_end - t_close) <= CLOSE_WAIT_S)
    rec["exit_after_close_s"] = (round(t_end - t_close, 2) if t_close else None)

    ex_after = ex_path.read_bytes() if ex_path.exists() else b""
    rec["except_sha16_after"] = hashlib.sha256(ex_after).hexdigest()[:16]
    rec["except_changed"] = (rec["except_sha16_after"]
                             != rec["except_sha16_before"])
    if rec["except_changed"]:
        (out_dir / "except_after.txt").write_bytes(ex_after)

    rec["guard"] = parse_guard_log(carrier / "ra2render.log")
    if (carrier / "ra2render.log").exists():
        shutil.copy2(carrier / "ra2render.log", out_dir / "ra2render.log")

    _cleanup(proc, carrier, rec, attached=True)
    return rec


def _cleanup(proc, carrier: Path, rec: dict, attached: bool) -> None:
    if attached and rec.get("pid"):
        k32.DebugActiveProcessStop(rec["pid"])
    if proc is not None and proc.poll() is None:
        try:
            proc.kill()
            proc.wait(timeout=10)
        except Exception as e:      # noqa: BLE001
            rec["kill_error"] = repr(e)
    own = os.getpid()
    rec["a8"] = a8_sweep(carrier, own)
    ok, err = rm_carrier(carrier)
    rec["carrier_deleted"] = ok
    if not ok:
        rec["carrier_delete_error"] = err
    rec["leftover_procs"] = game_procs()


# ---------------------------------------------------------------------------
# 正控：证明 RPM 通道本身能读
# ---------------------------------------------------------------------------
def positive_control(carrier_root: Path) -> dict:
    """★ 正控只证「RPM 能读目标进程」，不证「崩溃会发生」。

    做法：起一个**本进程自己**的句柄，读自己进程里的一个已知变量，
    断言读到的值等于写进去的值。通道坏 ⇒ 读到 None 或错值。
    """
    probe = ctypes.c_uint32(0xDEADBEEF)
    addr = ctypes.addressof(probe)
    hp = k32.OpenProcess(0x0400 | 0x0010, False, os.getpid())
    if not hp:
        return {"ok": False, "error": "OpenProcess(self)", "winerr": ctypes.get_last_error()}
    try:
        got = rpm_u32(hp, addr)
    finally:
        k32.CloseHandle(hp)
    return {"ok": (got == 0xDEADBEEF), "wrote": 0xDEADBEEF, "read": got,
            "addr": hex(addr)}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="_rc4_ab_probe.py")
    ap.add_argument("--arm", choices=["A", "B"], required=True)
    ap.add_argument("--dll", default=None, help="B 臂要注入的单层 DLL 名")
    ap.add_argument("--trips", type=int, default=3)
    ap.add_argument("--hold-s", type=float, default=6.0)
    ap.add_argument("--debug-timeout", type=float, default=120.0)
    ap.add_argument("--live", action="store_true", help="★ 真跑；缺省是 dry-run")
    ap.add_argument("--keep-dump", action="store_true")
    args = ap.parse_args(argv)

    print("=" * 78)
    print("RC-4 A/B 探针   arm=%s  trips=%d  live=%s" % (args.arm, args.trips, args.live))
    print("=" * 78)

    checks = []
    checks.append(("源 gamemd sha16", sha256_file(SRC / "gamemd.exe")[:16], GAMEMD_SHA16))
    checks.append(("源件数", str(len([f for f in SRC.iterdir() if f.is_file()])),
                   str(SRC_FILE_COUNT)))
    checks.append(("残留游戏进程", str(len(game_procs())), "0"))
    checks.append(("dump 目录存在", str(DUMP_DIR.is_dir()), "True"))

    if args.arm == "B":
        if not args.dll:
            print("!! B 臂必须给 --dll")
            return 2
        try:
            safe_name(args.dll)
        except ValueError as e:
            print("!! --dll 非法:", e)
            return 2
        for p in (CARD / "src" / "rc4_loader.exe", CARD / "src" / args.dll):
            checks.append((p.name + " 存在", str(p.is_file()), "True"))

    # ★ 载体目录长度预检（门禁卡目录）
    probe_dir = CARD / ("ab_%s_t1" % time.strftime("%Y%m%dT%H%M%S")) / "ct" / ("c" + "0" * 10)
    checks.append(("载体目录长度 <= %d" % CARRIER_PATH_MAX,
                   str(len(str(probe_dir))), "<=%d" % CARRIER_PATH_MAX))

    ok_all = True
    for name, got, want in checks:
        if want.startswith("<="):
            good = len(got) <= int(want[2:]) if not got.isdigit() else int(got) <= int(want[2:])
        else:
            good = got == want
        ok_all &= good
        print("  %-28s got=%-24s want=%-20s %s" % (name, got, want, "OK" if good else "MISMATCH"))

    pc = positive_control(CARD)
    print("  %-28s read=%-20s %s" % ("正控（RPM 读自身）", pc.get("read"),
                                     "OK" if pc["ok"] else "FAIL"))
    ok_all &= pc["ok"]

    if not ok_all:
        print("!! 预检不过，不发射")
        return 2

    if not args.live:
        print()
        print("★ dry-run：预检全过。加 --live 才真跑。")
        print("  将执行：arm=%s × %d 趟，每趟：建载体 → 启动 → 附加调试器 → "
              "hold %.1fs 后投 WM_CLOSE → 抓首次异常 → A8 清扫 → 删载体"
              % (args.arm, args.trips, args.hold_s))
        return 0

    results = []
    for i in range(1, args.trips + 1):
        print()
        print("-" * 78)
        print("[趟 %d/%d] arm=%s" % (i, args.trips, args.arm))
        r = one_trip(i, args.arm, args.dll, args.hold_s,
                     args.debug_timeout, args.keep_dump)
        results.append(r)
        h = r.get("rc4_hit")
        g = r.get("guard") or {}
        print("  events=%s closed_at=%s hit=%s clean_exit=%s guard_hits=%s"
              % (r.get("n_debug_events"), r.get("closed_at_s"),
                 ("Eip=%08X Access=%08X" % (h["address"],
                                            h["info"][1] if len(h["info"]) > 1 else -1))
                 if h else None,
                 r.get("clean_exit"), g.get("hits_total")))
        if r.get("abort"):
            print("  ABORT:", r["abort"])
        if i < args.trips:
            time.sleep(2.0)

    stamp = time.strftime("%Y%m%dT%H%M%S")
    out = CARD / ("AB_%s_%s.json" % (args.arm, stamp))
    out.write_text(json.dumps({"arm": args.arm, "dll": args.dll,
                               "trips": results}, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    n_hit = sum(1 for r in results if r.get("rc4_hit"))
    n_clean = sum(1 for r in results if r.get("clean_exit"))
    n_guard = sum(1 for r in results
                  if (r.get("guard") or {}).get("hits_total"))
    print()
    print("[结果]", out)
    print("[汇总] %d 趟：命中 RC-4 %d，正常退出 %d，守卫有计数 %d"
          % (len(results), n_hit, n_clean, n_guard))
    return 0


if __name__ == "__main__":
    sys.exit(main())

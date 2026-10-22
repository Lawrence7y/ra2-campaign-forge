#!/usr/bin/env python
"""RC-4 调试器级抓取探针（Arm A + DebugActiveProcess + 首次异常即时 dump）。

★ 为什么 v2（轮询 except.txt）抓到的栈是错的
  v2 实测：`WM_CLOSE` 后 **8.836 s** 才检测到 `except.txt` 变化。
  此时崩溃线程早已穿过 `__except` 返回，栈被复用
  ⇒ dump 里 `[0xF9A344]` = `039587EF`，而现场要求 `0x278`。
  ⇒ **「等游戏自己写完 except.txt 再抓」在时序上必然太晚**，这是结构性错误。

★ 正确做法
  以调试器身份附加（`DebugActiveProcess`），在
  `EXCEPTION_ACCESS_VIOLATION` 首次出现时进程被内核**整体冻结**，
  此刻抓 dump ⇒ 栈就是崩溃瞬间的栈，不经任何后续执行。

★ 判据（离线可复跑，见 VERIFY_RC4_MINIDUMP.py）
  崩溃现场三元组：`Eip=0x00724737` / `Access=0x00000250` / `Ecx=0`。
  本件在异常事件里直接读这三项，命中才抓 dump。

★ 纪律
  - 零改动母本：独立脚本，不 import / 不 patch harness4/harness5。
  - 不注入、不走 ra2loader ⇒ Arm A 语义。
  - 只调试**本趟自己启动**的进程（`subprocess.Popen` 的 pid）。
  - dump 落 `D:\\ra2dumps`（仓外），不上公开仓（铁律 10）。
  - 载体每趟排他新建，趟后精确终止 + 删除 + 复测残留。

★ 用法
  python _rc4_debugdump_probe.py --trips 1
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
SRC = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/"
       "qc161_u0400_trip/_src_L1_sf8_20261020").resolve()
CARD = (ROOT / "lead" / "goal2_rc4_trigger_20261022").resolve()
DUMP_DIR = Path(r"D:\ra2dumps").resolve()

GAMEMD_SHA16 = "73201cc021497c95"
SRC_FILE_COUNT = 88
WINDOW_CLASS = "Yuri's Revenge"
CARRIER_PATH_MAX = 130

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
WM_CLOSE = 0x0010

# ★ RC-4 现场三元组（判据，不是假设）
RC4_EIP = 0x00724737
RC4_ACCESS = 0x00000250

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)

k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.OpenProcess.restype = wt.HANDLE
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.CloseHandle.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_size_t,
                                  ctypes.POINTER(ctypes.c_size_t)]
k32.ReadProcessMemory.restype = wt.BOOL
k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD,
                                           wt.LPWSTR,
                                           ctypes.POINTER(wt.DWORD)]
k32.QueryFullProcessImageNameW.restype = wt.BOOL
k32.TerminateProcess.argtypes = [wt.HANDLE, wt.UINT]
k32.TerminateProcess.restype = wt.BOOL
k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
k32.WaitForSingleObject.restype = wt.DWORD
k32.DebugActiveProcess.argtypes = [wt.DWORD]
k32.DebugActiveProcess.restype = wt.BOOL
k32.DebugActiveProcessStop.argtypes = [wt.DWORD]
k32.DebugActiveProcessStop.restype = wt.BOOL
k32.ContinueDebugEvent.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD]
k32.ContinueDebugEvent.restype = wt.BOOL
k32.WaitForDebugEvent.argtypes = [ctypes.c_void_p, wt.DWORD]
k32.WaitForDebugEvent.restype = wt.BOOL

ENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [ENUMPROC, wt.LPARAM]
u32.EnumWindows.restype = wt.BOOL
u32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u32.GetClassNameW.restype = ctypes.c_int
u32.GetWindowThreadProcessId.argtypes = [wt.HWND,
                                         ctypes.POINTER(wt.DWORD)]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u32.PostMessageW.restype = wt.BOOL

dbg.MiniDumpWriteDump.argtypes = [wt.HANDLE, wt.DWORD, wt.HANDLE,
                                  ctypes.c_int, ctypes.c_void_p,
                                  ctypes.c_void_p, ctypes.c_void_p]
dbg.MiniDumpWriteDump.restype = wt.BOOL

MINIDUMP_WITH_DATA_SEGS = 0x00000001
MINIDUMP_WITH_FULL_MEMORY = 0x00000002
MINIDUMP_WITH_HANDLE_DATA = 0x00000004
MINIDUMP_WITH_UNLOADED_MODULES = 0x00000020
MINIDUMP_WITH_PRIVATE = 0x00080000
DUMP_TYPE_FULL = (MINIDUMP_WITH_DATA_SEGS | MINIDUMP_WITH_FULL_MEMORY
                  | MINIDUMP_WITH_HANDLE_DATA
                  | MINIDUMP_WITH_UNLOADED_MODULES
                  | MINIDUMP_WITH_PRIVATE)
DUMP_RIGHTS = 0x0400 | 0x0010

# 调试事件
EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
UNLOAD_DLL_DEBUG_EVENT = 7
OUTPUT_DEBUG_STRING_EVENT = 8
RIP_EVENT = 9

DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001

EXCEPTION_ACCESS_VIOLATION = 0xC0000005
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004


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


# ---------------------------------------------------------------------------
# 路径安全：落盘路径先过 safe_name()
# ---------------------------------------------------------------------------
def safe_name(name: str) -> str:
    """dump 文件名必须是单层、无分隔符、无 `..`。"""
    if not name or name in (".", ".."):
        raise ValueError("illegal dump name: %r" % (name,))
    if "/" in name or "\\" in name:
        raise ValueError("dump name contains separator: %r" % (name,))
    if Path(name).name != name:
        raise ValueError("dump name not single-level: %r" % (name,))
    return name


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


def list_procs() -> dict:
    k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
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
            if n.lower() in ("gamemd.exe", "ra2loader.exe", "game.exe")]


def kill_under(cdir: Path) -> list:
    target = str(cdir.resolve()).lower()
    killed = []
    for pid, nm in list(list_procs().items()):
        if nm.lower() not in ("gamemd.exe", "ra2loader.exe", "game.exe"):
            continue
        hp = k32.OpenProcess(0x0001 | 0x1000, False, pid)
        if not hp:
            continue
        try:
            buf = ctypes.create_unicode_buffer(1024)
            ln = wt.DWORD(1024)
            if k32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(ln)):
                img = buf.value.lower()
                if img == target or img.startswith(target + "\\"):
                    k32.TerminateProcess(hp, 1)
                    k32.WaitForSingleObject(hp, 6000)
                    killed.append((pid, nm))
        finally:
            k32.CloseHandle(hp)
    return killed


def find_main_window(pid: int):
    found = []

    def _cb(hwnd, _lp):
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, cls, 256)
        if cls.value != WINDOW_CLASS:
            return True
        wpid = wt.DWORD(0)
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value == pid:
            found.append(hwnd)
            return False
        return True

    u32.EnumWindows(ENUMPROC(_cb), 0)
    return found[0] if found else None


def rpm_u32(h, addr: int):
    buf = ctypes.create_string_buffer(4)
    n = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr),
                               ctypes.cast(buf, ctypes.c_void_p), 4,
                               ctypes.byref(n))
    if not ok or n.value != 4:
        return None
    return int.from_bytes(buf.raw, "little")


def sha256_file(p: Path) -> str:
    hh = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            hh.update(chunk)
    return hh.hexdigest()


def create_carrier(dst: Path) -> dict:
    dst.mkdir(parents=True, exist_ok=False)
    copied = {}
    for f in sorted(SRC.iterdir()):
        if not f.is_file():
            continue
        tgt = dst / safe_name(f.name)
        shutil.copy2(f, tgt)
        copied[f.name] = {"size": tgt.stat().st_size}
    return copied


def rm_carrier(cdir: Path):
    target = Path(cdir).resolve()
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


def write_minidump(pid: int, name: str) -> dict:
    """对**被调试器冻结**的目标进程抓全内存 minidump。

    ★ 唯一通道：WER LocalDumps 对该崩溃结构上无效
      （游戏自带 __except 吞掉 AV，进程不退出）。
    ★ 用 Win32 CreateFileW 拿句柄交给 dbghelp，不经 Python open()。
    """
    try:
        name = safe_name(name)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    dest = DUMP_DIR / name
    if dest.parent.resolve() != DUMP_DIR.resolve():
        return {"ok": False, "error": "dump dest parent mismatch"}
    DUMP_DIR.mkdir(parents=True, exist_ok=True)

    k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD,
                                ctypes.c_void_p, wt.DWORD, wt.DWORD,
                                wt.HANDLE]
    k32.CreateFileW.restype = wt.HANDLE
    GENERIC_WRITE = 0x40000000
    CREATE_ALWAYS = 2
    FILE_ATTRIBUTE_NORMAL = 0x80
    fh = k32.CreateFileW(str(dest), GENERIC_WRITE, 0, None,
                         CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, None)
    if not fh or fh == ctypes.c_void_p(-1).value:
        return {"ok": False, "error": "CreateFileW failed",
                "winerr": ctypes.get_last_error()}

    hp = k32.OpenProcess(DUMP_RIGHTS, False, pid)
    if not hp:
        k32.CloseHandle(fh)
        return {"ok": False, "error": "OpenProcess failed",
                "winerr": ctypes.get_last_error()}
    try:
        ok = dbg.MiniDumpWriteDump(hp, pid, fh, DUMP_TYPE_FULL,
                                   None, None, None)
        err = ctypes.get_last_error()
    finally:
        k32.CloseHandle(hp)
        k32.CloseHandle(fh)
    if not ok:
        return {"ok": False, "error": "MiniDumpWriteDump failed",
                "winerr": err}
    return {"ok": True, "path": str(dest),
            "size": dest.stat().st_size,
            "sha256": sha256_file(dest)}


def _exc_fields(de: DEBUG_EVENT) -> dict:
    er = de.u.Exception.ExceptionRecord
    n = er.NumberParameters
    info = []
    for i in range(min(n, 15)):
        info.append(int(er.ExceptionInformation[i] or 0))
    return {"code": int(er.ExceptionCode),
            "address": int(er.ExceptionAddress or 0),
            "first_chance": int(de.u.Exception.dwFirstChance),
            "nparams": int(n),
            "info": info,
            "thread": int(de.dwThreadId)}


def one_trip(idx: int, hold_s: float, window_timeout: float,
             debug_timeout: float) -> dict:
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = CARD / ("dbg_%s_t%d" % (stamp, idx))
    carrier = out_dir / "ct" / ("c_" + "0" * 12 + "_12345")
    rec = {"trip": idx, "carrier": str(carrier),
           "carrier_path_len": len(str(carrier)),
           "out_dir": str(out_dir)}
    if rec["carrier_path_len"] > CARRIER_PATH_MAX:
        rec["abort"] = "carrier_path_too_long"
        return rec

    out_dir.mkdir(parents=True, exist_ok=True)
    t_copy = time.time()
    files = create_carrier(carrier)
    rec["carrier_files"] = len(files)
    rec["carrier_copy_s"] = round(time.time() - t_copy, 1)
    rec["gamemd_sha16"] = sha256_file(carrier / "gamemd.exe")[:16]
    if rec["carrier_files"] != SRC_FILE_COUNT:
        rec["abort"] = "carrier_file_count_%d" % rec["carrier_files"]
        return rec
    if rec["gamemd_sha16"] != GAMEMD_SHA16:
        rec["abort"] = "gamemd_sha_mismatch"
        return rec

    ex_path = carrier / "except.txt"
    ex_before = ex_path.read_bytes() if ex_path.exists() else b""
    rec["except_sha16_before"] = hashlib.sha256(ex_before).hexdigest()[:16]

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t_launch = time.time()
    proc = subprocess.Popen([str(carrier / "gamemd.exe")],
                            cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    rec["pid"] = proc.pid
    pid = proc.pid

    # ★ 附加调试器（只调试本趟自己启动的 pid）
    if not k32.DebugActiveProcess(pid):
        rec["abort"] = "DebugActiveProcess_failed"
        rec["winerr"] = ctypes.get_last_error()
        _cleanup(proc, carrier, rec, attached=False)
        return rec
    rec["debugger_attached"] = True
    t_attach = time.time()

    events = []
    hit = None
    dump_rec = None
    n_events = 0
    hwnd_seen = None
    closed_at = None
    t_close = None

    de = DEBUG_EVENT()
    while time.time() - t_attach < debug_timeout:
        if not k32.WaitForDebugEvent(ctypes.byref(de), 200):
            err = ctypes.get_last_error()
            if err == 121:          # ERROR_SEM_TIMEOUT
                # 空闲：若已过 hold_s 且还没关窗 ⇒ 投 WM_CLOSE
                if closed_at is None and (time.time() - t_attach) >= hold_s:
                    hwnd_seen = find_main_window(pid)
                    if hwnd_seen:
                        u32.PostMessageW(hwnd_seen, WM_CLOSE, 0, 0)
                        t_close = time.time()
                        closed_at = round(time.time() - t_attach, 3)
                continue
            rec["wait_error"] = err
            break

        n_events += 1
        code = de.dwDebugEventCode

        if code == EXCEPTION_DEBUG_EVENT:
            ef = _exc_fields(de)
            # ★ 只记关键异常，避免日志爆掉
            if ef["code"] in (EXCEPTION_ACCESS_VIOLATION,
                              EXCEPTION_BREAKPOINT):
                events.append(ef)
            if ef["code"] == EXCEPTION_ACCESS_VIOLATION:
                access = ef["info"][1] if len(ef["info"]) > 1 else None
                if ef["address"] == RC4_EIP and access == RC4_ACCESS:
                    hit = dict(ef)
                    hit["since_attach_s"] = round(time.time() - t_attach, 3)
                    hit["since_close_s"] = (round(time.time() - t_close, 3)
                                            if t_close else None)
                    # ★ 进程此刻被内核冻结 ⇒ 立刻抓，栈即崩溃瞬间的栈
                    dump_rec = write_minidump(
                        pid, "rc4dbg_%s_t%d.dmp" % (stamp, idx))
                    hit["singleton_at_hit"] = None
                    hp = k32.OpenProcess(0x0400 | 0x0010, False, pid)
                    if hp:
                        hit["singleton_at_hit"] = rpm_u32(hp, G_SINGLETON)
                        hit["hwnd_at_hit"] = rpm_u32(hp, G_HWND)
                        hit["exitstate_at_hit"] = rpm_u32(hp, G_EXITSTATE)
                        k32.CloseHandle(hp)
                    # 交还给游戏自己的 __except（保持原有语义，只观察不改变）
                    k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId,
                                           DBG_EXCEPTION_NOT_HANDLED)
                    break
            k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId,
                                   DBG_EXCEPTION_NOT_HANDLED)
            continue

        if code == EXIT_PROCESS_DEBUG_EVENT:
            events.append({"code": "EXIT_PROCESS",
                           "since_attach_s": round(time.time() - t_attach, 3)})
            k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, DBG_CONTINUE)
            break

        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, DBG_CONTINUE)

    rec["n_debug_events"] = n_events
    rec["notable_events"] = events[-20:]
    rec["closed_at_s"] = closed_at
    rec["rc4_hit"] = hit
    rec["minidump"] = dump_rec

    ex_after = ex_path.read_bytes() if ex_path.exists() else b""
    rec["except_sha16_after"] = hashlib.sha256(ex_after).hexdigest()[:16]
    rec["except_changed"] = (rec["except_sha16_after"]
                             != rec["except_sha16_before"])
    if rec["except_changed"]:
        (out_dir / "except_after.txt").write_bytes(ex_after)
        rec["except_after_bytes"] = len(ex_after)

    _cleanup(proc, carrier, rec, attached=True)
    return rec


def _cleanup(proc, carrier: Path, rec: dict, attached: bool) -> None:
    if attached:
        k32.DebugActiveProcessStop(proc.pid)
    rec["killed_on_cleanup"] = kill_under(carrier)
    if proc.poll() is None:
        try:
            proc.kill()
            proc.wait(timeout=10)
        except Exception as e:      # noqa: BLE001
            rec["kill_error"] = repr(e)
    ok, err = rm_carrier(carrier)
    rec["carrier_deleted"] = ok
    if not ok:
        rec["carrier_delete_error"] = err
    rec["leftover_procs"] = game_procs()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="_rc4_debugdump_probe.py")
    ap.add_argument("--trips", type=int, default=1)
    ap.add_argument("--hold-s", type=float, default=6.0)
    ap.add_argument("--window-timeout", type=float, default=180.0)
    ap.add_argument("--debug-timeout", type=float, default=120.0)
    args = ap.parse_args(argv)

    print("=" * 78)
    print("RC-4 调试器级抓取探针（Arm A + 首次异常即时 dump）")
    print("=" * 78)

    checks = [("源 gamemd sha16", sha256_file(SRC / "gamemd.exe")[:16],
               GAMEMD_SHA16),
              ("源件数", str(len([f for f in SRC.iterdir() if f.is_file()])),
               str(SRC_FILE_COUNT)),
              ("残留游戏进程", str(len(game_procs())), "0"),
              ("dump 目录存在", str(DUMP_DIR.is_dir()), "True")]
    ok_all = True
    for name, got, want in checks:
        good = got == want
        ok_all &= good
        print("  %-22s got=%-20s want=%-20s %s"
              % (name, got, want, "OK" if good else "MISMATCH"))
    if not ok_all:
        print("!! 预检不过，不发射")
        return 2

    results = []
    for i in range(1, args.trips + 1):
        print()
        print("-" * 78)
        print("[趟 %d/%d]" % (i, args.trips))
        r = one_trip(i, args.hold_s, args.window_timeout,
                     args.debug_timeout)
        results.append(r)
        hit = r.get("rc4_hit")
        print("  events=%s closed_at=%s rc4_hit=%s dump=%s"
              % (r.get("n_debug_events"), r.get("closed_at_s"),
                 ("Eip=%08X Access=%08X @%.3fs"
                  % (hit["address"],
                     hit["info"][1] if len(hit["info"]) > 1 else -1,
                     hit["since_close_s"] or -1)) if hit else None,
                 (r.get("minidump") or {}).get("ok")))
        if r.get("abort"):
            print("  ABORT:", r["abort"])
        if i < args.trips:
            time.sleep(2.0)

    stamp = time.strftime("%Y%m%dT%H%M%S")
    out = CARD / ("PROBE_DBG_%s.json" % stamp)
    out.write_text(json.dumps({"trips": results}, ensure_ascii=False,
                              indent=2), encoding="utf-8")
    n = sum(1 for r in results if r.get("rc4_hit"))
    nd = sum(1 for r in results
             if (r.get("minidump") or {}).get("ok"))
    print()
    print("[结果]", out)
    print("[汇总] %d 趟，%d 趟命中 RC-4 首次异常，%d 份 dump"
          % (len(results), n, nd))
    return 0


if __name__ == "__main__":
    sys.exit(main())

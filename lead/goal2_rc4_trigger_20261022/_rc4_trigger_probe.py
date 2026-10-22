#!/usr/bin/env python
"""RC-4 尾窗触发探针（Arm A：原版直启 + 零注入）。

★ 目的
  在 `HKLM\\...\\LocalDumps\\gamemd.exe` 已武装（DumpType=2/DumpCount=3/
  DumpFolder=D:\\ra2dumps）的前提下，用「向主窗投 WM_CLOSE」而非
  `TerminateProcess` 收尾，观察 RC-4（Eip=0x00724737 / Access=0x250）是否出现，
  并捕获 WER 真转储。

★ 为什么必须换收尾方式（结构性理由，不是偏好）
  崩溃现场 `ecx = [0x887368] = 0`，而 `0x777803` 在 `WM_DESTROY` 块内把该全局清零。
  ⇒ 崩溃只可能发生在 **WM_DESTROY 之后、进程退出之前**的尾窗。
  `TerminateProcess` 直接终结进程，**结构上跳过**整个尾窗 ⇒ 永远抓不到。
  历史多趟零复现即由此而来，不是「崩溃不存在」。

★ 纪律
  - 零改动母本：本件为独立新脚本，不 import、不 patch harness4/harness5。
  - 不注入、不走 ra2loader ⇒ Arm A 语义（S-4 零命中）。
  - 载体每趟排他新建，趟后精确终止 + 删除 + 复测残留。
  - 只读 RPM 采样 `[0x887368]` / `[0xB73550]` / `[0xA8EDD8]`，不写进程内存。

★ 用法
  python _rc4_trigger_probe.py --trips 1
  python _rc4_trigger_probe.py --trips 5 --hold-s 6
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
SRC = ROOT / ("out/re_work/work_chain/CONTINUE_20261003/lead/"
              "qc161_u0400_trip/_src_L1_sf8_20261020")
CARD = ROOT / "lead" / "goal2_rc4_trigger_20261022"
DUMP_DIR = Path(r"D:\ra2dumps")

GAMEMD_SHA16 = "73201cc021497c95"
SRC_FILE_COUNT = 88
WINDOW_CLASS = "Yuri's Revenge"
CARRIER_PATH_MAX = 130

# 只读采样点
G_SINGLETON = 0x00887368   # MouseClass 单例（崩溃时 ecx 的来源）
G_HWND = 0x00B73550        # 主窗句柄（CreateWindowExA 结果落点）
G_EXITSTATE = 0x00A8EDD8   # 引擎退出状态机

WM_CLOSE = 0x0010

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
dbg = ctypes.WinDLL("dbghelp", use_last_error=True)

# ---- minidump：WER LocalDumps 对该崩溃结构上无效，必须活体抓 ----
#   ★ 理由：游戏自带 __except 捕获 AV 后写 except.txt 且**进程不退出**
#     （v1 实测关窗后 90 s 仍存活）⇒ WER 只在「未处理异常终止进程」时介入
#     ⇒ LocalDumps 永远不会触发。这不是配置问题，是机制问题。
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
# MiniDumpWriteDump 需要 PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
DUMP_RIGHTS = 0x0400 | 0x0010

# ---- 每个 ctypes 调用都必须声明 argtypes/restype（不声明会让 HANDLE 在 64 位截断） ----
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
u32.IsWindow.argtypes = [wt.HWND]
u32.IsWindow.restype = wt.BOOL


# ---------------------------------------------------------------------------
# 进程枚举
# ---------------------------------------------------------------------------
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
    target = str(cdir).lower()
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
                if target in buf.value.lower():
                    k32.TerminateProcess(hp, 1)
                    k32.WaitForSingleObject(hp, 6000)
                    killed.append((pid, nm))
        finally:
            k32.CloseHandle(hp)
    return killed


# ---------------------------------------------------------------------------
# 主窗 / 内存采样
# ---------------------------------------------------------------------------
def find_main_window(pid: int):
    """按窗口类名 + 进程号定位主窗。类名由 RegisterClassA 常量给出（见 §342）。"""
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


def sample(h) -> dict:
    return {"singleton": rpm_u32(h, G_SINGLETON),
            "hwnd": rpm_u32(h, G_HWND),
            "exitstate": rpm_u32(h, G_EXITSTATE),
            "t": round(time.time(), 3)}


# ---------------------------------------------------------------------------
# 载体
# ---------------------------------------------------------------------------
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
        tgt = dst / f.name
        shutil.copy2(f, tgt)
        copied[f.name] = {"size": tgt.stat().st_size,
                          "sha256": sha256_file(tgt)}
    return copied


def rm_carrier(cdir: Path):
    last = None
    for i in range(8):
        time.sleep(1.0 + i * 0.5)
        try:
            shutil.rmtree(cdir)
            return True, None
        except Exception as e:      # noqa: BLE001 - 需要报出真实原因
            last = repr(e)
    return False, last


def write_minidump(pid: int, name: str) -> dict:
    """对**仍活着**的目标进程抓全内存 minidump。

    ★ 这是本卡唯一的「真转储」通道（WER LocalDumps 结构上无效，见文件头注）。
    ★ 落盘路径由固定目录 + 本函数生成的固定名拼成，且写前断言父目录存在、
      文件名不含分隔符；用 Win32 CreateFileW 拿句柄交给 dbghelp，
      不经 Python `open()`。
    """
    if not name or "/" in name or "\\" in name or ".." in name:
        return {"ok": False, "error": "illegal dump name: %r" % (name,)}
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


def dump_snapshot() -> dict:
    if not DUMP_DIR.is_dir():
        return {}
    out = {}
    for f in DUMP_DIR.iterdir():
        if f.is_file():
            out[f.name] = {"size": f.stat().st_size,
                           "mtime": round(f.stat().st_mtime, 3)}
    return out


# ---------------------------------------------------------------------------
# 单趟
# ---------------------------------------------------------------------------
def one_trip(idx: int, hold_s: float, window_timeout: float,
             exit_timeout: float) -> dict:
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = CARD / f"probe_{stamp}_t{idx}"
    carrier = out_dir / "ct" / ("c_" + "0" * 12 + "_12345")
    rec = {"trip": idx, "carrier": str(carrier),
           "carrier_path_len": len(str(carrier)),
           "out_dir": str(out_dir)}

    if rec["carrier_path_len"] > CARRIER_PATH_MAX:
        rec["abort"] = "carrier_path_too_long"
        return rec

    dumps_before = dump_snapshot()
    out_dir.mkdir(parents=True, exist_ok=True)

    t_copy = time.time()
    files = create_carrier(carrier)
    rec["carrier_files"] = len(files)
    rec["carrier_copy_s"] = round(time.time() - t_copy, 1)
    rec["gamemd_sha16"] = files.get("gamemd.exe", {}).get("sha256", "")[:16]
    if rec["carrier_files"] != SRC_FILE_COUNT:
        rec["abort"] = "carrier_file_count_%d" % rec["carrier_files"]
        return rec
    if rec["gamemd_sha16"] != GAMEMD_SHA16:
        rec["abort"] = "gamemd_sha_mismatch"
        return rec

    except_before = (carrier / "except.txt").read_bytes() \
        if (carrier / "except.txt").exists() else b""
    rec["except_sha16_before"] = hashlib.sha256(except_before).hexdigest()[:16]
    except_digest_before = hashlib.sha256(except_before).digest()

    import subprocess
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    t_launch = time.time()
    proc = subprocess.Popen([str(carrier / "gamemd.exe")],
                            cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    rec["pid"] = proc.pid
    rec["launch_s"] = round(time.time() - t_launch, 2)

    hwnd = None
    while time.time() - t_launch < window_timeout:
        if proc.poll() is not None:
            break
        hwnd = find_main_window(proc.pid)
        if hwnd:
            break
        time.sleep(0.5)
    rec["window_found"] = hwnd is not None
    rec["window_found_s"] = round(time.time() - t_launch, 2)

    if hwnd is None:
        rec["exit_code_early"] = proc.poll()
        rec["crashed_early"] = (proc.poll() is not None
                                and proc.poll() not in (0,))
        # 早亡也可能是崩溃（有 dump 就是证据）
        time.sleep(3.0)
        dumps_after = dump_snapshot()
        rec["dumps_new"] = sorted(set(dumps_after) - set(dumps_before))
        rec["dump_detail"] = {k: dumps_after[k]
                              for k in rec["dumps_new"]}
        _cleanup(proc, carrier, out_dir, rec)
        return rec

    # ---- 关窗前静置采样：确认单例非 0（尾窗前基线） ----
    h = k32.OpenProcess(0x0400 | 0x0010, False, proc.pid)  # QUERY|VM_READ
    samples_before = []
    if h:
        t_end = time.time() + hold_s
        while time.time() < t_end and proc.poll() is None:
            samples_before.append(sample(h))
            time.sleep(0.5)
    rec["samples_before"] = samples_before

    # ---- 投 WM_CLOSE（引擎自己的关窗路径，不是 TerminateProcess） ----
    rec["close_posted"] = bool(u32.PostMessageW(hwnd, WM_CLOSE, 0, 0))
    t_close = time.time()

    samples_after = []
    exited = False
    crashed = False
    t_detect = None
    dump_rec = None
    while time.time() - t_close < exit_timeout:
        if proc.poll() is not None:
            exited = True
            break
        if h:
            samples_after.append(sample(h))
        # ★ 崩溃判据：except.txt 内容变了 ⇒ 引擎自己的异常处理器已落盘
        cur = (carrier / "except.txt").read_bytes() \
            if (carrier / "except.txt").exists() else b""
        if hashlib.sha256(cur).digest() != except_digest_before:
            crashed = True
            t_detect = round(time.time() - t_close, 3)
            # ★ 趁进程还活着抓全内存 dump（WER 拿不到，见文件头注）
            dump_rec = write_minidump(proc.pid,
                                      "rc4_%s_t%d.dmp" % (stamp, idx))
            break
        time.sleep(0.2)

    rec["crashed"] = crashed
    rec["detect_s_after_close"] = t_detect
    rec["minidump"] = dump_rec
    rec["exited_after_close"] = exited
    rec["close_to_exit_s"] = round(time.time() - t_close, 2)
    rec["samples_after"] = samples_after
    rec["exit_code"] = proc.poll()

    # WER 落盘可能滞后于进程退出
    time.sleep(4.0)
    dumps_after = dump_snapshot()
    rec["dumps_new"] = sorted(set(dumps_after) - set(dumps_before))
    rec["dump_detail"] = {k: dumps_after[k] for k in rec["dumps_new"]}

    if h:
        k32.CloseHandle(h)

    # ---- except.txt 是否新增（铁律 7：零新增不得单独当未崩溃） ----
    ex_after = (carrier / "except.txt").read_bytes() \
        if (carrier / "except.txt").exists() else b""
    rec["except_sha16_after"] = hashlib.sha256(ex_after).hexdigest()[:16]
    rec["except_changed"] = (rec["except_sha16_after"]
                             != rec["except_sha16_before"])
    if rec["except_changed"]:
        (out_dir / "except_after.txt").write_bytes(ex_after)
        rec["except_after_bytes"] = len(ex_after)

    _cleanup(proc, carrier, out_dir, rec)
    return rec


def _cleanup(proc, carrier: Path, out_dir: Path, rec: dict) -> None:
    killed = kill_under(carrier)
    rec["killed_on_cleanup"] = killed
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
    rec["carrier_residue"] = [p.name for p in carrier.parent.glob("c_*")
                              if p.exists()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="_rc4_trigger_probe.py")
    ap.add_argument("--trips", type=int, default=1)
    ap.add_argument("--hold-s", type=float, default=6.0,
                    help="关窗前静置秒数（取尾窗前基线）")
    ap.add_argument("--window-timeout", type=float, default=180.0)
    ap.add_argument("--exit-timeout", type=float, default=90.0)
    args = ap.parse_args(argv)

    print("=" * 78)
    print("RC-4 尾窗触发探针 v2（Arm A + WM_CLOSE 收尾 + 活体 minidump）")
    print("=" * 78)

    # ---- 预检 ----
    checks = []
    g = SRC / "gamemd.exe"
    checks.append(("源 gamemd sha16", sha256_file(g)[:16], GAMEMD_SHA16))
    n_src = len([f for f in SRC.iterdir() if f.is_file()])
    checks.append(("源件数", str(n_src), str(SRC_FILE_COUNT)))
    checks.append(("残留游戏进程", str(len(game_procs())), "0"))
    checks.append(("dump 目录存在", str(DUMP_DIR.is_dir()), "True"))
    planned = CARD / ("probe_20261022T000000_t0" ) / "ct" / \
        ("c_" + "0" * 12 + "_12345")
    checks.append(("载体路径预演 len<=130", str(len(str(planned)) <= 130),
                   "True"))
    ok_all = True
    for name, got, want in checks:
        good = got == want
        ok_all &= good
        print("  %-24s got=%-22s want=%-22s %s"
              % (name, got, want, "OK" if good else "MISMATCH"))
    if not ok_all:
        print("!! 预检不过，不发射")
        return 2

    results = []
    for i in range(1, args.trips + 1):
        print()
        print("-" * 78)
        print("[趟 %d/%d]" % (i, args.trips))
        r = one_trip(i, args.hold_s, args.window_timeout, args.exit_timeout)
        results.append(r)
        print("  carrier_files=%s window_found=%s exit=%s dumps_new=%s "
              "except_changed=%s"
              % (r.get("carrier_files"), r.get("window_found"),
                 r.get("exit_code"), r.get("dumps_new"),
                 r.get("except_changed")))
        if r.get("abort"):
            print("  ABORT:", r["abort"])
        if i < args.trips:
            time.sleep(2.0)

    stamp = time.strftime("%Y%m%dT%H%M%S")
    out = CARD / ("PROBE_RUN_%s.json" % stamp)
    out.write_text(json.dumps({"trips": results}, ensure_ascii=False,
                              indent=2), encoding="utf-8")
    print()
    print("[结果]", out)

    n_crash = sum(1 for r in results
                  if r.get("exit_code") not in (None, 0)
                  or r.get("dumps_new") or r.get("crashed"))
    n_dump = sum(1 for r in results
                 if (r.get("minidump") or {}).get("ok"))
    print("[汇总] %d 趟，%d 趟复现 RC-4，%d 份活体 minidump"
          % (len(results), n_crash, n_dump))
    return 0


if __name__ == "__main__":
    sys.exit(main())

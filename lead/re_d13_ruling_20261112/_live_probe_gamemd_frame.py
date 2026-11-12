# -*- coding: utf-8 -*-
"""E3 对 gamemd.exe 本体的**只读**帧号探针（最小侵入，先不挂起任何线程）。

目的：验证 G_FRAME=0xA8ED84 在真实 gamemd.exe 里是否可读、是否随帧推进。
      —— 这是把 E3 接到游戏上的最后一块前置。

★ 本脚本只做：
    OpenProcess(VM_READ|QUERY) → 反复 ReadProcessMemory(0xA8ED84) → 看值/状态
   **不挂起线程、不取上下文、不回溯、不写任何东西。**

退出方式：轮询 N 秒后 CloseHandle，并 terminate 自己启动的游戏进程（若 --launch）。
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import sys
import time
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
BASE = REPO / "lead" / "re_d13_ruling_20261112"
GAME_DIR = REPO / "ra2youli"
G_FRAME = 0x00A8ED84
G_TICK = 0x00A8ED80
G_EXITSTATE = 0x00A8EDD8
G_SINGLETON = 0x00887368

MEM_COMMIT = 0x1000


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p),
                ("AllocationProtect", wt.DWORD), ("RegionSize", ctypes.c_size_t),
                ("State", wt.DWORD), ("Protect", wt.DWORD), ("Type", wt.DWORD)]


def bind():
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = wt.HANDLE
    k.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k.CloseHandle.argtypes = [wt.HANDLE]
    k.ReadProcessMemory.restype = wt.BOOL
    k.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.restype = ctypes.c_size_t
    k.VirtualQueryEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_size_t]
    k.IsWow64Process.restype = wt.BOOL
    k.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]
    return k


def read_u32(k, h, addr):
    buf = (ctypes.c_char * 4)()
    n = ctypes.c_size_t(0)
    ok = k.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, 4, ctypes.byref(n))
    if ok and n.value == 4:
        return ("ok", int.from_bytes(buf.raw, "little"))
    mbi = MBI()
    got = k.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
    if got and mbi.State != MEM_COMMIT:
        return ("page_absent", {"state": mbi.State})
    return ("read_fail", {"err": ctypes.get_last_error()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=0, help="已运行游戏的 pid；0=自己启动")
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--exe", default=str(GAME_DIR / "gamemd.exe"))
    a = ap.parse_args()

    import subprocess
    proc = None
    pid = a.pid
    if pid == 0:
        exe = Path(a.exe)
        if not exe.exists():
            print("!! 找不到 %s" % exe); return 2
        print("启动 gamemd.exe（工作目录=%s）" % exe.parent)
        proc = subprocess.Popen([str(exe)], cwd=str(exe.parent),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = proc.pid
        time.sleep(3.0)      # 等它起来
    print("目标 pid = %d" % pid)

    k = bind()
    h = k.OpenProcess(0x0010 | 0x0400, False, pid)     # VM_READ | QUERY
    if not h:
        print("!! OpenProcess 失败 err=%d" % ctypes.get_last_error())
        if proc:
            proc.terminate()
        return 3
    try:
        foo = wt.BOOL(0)
        k.IsWow64Process(h, ctypes.byref(foo))
        print("IsWow64Process = %s (gamemd.exe 应为 True)" % bool(foo.value))

        # 先看目标地址的可读性（不挂起、不采样）
        print("\n-- 关键地址可读性 --")
        for name, addr in (("G_SINGLETON", G_SINGLETON), ("G_TICK", G_TICK),
                           ("G_FRAME", G_FRAME), ("G_EXITSTATE", G_EXITSTATE)):
            kind, val = read_u32(k, h, addr)
            print("  %-12s @ %#010x : %-12s %s"
                  % (name, addr, kind, val if kind == "ok" else val))

        # 轮询帧号，看是否推进
        print("\n-- 轮询 G_FRAME %g s（间隔 %g s）--" % (a.seconds, a.interval))
        t0 = time.monotonic()
        samples = []
        while time.monotonic() - t0 < a.seconds:
            kind, val = read_u32(k, h, G_FRAME)
            if kind == "ok":
                samples.append((round(time.monotonic() - t0, 3), val))
            else:
                samples.append((round(time.monotonic() - t0, 3), None))
            time.sleep(a.interval)

        vals = [v for _, v in samples if v is not None]
        print("  采样 %d 次，可读 %d 次" % (len(samples), len(vals)))
        if vals:
            print("  首值=%s 末值=%s 最小=%s 最大=%s 不同值数=%d"
                  % (vals[0], vals[-1], min(vals), max(vals), len(set(vals))))
            deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
            if deltas:
                print("  Δ 分布: min=%s max=%s  非零Δ次数=%d/%d"
                      % (min(deltas), max(deltas),
                         sum(1 for d in deltas if d != 0), len(deltas)))
            print("\n  前 10 个样本（t, G_FRAME）:")
            for t, v in samples[:10]:
                print("    %.2fs  %s" % (t, v))
            print("  ...")
            for t, v in samples[-5:]:
                print("    %.2fs  %s" % (t, v))

            # 判据
            print("\n-- 判据 --")
            moving = len(set(vals)) > 1
            print("  [%s] G_FRAME 在轮询窗口内变化过（%s）"
                  % ("OK" if moving else "NOTE", "随帧推进" if moving else "未变化/可能停在菜单"))
            readable = len(vals) == len(samples)
            print("  [%s] G_FRAME 全程可读" % ("OK" if readable else "NOTE"))
        else:
            print("  [FAIL] G_FRAME 全程不可读 —— 地址语义可能不适用于该构建/状态")
    finally:
        k.CloseHandle(h)
        if proc is not None:
            try:
                proc.terminate(); proc.wait(timeout=8)
                print("\n已终止 gamemd.exe rc=%r" % proc.returncode)
            except Exception as e:                       # noqa: BLE001
                print("\n终止失败: %s" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())

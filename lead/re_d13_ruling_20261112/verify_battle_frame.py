# -*- coding: utf-8 -*-
"""E3 手动对战 G_FRAME 只读验证 —— 自动发现已运行的 gamemd.exe。

用法（你先手动进对战，然后运行本脚本）:
    python -I -X utf8 <本文件>

本脚本会：
  1. 自动找到**已运行的** gamemd.exe（不需要你查 pid）
  2. 打印进程信息（pid / 位宽 / 路径）供你核对
  3. 只读探测四个关键地址可读性
  4. 轮询 G_FRAME 一段时间，报「是否递增 / Δ 分布 / 推算 fps」
  5. 可选：若检测到帧号停滞（连续 N 秒不变），**自动**做一次真栈回溯（拿冻结栈）

★ 全程只读 + 只在 --stack-on-stall 时做一次挂起采样（≤300ms，逐线程挂→走→立刻恢复）；
  **绝不修改游戏内存、不写文件到游戏目录、不终止你的游戏。**

参数：
  --seconds N        轮询秒数（默认 25）
  --interval S       采样间隔秒（默认 0.25）
  --stall-n S        判停滞的阈值秒（默认 1.0，与 C1 一致）
  --stack-on-stall   检测到停滞后自动做一次真栈回溯
  --pid P            指定 pid（省略则自动发现）
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import importlib.util
import os
import statistics
import sys
import time
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")

G_FRAME = 0x00A8ED84
G_TICK = 0x00A8ED80
G_SINGLETON = 0x00887368
G_EXITSTATE = 0x00A8EDD8

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.IsWow64Process.restype = wt.BOOL
k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]
k32.QueryFullProcessImageNameW.restype = wt.BOOL
k32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR,
                                           ctypes.POINTER(wt.DWORD)]

TH32CS_SNAPPROCESS = 0x00000002


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD), ("th32DefaultHeapID", ctypes.c_void_p),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD), ("pcPriClassBase", wt.LONG),
                ("dwFlags", wt.DWORD), ("szExeFile", wt.WCHAR * 260)]


k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Process32FirstW.restype = wt.BOOL
k32.Process32FirstW.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.Process32NextW.restype = wt.BOOL
k32.Process32NextW.argtypes = [wt.HANDLE, ctypes.c_void_p]


def find_gamemd():
    """返回 [(pid, exe_name)]，只找 gamemd.exe。"""
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    out = []
    if not snap or snap == -1:
        return out
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(pe))
        while ok:
            name = pe.szExeFile
            if name.lower() in ("gamemd.exe",):
                out.append((int(pe.th32ProcessID), name))
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            ok = k32.Process32NextW(snap, ctypes.byref(pe))
    finally:
        k32.CloseHandle(snap)
    return out


def proc_path(pid):
    h = k32.OpenProcess(0x1000, False, pid)          # QUERY_LIMITED_INFORMATION
    if not h:
        return "?"
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wt.DWORD(1024)
        if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return buf.value
        return "?"
    finally:
        k32.CloseHandle(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--seconds", type=float, default=25.0)
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--stall-n", type=float, default=1.0)
    ap.add_argument("--stack-on-stall", action="store_true")
    a = ap.parse_args()

    pid = a.pid
    if not pid:
        found = find_gamemd()
        print("自动发现 gamemd.exe: %s" % (found if found else "无"))
        if not found:
            print("\n!! 没找到正在运行的 gamemd.exe。")
            print("   请先：cd D:\\Project\\ra2-campaign-forge\\ra2youli && .\\gamemd.exe")
            print("   并手动点进一局遭遇战（进入局内、能看到自己的基地/单位）后再跑本脚本。")
            return 2
        if len(found) > 1:
            print("!! 有多个 gamemd.exe，请用 --pid 指定：%s" % found)
            return 2
        pid = found[0][0]

    print()
    print("=" * 74)
    print("E3 手动对战 G_FRAME 只读验证")
    print("=" * 74)
    print("目标 pid = %d" % pid)
    print("exe 路径 = %s" % proc_path(pid))

    h = k32.OpenProcess(0x0010 | 0x0400, False, pid)   # VM_READ | QUERY
    if not h:
        print("!! OpenProcess 失败 err=%d（权限不足？请以相同或更高权限运行）"
              % ctypes.get_last_error())
        return 3
    try:
        flag = wt.BOOL(0)
        k32.IsWow64Process(h, ctypes.byref(flag))
        print("IsWow64Process = %s（gamemd.exe 应为 True）" % bool(flag.value))

        def rd(addr):
            b = (ctypes.c_char * 4)()
            n = ctypes.c_size_t(0)
            ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), b, 4, ctypes.byref(n))
            return int.from_bytes(b.raw, "little") if ok and n.value == 4 else None

        print("\n-- 关键地址可读性 --")
        for name, addr in (("G_SINGLETON", G_SINGLETON), ("G_TICK", G_TICK),
                           ("G_FRAME", G_FRAME), ("G_EXITSTATE", G_EXITSTATE)):
            v = rd(addr)
            print("  %-12s @ %#010x : %s"
                  % (name, addr, ("%d (0x%X)" % (v, v)) if v is not None else "读不到"))

        print("\n-- 轮询 G_FRAME %.0fs（间隔 %.2fs）--" % (a.seconds, a.interval))
        t0 = time.monotonic()
        samples = []
        stall_flag = False
        stall_at = None
        det_base = None
        det_base_t = None
        last_stack = None
        while time.monotonic() - t0 < a.seconds:
            now = time.monotonic()
            v = rd(G_FRAME)
            samples.append((round(now - t0, 3), v))
            # 停滞检测（与 C1 同语义：读不到不算停滞）
            if v is not None:
                if det_base is None or v != det_base:
                    det_base, det_base_t = v, now
                elif (now - det_base_t) >= a.stall_n and not stall_flag:
                    stall_flag = True
                    stall_at = round(now - t0, 3)
                    print("  ★ 检测到帧号停滞 %.1fs @ t=%.2fs（frame=%s）"
                          % (a.stall_n, stall_at, v))
                    if a.stack_on_stall:
                        last_stack = do_stack_sample(pid)
            time.sleep(a.interval)

        vals = [v for _, v in samples if v is not None]
        print("\n-- 结果 --")
        print("  采样 %d 次，可读 %d 次" % (len(samples), len(vals)))
        if not vals:
            print("  [FAIL] G_FRAME 全程读不到 —— 检查是否真的在游戏里、权限是否足够")
            return 4
        print("  首值=%s 末值=%s min=%s max=%s 不同值数=%d"
              % (vals[0], vals[-1], min(vals), max(vals), len(set(vals))))
        deltas = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
        nz = [d for d in deltas if d != 0]
        print("  Δ: min=%s max=%s 非零Δ=%d/%d"
              % (min(deltas), max(deltas), len(nz), len(deltas)))

        advancing = len(set(vals)) > 1
        print()
        if advancing:
            med = statistics.median(nz)
            fps = med / a.interval
            print("  [PASS] G_FRAME **确实随帧推进**")
            print("         0.25s 采样下 Δ 中位 = %s ⇒ 约 %.1f fps" % (med, fps))
            print("         Δ 范围 = %s..%s" % (min(nz), max(nz)))
        else:
            print("  [NOTE] G_FRAME 全程不变（值恒为 %s）" % vals[0])
            print("         ⇒ 可能：仍在主菜单/加载中；或该构建的 G_FRAME 语义与预期不同")

        if stall_flag:
            print("\n  ★ 观测到一次停滞事件 @ t=%.2fs" % stall_at)
            print("    这是 E3 的**目标触发条件**，已按 C1 语义正确识别。")
            if last_stack is not None:
                print("    冻结瞬间栈：")
                for i, f in enumerate((last_stack or [])[:8]):
                    if isinstance(f, dict):
                        print("      #%d %s" % (i, f.get("name") or hex(f.get("addr") or 0)))
    finally:
        k32.CloseHandle(h)

    print("\n" + "=" * 74)
    print("完成（本脚本未修改游戏任何内存，也未终止游戏）")
    print("=" * 74)
    return 0


def do_stack_sample(pid):
    """在停滞后做一次真栈回溯（≤300ms 预算，逐线程挂→走→立刻恢复）。"""
    print("    → 触发一次真栈回溯（只读+短挂起，逐线程立刻恢复）")
    try:
        spec = importlib.util.spec_from_file_location(
            "cand", str(BASE / "e3_stack_sampler_candidate.py"))
        cand = importlib.util.module_from_spec(spec)
        sys.argv = ["x"]
        try:
            spec.loader.exec_module(cand)
        except SystemExit:
            pass
        cand.bind_real_ops()
        s = cand.StackSampler(budget_ms=300.0)
        hproc = cand.OPS["open_process"](0x0010 | 0x0400, pid)
        if not hproc:
            print("      !! OpenProcess 失败，跳过回溯")
            return None
        try:
            is32 = cand.OPS["is_wow64"](hproc)
            ok, err = cand.attach_stackwalker(s, hproc, pid, bool(is32))
            if not ok:
                print("      !! StackWalker 挂载失败(%s) ⇒ 只报单帧" % err)
            res = s.sample(pid)
            try:
                if ok:
                    s.stack_walker.cleanup()
            except Exception:                          # noqa: BLE001
                pass
            got = [x for x in res.get("threads", []) if x.get("frames")]
            best = max(got, key=lambda x: len(x["frames"])) if got else None
            print("      采到 %d 线程，errors=%s" % (len(got), res.get("errors")))
            return best["frames"] if best else None
        finally:
            cand.OPS["close_handle"](hproc)
    except Exception as e:                             # noqa: BLE001
        print("      !! 回溯异常: %s" % e)
        return None


if __name__ == "__main__":
    sys.exit(main())

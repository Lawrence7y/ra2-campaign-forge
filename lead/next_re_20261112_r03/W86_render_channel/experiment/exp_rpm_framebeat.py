# -*- coding: utf-8 -*-
"""W86 最小实验 · 候选2：cnc-ddraw 限帧放行节拍（RPM 只读通道）。

用法（Lead 真机批）：
    1. 正常启动游戏（不动任何文件），进入对局后取得 gamemd.exe 的 PID；
    2. python exp_rpm_framebeat.py <PID> [采样秒数，默认120] [输出目录，默认 ./out]
    3. 结束后输出 CSV + 预注册指标报告。

脚本性质：进程外只读（OpenProcess PROCESS_VM_READ + EnumProcessModules），
不注入、不写目标内存、不启动游戏。与 A 线既有 RPM 读 [0xA8ED84] 同一授权类。

观测对象（ddraw.dll .data，RVA；运行时 VA = 实际基址 + RVA）：
    +0x594E8  maxfps 解析值（自洽校验：应=60）
    +0x5EE48  参考上限（自洽校验：应=60）
    +0x5F128  帧间隔 ms（自洽校验：应=16）
    +0x5F120  ★ 上一帧放行时刻（timeGetTime 值，每帧更新一次）
    +0x5F124  最近一次门闸检查时刻

语义纪律（RULING_GPT61SOL.md Q3）：
    本通道测的是「cnc-ddraw 限帧放行层节拍」，报告措辞必须为
    「限帧放行间隔」，不得写「显示帧时间」或「画面流畅」。

预注册指标（裁决原文）：
    有效放行间隔的中位 / p95 / p99 + 每分钟超过 max(50ms, 3T) 的间隔次数
    （T=16ms → 阈值 50ms）+ 有效时长与样本数。
扰动校准（真机批另做）：ETW 开/关 与 RPM 轮询开/关 各做 ≥5 个 ABBA 区组；
无独立画面参照时，本脚本只产「轮询开启时观察到的放行节奏」。
"""
import ctypes
import ctypes.wintypes as wt
import math
import os
import statistics
import sys
import time

k32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

LIST_MODULES_ALL = 0x03


def die(msg):
    print("[FATAL]", msg)
    sys.exit(1)


def open_proc(pid):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    return h


def read_u32(h, addr):
    buf = ctypes.create_string_buffer(4)
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr), buf, 4, ctypes.byref(got)):
        return None
    return ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint32)).contents.value


def module_base(h, needle):
    """枚举目标进程模块，返回小写名为 needle 的模块实际基址。"""
    LIST_MODULES_ALL_ = LIST_MODULES_ALL
    needed = wt.DWORD()
    if not psapi.EnumProcessModulesEx(h, None, 0, ctypes.byref(needed), LIST_MODULES_ALL_):
        return None
    count = needed.value // ctypes.sizeof(ctypes.c_void_p)
    arr = (ctypes.c_void_p * count)()
    if not psapi.EnumProcessModulesEx(h, arr, ctypes.sizeof(arr), ctypes.byref(needed), LIST_MODULES_ALL_):
        return None
    count = min(count, needed.value // ctypes.sizeof(ctypes.c_void_p))
    name_buf = ctypes.create_unicode_buffer(512)
    for i in range(count):
        psapi.GetModuleFileNameExW(h, ctypes.c_void_p(arr[i]), name_buf, 512)
        base_name = os.path.basename(name_buf.value).lower()
        if base_name == needle:
            return arr[i]
    return None


def main():
    if len(sys.argv) < 2:
        die("usage: exp_rpm_framebeat.py <pid> [seconds] [outdir]")
    pid = int(sys.argv[1])
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0
    outdir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(outdir, exist_ok=True)

    h = open_proc(pid)
    if not h:
        die("OpenProcess(%d) failed err=%d（需要管理员）" % (pid, k32.GetLastError()))
    print("[OK] opened pid=%d handle=%#x" % (pid, h))

    base = module_base(h, "ddraw.dll")
    if not base:
        die("目标进程未加载 ddraw.dll（cnc-ddraw 未生效？）")
    print("[OK] ddraw.dll runtime base = 0x%08X" % (base or 0))
    base_i = int(base)

    A_MAXFPS = base_i + 0x594E8
    A_CLAMP = base_i + 0x5EE48
    A_INTERVAL = base_i + 0x5F128
    A_LAST_T = base_i + 0x5F120
    A_CUR_T = base_i + 0x5F124

    maxfps = read_u32(h, A_MAXFPS)
    clamp = read_u32(h, A_CLAMP)
    interval = read_u32(h, A_INTERVAL)
    print("[SELF-CHECK] maxfps=%s clamp=%s interval=%s  (期望 60/60/16)" % (maxfps, clamp, interval))
    if maxfps != 60 or interval not in (16, 15, 17):
        print("[WARN] 自洽校验未过——配置可能与 1366x768/maxfps=60 基线不同，指标 T 需按 interval 重定")

    T = interval if interval else 16
    thresh = max(50, 3 * T)
    print("[INFO] T=%dms  长间隔阈值=%dms  采样时长=%.0fs" % (T, thresh, dur))

    csv_path = os.path.join(outdir, "framebeat_%d.csv" % int(time.time()))
    f = open(csv_path, "w", encoding="ascii")
    f.write("poll_epoch_ms,last_t,cur_t\n")

    # 主循环：~1kHz 轮询 last_t
    t_end = time.perf_counter() + dur
    last_seen = read_u32(h, A_LAST_T)
    cur_seen = read_u32(h, A_CUR_T)
    if last_seen is None:
        die("ReadProcessMemory(last_t) 失败 err=%d" % k32.GetLastError())
    frames = []          # [(epoch_ms, new_last_t)]
    read_fail = 0
    poll_n = 0
    qpc_freq = ctypes.c_longlong()
    k32.QueryPerformanceFrequency(ctypes.byref(qpc_freq))
    t0_qpc = ctypes.c_longlong()
    k32.QueryPerformanceCounter(ctypes.byref(t0_qpc))

    while time.perf_counter() < t_end:
        v = read_u32(h, A_LAST_T)
        poll_n += 1
        if v is None:
            read_fail += 1
            continue
        if v != last_seen:
            # 新的一帧被放行（timeGetTime 值推进；49.7天回绕忽略）
            q = ctypes.c_longlong()
            k32.QueryPerformanceCounter(ctypes.byref(q))
            ep_ms = int((q.value - t0_qpc.value) * 1000 / qpc_freq.value)
            frames.append((ep_ms, v))
            f.write("%d,%d,%s\n" % (ep_ms, v, cur_seen if cur_seen is not None else ""))
            last_seen = v
        c = read_u32(h, A_CUR_T)
        if c is not None:
            cur_seen = c
        time.sleep(0.0005)
    f.close()

    # 指标
    print("=" * 72)
    print("采样: poll_n=%d  帧数=%d  读失败=%d  有效时长=%.1fs" % (poll_n, len(frames), read_fail, dur))
    if read_fail:
        print("[WARN] 读失败>0 —— 需排查（进程退出/权限），区间有效性打折")
    if len(frames) < 3:
        print("[WARN] 帧数过少，无统计意义")
        sys.exit(0)
    ivs = [frames[i + 1][0] - frames[i][0] for i in range(len(frames) - 1)]
    ivs_sorted = sorted(ivs)
    n = len(ivs)
    med = statistics.median(ivs)
    p95 = ivs_sorted[int(math.ceil(0.95 * n)) - 1]
    p99 = ivs_sorted[int(math.ceil(0.99 * n)) - 1]
    long_cnt = sum(1 for x in ivs if x > thresh)
    minutes = dur / 60.0
    print("【限帧放行间隔】 n=%d" % n)
    print("  中位 = %.2f ms" % med)
    print("  p95  = %.2f ms" % p95)
    print("  p99  = %.2f ms" % p99)
    print("  >%dms 间隔 = %d 次 (%.2f 次/分钟)" % (thresh, long_cnt, long_cnt / minutes))
    print("  最大间隔 = %d ms  最小 = %d ms" % (ivs_sorted[-1], ivs_sorted[0]))
    print("=" * 72)
    print("措辞纪律：本报告为「限帧放行间隔」（cnc-ddraw 限帧层），非显示帧时间。")
    print("CSV: %s" % csv_path)

    k32.CloseHandle(h)


if __name__ == "__main__":
    main()

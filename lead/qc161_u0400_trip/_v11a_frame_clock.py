"""① V11-a 独立帧钟观测器（只读 RPM，不改游戏、不注入、不发消息）。

## 为什么需要这个

`qc151_trip.harness6.py` 在 `--fullscreen` 下，帧阶段有一个结构性的 125 s 空等：

    :7979  while rect != (800,600) and time.monotonic() < deadline:
               time.sleep(0.5)                    # deadline = begin + 150 s

全屏下 `rect_of(hwnd)` 恒为 2560×1440（≠800×600）⇒ 这个 while 必然跑到
`deadline`（实测 polls=251×0.5 ≈ 125 s，见 `pre_capture_wait_polls`）。
该空等**已登记为 harness 缺陷 #3**（台账 §7 新登记项，属 D-113 设计内降级）。

后果（本轮三趟实测）：31 档下这 125 s 推进约 3500 逻辑帧 ⇒ 战斗在
measure 窗打开前就结束（`in_tactical_target = skirmish_score`）⇒
`pre_fps15 = 0.0`、`verdict = no_advance`。**这是测不到，不是档位不够。**

## 本工具的口径

严格复刻 harness 的 `_measure_run` 在局闸算法（同 VA / 同频率 / 同公式），
但**在战斗仍在进行时**采样：

  - `MEASURE_CURRENT_FRAME_VA = 0x00A8ED84`（harness6:3831，逐字同源）
  - `MEASURE_UNITS_VA        = 0x008B4118`（harness6:3834）
  - `MEASURE_HZ              = 500`        （harness6:3843）
  - `MEASURE_SETTLE_S        = 4.0`        （harness6:3846）
  - `MEASURE_GATE_SPAN_S     = 1.5`        （harness6:3848）
  - `pre_fps15 = (f[-1] - f[0]) / (t[-1] - t[0])`，取 `t >= t0 + 4.0 - 1.5` 的点

判据阈值（V11 设计件 §3.1 V11-a）：`pre_fps15 >= 25` ⇒ 31 档。

## 安全边界

- 只调 `OpenProcess(PROCESS_VM_READ|SYNCHRONIZE)` + `ReadProcessMemory`
- **零写入**：本文件不含 `WriteProcessMemory`
- **零注入**：不 `CreateRemoteThread`、不 `LoadLibrary`、不改 DLL
- **零消息**：不 `PostMessage`/`SendMessage`
- 只观测**调用方自己起的** pid（`--pid` 必须由调用方传入）
"""
import argparse
import ctypes
import json
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

# ---- 与 harness6 逐字同源的常量 ----
MEASURE_CURRENT_FRAME_VA = 0x00A8ED84
MEASURE_UNITS_VA = 0x008B4118
MEASURE_HZ = 500
MEASURE_SETTLE_S = 4.0
MEASURE_GATE_SPAN_S = 1.5
GATE_MIN = 25.0            # V11-a（设计件 §3.1）

PROCESS_VM_READ = 0x0010
SYNCHRONIZE = 0x00100000

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


def open_proc(pid):
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    h = k32.OpenProcess(PROCESS_VM_READ | SYNCHRONIZE, False, pid)
    return h or None


def rpm_u32(h, va):
    """读 u32；失败 ⇒ None（不抛，与 harness `_rpm_u32` 同口径）。"""
    k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                      ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.POINTER(ctypes.c_size_t)]
    k32.ReadProcessMemory.restype = wt.BOOL
    buf = wt.DWORD()
    got = ctypes.c_size_t()
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), ctypes.byref(buf),
                               ctypes.sizeof(buf), ctypes.byref(got))
    return buf.value if ok else None


def alive(h):
    k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    k32.WaitForSingleObject.restype = wt.DWORD
    return k32.WaitForSingleObject(h, 0) == 0x102   # WAIT_TIMEOUT


def close(h):
    k32.CloseHandle.argtypes = [wt.HANDLE]
    k32.CloseHandle(h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True,
                    help="★ 调用方自己起的 gamemd pid（本工具只读该 pid）")
    ap.add_argument("--window", type=int, default=3,
                    help="★ 采样窗数（缺省 3，同 harness MEASURE_WINDOWS）")
    ap.add_argument("--window-s", type=float, default=25.0,
                    help="★ 单窗秒数（缺省 25.0，同 harness MEASURE_WINDOW_S）")
    ap.add_argument("--out", default=None, help="★ 结果 JSON 路径")
    a = ap.parse_args()

    print("=" * 78)
    print("① V11-a 独立帧钟观测器（只读 RPM）")
    print("=" * 78)
    print("  pid          : %d" % a.pid)
    print("  CurrentFrame : VA 0x%08X" % MEASURE_CURRENT_FRAME_VA)
    print("  units        : VA 0x%08X" % MEASURE_UNITS_VA)
    print("  hz           : %d" % MEASURE_HZ)
    print("  窗数 × 秒    : %d × %.1f s" % (a.window, a.window_s))
    print("  判据         : pre_fps15 >= %.1f ⇒ 31 档" % GATE_MIN)
    print()

    h = open_proc(a.pid)
    if not h:
        print("!! OpenProcess 失败 err=%d" % ctypes.get_last_error())
        return 2
    if not alive(h):
        print("!! 进程已退出")
        close(h)
        return 2

    results = []
    try:
        for w in range(a.window):
            # ---- settle 4 s（同 harness）----
            t_settle0 = time.perf_counter()
            s_samples = []
            period = 1.0 / MEASURE_HZ
            while time.perf_counter() - t_settle0 < MEASURE_SETTLE_S:
                t = time.perf_counter() - t_settle0
                f = rpm_u32(h, MEASURE_CURRENT_FRAME_VA)
                u = rpm_u32(h, MEASURE_UNITS_VA)
                if f is not None:
                    s_samples.append((t, f, u))
                time.sleep(period)
            t0s = 0.0

            # ---- 窗前在局闸：1.5 s 内推进 ----
            pre_fps15 = None
            if len(s_samples) >= 2:
                t_cut = t0s + MEASURE_SETTLE_S - MEASURE_GATE_SPAN_S
                gp = [(t, f) for t, f, _ in s_samples if t >= t_cut]
                if len(gp) >= 2:
                    span = gp[-1][0] - gp[0][0]
                    if span > 0:
                        pre_fps15 = (gp[-1][1] - gp[0][1]) / span
            units0 = next((u for _, _, u in s_samples if u is not None), None)

            # ---- 主窗（25 s，同 harness）----
            t_win0 = time.perf_counter()
            w_samples = []
            while time.perf_counter() - t_win0 < a.window_s:
                t = time.perf_counter() - t_win0
                f = rpm_u32(h, MEASURE_CURRENT_FRAME_VA)
                u = rpm_u32(h, MEASURE_UNITS_VA)
                if f is not None:
                    w_samples.append((t, f, u))
                time.sleep(period)

            fps_avg = None
            logic_frames = 0
            max_stall = 0.0
            if len(w_samples) >= 2:
                span = w_samples[-1][0] - w_samples[0][0]
                df = w_samples[-1][1] - w_samples[0][1]
                logic_frames = df
                if span > 0:
                    fps_avg = df / span
                prev_t, prev_f = w_samples[0][0], w_samples[0][1]
                for t, f, _ in w_samples[1:]:
                    if f != prev_f:
                        gap = t - prev_t
                        if gap > max_stall:
                            max_stall = gap
                        prev_t, prev_f = t, f
                else:
                    if w_samples[-1][1] == prev_f:
                        tail = w_samples[-1][0] - prev_t
                        if tail > max_stall:
                            max_stall = tail

            row = {"window": w, "pre_fps15": (round(pre_fps15, 3)
                                              if pre_fps15 is not None else None),
                   "units0": units0,
                   "fps_avg": (round(fps_avg, 3) if fps_avg is not None else None),
                   "logic_frames": logic_frames,
                   "max_stall_s": round(max_stall, 3),
                   "samples": len(w_samples),
                   "gate_pass": bool(pre_fps15 is not None and pre_fps15 >= GATE_MIN)}
            results.append(row)
            print("  W%d  pre_fps15=%-8s units0=%-6s fps_avg=%-8s logic_frames=%-5s max_stall=%-6s %s"
                  % (w, row["pre_fps15"], row["units0"], row["fps_avg"],
                     row["logic_frames"], row["max_stall_s"],
                     "PASS" if row["gate_pass"] else "FAIL"))

            if not alive(h):
                print("  !! 进程在第 %d 窗后退出" % w)
                break
    finally:
        close(h)

    pre = [r["pre_fps15"] for r in results if r["pre_fps15"] is not None]
    print()
    if pre:
        mn = min(pre)
        tier = "31" if mn >= GATE_MIN else "10"
        print("  pre_fps15 范围 : [%.3f, %.3f]" % (mn, max(pre)))
        print("  档位           : %s" % tier)
        print("  V11-a          : %s" % ("PASS" if mn >= GATE_MIN else "FAIL"))
    else:
        tier = "unknown"
        print("  pre_fps15      : 全部不可测")

    payload = {"schema": "ra2cf.v11a_frame_clock/1",
               "pid": a.pid,
               "constants": {"current_frame_va": hex(MEASURE_CURRENT_FRAME_VA),
                             "units_va": hex(MEASURE_UNITS_VA),
                             "hz": MEASURE_HZ,
                             "settle_s": MEASURE_SETTLE_S,
                             "gate_span_s": MEASURE_GATE_SPAN_S,
                             "gate_min": GATE_MIN,
                             "window_s": a.window_s},
               "windows": results,
               "tier": tier,
               "v11a_pass": bool(pre and min(pre) >= GATE_MIN)}
    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                     encoding="utf-8")
        print("\n  json: %s" % p)
    return 0 if payload["v11a_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

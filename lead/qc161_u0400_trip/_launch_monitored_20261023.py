"""① 并发帧钟监测发射器（harness 跑，我在旁边读帧计数）。

## 为什么需要这个

`qc151_trip.harness6.py` 在 `--fullscreen` 下，帧阶段有一个结构性的 125 s 空等：

    :7979  while rect != (800,600) and time.monotonic() < deadline:
               time.sleep(0.5)                    # deadline = begin + 150 s

全屏下 `rect_of(hwnd)` 恒为 2560×1440（≠800×600）⇒ 这个 while 必然跑到
`deadline`（实测 `pre_capture_wait_polls=251` × 0.5 ≈ 125 s）。
该空等**已登记为 harness 缺陷 #3**（台账 §7，属 D-113 设计内降级）。

后果（2026-10-23 三趟实测）：31 档下这 125 s 推进约 3500 逻辑帧 ⇒
战斗在 measure 窗打开前结束（`in_tactical_target = skirmish_score`）⇒
`pre_fps15 = 0.0`、`verdict = no_advance`。**是测不到，不是档位不够。**

## 做法

本脚本用 `os.spawnv(P_WAIT, ...)` 起 harness（与 `_launch_l1_20261023.py`
同一被放行模式；**游戏仍由 harness 自己 plain Popen 起，无 stdio 重定向**
—— 遵守 gamemd PIPE 敏感纪律），同时在旁路线程里按 harness 同源 VA
采样 `CurrentFrame` / `units`，把整趟时间序列落盘。

离线再从时间序列按 harness 的 `pre_fps15` 公式
（`(f[-1]-f[0])/(t[-1]-t[0])`，1.5 s 跨度）算滑动分布，
取**战斗仍在进行时**（帧在推进）的窗。

## 安全边界

- 只读：`OpenProcess(PROCESS_VM_READ)` + `ReadProcessMemory`
- 零写入 / 零注入 / 零窗口消息
- 只观测本趟载体目录下的 gamemd（按镜像路径精确匹配）
- **无 CLI 透传参数**：全部发射参数为模块级常量，不经命令行拼接
"""
import ctypes
import json
import os
import sys
import threading
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead"
TRIP = LEAD / "qc161_u0400_trip"
HARNESS = ROOT / "lead/goal1_harness6_20261022/qc151_trip.harness6.py"

# ---- 与 harness6 逐字同源的 VA ----
MEASURE_CURRENT_FRAME_VA = 0x00A8ED84
MEASURE_UNITS_VA = 0x008B4118
MEASURE_INFANTRY_VA = 0x00A83DF8
MEASURE_TECHNO_VA = 0x00A8EC88
SAMPLE_HZ = 200

# ---- 本趟固定配置（常量，非 CLI）----
VARIANT = "L1"
SUFFIX = "c"
PROBE_FRAMES = "3900,4200,4500,4800,5100,5400,5700,6000"

VARIANTS = {
    "L1": {"src": "_src_L1_sf8_20261020",
           "map_sha": "0add791d11aea84d7876aa3f908165259ec77f681ee721f83fd9966facdf60bc",
           "prefix": "QC161-U0800-L1"},
    "L3": {"src": "_src_L3_sf10c_20261021",
           "map_sha": "f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36",
           "prefix": "QC161-U0800-L3"},
}
DEFAULT_CARRIER_FILES = ("gamemd.exe", "ra2loader.exe", "ra2render.dll",
                         "ra2opt_play.bat", "except.txt")

PROCESS_VM_READ = 0x0010
k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class PE32(ctypes.Structure):
    _fields_ = [("dwSize", wt.DWORD), ("cntUsage", wt.DWORD),
                ("th32ProcessID", wt.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wt.DWORD), ("cntThreads", wt.DWORD),
                ("th32ParentProcessID", wt.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wt.DWORD),
                ("szExeFile", wt.WCHAR * 260)]


def list_procs():
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


def proc_image_path(pid):
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    k32.QueryFullProcessImageNameW.argtypes = [
        wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD)]
    k32.QueryFullProcessImageNameW.restype = wt.BOOL
    k32.CloseHandle.argtypes = [wt.HANDLE]
    hp = k32.OpenProcess(0x1000, False, pid)
    if not hp:
        return None
    try:
        buf = ctypes.create_unicode_buffer(1024)
        ln = wt.DWORD(1024)
        if k32.QueryFullProcessImageNameW(hp, 0, buf, ctypes.byref(ln)):
            return buf.value
    finally:
        k32.CloseHandle(hp)
    return None


def open_read(pid):
    k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    k32.OpenProcess.restype = wt.HANDLE
    return k32.OpenProcess(PROCESS_VM_READ, False, pid) or None


def rpm_u32(h, va):
    k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p,
                                      ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.POINTER(ctypes.c_size_t)]
    k32.ReadProcessMemory.restype = wt.BOOL
    buf = wt.DWORD()
    got = ctypes.c_size_t()
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(va), ctypes.byref(buf),
                               ctypes.sizeof(buf), ctypes.byref(got))
    return buf.value if ok else None


class Monitor(threading.Thread):
    """旁路采样线程：按载体路径锁定 gamemd pid，逐拍记录帧计数与实体数。"""

    def __init__(self, carrier_dir):
        super().__init__(daemon=True)
        self.carrier = str(carrier_dir).lower()
        self.stop_ev = threading.Event()
        self.rows = []
        self.pid = None

    def _find_pid(self):
        for pid, nm in list_procs().items():
            if nm.lower() != "gamemd.exe":
                continue
            ip = proc_image_path(pid)
            if ip and self.carrier in ip.lower():
                return pid
        return None

    def run(self):
        period = 1.0 / SAMPLE_HZ
        h = None
        t0 = None
        misses = 0
        while not self.stop_ev.is_set():
            if h is None:
                self.pid = self._find_pid()
                if self.pid:
                    h = open_read(self.pid)
                    t0 = time.perf_counter()
                else:
                    time.sleep(0.2)
                    continue
            if h is None:
                time.sleep(0.2)
                continue
            t = time.perf_counter() - t0
            f = rpm_u32(h, MEASURE_CURRENT_FRAME_VA)
            if f is None:
                misses += 1
                if misses > 400:
                    break
                time.sleep(0.05)
                continue
            misses = 0
            self.rows.append((round(t, 4), f,
                              rpm_u32(h, MEASURE_UNITS_VA),
                              rpm_u32(h, MEASURE_INFANTRY_VA),
                              rpm_u32(h, MEASURE_TECHNO_VA)))
            time.sleep(period)
        if h:
            k32.CloseHandle(h)

    def stop(self):
        self.stop_ev.set()


def analyze(rows, span_s=1.5, win_s=25.0, gate_min=25.0):
    """按 harness `_measure_run` 口径重算：滑动 pre_fps15 + 25 s 主窗 fps。"""
    out = {"samples": len(rows), "gate_min": gate_min}
    if len(rows) < 10:
        out["error"] = "样本不足"
        return out

    pre_vals = []
    j = 0
    for i in range(len(rows)):
        while j < len(rows) and rows[j][0] - rows[i][0] < span_s:
            j += 1
        if j >= len(rows):
            break
        dt = rows[j][0] - rows[i][0]
        if dt <= 0:
            continue
        df = rows[j][1] - rows[i][1]
        if df <= 0:
            continue
        pre_vals.append((rows[i][0], df / dt))

    out["pre_fps15_n"] = len(pre_vals)
    if pre_vals:
        v = sorted(x[1] for x in pre_vals)
        out["pre_fps15_min"] = round(v[0], 3)
        out["pre_fps15_p10"] = round(v[int(len(v) * 0.10)], 3)
        out["pre_fps15_p50"] = round(v[len(v) // 2], 3)
        out["pre_fps15_p90"] = round(v[int(len(v) * 0.90)], 3)
        out["pre_fps15_max"] = round(v[-1], 3)
        above = sum(1 for x in v if x >= gate_min)
        out["pre_fps15_above_gate"] = above
        out["pre_fps15_above_gate_frac"] = round(above / len(v), 4)
        best = cur = 0
        best_t = cur_t = None
        for t, val in pre_vals:
            if val >= gate_min:
                if cur == 0:
                    cur_t = t
                cur += 1
                if cur > best:
                    best = cur
                    best_t = (cur_t, t)
            else:
                cur = 0
        out["above_gate_longest_n"] = best
        out["above_gate_longest_span_s"] = (round(best_t[1] - best_t[0], 3)
                                            if best_t else None)

    best_win = None
    for i in range(len(rows)):
        lo, hi = i, len(rows) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if rows[mid][0] - rows[i][0] < win_s:
                lo = mid + 1
            else:
                hi = mid
        if rows[lo][0] - rows[i][0] < win_s:
            break
        dt = rows[lo][0] - rows[i][0]
        df = rows[lo][1] - rows[i][1]
        if dt <= 0 or df <= 0:
            continue
        fps = df / dt
        if best_win is None or fps > best_win["fps_avg"]:
            best_win = {"t_start": round(rows[i][0], 2),
                        "t_end": round(rows[lo][0], 2),
                        "fps_avg": round(fps, 3),
                        "logic_frames": df,
                        "units_at_start": rows[i][2],
                        "units_at_end": rows[lo][2]}
    out["best_25s_window"] = best_win

    out["frame_first"] = rows[0][1]
    out["frame_last"] = rows[-1][1]
    out["t_span_s"] = round(rows[-1][0] - rows[0][0], 2)
    return out


def main():
    v = VARIANTS[VARIANT]
    src = TRIP / v["src"]
    manifest = TRIP / (v["src"] + "_MANIFEST.json")
    out_dir = TRIP / ("l%s_20261023%s" % (VARIANT[1:].lower(), SUFFIX))
    trip_id = v["prefix"] + "-20261023" + SUFFIX.upper()

    print("=" * 78)
    print("① 并发帧钟监测发射器 · 变体 %s · 趟 %s" % (VARIANT, out_dir.name))
    print("=" * 78)

    mf = json.loads(manifest.read_text(encoding="utf-8"))
    names = sorted(mf["files"].keys())
    extra = [n for n in names if n not in DEFAULT_CARRIER_FILES]
    print("  载体件集: %d 件 = 默认 %d + 附加 %d"
          % (len(names), len(DEFAULT_CARRIER_FILES), len(extra)))
    assert len(names) == 88, "冻结清单应为 88 条，实得 %d" % len(names)
    assert len(extra) == 83, "附加件应为 83 条，实得 %d" % len(extra)
    for n in extra:
        assert "," not in n, "件名含逗号会破坏整串切分: %r" % n

    planned = out_dir / "ct" / ("c_" + "0" * 12 + "_12345")
    print("  路径长度: %d (门禁 130)" % len(str(planned)))
    assert len(str(planned)) <= 130

    left = [n for n in list_procs().values()
            if n.lower() in ("gamemd.exe", "ra2loader.exe")]
    print("  发射前残留进程: %s" % (left or "无"))
    if left:
        print("!! 有残留，不发射")
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)

    argv = [
        str(HARNESS),
        "--target-map", str(src / "XMP29U2.MAP"),
        "--target-sha256", v["map_sha"],
        "--carrier", str(out_dir / "ct"),
        "--carrier-create-from", str(src),
        "--carrier-create-files", ",".join(extra),
        "--trip-id", trip_id,
        "--out-dir", str(out_dir),
        "--measure", "1",
        "--fullscreen",
        "--evid-diff",
        "--probe-frames", PROBE_FRAMES,
    ]
    spawn_argv = [sys.executable]
    for a in argv:
        spawn_argv.append('"%s"' % a if (" " in a and not a.startswith('"')) else a)

    print("  [发射] harness6（游戏由 harness 自己 plain Popen 起，无 stdio 重定向）")

    mon = Monitor(out_dir / "ct")
    mon.start()
    t0 = time.monotonic()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    # ★ os.spawnv：不经 shell，argv[0]=解释器，argv[1:]=脚本+参数（既有被放行模式）
    pid = os.spawnv(os.P_WAIT, sys.executable, spawn_argv)
    dur = time.monotonic() - t0
    mon.stop()
    mon.join(timeout=10)

    print("\n  [harness] rc=%d  用时 %.1fs  gamemd_pid=%s  样本 %d"
          % (pid, dur, mon.pid, len(mon.rows)))

    an = analyze(mon.rows)
    payload = {"schema": "ra2cf.v11a_concurrent_clock/1",
               "trip_id": trip_id, "variant": VARIANT,
               "out_dir": str(out_dir), "harness_rc": pid,
               "duration_s": round(dur, 1), "gamemd_pid": mon.pid,
               "constants": {"current_frame_va": hex(MEASURE_CURRENT_FRAME_VA),
                             "units_va": hex(MEASURE_UNITS_VA),
                             "sample_hz": SAMPLE_HZ,
                             "settle_s": 4.0, "gate_span_s": 1.5,
                             "window_s": 25.0, "gate_min": 25.0},
               "analysis": an,
               "series": mon.rows}
    jp = out_dir / "_v11a_concurrent_clock.json"
    jp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    print("\n  === 分析 ===")
    for k in ("samples", "pre_fps15_n", "pre_fps15_min", "pre_fps15_p10",
              "pre_fps15_p50", "pre_fps15_p90", "pre_fps15_max",
              "pre_fps15_above_gate", "pre_fps15_above_gate_frac",
              "above_gate_longest_n", "above_gate_longest_span_s",
              "frame_first", "frame_last", "t_span_s"):
        if k in an:
            print("    %-30s = %s" % (k, an[k]))
    if an.get("best_25s_window"):
        print("    best_25s_window = %s"
              % json.dumps(an["best_25s_window"], ensure_ascii=False))

    time.sleep(1.0)
    left = [n for n in list_procs().values()
            if n.lower() in ("gamemd.exe", "ra2loader.exe")]
    print("\n  [卫生] 残留进程: %s" % (left or "无"))
    print("  [结果] %s" % jp)
    return pid


if __name__ == "__main__":
    sys.exit(main())

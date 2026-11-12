# -*- coding: utf-8 -*-
"""E3 最终闭环：高负载对局 + 帧号停滞检测 + 停滞瞬间真栈捕获。

流程（全部用已验证的控件消息自动化，零坐标点击）：
  N1 主菜单 → BM_CLICK('GUI:SinglePlayer')
  N2 单人菜单 → BM_CLICK('GUI:Skirmish')
  N3 遭遇战界面 → 枚举 ListBox（地图列表）与 ComboBox（玩家/单位数等）
     · 打印所有可选地图，尝试选中高单位负载图（U0800/U0400/LoadBench）
     · 尝试把 UnitCount 拉高（trackbar 或 ComboBox）
  N4 BM_CLICK('GUI:StartGame') 开局
  N5 轮询 G_FRAME（FrameSource 语义：读失败不推进/不重置/不判停滞）
     · 记录完整帧率曲线
     · 检测「连续 ≥ STALL_N 秒不变」→ 判停滞
  N6 停滞时立即 StackSampler.sample()（≤budget ms，逐线程挂→即时恢复）
  N7 输出：帧率统计 + 停滞事件表 + 每个停滞事件的真栈

用法：
  python -I -X utf8 _e3_stall_capture.py --pid <PID> [--stall-n 1.0] [--seconds 120]
                                        [--map-hint U0800] [--unit-count 8]
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")
G_FRAME = 0x00A8ED84
G_TICK = 0x00A8ED80

u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

u.SendMessageW.restype = ctypes.c_void_p
u.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u.PostMessageW.restype = wt.BOOL
u.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
u.GetWindowThreadProcessId.restype = wt.DWORD
u.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u.GetWindowTextLengthW.restype = ctypes.c_int
u.GetWindowTextLengthW.argtypes = [wt.HWND]
u.GetWindowTextW.restype = ctypes.c_int
u.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u.GetClassNameW.restype = ctypes.c_int
u.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u.EnumWindows.restype = wt.BOOL
u.EnumWindows.argtypes = [ctypes.c_void_p, wt.LPARAM]
u.EnumChildWindows.restype = wt.BOOL
u.EnumChildWindows.argtypes = [wt.HWND, ctypes.c_void_p, wt.LPARAM]
u.IsWindowVisible.restype = wt.BOOL
u.IsWindowVisible.argtypes = [wt.HWND]
u.SendMessageW  # LB_GETCOUNT etc use SendMessageW with same sig

k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.IsWow64Process.restype = wt.BOOL
k32.IsWow64Process.argtypes = [wt.HANDLE, ctypes.POINTER(wt.BOOL)]

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

LB_GETCOUNT = 0x018B
LB_GETTEXT = 0x0189
LB_GETTEXTLEN = 0x018A
LB_SETCURSEL = 0x0186
BM_CLICK = 0x00F5
WM_SETTEXT = 0x000C


def wtxt(h):
    n = u.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(max(n + 1, 2))
    u.GetWindowTextW(h, b, n + 1)
    return b.value


def wcls(h):
    b = ctypes.create_unicode_buffer(256)
    u.GetClassNameW(h, b, 256)
    return b.value


def all_controls(pid):
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
    for h, c, t, v in all_controls(pid):
        if c == "Button" and name.lower() in (t or "").lower():
            return h
    return None


def find_cls(pid, cls):
    for h, c, t, v in all_controls(pid):
        if c == cls:
            return h
    return None


def find_all_cls(pid, cls):
    return [(h, t) for h, c, t, v in all_controls(pid) if c == cls]


def lb_items(h):
    n = u.SendMessageW(h, LB_GETCOUNT, 0, 0) or 0
    out = []
    for i in range(int(n)):
        ln = u.SendMessageW(h, LB_GETTEXTLEN, i, 0) or 0
        buf = ctypes.create_unicode_buffer(int(ln) + 2)
        u.SendMessageW(h, LB_GETTEXT, i, ctypes.cast(buf, ctypes.c_void_p).value)
        out.append(buf.value)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", type=int, required=True)
    ap.add_argument("--stall-n", type=float, default=1.0)
    ap.add_argument("--seconds", type=float, default=120.0)
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("--map-hint", default="U0800")
    ap.add_argument("--unit-count", type=int, default=0,
                    help=">0 时尝试把 UnitCount 滑条拉到该档位（0=不动）")
    ap.add_argument("--budget", type=float, default=400.0)
    ap.add_argument("--max-threads", type=int, default=0)
    ap.add_argument("--no-nav", action="store_true", help="跳过导航，直接轮询（已在对局内）")
    a = ap.parse_args()
    pid = a.pid

    print("=" * 78)
    print("E3 最终闭环：高负载对局 + 停滞检测 + 停滞瞬间真栈")
    print("=" * 78)

    if not a.no_nav:
        print("\n[N1] 主菜单 → GUI:SinglePlayer")
        h = find_btn(pid, "GUI:SinglePlayer")
        if not h:
            print("  !! 找不到 GUI:SinglePlayer（当前控件如下）")
            for hh, cc, tt, vv in all_controls(pid):
                if vv:
                    print("     %-10d %-22s %r" % (hh, cc, tt))
            return 3
        u.SendMessageW(h, BM_CLICK, 0, 0)
        time.sleep(2.0)

        print("\n[N2] 单人菜单 → GUI:Skirmish")
        h = find_btn(pid, "GUI:Skirmish")
        if not h:
            print("  !! 找不到 GUI:Skirmish")
            for hh, cc, tt, vv in all_controls(pid):
                if vv:
                    print("     %-10d %-22s %r" % (hh, cc, tt))
            return 3
        u.SendMessageW(h, BM_CLICK, 0, 0)
        time.sleep(2.5)

        print("\n[N3] 遭遇战界面：枚举控件")
        ctrls = all_controls(pid)
        lbs = [(h, t) for h, c, t, v in ctrls if c == "ListBox"]
        cbs = [(h, t) for h, c, t, v in ctrls if c == "ComboBox"]
        tbs = [(h, t) for h, c, t, v in ctrls if "trackbar" in (c or "")]
        print("  ListBox %d / ComboBox %d / TrackBar %d" % (len(lbs), len(cbs), len(tbs)))
        for h, t in lbs:
            items = lb_items(h)
            print("  ListBox hwnd=%d  条目 %d 个：" % (h, len(items)))
            for i, it in enumerate(items[:40]):
                mark = ""
                if a.map_hint and a.map_hint.lower() in (it or "").lower():
                    mark = "  <<< 命中 map-hint"
                print("     [%2d] %r%s" % (i, it, mark))
            if len(items) > 40:
                print("     ... 共 %d 条" % len(items))

        # 选地图
        chosen = None
        for h, t in lbs:
            items = lb_items(h)
            for i, it in enumerate(items):
                if a.map_hint and a.map_hint.lower() in (it or "").lower():
                    u.SendMessageW(h, LB_SETCURSEL, i, 0)
                    chosen = (h, i, it)
                    break
            if chosen:
                break
        if chosen:
            print("\n  ★ 已选中地图 [%d] %r（ListBox hwnd=%d）"
                  % (chosen[1], chosen[2], chosen[0]))
        else:
            print("\n  !! 地图列表里没找到含 %r 的条目 —— 仍用当前默认地图开局"
                  % a.map_hint)

        print("\n[N4] GUI:StartGame")
        h = find_btn(pid, "GUI:StartGame")
        if not h:
            print("  !! 找不到 GUI:StartGame")
            return 3
        u.SendMessageW(h, BM_CLICK, 0, 0)
        print("  已点击，等待加载...")

    # ---- N5/N6：轮询 + 停滞检测 + 抓栈 ----
    hproc = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    if not hproc:
        print("!! OpenProcess 失败")
        return 4

    cand = None
    sampler = None
    walker_ok = False
    try:
        flag = wt.BOOL(0)
        k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        print("\n目标 is32=%s" % is32)

        spec = importlib.util.spec_from_file_location(
            "cand", str(BASE / "e3_stack_sampler_candidate.py"))
        cand = importlib.util.module_from_spec(spec)
        sys.argv = ["x"]
        try:
            spec.loader.exec_module(cand)
        except SystemExit:
            pass
        cand.bind_real_ops()
        sampler = cand.StackSampler(budget_ms=a.budget)
        if a.max_threads > 0:
            sampler.max_threads = a.max_threads
        sampler._target_is32 = is32
        walker_ok, werr = cand.attach_stackwalker(sampler, hproc, pid, is32)
        print("StackWalker 挂载: %s %s" % (walker_ok, werr or ""))
        det = cand.StallDetector(n_seconds=a.stall_n, min_obs=6)

        def rd(addr):
            b = (ctypes.c_char * 4)()
            n = ctypes.c_size_t(0)
            ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), b, 4,
                                       ctypes.byref(n))
            return int.from_bytes(b.raw, "little") if ok and n.value == 4 else None

        print("\n[N5] 轮询 G_FRAME %.0fs（间隔 %.2fs，停滞阈值 %.1fs）"
              % (a.seconds, a.interval, a.stall_n))
        t0 = time.monotonic()
        samples = []
        events = []
        while time.monotonic() - t0 < a.seconds:
            now = time.monotonic()
            v = rd(G_FRAME)
            samples.append((round(now - t0, 3), v))
            if det.observe(now, v):
                ev = {"t": round(now - t0, 3), "frame": v, "stack": None}
                print("  ★ 停滞 @ t=%.2fs (frame=%s) → 抓栈" % (ev["t"], v))
                res = sampler.sample(pid)
                ev["errors"] = res.get("errors", [])
                ev["paused_ms"] = res.get("paused_ms")
                got = [x for x in res.get("threads", []) if x.get("frames")]
                if got:
                    best = max(got, key=lambda x: len(x["frames"]))
                    ev["stack"] = {"tid": best["tid"], "bits": best["ctx"]["bits"],
                                   "n_frames": len(best["frames"]),
                                   "frames": best["frames"]}
                    print("      采到 %d 线程，最长栈 %d 帧（tid=%d, paused=%sms）"
                          % (len(got), len(best["frames"]), best["tid"],
                             res.get("paused_ms")))
                    for i, f in enumerate(best["frames"][:8]):
                        nm = f.get("name") if isinstance(f, dict) else f
                        ad = f.get("addr") if isinstance(f, dict) else 0
                        print("        #%d %s" % (i, nm or hex(ad)))
                else:
                    print("      未采到栈，errors=%s" % ev["errors"])
                events.append(ev)
            time.sleep(a.interval)

        # ---- 统计 ----
        vals = [v for _, v in samples if v is not None]
        print("\n[N7] 结果")
        print("  采样 %d 次，可读 %d 次（%.1f%%）"
              % (len(samples), len(vals), 100.0 * len(vals) / max(1, len(samples))))
        if vals:
            print("  首值=%s 末值=%s min=%s max=%s 不同值=%d"
                  % (vals[0], vals[-1], min(vals), max(vals), len(set(vals))))
            d = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
            nz = [x for x in d if x != 0]
            print("  Δ: min=%s max=%s 非零Δ=%d/%d" % (min(d), max(d), len(nz), len(d)))
            if nz:
                med = statistics.median(nz)
                print("  Δ 中位=%s ⇒ 约 %.1f fps（%.2fs 采样）"
                      % (med, med / a.interval, a.interval))
                # 停滞段统计：Δ==0 的连续段
                runs, cur = [], 0
                for x in d:
                    if x == 0:
                        cur += 1
                    else:
                        if cur:
                            runs.append(cur)
                        cur = 0
                if cur:
                    runs.append(cur)
                if runs:
                    print("  零 Δ 连续段（次数=%d）: 最长 %d 个采样间隔 ≈ %.2fs"
                          % (len(runs), max(runs), max(runs) * a.interval))
                    print("  ≥%.1fs 的停滞段数 = %d"
                          % (a.stall_n, sum(1 for r in runs if r * a.interval >= a.stall_n)))
        print("  停滞事件（StallDetector 触发）= %d 次" % len(events))

        out = {"pid": pid, "is32": is32, "stall_n": a.stall_n,
               "seconds": a.seconds, "interval": a.interval,
               "walker_ok": walker_ok,
               "n_samples": len(samples), "n_readable": len(vals),
               "events": events,
               "fps_estimate": (statistics.median([x for x in
                   [vals[i+1]-vals[i] for i in range(len(vals)-1)] if x != 0]) / a.interval)
                   if len(set(vals)) > 1 else None}
        p = BASE / ("_stall_capture_%d.json" % pid)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("  落盘: %s" % p)
        try:
            if walker_ok:
                sampler.stack_walker.cleanup()
        except Exception:                                  # noqa: BLE001
            pass
    finally:
        if cand is not None:
            try:
                cand.OPS["close_handle"](hproc)
            except Exception:                              # noqa: BLE001
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

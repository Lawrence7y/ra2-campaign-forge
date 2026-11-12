# -*- coding: utf-8 -*-
"""E3 高负载局：启动 → 导航 → 读地图列表找 _H1 → 选中 → 开局 → 停滞监测。

一键完成，避免多轮交互：
  N1 启动游戏（WMI 分离，不阻塞 shell）
  N2 等主菜单就绪（轮询控件）
  N3 BM_CLICK SinglePlayer → Skirmish
  N4 BM_CLICK ChooseMap → 读 271 条目（LB_GETITEMDATA + UTF-16LE）→ 找 pattern
  N5 LB_SETCURSEL → BM_CLICK UseMap
  N6 BM_CLICK StartGame
  N7 轮询 G_FRAME，停滞即抓栈

用法：
  python -I -X utf8 _run_hl_match.py --pattern H1 --seconds 240
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import importlib.util
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")
GAME_DIR = r"D:\Project\ra2-campaign-forge\ra2youli"

u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)

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

ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
BM_CLICK = 0x00F5
LB_GETCOUNT = 0x018B
LB_GETITEMDATA = 0x0199
LB_SETCURSEL = 0x0186


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
        print("    !! 无 %s" % name)
        return False
    ok = u.PostMessageW(h, BM_CLICK, 0, 0)
    print("    click %-22s hwnd=%-10d -> %s" % (name, h, bool(ok)))
    time.sleep(wait)
    return True


def find_maplist(pid, minitems=50):
    for h, c, t, v in controls(pid):
        if c == "ListBox" and v:
            n = int(smt(h, LB_GETCOUNT))
            if n >= minitems:
                return h, n
    return None, 0


def launch_game():
    ps = (
        "Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @"
        "{CommandLine='cmd.exe /c cd /d \"%s\" && start \"\" \"gamemd.exe\"'}"
        % GAME_DIR
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   capture_output=True, timeout=60)



GAME_WND_CLASS = "Yuri's Revenge"


def game_window_thread(pid):
    """返回游戏主窗口所属线程 id（跑游戏主循环的那个线程）。"""
    hwnds = []

    def cb(h, l):
        q = wt.DWORD(0)
        u.GetWindowThreadProcessId(h, ctypes.byref(q))
        if q.value == pid and wcls(h) == GAME_WND_CLASS:
            hwnds.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    if not hwnds:
        return None
    # ★ 关键：GetWindowThreadProcessId 的**返回值**才是线程 id；
    #   lpdwProcessId 收到的是进程 id。早期版本读反了 ⇒ 一直退化成兜底路径。
    p_out = wt.DWORD(0)
    ret = u.GetWindowThreadProcessId(hwnds[0], ctypes.byref(p_out))
    return int(ret)


def pick_thread(threads, want_tid):
    """优先选游戏窗口线程；否则选含 gamemd.exe 帧最多者；再否则选帧最多者。"""
    got = [t for t in threads if t.get("frames")]
    if not got:
        return None, "no_threads"
    if want_tid:
        for t in got:
            if t.get("tid") == want_tid:
                return t, "window_thread"
    def n_game(t):
        return sum(1 for f in t["frames"]
                   if isinstance(f, dict) and "gamemd" in (f.get("name") or "").lower())
    game = [t for t in got if n_game(t) > 0]
    if game:
        return max(game, key=n_game), "most_gamemd_frames"
    return max(got, key=lambda t: len(t["frames"])), "longest"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pattern", default="H1")
    ap.add_argument("--seconds", type=float, default=240.0)
    ap.add_argument("--interval", type=float, default=0.2)
    ap.add_argument("--stall-n", type=float, default=1.0)
    ap.add_argument("--budget", type=float, default=400.0)
    ap.add_argument("--pid", type=int, default=0)
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--only-tid", action="store_true",
                    help="只采游戏窗口线程（1 线程），用于压进 <=50ms 预算")
    a = ap.parse_args()

    pid = a.pid
    if not pid:
        print("[N1] 启动游戏（WMI 分离）")
        launch_game()
        for _ in range(40):
            time.sleep(2)
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-Process -Name gamemd -ErrorAction SilentlyContinue).Id"],
                capture_output=True, text=True, timeout=30)
            s = out.stdout.strip()
            if s:
                pid = int(s.split()[0])
                break
        if not pid:
            print("!! 启动失败")
            return 3
    print("[N1] pid=%d" % pid)

    # 等主菜单就绪
    print("[N2] 等主菜单就绪")
    for i in range(45):
        if find_btn(pid, "GUI:SinglePlayer"):
            print("    就绪（%.0fs）" % (i * 2))
            break
        time.sleep(2)
    else:
        print("    !! 主菜单超时")
        return 3

    print("[N3] 导航")
    click(pid, "GUI:SinglePlayer", 3.0)
    click(pid, "GUI:Skirmish", 3.5)

    print("[N4] 打开地图对话框")
    click(pid, "GUI:ChooseMap", 3.0)
    lb, n = find_maplist(pid)
    print("    地图 ListBox=%s 条目=%d" % (lb, n))
    if not lb:
        print("    !! 没拿到地图列表")
        return 3

    hp = k32.OpenProcess(0x0010 | 0x0400, False, pid)

    def rw(addr, maxch=240):
        buf = (ctypes.c_char * (maxch * 2))()
        got = ctypes.c_size_t(0)
        if not k32.ReadProcessMemory(hp, ctypes.c_void_p(addr), buf, maxch * 2,
                                     ctypes.byref(got)):
            return None
        raw = bytes(buf[:got.value])
        out = bytearray()
        for i in range(0, len(raw) - 1, 2):
            if raw[i] == 0 and raw[i + 1] == 0:
                break
            out += raw[i:i + 2]
        try:
            return bytes(out).decode("utf-16-le")
        except Exception:
            return None

    names = []
    for i in range(n):
        d = int(smt(lb, LB_GETITEMDATA, i)) & 0xFFFFFFFF
        s = rw(d)
        names.append((i, s))
    k32.CloseHandle(hp)

    # 全部含 LoadBench 的
    print("    -- 含 LoadBench 的条目 --")
    lb_hits = [(i, s) for i, s in names if s and "LoadBench" in s]
    for i, s in lb_hits:
        print("       [%3d] %r" % (i, s))
    if not lb_hits:
        print("       （无）")

    target = None
    for i, s in names:
        if s and a.pattern in s:
            target = (i, s)
            if "LoadBench" in s:
                break
    print("    目标匹配 %r -> %s" % (a.pattern, target))
    if a.list_only:
        return 0
    if not target:
        print("!! 未找到含 %r 的地图" % a.pattern)
        return 4

    print("[N5] 选中 + UseMap")
    print("    LB_SETCURSEL(%d) -> %s" % (target[0], smt(lb, LB_SETCURSEL, target[0])))
    time.sleep(0.6)
    click(pid, "GUI:UseMap", 3.0)

    print("[N6] 开局")
    click(pid, "GUI:StartGame", 1.0)
    print("    等待加载 15s")
    time.sleep(15)

    # ---- 监测 ----
    print("[N7] 监测 %.0fs（停滞阈值 %.1fs）" % (a.seconds, a.stall_n))
    hproc = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    if not hproc:
        print("!! OpenProcess 失败")
        return 5
    try:
        flag = wt.BOOL(0)
        k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
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
        sampler._target_is32 = is32
        wok, werr = cand.attach_stackwalker(sampler, hproc, pid, is32)
        print("    StackWalker=%s %s" % (wok, werr or ""))
        det = cand.StallDetector(n_seconds=a.stall_n, min_obs=6)

        def rd(addr):
            b = (ctypes.c_char * 4)()
            cnt = ctypes.c_size_t(0)
            ok = k32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), b, 4,
                                       ctypes.byref(cnt))
            return int.from_bytes(b.raw, "little") if ok and cnt.value == 4 else None

        want_tid = game_window_thread(pid)
        print("    游戏窗口线程 tid=%s" % want_tid)
        t0 = time.monotonic()
        samples, events = [], []
        while time.monotonic() - t0 < a.seconds:
            now = time.monotonic()
            v = rd(0x00A8ED84)
            samples.append((round(now - t0, 3), v))
            if det.observe(now, v):
                print("  ★★ 停滞 @ t=%.2fs frame=%s → 抓栈" % (now - t0, v))
                res = sampler.sample(pid)
                if a.only_tid and want_tid:
                    t1 = time.monotonic()
                    one = sampler.sample_one_thread(want_tid)
                    cost = (time.monotonic() - t1) * 1000.0
                    ev = {"t": round(now - t0, 3), "frame": v,
                          "mode": "single_thread",
                          "paused_ms": round(cost, 1),
                          "errors": one.get("errors") if isinstance(one, dict) else None,
                          "picked_by": "only_tid"}
                    if isinstance(one, dict) and one.get("frames"):
                        ev["stack"] = {"tid": want_tid,
                                       "bits": (one.get("ctx") or {}).get("bits"),
                                       "n": len(one["frames"]),
                                       "frames": one["frames"]}
                        print("      单线程采样 tid=%d %d 帧  cost=%.1fms"
                              % (want_tid, len(one["frames"]), cost))
                        for i2, f2 in enumerate(one["frames"][:12]):
                            nm = f2.get("name") if isinstance(f2, dict) else f2
                            ad = f2.get("addr") if isinstance(f2, dict) else 0
                            print("        #%-2d %s" % (i2, nm or hex(ad)))
                    else:
                        print("      单线程采样无帧 cost=%.1fms %s" % (cost, one))
                    events.append(ev)
                    time.sleep(a.interval)
                    continue
                threads = res.get("threads", [])
                got = [x for x in threads if x.get("frames")]
                best, how = pick_thread(threads, want_tid)
                ev = {"t": round(now - t0, 3), "frame": v,
                      "errors": res.get("errors"), "paused_ms": res.get("paused_ms"),
                      "picked_by": how,
                      "all_threads": [{"tid": x["tid"],
                                        "bits": x["ctx"]["bits"],
                                        "n": len(x["frames"])} for x in threads]}
                if best:
                    ev["stack"] = {"tid": best["tid"],
                                   "bits": best["ctx"]["bits"],
                                   "n": len(best["frames"]),
                                   "frames": best["frames"]}
                    print("      采 %d 线程，选中 tid=%d（%s）%d 帧 paused=%sms"
                          % (len(got), best["tid"], how, len(best["frames"]),
                             res.get("paused_ms")))
                    for i2, f in enumerate(best["frames"][:12]):
                        nm = f.get("name") if isinstance(f, dict) else f
                        ad = f.get("addr") if isinstance(f, dict) else 0
                        print("        #%-2d %s" % (i2, nm or hex(ad)))
                events.append(ev)
            time.sleep(a.interval)

        vals = [v for _, v in samples if v is not None]
        print("\n[结果] 采样 %d 可读 %d" % (len(samples), len(vals)))
        if vals:
            d = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
            nz = [x for x in d if x != 0]
            print("  frame %s→%s  Δ中位=%s  ⇒ %.1f fps" %
                  (vals[0], vals[-1],
                   statistics.median(nz) if nz else "-",
                   (statistics.median(nz) / a.interval) if nz else 0))
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
                print("  零Δ段 %d 个，最长 %.2fs，≥%.1fs 的 %d 个"
                      % (len(runs), max(runs) * a.interval, a.stall_n,
                         sum(1 for r in runs if r * a.interval >= a.stall_n)))
        print("  停滞事件 = %d" % len(events))
        p = BASE / ("_hl_match_%d.json" % pid)
        p.write_text(json.dumps({"pid": pid, "pattern": a.pattern,
                                 "target": target, "is32": is32,
                                 "n_samples": len(samples),
                                 "n_readable": len(vals), "events": events},
                                ensure_ascii=False, indent=1), encoding="utf-8")
        print("  落盘 %s" % p)
        try:
            if wok:
                sampler.stack_walker.cleanup()
        except Exception:                                  # noqa: BLE001
            pass
    finally:
        k32.CloseHandle(hproc)
    return 0


if __name__ == "__main__":
    sys.exit(main())

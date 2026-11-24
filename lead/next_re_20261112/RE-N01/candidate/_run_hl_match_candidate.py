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

===============================================================================
RE-N01 候选副本（由 lead/re_d13_ruling_20261112/_run_hl_match.py 复制后最小改动）
===============================================================================
本轮 run_id = NEXT_RE_20261112_R01。本副本**只做离线候选与离线测试**：
  * 未启动游戏、未 attach 活进程、未 ReadProcessMemory 活进程、
    未 SuspendThread / ResumeThread / StackWalk64 / 断点 / 注入 / 部署 / taskkill；
  * main() 的 N1-N6 导航代码与原件逐字相同（保留原 CLI 语义），
    但本轮**不执行 main() 的游戏路径**；离线测试只调用可注入的 run_monitor()；
  * 所有 Win32 调用在离线测试中均为 stub / fake，真实 Win32 行为未验。

相对原件的关键修正（详见 DIFF.md；FACT_CHECK.md 逐条对账前代理声称）：
  A  --only-tid 与全线程路径互斥（绝不先调 sample(pid) 再丢弃结果）
  B  单线程入口改为 sampler.sample_single()：preflight_target() 显式契约、
     恢复返回值/异常/预算/线程数/归属校验全部入事件、try/except 不穿透循环
  C  逐条流式 NDJSON（每行 flush，可选 fsync），异常退出仍保留此前原始记录；
     摘要可由 replay_re_n01.py 从同一 NDJSON 离线重算
  C2 读失败区间分段并保留真实时间间隔，不把两端同值拼成连续冻结
  D  计时统一 perf_counter_ns()；不再输出「median(非零Δ)/interval ⇒ fps」伪帧率

   E  不再把结果写回**只读原件目录** BASE；全部产物落在本轮写域

★ 对账提示：本副本的第一版**只改了本 docstring**，N7 循环仍是原件逻辑
  （无条件 sampler.sample(pid) → 再判 --only-tid → 直接 sample_one_thread）。
  本轮续做才把 A/C/C2/E 真正落到代码里（委托 re_n01_monitor.run_monitor）；
  详见 FACT_CHECK.md「原代理声称 / 实际」。

用法：
  python -I -X utf8 _run_hl_match_candidate.py --pattern H1 --seconds 240
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

# RE-N01：从本副本所在目录的上一级导入只读重算器（纯 Python，无 Win32）
_RE_N01_ROOT = Path(__file__).resolve().parent.parent
if str(_RE_N01_ROOT) not in sys.path:
    sys.path.insert(0, str(_RE_N01_ROOT))

RUN_ID = "NEXT_RE_20261112_R01"

BASE = Path(r"D:\Project\ra2-campaign-forge\lead\re_d13_ruling_20261112")
GAME_DIR = r"D:\Project\ra2-campaign-forge\ra2youli"
# RE-N01：候选件母本目录（Sampling r2 与本驱动副本同目录）
CANDIDATE_DIR = Path(__file__).resolve().parent
if str(CANDIDATE_DIR) not in sys.path:
    sys.path.insert(0, str(CANDIDATE_DIR))

# 纯 Python 的流式记录 / 分段 / 在线摘要模块（无任何 Win32）
import re_n01_monitor as mon  # noqa: E402


def _load_sampler_module():
    """从候选目录加载 r2 采样器（不触碰只读原件目录）。"""
    spec = importlib.util.spec_from_file_location(
        "re_n01_sampler_r2", str(CANDIDATE_DIR / "e3_stack_sampler_candidate_r2.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# RE-N01：Win32 绑定**延迟到 main()**，离线 import 本模块不加载任何 DLL、
# 不产生任何 Win32 副作用；离线测试注入的 rd / sampler / clock 全是假对象。
u = None
k32 = None


def _bind_win32():
    global u, k32
    if u is not None and k32 is not None:
        return
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
    ap.add_argument("--ndjson", default=None,
                    help="流式原始 NDJSON 输出路径（默认 out/run_<pid>.ndjson）")
    ap.add_argument("--summary", default=None,
                    help="在线摘要 JSON 输出路径；可由 replay_re_n01.py 离线重算")
    a = ap.parse_args()
    _bind_win32()

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

    # ---- 监测（RE-N01：委托给可注入的 run_monitor；P1/P2/P3/P5/P6 都在此实现）----
    # 与原件的关键差别：不再无条件先调 sample(pid) 再丢弃结果（问题 A），
    # 不再用 time.monotonic() 只记最后一次函数调用耗时（问题 B），
    # 不再把摘要写进只读原件目录 BASE；全部原始记录流式落进本轮写域。
    print("[N7] 监测 %.0fs（停滞阈值 %.1fs）" % (a.seconds, a.stall_n))
    hproc = k32.OpenProcess(0x0010 | 0x0400, False, pid)
    if not hproc:
        print("!! OpenProcess 失败")
        return 5
    try:
        flag = wt.BOOL(0)
        k32.IsWow64Process(hproc, ctypes.byref(flag))
        is32 = bool(flag.value)
        cand = _load_sampler_module()
        cand.bind_real_ops()
        sampler = cand.StackSampler(budget_ms=a.budget)
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
        ndjson_path = Path(a.ndjson) if a.ndjson else (
            _RE_N01_ROOT / "out" / ("run_%d.ndjson" % pid))
        summary_path = Path(a.summary) if a.summary else (
            _RE_N01_ROOT / "out" / ("online_summary_%d.json" % pid))
        cfg = mon.default_cfg(
            run_id=RUN_ID, provenance="live_run_not_executed_this_round")
        cfg["stall_n_ns"] = int(a.stall_n * 1e9)
        cfg["nominal_interval_ns"] = int(a.interval * 1e9)
        cfg["gap_max_ns"] = int(3 * a.interval * 1e9)
        sink = mon.NDJSONSink(ndjson_path)

        def rd_frame(_i):
            return {"frame": rd(0x00A8ED84), "pid": pid}

        out = mon.run_monitor(
            pid=pid, want_tid=want_tid,
            only_tid=bool(a.only_tid and want_tid),
            sampler=sampler, detector=det, rd=rd_frame, sink=sink, cfg=cfg,
            interval_s=a.interval,
            max_ticks=max(1, int(a.seconds / max(a.interval, 1e-6))),
            summary_path=summary_path)
        s = out["summary"]
        print("\n[结果] 原始记录 %d 行（frame_read=%d event=%d 段=%d）"
              % (s["n_records"], s["n_frame_reads"], s["n_events"],
                 s["n_segments"]))
        print("  已证实连续冻结=%d 缺测打断段=%d 事件数=%d"
              % (s["n_confirmed_continuous_freezes"],
                 s["n_gap_interrupted_runs"], len(out["events"])))
        print("  NDJSON  %s" % ndjson_path)
        print("  在线摘要 %s（可由 replay_re_n01.py 离线重算逐字段比对）"
              % summary_path)
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

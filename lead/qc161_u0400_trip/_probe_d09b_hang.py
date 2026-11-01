#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-09 选项 B：钉死「守卫开臂不崩也不退」的挂死机制（真机，两臂对照）。

★ 为什么要这一趟（§426 留下的不可区分）：
  ab24 开臂三趟**全程挂在 DebugActiveProcess 下**（且边泵事件边继续）。
  关窗后 24–114 s 无 EXIT_PROCESS，但两种机制在「只投 WM_CLOSE」的观测下同形：
    (i) 调试器附加本身就是扰动（首次异常交付/继续的时序改变退出链）；
    (ii) 守卫把崩溃换成了挂死（真实行为）。
  ⇒ 反事实主臂 = **开臂 + 无调试器**：仍不退 ⇒ 挂死是真的（D-09 走改件）；
    正常退 ⇒ §426 的挂死是调试器产物，D-09 判据要重写。

★ 两臂（各自独立判据，互不替代）：
  MAIN   Guard=1 无调试器   反事实主臂
  CTRL1  Guard=0 无调试器   基线：游戏自己的 __except 吞掉 AV 之后，
                           **不加任何外力**进程到底退不退。
                           ★ 这臂不是可选项：若 CTRL1 也挂 ⇒ 「不退」不是守卫造成的
                           （崩溃本身已断退出链），D-09 的问题定义整个要改写。
  （有调试器开臂 = ab24 三趟已录，不重跑；本件的无调试器附加不泵事件，
    那种「假挂」是另一种扰动，不做。）

★ 采样（无调试器 ⇒ 进程不被暂停，旁路 100 ms 读）：
  singleton[0x887368] / hwnd[0x00B73550] / exitstate[0x00A8EDD8] / frame[0x00A8ED84]
  + WaitForSingleObject 返回值枚举（0=退出 258=活着 其它=**不判死**，防假退出）
  + 工作集 + **顶层窗口集变化**（抓「press OK」类对话框）
  + 趟末 GetExitCodeProcess 真实码（§402 语义）

★ 纪律
  - 他线件（探针/守卫 DLL/loader）一字不改，sha 预检：b063052c / 0e2a9995 / ebddf6a6；
  - 只读 gamemd 母本，载体建在本线写域 lead/qc161_u0400_trip/d09b/，趟内删 ct 树；
  - gamemd stdio 敏感 ⇒ stdout/stderr=DEVNULL，零 PIPE；
  - 无调试器臂不产 dump（MiniDump 要调试事件），设计内取舍：本趟判「退不退」，
    崩溃现场已由 ab24 的 7 份 dump 定谳；
  - ★ 全部 Win32 句柄声明 argtypes/restypes（x64 截断坑 [[ctypes-argtypes-win32-real-machine-trap]]）。
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "d09b"
THEIR = ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py"
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
GAMEMD_SHA16 = "73201cc021497c95"
GUARD_DLL_SHA16 = "0e2a9995ad71184c"
LOADER_SHA16 = "ebddf6a61273c874"
THEIR_SHA16 = "b063052cd02df28c"
CARRIER_PATH_MAX = 130

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
G_FRAME = 0x00A8ED84
WM_CLOSE = 0x0010
WAIT_TIMEOUT, WAIT_OBJECT_0 = 258, 0

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)

# ★ x64：句柄一律 c_void_p/HANDLE，禁止默认 int 截断
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.WaitForSingleObject.restype = wt.DWORD
k32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
k32.GetExitCodeProcess.restype = wt.BOOL
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.TerminateProcess.restype = wt.BOOL
k32.TerminateProcess.argtypes = [wt.HANDLE, ctypes.c_uint]
k32.ReadProcessMemory.restype = wt.BOOL
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
class PMEMCT(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
psapi.GetProcessMemoryInfo.restype = wt.BOOL
psapi.GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMEMCT), wt.DWORD]
u32.PostMessageW.restype = wt.BOOL
u32.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.IsWindowVisible.restype = wt.BOOL
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.GetWindowTextW.restype = ctypes.c_int
u32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u32.GetWindowRect.restype = wt.BOOL
u32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
u32.GetClassNameW.restype = ctypes.c_int
u32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]

ENUMPROC_T = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [ENUMPROC_T, wt.LPARAM]


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_their():
    spec = importlib.util.spec_from_file_location("rc4_ab_probe", THEIR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = None  # main() 里初始化（他线件只读复用：list_procs/query_image/under_carrier/k32/rpm_u32）


def set_enable(ini: Path, val: int) -> None:
    """只认独占一行的 [Logic] 节头 + 写后回读验证（§426 注释陷阱的修复版）。"""
    lines = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = next((i for i, ln in enumerate(lines) if ln.strip() == "[Logic]"), None)
    if idx is None:
        lines += ["", "[Logic]", "EnableRC4Guard=%d" % val]
    else:
        end = next((j for j in range(idx + 1, len(lines))
                    if lines[j].strip().startswith("[")), len(lines))
        for k in range(idx + 1, end):
            if lines[k].strip().startswith("EnableRC4Guard="):
                lines[k] = "EnableRC4Guard=%d" % val
                break
        else:
            lines.insert(idx + 1, "EnableRC4Guard=%d" % val)
    ini.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    chk = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next((i for i, ln in enumerate(chk) if ln.strip() == "[Logic]"), None)
    if hi is None or not any(l.strip() == "EnableRC4Guard=%d" % val for l in chk[hi + 1:hi + 6]):
        raise RuntimeError("set_enable 回读验证失败（键未落在节内）")


def build_carrier(dst: Path, extra, enable):
    dst.mkdir(parents=True, exist_ok=False)
    n = 0
    for f in sorted(GAME_SRC.iterdir()):
        if f.is_file():
            shutil.copy2(f, dst / f.name)
            n += 1
    for f in extra or []:
        shutil.copy2(f, dst / f.name)
    if enable is not None:
        set_enable(dst / "ra2render.ini", enable)
    return n


def rpm_u32(h, addr):
    buf = ctypes.create_string_buffer(4)
    n = ctypes.c_size_t(0)
    if not k32.ReadProcessMemory(h, ctypes.c_void_p(addr),
                                 ctypes.cast(buf, ctypes.c_void_p), 4,
                                 ctypes.byref(n)):
        return None
    return int.from_bytes(buf.raw[:4], "little")


def working_set_kb(h):
    m = PMEMCT()
    m.cb = ctypes.sizeof(m)
    if not psapi.GetProcessMemoryInfo(h, ctypes.byref(m), m.cb):
        return None
    return m.WorkingSetSize // 1024 if m.WorkingSetSize else None


def enum_windows_for(pid):
    wins = []

    def _cb(hwnd, _):
        w = wt.DWORD(0)
        # ★★ 10-25 修的**过滤器自杀 bug**：GetWindowThreadProcessId 的**返回值=线程 id**，
        #   出参 w 才是 pid。旧写法拿返回值比 pid ⇒ 恒不等 ⇒ **任何窗口都不匹配**，
        #   造成「9 连败无窗」假墙（他线 find_main_window 用 out-param 故从未有此问题）。
        #   ⇒ 正确判据=比对 **w.value**。
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(w))
        if w.value != pid:
            return True
        buf = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, buf, 256)
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, cls, 256)
        r = wt.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(r))
        wins.append({"hwnd": hwnd, "title": buf.value, "class": cls.value,
                     "visible": bool(u32.IsWindowVisible(hwnd)),
                     "rect": [r.left, r.top, r.right, r.bottom]})
        return True

    u32.EnumWindows(ENUMPROC_T(_cb), 0)
    return wins


def find_game_window(pid):
    for w in enum_windows_for(pid):
        if w["class"] == "Yuri's Revenge":
            return w
    return None


def sample_loop(h, pid, t_end, period=0.1):
    """旁路采样。★存活只认 WaitForSingleObject 返回值枚举：
    0=退出 258=活着 其它（含 WAIT_FAILED）=不判死——防「句柄坏了误记假退出」。"""
    rows, seen = [], None
    while time.time() < t_end:
        res = k32.WaitForSingleObject(h, 0)
        alive = (res == WAIT_TIMEOUT)
        ex = wt.DWORD(0)
        k32.GetExitCodeProcess(h, ctypes.byref(ex))
        r = {"t": round(time.time(), 3), "wait_res": res,
             "exitcode": ex.value if res == WAIT_OBJECT_0 else None,
             "singleton": rpm_u32(h, G_SINGLETON),
             "hwnd_glob": rpm_u32(h, G_HWND),
             "exitstate": rpm_u32(h, G_EXITSTATE),
             "frame": rpm_u32(h, G_FRAME),
             "ws_kb": working_set_kb(h) if alive else None}
        if alive:
            wins = enum_windows_for(pid)
            key = tuple(sorted((w["hwnd"], w["title"]) for w in wins))
            if key != seen:
                r["windows"] = wins
                seen = key
        rows.append(r)
        if res == WAIT_OBJECT_0:
            break
        time.sleep(period)
    return rows


def _cleanup(proc, carrier, rec):
    # ★ 日志拷贝**先于**任何删除/返回：abort 路径（no_game_window 等）也必须留证。
    #   旧版把拷贝放在采样段之后，abort 臂直接 return ⇒ guard_lines=None，
    #   而 diag 实测守卫「已装 8/8」存在 ⇒ 假「install=False」（读不到≠没装）。
    try:
        logf = carrier / "ra2render.log"
        if logf.exists():
            out_dir = Path(rec.get("out_dir") or ".")
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(logf, out_dir / "ra2render.log")
            rec["guard_lines"] = [l for l in (out_dir / "ra2render.log")
                                  .read_text(encoding="utf-8", errors="replace").splitlines()
                                  if "[ra2rc4guard]" in l]
    except Exception as e:
        rec["guard_log_copy_err"] = repr(e)
    for p, nm in list(MOD.list_procs().items()):
        if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, carrier):
                hh = k32.OpenProcess(0x0001 | 0x100000, False, p)  # Terminate|Synchronize
                if hh:
                    k32.TerminateProcess(hh, 1)
                    k32.CloseHandle(hh)
                    rec.setdefault("killed_on_cleanup", []).append([p, nm])
    try:
        proc.wait(timeout=5)
    except Exception:
        pass
    # ★ 10-25 修（§428 四）：TerminateProcess 后进程表摘除是**异步**的，
    #   旧写法立即枚举 ⇒ 刚杀的 pid 还在表里 ⇒ a8 V_FAIL 竞态假红。
    #   改为**有界轮询**（≤3 s）直到载体内目标从表里消失或超时。
    deadline = time.time() + 3.0
    while time.time() < deadline:
        rem = [p for p, nm in MOD.list_procs().items()
               if nm.lower() in ("gamemd.exe", "rc4_loader.exe")
               and (MOD.query_image(p) or "").lower().startswith(str(carrier).lower())]
        if not rem:
            break
        time.sleep(0.25)
    rec["a8_remaining"] = rem
    # ★ 枚举器正控（查得到自己进程才算「看得见」；空表=false-PASS 禁止）
    rec["a8_enum_ok"] = os_getpid_in(MOD.list_procs())
    rec["a8_verdict"] = "PASS" if (not rem and rec["a8_enum_ok"]) else "V_FAIL"
    for _att in range(6):                    # rmtree 同样要等映像句柄释放
        shutil.rmtree(carrier.parent, ignore_errors=True)
        if not carrier.parent.exists():
            break
        time.sleep(0.5)
    rec["carrier_deleted"] = not carrier.parent.exists()


def os_getpid_in(procs):
    return os.getpid() in procs


def run_trip(tag, guard_enable, watch_s=60.0, hold_s=6.0):
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = MYCARD / ("%s_%s" % (stamp, tag))
    carrier = out_dir / "ct" / ("c" + "0" * 10)
    rec = {"tag": tag, "guard_enable": guard_enable, "attach_debugger": False,
           "carrier_len": len(str(carrier)), "out_dir": str(out_dir)}
    if rec["carrier_len"] > CARRIER_PATH_MAX:
        rec["abort"] = "carrier_path_too_long"
        return rec
    out_dir.mkdir(parents=True, exist_ok=True)

    extra = [GUARD_DIR / "rc4_loader.exe", GUARD_DIR / "ra2rc4guard.dll"]
    rec["carrier_files"] = build_carrier(carrier, extra, guard_enable)
    rec["gamemd_sha16"] = sha16(carrier / "gamemd.exe")
    if rec["gamemd_sha16"] != GAMEMD_SHA16:
        rec["abort"] = "gamemd_sha_mismatch"
        _cleanup(None, carrier, rec)
        return rec

    ex_path = carrier / "except.txt"
    rec["except_before"] = sha16(ex_path) if ex_path.exists() else None

    # ★ env 必须是**继承全量再叠加**（他线件同法 env=dict(os.environ)+键）。
    #   env={...} 直接替换整环境（PATH/SystemRoot 全丢）⇒ loader 起得来但游戏
    #   40 s 无窗口（本探针首跑两臂实测此失效形态，gamemd_pid 有、window 无）。
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen([str(carrier / "rc4_loader.exe"), "ra2rc4guard.dll"],
                            cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec["loader_pid"] = proc.pid
    t_launch = time.time()

    pid = None
    for _ in range(150):
        time.sleep(0.1)
        for p, nm in MOD.list_procs().items():
            if nm.lower() != "gamemd.exe":
                continue
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, carrier):
                pid = p
                break
        if pid:
            break
    if pid is None:
        rec["abort"] = "gamemd_not_found_under_carrier"
        _cleanup(proc, carrier, rec)
        return rec
    rec["gamemd_pid"] = pid

    win = None
    while time.time() - t_launch < 40.0:
        win = find_game_window(pid)
        if win:
            break
        time.sleep(0.5)
    rec["game_window_s"] = round(time.time() - t_launch, 2)
    rec["game_window"] = bool(win)
    if not win:
        rec["abort"] = "no_game_window_40s"
        _cleanup(proc, carrier, rec)
        return rec

    time.sleep(hold_s)
    pre_wins = {w["hwnd"]: w["title"] for w in enum_windows_for(pid)}
    u32.PostMessageW(wt.HWND(win["hwnd"]), WM_CLOSE, 0, 0)
    t_close = time.time()
    rec["closed_at_s"] = round(t_close - t_launch, 3)

    h = k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)  # QUERY|VM|SYNCHRONIZE
    if not h:
        rec["abort"] = "OpenProcess_failed err=%d" % ctypes.get_last_error()
        _cleanup(proc, carrier, rec)
        return rec
    try:
        rows = sample_loop(h, pid, t_close + watch_s, period=0.1)
    finally:
        k32.CloseHandle(h)
    rec["n_sample"] = len(rows)
    rec["wait_failed_rows"] = sum(1 for r in rows if r["wait_res"] not in (WAIT_TIMEOUT, WAIT_OBJECT_0))
    rec["sample_head"] = rows[:5]
    rec["sample_tail"] = rows[-15:]

    exit_row = next((r for r in rows if r["wait_res"] == WAIT_OBJECT_0), None)
    rec["exited_within_watch"] = exit_row is not None
    rec["exit_after_close_s"] = round(exit_row["t"] - t_close, 2) if exit_row else None
    rec["final_exitcode"] = exit_row["exitcode"] if exit_row else None

    def traj(key):
        vs = [(round(r["t"] - t_close, 2), r[key]) for r in rows if r.get(key) is not None]
        return {"first": vs[0] if vs else None, "last": vs[-1] if vs else None,
                "distinct_n": len(set(v for _t, v in vs))}
    rec["traj_frame"] = traj("frame")
    rec["traj_exitstate"] = traj("exitstate")
    rec["traj_singleton"] = traj("singleton")
    rec["traj_ws"] = traj("ws_kb")

    new_wins = {}
    for r in rows:
        for w in (r.get("windows") or []):
            if w["visible"] and w["hwnd"] != win["hwnd"] and w["hwnd"] not in pre_wins:
                new_wins[w["hwnd"]] = {"title": w["title"], "class": w["class"],
                                       "rect": w["rect"]}
    rec["extra_windows_after_close"] = list(new_wins.values())

    if (carrier / "except.txt").exists():
        rec["except_after"] = sha16(carrier / "except.txt")
        rec["except_changed"] = rec["except_after"] != rec["except_before"]
    if (carrier / "ra2render.log").exists():
        shutil.copy2(carrier / "ra2render.log", out_dir / "ra2render.log")
        rec["guard_lines"] = [l for l in
                              (out_dir / "ra2render.log").read_text(
                                  encoding="utf-8", errors="replace").splitlines()
                              if "[ra2rc4guard]" in l]
    _cleanup(proc, carrier, rec)
    return rec


def main() -> int:
    global MOD
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--watch", type=float, default=60.0)
    a = ap.parse_args()
    MOD = load_their()

    print("=" * 78)
    print("D-09-B 挂死机制双臂探针   live=%s   watch=%.0f s" % (a.live, a.watch))
    print("=" * 78)
    fails = []
    for name, ok, det in [
        ("他线探针未改 sha", sha16(THEIR) == THEIR_SHA16, sha16(THEIR)),
        ("gamemd 母本 sha", sha16(GAME_SRC / "gamemd.exe") == GAMEMD_SHA16, ""),
        ("守卫 dll sha", sha16(GUARD_DIR / "ra2rc4guard.dll") == GUARD_DLL_SHA16, ""),
        ("loader sha", sha16(GUARD_DIR / "rc4_loader.exe") == LOADER_SHA16, ""),
        ("残留进程=0", not MOD.game_procs(), str(MOD.game_procs())),
    ]:
        print("  [%s] %-36s %s" % ("OK" if ok else "RED", name, det))
        fails.append(name) if not ok else None
    if fails:
        return 2
    if not a.live:
        print("\n★ 预检全过；--live 发射两臂（MAIN=开臂无调试器 / CTRL1=关臂无调试器）。")
        return 0

    MYCARD.mkdir(parents=True, exist_ok=True)
    results = []
    for tag, enable in [("MAIN_OnNoDbg", 1), ("CTRL1_OffNoDbg", 0)]:
        print("\n" + "-" * 78)
        print("[臂 %s] Guard=%s 无调试器" % (tag, enable))
        r = run_trip(tag, enable, watch_s=a.watch)
        results.append(r)
        print("   exited=%s after=%s code=%s windows=%s install=%s a8=%s"
              % (r.get("exited_within_watch"), r.get("exit_after_close_s"),
                 r.get("final_exitcode"), len(r.get("extra_windows_after_close") or []),
                 any("已装 8/8" in l for l in r.get("guard_lines") or []),
                 r.get("a8_verdict")))
        if r.get("abort"):
            print("   ABORT:", r["abort"])
        leftover = MOD.game_procs()
        if leftover:
            r["leftover_between"] = leftover
            print("   !! 臂间残留 %s ⇒ 停后续" % leftover)
            break
        Path(r["out_dir"]).mkdir(parents=True, exist_ok=True)
        (Path(r["out_dir"]) / "_rec.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")

    (MYCARD / "d09b_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n" + "=" * 78)
    for r in results:
        print("  %-15s exited=%-5s after=%-7s code=%-4s newwins=%-2s install=%-5s a8=%s abort=%s"
              % (r.get("tag"), r.get("exited_within_watch"), r.get("exit_after_close_s"),
                 r.get("final_exitcode"), len(r.get("extra_windows_after_close") or []),
                 any("已装 8/8" in l for l in r.get("guard_lines") or []),
                 r.get("a8_verdict"), r.get("abort")))
    print("残留:", MOD.game_procs() or "0")
    return 0


if __name__ == "__main__":
    sys.exit(main())

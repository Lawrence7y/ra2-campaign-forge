#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C26-01 ②收尾：c″ 已装态 **L1 进局回归 + 回滚** 真机一趟（MAIN 配置）。

★ 裁决依据（RULINGS.md C26-01 末段）：「若 MAIN 成功，先记 RC-4 退出场景候选修复通过，
  再做已批准 L1 进局回归与回滚」。A/B（c2ab/）已全过 ⇒ 本件补进局面。

★ 判据（全部满足才算过）：
  R1 进局：第三次点击后 CurrentFrame(0x00A8ED84) 持续推进（≥20 帧增量带）⇒ 真进战斗
  R2 局内非干扰：战斗中 exitstate(0xA8EDD8)=0、hwnd(0xB73550)≠0、单例≠0、
     站点 0x6BE0E1 hook 窗全程 == E9+90（c″ 在位且从未被触发移除）
  R3 局内退出：WM_CLOSE 后 **20 s 内自然退出**、exitcode 可读（同 A/B MAIN 门槛，
     战斗上下文=更强的回归：泵环在退出序列内被真跑到）
  R4 零错误：无新增 #32770 / 任何新可见窗口；except.txt 哈希不变；趟窗事件日志零 AV
  R5 回滚：ra2render.log 卸载行=8/8 一致 + FNV 前后相等（守卫+c″ 双事务）；
     载体删净、残留=0、gamemd 母本四哈希不变

★ 进局方法学：逐字复用 harness7（在用件，D-08 有限升格）的
  `find_main_window / _focus_foreground / click_logical(FS 直通映射) / _rpm_*`，
  import-only、零改动他件源码；`_QC151FS["on"]=True` 状态位=与 hc 趟同映射。
  点击序列=NAV_SIG_PLAN 三连（700,218 → 700,304 → 700,262）+ 固定等待
  （无 sig 闸门：以「帧钟推进」为进局正判据，比截图签名更强）。

★ 纪律
  - 他线件 sha 预检；gamemd 只读；ra2youli 不动；载体全落本线写域 c2ab/；
  - gamemd stdio 敏感 ⇒ DEVNULL 零 PIPE；全部句柄 argtypes/restypes。
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
from ctypes import wintypes as wt
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MYCARD = ROOT / "lead" / "qc161_u0400_trip" / "c2ab"
H7_PATH = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
H7_SHA16 = "d019e8beecfb5fd8"          # 在用件（KNOWN_HARNESS 在册）
GAME_SRC = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/_src_L1_sf8_20261020"
GUARD_DIR = ROOT / "lead/goal2_rc4_fixv5_20261022/src"
C2_DIR = ROOT / "lead/qc161_u0400_trip/d09a_c2_candidate"

GAMEMD_SHA16 = "73201cc021497c95"
LOADER_SHA16 = "ebddf6a61273c874"
MOTHER_DLL_SHA16 = "0e2a9995ad71184c"
C2_DLL_SHA256 = "edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de"

G_SINGLETON = 0x00887368
G_HWND = 0x00B73550
G_EXITSTATE = 0x00A8EDD8
G_FRAME = 0x00A8ED84
BAIL_SITE = 0x006BE0E1
WM_CLOSE = 0x0010
WAIT_TIMEOUT, WAIT_OBJECT_0 = 258, 0
NAV_CLICKS = ((700, 218), (700, 304), (700, 262))   # NAV_SIG_PLAN 三连（harness7:331）

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
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
u32.PostMessageW.restype = wt.BOOL
u32.PostMessageW.argtypes = [wt.HWND, ctypes.c_uint, wt.WPARAM, wt.LPARAM]
u32.GetWindowThreadProcessId.restype = wt.DWORD
u32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
u32.IsWindowVisible.restype = wt.BOOL
u32.IsWindowVisible.argtypes = [wt.HWND]
u32.GetWindowTextW.restype = ctypes.c_int
u32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
u32.GetClassNameW.restype = ctypes.c_int
u32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
ENUMPROC_T = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
u32.EnumWindows.argtypes = [ENUMPROC_T, wt.LPARAM]


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load_h7():
    os.environ["QC151_OUT_DIR"] = str(MYCARD / "_h7_workdir")   # 重定向其模块级 WORKDIR，防污染
    spec = importlib.util.spec_from_file_location("harness7_ro", H7_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_probe():
    spec = importlib.util.spec_from_file_location("rc4_ab_probe",
                                                  ROOT / "lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PROBE = None


def write_keys(ini: Path, guard: int, bail: int, dry: int) -> None:
    """同 _drive_c2_ab.write_keys：独占一行 [Logic] + 回读验证。"""
    want = {"EnableRC4Guard": guard, "EnableRC4ExitBail": bail, "RC4GuardDryRun": dry}
    lines = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = next((i for i, ln in enumerate(lines) if ln.strip() == "[Logic]"), None)
    assert idx is not None, "源 ini 缺 [Logic] 节头"
    end = next((j for j in range(idx + 1, len(lines))
                if lines[j].strip().startswith("[")), len(lines))
    for k in range(idx + 1, end):
        for key in list(want):
            if lines[k].strip().startswith(key + "="):
                lines[k] = "%s=%d" % (key, want.pop(key))
                break
    for key, val in want.items():
        lines.insert(idx + 1, "%s=%d" % (key, val))
    ini.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")
    chk = ini.read_text(encoding="utf-8", errors="replace").splitlines()
    hi = next((i for i, ln in enumerate(chk) if ln.strip() == "[Logic]"), None)
    sec = chk[hi + 1:]
    stop = next((i for i, ln in enumerate(sec) if ln.strip().startswith("[")), len(sec))
    for key, val in {"EnableRC4Guard": guard, "EnableRC4ExitBail": bail,
                     "RC4GuardDryRun": dry}.items():
        if not any(ln.strip() == "%s=%d" % (key, val) for ln in sec[:stop]):
            raise RuntimeError("write_keys 回读失败：%s" % key)


def rpm(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    got = ctypes.c_size_t(0)
    ok = k32.ReadProcessMemory(h, ctypes.c_void_p(addr), ctypes.cast(buf, ctypes.c_void_p),
                               size, ctypes.byref(got))
    return buf.raw[:got.value] if ok else None


def rpm_u32(h, addr):
    raw = rpm(h, addr, 4)
    return struct.unpack("<I", raw)[0] if raw is not None else None


def enum_windows_for(pid):
    wins = []

    def _cb(hwnd, _):
        w = wt.DWORD(0)
        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(w))
        if w.value != pid:
            return True
        buf = ctypes.create_unicode_buffer(256)
        u32.GetWindowTextW(hwnd, buf, 256)
        cls = ctypes.create_unicode_buffer(256)
        u32.GetClassNameW(hwnd, cls, 256)
        wins.append({"hwnd": hwnd, "title": buf.value, "class": cls.value,
                     "visible": bool(u32.IsWindowVisible(hwnd))})
        return True

    u32.EnumWindows(ENUMPROC_T(_cb), 0)
    return wins


def bail_hook_expect(cave_base):
    rel = cave_base - (BAIL_SITE + 5)
    return (b"\xE9" + struct.pack("<i", rel) + b"\x90").hex()


def find_cave_base(log_lines):
    for l in log_lines or []:
        if "[ra2rc4exitbail]" in l and "已装 1/1" in l:
            m = re.search(r"cave 0x([0-9A-Fa-f]{1,8})", l)
            if m:
                return int(m.group(1), 16)
    return None


def snapshot_globals(h, hh_proc, pid, h7):
    """局内快照：帧钟、状态全局、hook 窗、可见窗口集。"""
    out = {"t": round(time.time(), 3),
           "frame": rpm_u32(h, G_FRAME),
           "exitstate": rpm_u32(h, G_EXITSTATE),
           "hwnd_glob": rpm_u32(h, G_HWND),
           "singleton": rpm_u32(h, G_SINGLETON),
           "hook6": (rpm(hh_proc, BAIL_SITE, 6) or b"").hex(),
           "vis_windows": [{"title": w["title"], "class": w["class"]}
                           for w in enum_windows_for(pid) if w["visible"]]}
    return out


def main() -> int:
    global PROBE
    PROBE = load_probe()
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--play-s", type=float, default=60.0, help="战斗采样窗")
    ap.add_argument("--watch", type=float, default=150.0, help="关窗后观察上限")
    a = ap.parse_args()

    print("=" * 78)
    print("C26-01 L1 进局回归（c″ 已装 MAIN 配置）  live=%s" % a.live)
    print("=" * 78)

    fails = []

    def pre(name, ok, detail=""):
        print("  [%s] %-44s %s" % ("OK" if ok else "RED", name, detail))
        if not ok:
            fails.append(name)

    pre("harness7 sha", sha16(H7_PATH) == H7_SHA16, sha16(H7_PATH))
    pre("gamemd 母本 sha", sha16(GAME_SRC / "gamemd.exe") == GAMEMD_SHA16, "")
    pre("loader sha", sha16(GUARD_DIR / "rc4_loader.exe") == LOADER_SHA16, "")
    pre("母本守卫 DLL sha", sha16(GUARD_DIR / "ra2rc4guard.dll") == MOTHER_DLL_SHA16, "")
    pre("c″ 候选 DLL sha256",
        hashlib.sha256((C2_DIR / "ra2rc4guard_c2.dll").read_bytes()).hexdigest() == C2_DLL_SHA256, "")
    pre("残留游戏进程=0", not load_probe().game_procs(), "")
    if fails:
        print("!! 预检 %d 项红，不发射" % len(fails))
        return 2
    if not a.live:
        print("\n★ 预检全过；加 --live 发射。")
        return 0

    h7 = load_h7()
    h7._QC151FS["on"] = True   # 全屏直通映射（与 hc 趟同口径）——仅进程内状态位，零源码改动

    stamp = time.strftime("%Y%m%dT%H%M%S")
    out_dir = MYCARD / ("%s_L1REG" % stamp)
    carrier = out_dir / "ct" / ("c" + "0" * 10)
    assert len(str(carrier)) <= 130, "carrier path too long"
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = {"tag": "L1REG", "guard_enable": 1, "exitbail_enable": 1, "dry_run": 0,
           "out_dir": str(out_dir)}

    # —— 载体（MAIN 配置：双开）——
    carrier.mkdir(parents=True, exist_ok=False)
    n = 0
    for f in sorted(GAME_SRC.iterdir()):
        if f.is_file():
            shutil.copy2(f, carrier / f.name)
            n += 1
    shutil.copy2(GUARD_DIR / "rc4_loader.exe", carrier / "rc4_loader.exe")
    shutil.copy2(C2_DIR / "ra2rc4guard_c2.dll", carrier / "ra2rc4guard_c2.dll")
    write_keys(carrier / "ra2render.ini", 1, 1, 0)
    rec["carrier_files"] = n
    rec["gamemd_sha16"] = sha16(carrier / "gamemd.exe")
    ex_path = carrier / "except.txt"
    rec["except_before"] = sha16(ex_path) if ex_path.exists() else None

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen([str(carrier / "rc4_loader.exe"), "ra2rc4guard_c2.dll"],
                            cwd=str(carrier), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rec["loader_pid"] = proc.pid
    t0 = time.time()

    def find_pid():
        for p, nm in PROBE.list_procs().items():
            if nm.lower() != "gamemd.exe":
                continue
            img = PROBE.query_image(p)
            if img and PROBE.under_carrier(img, carrier):
                return p
        return None

    pid = None
    for _ in range(200):
        time.sleep(0.1)
        pid = find_pid()
        if pid:
            break
    if pid is None:
        rec["abort"] = "gamemd_not_found"
        print("ABORT", rec["abort"])
        return 2
    rec["gamemd_pid"] = pid
    print("gamemd pid=%d (+%.1fs)" % (pid, time.time() - t0))

    def cleanup_and_report(code=0):
        # 日志先拷贝（abort 路径也留证）
        try:
            shutil.copy2(carrier / "ra2render.log", out_dir / "ra2render.log")
            rec["guard_lines"] = [l for l in (out_dir / "ra2render.log").read_text(
                encoding="utf-8", errors="replace").splitlines() if "[ra2rc4" in l]
        except Exception as e:
            rec["guard_log_copy_err"] = repr(e)
        for p, nm in list(PROBE.list_procs().items()):
            if nm.lower() in ("gamemd.exe", "rc4_loader.exe"):
                img = PROBE.query_image(p)
                if img and PROBE.under_carrier(img, carrier):
                    hh = k32.OpenProcess(0x0001 | 0x100000, False, p)
                    if hh:
                        k32.TerminateProcess(hh, 1)
                        k32.CloseHandle(hh)
                        rec.setdefault("killed_on_cleanup", []).append([p, nm])
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
        deadline = time.time() + 3.0
        while time.time() < deadline:
            rem = [p for p, nm in PROBE.list_procs().items()
                   if nm.lower() in ("gamemd.exe", "rc4_loader.exe")
                   and (PROBE.query_image(p) or "").lower().startswith(str(carrier).lower())]
            if not rem:
                break
            time.sleep(0.25)
        rec["a8_remaining"] = rem
        rec["a8_enum_ok"] = os.getpid() in PROBE.list_procs()
        rec["a8_verdict"] = "PASS" if (not rem and rec["a8_enum_ok"]) else "V_FAIL"
        # ★ 20261026 修：except 取证必须在 rmtree **之前**（161412 趟把此检查放在
        #   删载体之后 ⇒ except_after=None，证据靠事件日志旁证补齐——采证顺序缺陷）。
        if (carrier / "except.txt").exists():
            rec["except_after"] = sha16(carrier / "except.txt")
            rec["except_changed"] = rec["except_after"] != rec["except_before"]
        for _att in range(6):
            shutil.rmtree(carrier.parent, ignore_errors=True)
            if not carrier.parent.exists():
                break
            time.sleep(0.5)
        rec["carrier_deleted"] = not carrier.parent.exists()
        (out_dir / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
        print("\n== 汇总 ==")
        for k in ("in_battle", "nav_result", "exited_within_watch", "exit_after_close_s",
                  "final_exitcode", "except_changed", "a8_verdict", "carrier_deleted", "abort"):
            print("  %-22s %s" % (k, rec.get(k)))
        return code

    # —— 游戏主窗 ——
    hwnd = None
    while time.time() - t0 < 60.0:
        hwnd, _info = h7.find_main_window(pid)
        if hwnd:
            break
        time.sleep(0.5)
    if not hwnd:
        rec["abort"] = "no_main_window_60s"
        return cleanup_and_report(2)
    rec["hwnd"] = hwnd
    rec["window_found_at_s"] = round(time.time() - t0, 1)

    # —— 等主菜单渲染 ——
    time.sleep(35.0)

    # —— NAV 三连 ——
    nav = []
    for i, (lx, ly) in enumerate(NAV_CLICKS):
        foc = h7._focus_foreground(hwnd)
        h7.click_logical(hwnd, lx, ly)
        time.sleep(12.0)
        nav.append({"step": i, "coord": [lx, ly], "focus_ok": foc["ok"],
                    "at": round(time.time() - t0, 1)})
        print("nav step %d (%d,%d) focus_ok=%s" % (i, lx, ly, foc["ok"]))
    rec["nav_result"] = nav

    # —— 进局判定：帧钟推进 ——
    hh = k32.OpenProcess(0x0400 | 0x0010, False, pid)   # QUERY|VM
    if not hh:
        rec["abort"] = "OpenProcess_vm_failed"
        return cleanup_and_report(2)
    in_battle = False
    load_deadline = time.time() + 150.0
    f_prev = None
    while time.time() < load_deadline:
        f = rpm_u32(hh, G_FRAME)
        if f is not None and f_prev is not None and f - f_prev >= 8:
            in_battle = True
            break
        f_prev = f
        time.sleep(3.0)
    rec["in_battle"] = in_battle
    rec["frame_at_entry"] = f_prev
    print("in_battle=%s frame=%s" % (in_battle, f_prev))

    # 守卫 DLL 已写日志 ⇒ 取 cave 基址
    log_now = []
    if (carrier / "ra2render.log").exists():
        log_now = [l for l in (carrier / "ra2render.log").read_text(
            encoding="utf-8", errors="replace").splitlines() if "[ra2rc4" in l]
    cave_base = find_cave_base(log_now)
    rec["cave_base"] = hex(cave_base) if cave_base else None

    # —— 战斗采样窗 ——
    shots = []
    t_play0 = time.time()
    while time.time() - t_play0 < a.play_s:
        hsite = k32.OpenProcess(0x0400 | 0x0010, False, pid)
        shots.append(snapshot_globals(hh, hsite or hh, pid, h7))
        if hsite:
            k32.CloseHandle(hsite)
        time.sleep(2.0)
    rec["play_shots_n"] = len(shots)
    rec["play_shots_head"] = shots[:2]
    rec["play_shots_tail"] = shots[-4:]
    frames = [s["frame"] for s in shots if s["frame"] is not None]
    rec["frame_advance_total"] = (frames[-1] - frames[0]) if len(frames) >= 2 else None
    rec["play_wall_s"] = round(shots[-1]["t"] - shots[0]["t"], 2) if shots else None
    expect_hook = bail_hook_expect(cave_base) if cave_base else None
    hook_ok = all(s["hook6"] == expect_hook for s in shots) if expect_hook else False
    rec["hook_live_during_play"] = hook_ok
    rec["exitstate_during_play"] = sorted(set(s["exitstate"] for s in shots))
    rec["new_windows_during_play"] = [w for s in shots for w in s["vis_windows"]
                                      if w["class"] == "#32770"]

    # —— 局内 WM_CLOSE（R3 硬门槛）——
    pre_vis = {tuple(sorted(w["title"] for w in s["vis_windows"])) for s in shots[-1:]}
    u32.PostMessageW(wt.HWND(hwnd), WM_CLOSE, 0, 0)
    t_close = time.time()
    rec["closed_at_s"] = round(t_close - t0, 3)

    hs = k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)
    exit_row = None
    rows = []
    if hs:
        while time.time() < t_close + a.watch:
            res = k32.WaitForSingleObject(hs, 0)
            ex = wt.DWORD(0)
            k32.GetExitCodeProcess(hs, ctypes.byref(ex))
            row = {"t": round(time.time(), 3), "wait_res": res,
                   "exitstate": rpm_u32(hs, G_EXITSTATE),
                   "frame": rpm_u32(hs, G_FRAME)}
            rows.append(row)
            if res == WAIT_OBJECT_0:
                exit_row = {"exitcode": ex.value, "after_close_s": round(time.time() - t_close, 2)}
                break
            time.sleep(0.1)
        k32.CloseHandle(hs)
    k32.CloseHandle(hh)
    rec["close_rows_n"] = len(rows)
    rec["close_rows_tail"] = rows[-6:]
    rec["exited_within_watch"] = exit_row is not None
    rec["exit_after_close_s"] = exit_row["after_close_s"] if exit_row else None
    rec["final_exitcode"] = exit_row["exitcode"] if exit_row else None
    rec["exited_within_20s"] = bool(exit_row and exit_row["after_close_s"] <= 20.0)

    return cleanup_and_report(0)


if __name__ == "__main__":
    sys.exit(main())

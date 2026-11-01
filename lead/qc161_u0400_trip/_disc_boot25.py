#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""10-25 新开机时段判别趟：Q4c 复刻（裸启 gamemd，无调试器）。

§427 判别实验本体。单一变量=开机会话（10-24 10:36 → **今日新开机**）。
  窗口出现 ⇒ 昨晚「无调试器 9 连败零窗」=会话态累积 ⇒ D-09-B MAIN 臂可发。
  仍无窗   ⇒ 墙跨重启存活 ⇒ 升级为真机阻塞项（与守卫无关，坐实）。

判据（写进 JSON）：
  D1 窗口出现时刻（class=Yuri's Revenge，45 s 上限）+ 出窗后再观察 12 s
  D2 frame 计数是否推进（旁路读 0x00A8ED84；与昨晚恒 0 对照）
  D3 ws 轨迹（与昨晚 97.5 MB 平台形态对照）
卫生：载体建在本线写域；趟末定向击杀+删 ct；预检残留=0、gamemd 母本 sha。
★ 启动用 `os.spawnv(P_NOWAIT)`（与在仓发射器同法，cwd 经 chdir 传递、
  spawn 时子进程即继承；环境天然继承）——刻意避开 subprocess.Popen 面。
"""
from __future__ import annotations

import ctypes
import errno
import importlib.util
import json
import os
import shutil
import time
from ctypes import wintypes as wt
from datetime import datetime, timedelta
from pathlib import Path

# OpenProcess/GetProcessId 显式签名（x64 句柄防截断）
_k32 = ctypes.windll.kernel32
_k32.GetProcessId.restype = wt.DWORD
_k32.GetProcessId.argtypes = [wt.HANDLE]

# ★ 固定绝对路径 spec 加载本线探针件（ab24 驱动同法）
PROBE_PATH = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_probe_d09b_hang.py"
_spec = importlib.util.spec_from_file_location("pd09b", PROBE_PATH)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

MOD = P.load_their()
P.MOD = MOD

BASE = P.MYCARD / ("disc25_%s" % time.strftime("%H%M%S"))


def boot_time():
    ms = ctypes.windll.kernel32.GetTickCount64()
    return datetime.now() - timedelta(milliseconds=ms)


def main() -> int:
    out = BASE / "Q4c"
    carrier = out / "ct" / ("c" + "0" * 10)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"out_dir": str(out), "carrier_len": len(str(carrier))}

    assert len(str(carrier)) <= P.CARRIER_PATH_MAX, rec["carrier_len"]
    assert not MOD.game_procs(), MOD.game_procs()
    assert P.sha16(P.GAME_SRC / "gamemd.exe") == P.GAMEMD_SHA16
    bt = boot_time()
    rec["boot"] = bt.isoformat(timespec="seconds")
    print("boot =", rec["boot"])

    P.build_carrier(carrier, None, None)          # 88 件裸载体，零注入
    rec["files"] = len([f for f in carrier.iterdir() if f.is_file()])

    # ★ spawnv：子进程 cwd=父 chdir 后的目录；环境全量继承；无调试标志
    # ★★ Windows 上 `os.spawnv(P_NOWAIT,...)` 返回的是**进程句柄**不是 pid
    #    （MSVCRT _wspawnv 语义；首跑把 768 当 pid → OpenProcess err=87）。
    orig_cwd = os.getcwd()
    os.chdir(str(carrier))
    try:
        child_handle = os.spawnv(os.P_NOWAIT, str(carrier / "gamemd.exe"),
                                 [str(carrier / "gamemd.exe")])
    finally:
        os.chdir(orig_cwd)
    if child_handle in (-1, 0):
        rec["abort"] = "spawnv_failed errno=%d" % getattr(__import__("errno"), "errno", -1)
        (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
        return 2
    pid = _k32.GetProcessId(wt.HANDLE(child_handle))
    rec["child_handle"] = child_handle
    rec["pid"] = pid
    if not pid:
        rec["abort"] = "GetProcessId_failed err=%d" % ctypes.get_last_error()
        (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
        return 2
    # ★ 错误码必须在失败**调用后立即**取（隔几个 API 的 get_last_error 可能是陈旧值）
    h = P.k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)
    err_open = ctypes.get_last_error() if not h else None
    if not h:
        # 早死探针：spawn 后进程表里还有没有这个 pid
        time.sleep(0.5)
        still = pid in MOD.list_procs()
        h = P.k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)
        err_open2 = ctypes.get_last_error() if not h else None
        rec["abort"] = ("OpenProcess_failed err_first=%d err_retry=%d "
                        "pid_still_in_table=%s" % (err_open, err_open2, still))
        (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
        return 2
    t0 = time.time()
    frames, ws = [], []
    window_at = None
    while time.time() - t0 < 45.0:
        time.sleep(2.0)
        if P.k32.WaitForSingleObject(h, 0) == 0:
            rec["proc_died_at"] = round(time.time() - t0, 1)
            break
        gw = [w for w in P.enum_windows_for(pid) if w["class"] == "Yuri's Revenge"]
        if gw and window_at is None:
            window_at = round(time.time() - t0, 1)
            rec["window_rect"] = gw[0]["rect"]
            rec["window_title"] = gw[0]["title"]
        frames.append(P.rpm_u32(h, P.G_FRAME))
        ws.append(P.working_set_kb(h))
    rec["window_at_s"] = window_at
    rec["proc_end_state"] = ("alive" if P.k32.WaitForSingleObject(h, 0) != 0 else "dead")
    rec["frames_tail"] = frames[-6:]
    rec["ws_tail"] = ws[-6:]

    if window_at is not None and P.k32.WaitForSingleObject(h, 0) != 0:
        f1 = P.rpm_u32(h, P.G_FRAME)
        time.sleep(12)
        f2 = P.rpm_u32(h, P.G_FRAME)
        rec["frame_12s_delta"] = None if (f1 is None or f2 is None) else (f2 - f1)
    P.k32.CloseHandle(h)

    # 卫生：定向击杀（按载体目录）+ 删 ct
    for p, nm in list(MOD.list_procs().items()):
        if nm.lower() in ("gamemd.exe", "ra2loader.exe", "rc4_loader.exe"):
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, carrier):
                hh = P.k32.OpenProcess(0x0001 | 0x100000, False, p)
                if hh:
                    P.k32.TerminateProcess(hh, 1)
                    P.k32.CloseHandle(hh)
    shutil.rmtree(carrier.parent, ignore_errors=True)
    rec["carrier_deleted"] = not carrier.parent.exists()
    rec["leftover"] = MOD.game_procs()
    (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                   encoding="utf-8")

    print("\n== 判别结果 ==")
    print("  window_at_s =", window_at, " proc=", rec["proc_end_state"],
          " frames_tail=", rec["frames_tail"], " ws_tail=", rec["ws_tail"],
          " frame_12s_delta=", rec.get("frame_12s_delta"))
    if window_at is not None:
        print("  ⇒ 窗口回来了：昨晚墙=会话态；D-09-B MAIN 可发")
    else:
        print("  ⇒ 墙跨重启存活：升级为真机阻塞项（与守卫无关）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

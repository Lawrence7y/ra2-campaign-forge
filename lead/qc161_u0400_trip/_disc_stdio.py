#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""单变量判别：裸启 gamemd 的 stdio 句柄类型 = 昨晚墙的根因假设。

已证事实链（§427 + 今日）：
  · 权威链（launcher→harness7→gamemd，继承链=**文件** stdio）：今日重启后照常 25.25 s 出窗；
  · 我的裸启（bash 管道 stdio 或 DEVNULL）：10 次发射 0 窗口（进程活着、ws 平台、frame=0）。
⇒ 唯一未测变量=stdio 句柄类型。本件把它钉死：
  arm F: gamemd Popen，stdout/stderr=**打开的文件句柄**（非 PIPE、非 DEVNULL）
  判据：窗口出现（class=Yuri's Revenge，60 s 上限）+ frame 推进。
卫生与 _disc_boot25 同（载体在本线写域、趟末定向击杀、删 ct、预检母本 sha）。
★ 本件只发射 1 趟。
"""
from __future__ import annotations

import ctypes
import importlib.util
import json
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

PROBE_PATH = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_probe_d09b_hang.py"
_spec = importlib.util.spec_from_file_location("pd09b", PROBE_PATH)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

MOD = P.load_their()
P.MOD = MOD

BASE = P.MYCARD / ("stdioF_%s" % time.strftime("%H%M%S"))


def main() -> int:
    assert not MOD.game_procs(), MOD.game_procs()
    assert P.sha16(P.GAME_SRC / "gamemd.exe") == P.GAMEMD_SHA16
    out = BASE / "F"
    carrier = out / "ct" / ("c" + "0" * 10)
    out.mkdir(parents=True, exist_ok=True)
    rec = {"out_dir": str(out), "boot": (datetime.now() - timedelta(
        milliseconds=ctypes.windll.kernel32.GetTickCount64())).isoformat(timespec="seconds")}
    assert len(str(carrier)) <= P.CARRIER_PATH_MAX
    P.build_carrier(carrier, None, None)

    logf = out / "gamemd_stdio.log"
    fh = open(logf, "wb")
    proc = subprocess.Popen([str(carrier / "gamemd.exe")], cwd=str(carrier),
                            stdout=fh, stderr=subprocess.STDOUT, shell=False)
    rec["pid"] = proc.pid
    h = P.k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, proc.pid)
    t0 = time.time()
    window_at, frames = None, []
    while time.time() - t0 < 60.0:
        time.sleep(2.0)
        if P.k32.WaitForSingleObject(h, 0) == 0:
            rec["proc_died_at"] = round(time.time() - t0, 1)
            break
        gw = [w for w in P.enum_windows_for(proc.pid) if w["class"] == "Yuri's Revenge"]
        if gw and window_at is None:
            window_at = round(time.time() - t0, 1)
            rec["window_rect"] = gw[0]["rect"]
        frames.append(P.rpm_u32(h, P.G_FRAME))
    rec["window_at_s"] = window_at
    rec["frames_tail"] = frames[-4:]
    if window_at is not None:
        f1 = P.rpm_u32(h, P.G_FRAME)
        time.sleep(10)
        rec["frame_10s_delta"] = (P.rpm_u32(h, P.G_FRAME) or 0) - (f1 or 0)
    P.k32.CloseHandle(h)
    fh.close()

    # 卫生
    for p, nm in list(MOD.list_procs().items()):
        if nm.lower() in ("gamemd.exe",):
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, carrier):
                hh = P.k32.OpenProcess(0x0001 | 0x100000, False, p)
                if hh:
                    P.k32.TerminateProcess(hh, 1)
                    P.k32.CloseHandle(hh)
    try:
        proc.wait(timeout=8)
    except Exception:
        pass
    import shutil
    shutil.rmtree(carrier.parent, ignore_errors=True)
    rec["leftover"] = MOD.game_procs()
    rec["stdio_log_bytes"] = logf.stat().st_size
    (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    print("arm F (file stdio): window_at_s =", window_at,
          " frames_tail=", rec.get("frames_tail"),
          " delta10s=", rec.get("frame_12s_delta") or rec.get("frame_10s_delta"))
    print("判读:", "文件 stdio=出窗 ⇒ 墙根因=stdio 句柄类型（管道/DEVNULL 卡 ddraw init）"
          if window_at else "文件 stdio 也无窗 ⇒ stdio 假设死，另找变量")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

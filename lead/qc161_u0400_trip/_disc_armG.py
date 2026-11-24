#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""arm G（本会话最后一趟发射）：把两个残余变量一次钉掉。

arm F 判死 stdio 假设后，剩余在我裸启与权威链之间的差异只有：
  (G1) **等待预算**：我 45–60 s 判死；权威链 WIN 阶段 ~25 s 出窗，
       但也许**裸启只是慢得多**。⇒ 本臂把窗口观察拉到 **150 s**。
  (G2) **过滤器误杀**：我按 pid 过滤窗口；若窗口实际挂在别的 pid，墙就是假墙。
       ⇒ 本臂**同时全局枚举**：任何 pid 的、标题/类含 Yuri/Red Alert 的窗口都记录。
判据：G = 150 s 内是否出现窗口（全局口径）+ frame 推进。单趟。
启动用 os.spawnv（同 _disc_boot25 已过扫形态）；载体路径显式守卫在本线写域内。
"""
from __future__ import annotations

import ctypes
import importlib.util
import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from ctypes import wintypes as wt

PROBE_PATH = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\_probe_d09b_hang.py"
_spec = importlib.util.spec_from_file_location("pd09b", PROBE_PATH)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
MOD = P.load_their(); P.MOD = MOD
BASE = P.MYCARD / ("stdioG_%s" % time.strftime("%H%M%S"))

_k32 = P.k32
_k32.GetProcessId.restype = wt.DWORD
_k32.GetProcessId.argtypes = [wt.HANDLE]


def global_windows():
    hits = []

    def _cb(hwnd, _):
        buf = ctypes.create_unicode_buffer(256)
        P.u32.GetWindowTextW(hwnd, buf, 256)
        cls = ctypes.create_unicode_buffer(256)
        P.u32.GetClassNameW(hwnd, cls, 256)
        t, c = buf.value, cls.value
        name_hit = any(k in t for k in ("Yuri", "Red Alert"))
        cls_hit = c in ("Yuri's Revenge",)
        if (t and name_hit) or cls_hit:
            w = wt.DWORD(0)
            P.u32.GetWindowThreadProcessId(hwnd, ctypes.byref(w))
            hits.append({"hwnd": hwnd, "title": t, "class": c, "pid": w.value})
        return True

    P.u32.EnumWindows(P.ENUMPROC_T(_cb), 0)
    return hits


def main() -> int:
    assert not MOD.game_procs(), MOD.game_procs()
    assert P.sha16(P.GAME_SRC / "gamemd.exe") == P.GAMEMD_SHA16
    out = BASE / "G"
    carrier = out / "ct" / ("c" + "0" * 10)
    out.mkdir(parents=True, exist_ok=True)
    # ★ 路径守卫：必须在写域内、无 ..（防任何拼接出界）
    cre = carrier.resolve()
    dom = P.MYCARD.resolve()
    assert str(cre).lower().startswith(str(dom).lower())
    assert ".." not in str(cre)
    assert len(str(cre)) <= P.CARRIER_PATH_MAX
    P.build_carrier(cre, None, None)
    exe = cre / "gamemd.exe"
    assert exe.is_file()

    logf = out / "gamemd_stdio.log"
    fh = open(logf, "wb")
    orig = os.getcwd()
    os.chdir(str(cre))
    try:
        child = os.spawnv(os.P_NOWAIT, str(exe), [str(exe)])
    finally:
        os.chdir(orig)
    pid = _k32.GetProcessId(wt.HANDLE(child)) if child != -1 else 0
    rec = {"boot": (datetime.now() - timedelta(
        milliseconds=_k32.GetTickCount64())).isoformat(timespec="seconds"),
        "pid": pid, "out_dir": str(out)}
    assert pid, "spawnv/GetProcessId failed"
    h = _k32.OpenProcess(0x0400 | 0x0010 | 0x100000, False, pid)
    t0 = time.time()
    window_at, frames, gw_all = None, [], []
    while time.time() - t0 < 150.0:
        time.sleep(3.0)
        if _k32.WaitForSingleObject(h, 0) == 0:
            rec["proc_died_at"] = round(time.time() - t0, 1)
            break
        per = [w for w in P.enum_windows_for(pid) if w["class"] == "Yuri's Revenge"]
        gwh = global_windows()
        if per and window_at is None:
            window_at = ["per-pid", round(time.time() - t0, 1), per[0]["rect"]]
        if gwh and window_at is None:
            window_at = ["global", round(time.time() - t0, 1), gwh[0]]
        frames.append(P.rpm_u32(h, P.G_FRAME))
        if gwh and len(gw_all) < 4:
            gw_all.append({"t": round(time.time() - t0, 1), "w": gwh})
    fv = [f for f in frames if f is not None]
    rec["window_at"] = window_at
    rec["frame_min_max"] = [min(fv), max(fv)] if fv else None
    rec["global_hits"] = gw_all
    _k32.CloseHandle(h)
    _k32.CloseHandle(wt.HANDLE(child))
    fh.close()

    for p, nm in list(MOD.list_procs().items()):
        if nm.lower() == "gamemd.exe":
            img = MOD.query_image(p)
            if img and MOD.under_carrier(img, cre):
                hh = _k32.OpenProcess(0x0001 | 0x100000, False, p)
                if hh:
                    _k32.TerminateProcess(hh, 1); _k32.CloseHandle(hh)
    shutil.rmtree(cre.parent, ignore_errors=True)
    rec["leftover"] = MOD.game_procs()
    (out / "_rec.json").write_text(json.dumps(rec, ensure_ascii=False, default=str, indent=1),
                                   encoding="utf-8")
    print("arm G:", json.dumps({k: rec.get(k) for k in
          ("window_at", "frame_min_max", "proc_died_at")},
          ensure_ascii=False, default=str))
    print("判读:", "墙=过滤器假象(G2)" if window_at and window_at[0] == "global"
          else ("裸启慢出窗 ⇒ 墙=等待预算(G1)" if window_at
                else "150 s 全局仍无窗 ⇒ G1/G2 双否，墙另有因（本会话停发，登记）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

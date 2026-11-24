#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W45 - standalone desktop visibility precheck (B-half hard gate).

Adapted (read-only) from W44 tools/w44_lib.py:609-683 `desktop_precheck`.

Rule (task card): within 30 s of launch, EnumWindows >= 1 AND screenshot does
not throw; otherwise STOP and judge "环境阻塞".  This standalone probe is run
BEFORE any game launch to decide whether the B-half dual-track is even
possible; the per-run step0 gate is run again inside the harness after each
WMI launch.

Writes ONLY W45_b_line_equivalence/out/desktop_precheck.json.
Exit 0 = pass; exit 1 = FAIL (environment blocked).
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
CARD = ROOT / "lead" / "next_re_20261112_r02" / "W45_b_line_equivalence"
OUT = CARD / "out"

u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
UOI_NAME = 2
DESKTOP_READOBJECTS = 0x0001
ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

u.GetProcessWindowStation.restype = wt.HANDLE
u.GetThreadDesktop.restype = wt.HANDLE
u.GetThreadDesktop.argtypes = [wt.DWORD]
u.OpenInputDesktop.restype = wt.HANDLE
u.OpenInputDesktop.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
u.GetUserObjectInformationW.restype = wt.BOOL
u.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int,
                                        ctypes.c_void_p, wt.DWORD,
                                        ctypes.POINTER(wt.DWORD)]
u.CloseDesktop.restype = wt.BOOL
u.CloseDesktop.argtypes = [wt.HANDLE]
k32.GetCurrentThreadId.restype = wt.DWORD


def obj_name(h):
    if not h:
        return None
    n = wt.DWORD(0)
    buf = ctypes.create_unicode_buffer(512)
    ok = u.GetUserObjectInformationW(h, UOI_NAME, buf,
                                     ctypes.sizeof(buf), ctypes.byref(n))
    return buf.value if ok else "<err=%d>" % ctypes.get_last_error()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"kind": "w45_desktop_precheck", "standalone": True,
           "t_utc": datetime.now(timezone.utc).isoformat()}
    res["window_station"] = obj_name(u.GetProcessWindowStation())
    res["thread_desktop"] = obj_name(u.GetThreadDesktop(k32.GetCurrentThreadId()))
    hin = u.OpenInputDesktop(0, False, DESKTOP_READOBJECTS)
    res["input_desktop"] = obj_name(hin) if hin else "<OpenInputDesktop NULL>"
    if hin:
        u.CloseDesktop(hin)

    tops = []

    def cb(h, _l):
        tops.append(h)
        return True

    u.EnumWindows(ENUM(cb), 0)
    res["enum_windows_total"] = len(tops)
    res["enum_windows_visible"] = sum(1 for h in tops if u.IsWindowVisible(h))

    child_total = 0
    for h in [x for x in tops if u.IsWindowVisible(x)][:8]:
        kids = []

        def ccb(kk, _l):
            kids.append(kk)
            return True
        u.EnumChildWindows(h, ENUM(ccb), 0)
        child_total += len(kids)
    res["enum_child_windows_total_first8"] = child_total

    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        res["imagegrab"] = "OK"
        res["imagegrab_size"] = [img.width, img.height]
        p = OUT / "precheck_desktop.png"
        img.save(p)
        res["screenshot_path"] = str(p)
    except Exception as e:  # noqa: BLE001 - the gate must REPORT, not crash
        res["imagegrab"] = "FAILED: %r" % (e,)

    res["enum_ok"] = res["enum_windows_total"] >= 1
    res["grab_ok"] = res.get("imagegrab") == "OK"
    res["pass"] = bool(res["enum_ok"] and res["grab_ok"])
    (OUT / "desktop_precheck.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

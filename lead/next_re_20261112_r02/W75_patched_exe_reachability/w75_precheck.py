#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W75 step-0: confirm this observation process can see the interactive desktop
(W35 agy blocker) and decode the CSF tooltip value for later screenshot reading.
No game is launched here. Pure read-only."""
import ctypes, ctypes.wintypes as wt, json, sys
u = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u.GetProcessWindowStation.restype = wt.HANDLE
u.GetThreadDesktop.restype = wt.HANDLE
u.GetThreadDesktop.argtypes = [wt.DWORD]
u.GetUserObjectInformationW.restype = wt.BOOL
u.GetUserObjectInformationW.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                        wt.DWORD, ctypes.POINTER(wt.DWORD)]
k32.GetCurrentThreadId.restype = wt.DWORD
ENUM = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

def obj_name(h):
    if not h: return None
    n = wt.DWORD(0); b = ctypes.create_unicode_buffer(512)
    ok = u.GetUserObjectInformationW(h, 2, b, ctypes.sizeof(b), ctypes.byref(n))
    return b.value if ok else "<err>"

res = {}
res["window_station"] = obj_name(u.GetProcessWindowStation())
res["thread_desktop"] = obj_name(u.GetThreadDesktop(k32.GetCurrentThreadId()))
tops = []
def cb(h, _l):
    tops.append(h); return True
u.EnumWindows(ENUM(cb), 0)
res["enum_windows_total"] = len(tops)
res["enum_windows_visible"] = sum(1 for h in tops if u.IsWindowVisible(h))
try:
    from PIL import ImageGrab
    img = ImageGrab.grab()
    res["imagegrab"] = "OK"; res["imagegrab_size"] = [img.width, img.height]
except Exception as e:
    res["imagegrab"] = "FAILED: %r" % (e,)
res["pass"] = res["enum_windows_total"] >= 1 and res["imagegrab"] == "OK"

# CSF values from W61 EVIDENCE/csf_values.txt are UTF-16LE with each byte XOR 0xFF
# (EA CSF obfuscation). Recover the real Chinese display text.
mojibake = {
    "STT:CampaignAnimTutorial": "ꠈ瞳骦ꒇ넄괦쿽",
    "STT:CampaignAnimSoviet": "橴\ua634秸羐鷏ꂆ쿽",
    "STT:CampaignAnimAllied": "橴\ua634褠焲骺녴鷏ꂆ쿽",
    "GUI:TutorialCampaign": "驏꺊痬舋踠",
    "GUI:SelectCampaign": "澇鬸鷏ꂆ",
}
dec = {}
for k, s in mojibake.items():
    try:
        raw = s.encode("utf-16-le")
        dec[k] = bytes(b ^ 0xFF for b in raw).decode("utf-16-le", errors="replace")
    except Exception as e:
        dec[k] = "<decode failed %r>" % (e,)
res["csf_decoded"] = dec
print(json.dumps(res, ensure_ascii=False, indent=2))
sys.exit(0 if res["pass"] else 3)

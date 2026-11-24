"""S09-F1 recon 02: indirect IAT calls, WndProc jump table, mouse message dispatch."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin(); atlas = Atlas()
calls, jmps, nins = sweep_calls(b)

def scan_iat_calls(bin_, iat_va):
    """Find `call dword ptr [IAT]` = FF 15 <disp32 iat_va> in .text."""
    t = bin_.text; data = bin_.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
    pat = b"\xff\x15" + struct.pack("<I", iat_va)
    hits = []; pos = 0
    while True:
        i = data.find(pat, pos)
        if i < 0: break
        hits.append(t["va"] + i); pos = i + 1
    return hits

names = ["PeekMessageA","GetMessageA","DispatchMessageA","TranslateMessage",
         "RegisterClassA","RegisterClassExA","CreateWindowExA","DefWindowProcA",
         "GetCursorPos","SetCursorPos","GetAsyncKeyState","GetKeyState",
         "SetCapture","ReleaseCapture","DialogBoxParamA","CreateDialogParamA","MessageBoxA"]
iat = iat_lookup(b, set(names))
print("=== indirect IAT call sites (call [IAT]) ===")
for n in names:
    if n not in iat: continue
    va = iat[n]; sites = scan_iat_calls(b, va)
    print("%-18s IAT=%08X sites=%d: %s" % (n, va, len(sites), " ".join("%08X"%s for s in sites[:15])))

# WndProc jump table for 0x100..0x105
print("\n=== WndProc msg jump table @ 0x54FB4C (WM_KEYFIRST..0x105) ===")
for i in range(6):
    print("  msg %04X -> %08X" % (0x100+i, b.u32(0x54FB4C+i*4)))

# Dump WndProc from 0x54F7F1 onward (msg dispatch), larger
print("\n=== WndProc 0x54F7F1..0x54F950 ===")
print(dump(b, 0x54F7F1, 0x160))

# find imm32 == WndProc 0x54F790 anywhere in data/rdata (WndProc registration)
target = struct.pack("<I", 0x54F790)
for secname in [".text",".rdata",".data"]:
    s = b.sec(secname); data = b.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    pos = 0; hits = []
    while True:
        i = data.find(target, pos)
        if i<0: break
        hits.append(s["va"]+i); pos = i+1
    print("\nimm32 54F790 in %s: %d hits %s" % (secname, len(hits), " ".join("%08X"%h for h in hits[:20])))

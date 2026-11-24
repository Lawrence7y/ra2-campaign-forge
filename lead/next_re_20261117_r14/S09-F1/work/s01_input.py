"""S09-F1 recon 01: input entry / WndProc / window APIs / clue address verification."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09-F1\work")
from s09lib import *

b = Bin()
atlas = Atlas()
calls, jmps, nins = sweep_calls(b)
print("[sweep] .text insns =", nins)

# 1) window/message IAT
names = {"PeekMessageA", "PeekMessageW", "GetMessageA", "GetMessageW", "DispatchMessageA",
         "DispatchMessageW", "TranslateMessage", "RegisterClassA", "RegisterClassW",
         "RegisterClassExA", "RegisterClassExW", "CreateWindowExA", "CreateWindowExW",
         "DefWindowProcA", "DefWindowProcW", "GetKeyState", "GetAsyncKeyState", "SetCapture",
         "ReleaseCapture", "GetCursorPos", "SetCursorPos", "ClientToScreen", "ScreenToClient",
         "MessageBoxA", "DialogBoxParamA", "CreateDialogParamA", "LoadIconA", "LoadCursorA"}
iat = iat_lookup(b, names)
print("\n=== IAT window/message APIs ===")
for n, va in sorted(iat.items()):
    uses = calls.get(va, [])
    print("%-20s IAT=%08X  callers=%d %s" % (n, va, len(uses), " ".join("%08X" % x for x in uses[:12])))

# 2) who calls the candidate WndProc / GetEvent
for addr, label in [(0x54F790, "clue:WndProc"), (0x54F050, "clue:GetEvent"),
                    (0x4AB9B0, "clue:LMBUp"), (0x4AC380, "clue:LMBDown"),
                    (0x40D280, "clue:RMBUp")]:
    c = calls.get(addr, [])
    print("\n%s 0x%08X direct callers = %d" % (label, addr, len(c)))
    for s in c[:30]:
        info = atlas.contains(s)
        print("   site %08X in fn %s" % (s, ("%08X+%d" % (info[0], info[1])) if info else "ATLAS-HOLE"))

# 3) dump first instructions of candidate WndProc / GetEvent
for addr, label in [(0x54F790, "WndProc"), (0x54F050, "GetEvent")]:
    print("\n=== %s @ %08X ===" % (label, addr))
    print(dump(b, addr, 160))

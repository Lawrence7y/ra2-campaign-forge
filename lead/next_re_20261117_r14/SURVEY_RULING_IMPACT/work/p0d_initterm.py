# -*- coding: utf-8 -*-
"""probe: locate the _initterm table structurally (push end; push start; call _initterm)
and check the two control functions for membership. No atlas input used."""
import struct
import sys
import os

import pefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

img = open(L.EXE, "rb").read()
pe = pefile.PE(L.EXE, fast_load=True)
secs = [(s.Name.rstrip(b"\x00").decode("latin1"),
         pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress,
         s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData) for s in pe.sections]
TEXT = [s for s in secs if s[0] == ".text"][0]
tstart, tlen, tro = TEXT[1], TEXT[3], TEXT[4]
tbytes = img[tro:tro + tlen]
tend = tstart + tlen


def sec_of(va):
    for nm, sva, vs, rs, ro in secs:
        if sva <= va < sva + rs:
            return nm
    return None


def rd(va):
    for nm, sva, vs, rs, ro in secs:
        if sva <= va < sva + rs:
            return struct.unpack_from("<I", img, ro + (va - sva))[0]
    return None


# 1) find 'push imm32 ; push imm32 ; call rel32' with both imms in .data and end>start
print("push end / push start / call patterns with both imms in .data:")
found = []
for i in range(len(tbytes) - 16):
    if tbytes[i] == 0x68 and tbytes[i + 5] == 0x68 and tbytes[i + 10] == 0xE8:
        a = struct.unpack_from("<I", tbytes, i + 1)[0]
        b = struct.unpack_from("<I", tbytes, i + 6)[0]
        rel = struct.unpack_from("<i", tbytes, i + 11)[0]
        tgt = tstart + i + 15 + rel
        if sec_of(a) == ".data" and sec_of(b) == ".data" and a > b and (a - b) % 4 == 0:
            found.append((tstart + i, b, a, a - b, tgt))
for f in found[:12]:
    print("  site 0x%08X start 0x%08X end 0x%08X count %d call 0x%08X"
          % (f[0], f[1], f[2], f[3] // 4, f[4]))
print("  total:", len(found))

# 2) validate the candidate run at 0x00812004 (3944 entries) as a valid table
start = 0x00812004
n = 3944
ok = all(tstart <= (rd(start + 4 * k) or 0) < tend for k in range(n))
print("\nrun 0x%08X x %d all point into .text: %s ; next dword after run in .text? %s"
      % (start, n, ok, tstart <= (rd(start + 4 * n) or 0) < tend))

# 3) is the init-table the one at 0x00812004?
for f in found:
    if f[1] == 0x00812004:
        print("init-table confirmed: push 0x%08X ; push 0x%08X ; call 0x%08X (count %d)"
              % (f[2], f[1], f[4], f[3] // 4))

# 4) membership of control functions
def run_contains(run_start, count, fn):
    return any((rd(run_start + 4 * k) or 0) == fn for k in range(count))

for fn in (0x00438550, 0x004E6AE0, 0x00438590, 0x004E6B20):
    print("  0x%08X in init table(3944)? %s" % (fn, run_contains(start, n, fn)))

# 5) atexit registrations with a 64-byte lookback
print("\natexit registrations (lookback 64B for push imm32 in .text):")
regs = []
for i in range(len(tbytes) - 5):
    if tbytes[i] == 0xE8:
        rel = struct.unpack_from("<i", tbytes, i + 1)[0]
        if (tstart + i + 5 + rel) == 0x7C978A:
            site = tstart + i
            best = None
            for k in range(i - 1, max(-1, i - 70), -1):
                if tbytes[k] == 0x68 and k + 5 <= len(tbytes):
                    imm = struct.unpack_from("<I", tbytes, k + 1)[0]
                    if tstart <= imm < tend:
                        best = imm
                        break
            regs.append((site, best))
print("  total atexit calls:", len(regs), " with a .text push:", sum(1 for _, b in regs if b))
for site, b in regs[:6]:
    print("   call@0x%08X -> registered fn 0x%08X" % (site, b or 0))
regset = set(b for _, b in regs if b)
print("  00438590 registered?", 0x00438590 in regset, " 004E6B20 registered?", 0x004E6B20 in regset)
print("  distinct registered fns:", len(regset))

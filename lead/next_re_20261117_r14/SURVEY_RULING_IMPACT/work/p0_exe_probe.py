# -*- coding: utf-8 -*-
"""p0_exe_probe: PE map + first look at the raw byte channels, checked against the
known ground-truth pairs recorded in R14_COMMON 8.1 (23).

Controls (from COMMON 8.1 (23), used as positive/negative controls for my own scanner):
  live  00A83DE8 <- 007E43C8 @ 004E6AFD  (ctor init 004E6AE0)
  dead  00A83DE8 <- 007E43E8 @ 004E6B28  (fn 004E6B20, push 004E6B20; call 0x7C978A)
  live  0089C668 <- 007E17CC @ 0043856D  (ctor 00438550)
  dead  0089C668 <- 007E17EC @ 00438598  (dtor 00438590)
"""
import collections
import struct
import sys
import os

import pefile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_survey as L

pe = pefile.PE(L.EXE, fast_load=True)
print("imagebase 0x%08X" % pe.OPTIONAL_HEADER.ImageBase)
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b"\x00").decode("latin1")
    va = pe.OPTIONAL_HEADER.ImageBase + s.VirtualAddress
    secs.append((nm, va, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
    print("  %-8s VA=0x%08X vsize=0x%08X rawsize=0x%08X rawoff=0x%08X"
          % (nm, va, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))

img = open(L.EXE, "rb").read()
print("file size", len(img))

TEXT = [s for s in secs if s[0] == ".text"][0]
RDATA = [s for s in secs if s[0] == ".rdata"][0]
DATA = [s for s in secs if s[0] == ".data"][0]
tstart, tend = TEXT[1], TEXT[1] + TEXT[3]       # file-backed range
tbytes = img[TEXT[4]:TEXT[4] + TEXT[3]]
print("text VA 0x%08X..0x%08X  len %d" % (tstart, tend, len(tbytes)))
print("rdata VA 0x%08X..0x%08X" % (RDATA[1], RDATA[1] + RDATA[3]))
print("data  VA 0x%08X..0x%08X" % (DATA[1], DATA[1] + DATA[3]))


def rd32(va):
    for nm, sva, vs, rs, ro in secs:
        if sva <= va < sva + rs:
            off = ro + (va - sva)
            return struct.unpack_from("<I", img, off)[0]
    return None


# --- negative/positive control: find 'mov dword [abs], imm32' writes of those VTs
def find_c705(target_imm):
    hits = []
    pat = b"\xC7\x05"
    i = 0
    while True:
        i = tbytes.find(pat, i)
        if i < 0:
            break
        if i + 10 <= len(tbytes):
            absv, imm = struct.unpack_from("<II", tbytes, i + 2)
            if imm == target_imm:
                hits.append((tstart + i, absv))
        i += 1
    return hits


for vt in (0x007E43C8, 0x007E43E8, 0x007E17CC, 0x007E17EC):
    print("C7 05 writes of VT 0x%08X:" % vt, ["0x%08X->[0x%08X]" % h for h in find_c705(vt)])

# --- is 0x7C978A a real call target (atexit)?
print("\nE8 rel32 targets equal to 0x7C978A:")
cnt = 0
i = 0
while True:
    i = tbytes.find(b"\xE8", i)
    if i < 0:
        break
    if i + 5 <= len(tbytes):
        rel = struct.unpack_from("<i", tbytes, i + 1)[0]
        if (tstart + i + 5 + rel) == 0x7C978A:
            cnt += 1
            if cnt <= 6:
                print("  call atexit from 0x%08X" % (tstart + i))
    i += 1
print("  total call->7C978A raw hits:", cnt)

# --- push imm32 ; call 0x7C978A  (atexit registration) => registered function
print("\n'push <fn>; call 0x7C978A' registrations (first 10):")
regs = []
i = 0
while True:
    i = tbytes.find(b"\x68", i)
    if i < 0:
        break
    if i + 10 <= len(tbytes) and tbytes[i + 5] == 0xE8:
        fn = struct.unpack_from("<I", tbytes, i + 1)[0]
        rel = struct.unpack_from("<i", tbytes, i + 6)[0]
        if (tstart + i + 10 + rel) == 0x7C978A:
            regs.append((tstart + i, fn))
    i += 1
for a, fn in regs[:10]:
    print("  0x%08X push 0x%08X" % (a, fn))
print("  total registrations:", len(regs))
print("  004E6B20 registered?", any(fn == 0x004E6B20 for _, fn in regs))
print("  00438590 registered?", any(fn == 0x00438590 for _, fn in regs))

# -*- coding: utf-8 -*-
"""probe: dump bytes around the known dtor/ctor sites to learn the real atexit shape."""
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


def off(va):
    for nm, sva, vs, rs, ro in secs:
        if sva <= va < sva + rs:
            return ro + (va - sva)
    return None


def dump(va, n=40, label=""):
    o = off(va)
    b = img[o:o + n]
    print("%s @0x%08X: %s" % (label, va, b.hex(" ")))


for va, label in [(0x004E6AF0, "ctor 004E6AE0 tail"), (0x004E6B20, "dtor 004E6B20"),
                  (0x00438550, "ctor 00438550"), (0x00438590, "dtor 00438590")]:
    dump(va, 48, label)

# find all 'push imm32' whose imm is a .text VA followed (<=6 bytes later) by call to atexit
TEXT = [s for s in secs if s[0] == ".text"][0]
tstart, tlen = TEXT[1], TEXT[3]
tbytes = img[TEXT[4]:TEXT[4] + tlen]
tend = tstart + tlen

targets = set()
for i in range(len(tbytes) - 10):
    if tbytes[i] == 0x68:
        fn = struct.unpack_from("<I", tbytes, i + 1)[0]
        if tstart <= fn < tend:
            # allow the call to sit 0..8 bytes after the push
            for j in range(i + 5, min(i + 14, len(tbytes) - 5)):
                if tbytes[j] == 0xE8:
                    rel = struct.unpack_from("<i", tbytes, j + 1)[0]
                    if (tstart + j + 5 + rel) == 0x7C978A:
                        targets.add(fn)
                        break
print("\ndistinct functions registered via push <fn> ; ... call atexit: ", len(targets))
for probe_va in (0x004E6B20, 0x00438590, 0x004E6AE0, 0x00438550):
    print("  0x%08X registered? %s" % (probe_va, probe_va in targets))

# relaxed: any 'mov [abs], vt' whose containing fn is atexit-registered?
# show which registrations are near our four sites
near = sorted(t for t in targets if abs(t - 0x004E6B20) < 0x400 or abs(t - 0x00438590) < 0x400)
print("\nregistrations near control sites:", ["0x%08X" % t for t in near])

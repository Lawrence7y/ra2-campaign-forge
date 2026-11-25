#!/usr/bin/env python3
# Parse PE section table (own implementation, also cross-check with pefile)
import struct, sys

PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
data = open(PATH, "rb").read()
print("filesize", len(data))

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
print("e_lfanew", hex(e_lfanew))
assert data[e_lfanew:e_lfanew+4] == b"PE\0\0"
coff = e_lfanew + 4
machine, nsec, tds, psym, nsym, optsz, chars = struct.unpack_from("<HHIIIHH", data, coff)
print("machine", hex(machine), "nsec", nsec, "optsz", hex(optsz))
opt = coff + 20
magic = struct.unpack_from("<H", data, opt)[0]
print("opt magic", hex(magic))
imagebase = struct.unpack_from("<I", data, opt + 28)[0]
print("ImageBase", hex(imagebase))
sectab = opt + optsz
secs = []
for i in range(nsec):
    off = sectab + i * 40
    name = data[off:off+8].rstrip(b"\0").decode("latin1")
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, off+8)
    sflags = struct.unpack_from("<I", data, off+36)[0]
    secs.append(dict(name=name, vsize=vsize, vaddr=vaddr, rawsize=rawsize,
                     rawptr=rawptr, flags=sflags))
    print(f"{name:8s} VA={vaddr:#010x} VSize={vsize:#010x} RawPtr={rawptr:#010x} RawSize={rawsize:#010x} Flags={sflags:#010x}")

# NOTE: first draft used relative vaddr against absolute va -> all lookups beyond
# section 0 returned None. Fixed by adding ImageBase.
def va2off(va):
    for s in secs:
        base = imagebase + s["vaddr"]
        if base <= va < base + s["rawsize"]:
            return s["rawptr"] + (va - base)
    return None

def va2sec(va):
    for s in secs:
        base = imagebase + s["vaddr"]
        if base <= va < base + max(s["vsize"], s["rawsize"]):
            return s
    return None

def off2va(off):
    for s in secs:
        if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
            return imagebase + s["vaddr"] + (off - s["rawptr"])
    return None

for va in (0x6bedb0, 0x41c250, 0x817bc0, 0x817bb0, 0x6bc342):
    print(f"va {va:#x} -> off {va2off(va)!r}")

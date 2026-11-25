#!/usr/bin/env python3
# Extra cross-checks:
#  (1) whole-FILE 0xE8 scan (not just .text), reporting the containing section;
#  (2) verify each reported call site really decodes as E8+imm32 at that address.
import struct
import capstone

PATH = "/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe"
IMGBASE = 0x400000
data = open(PATH, "rb").read()
u16 = lambda o: struct.unpack_from("<H", data, o)[0]
u32 = lambda o: struct.unpack_from("<I", data, o)[0]

e_lfanew = u32(0x3C); coff = e_lfanew + 4
nsec = u16(coff + 2); optsz = u16(coff + 16); opt = coff + 20
sectab = opt + optsz
secs = []
for i in range(nsec):
    o = sectab + i * 40
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o+8)
    secs.append(dict(name=data[o:o+8].rstrip(b"\0").decode("latin1"),
                     vsize=vsize, vaddr=vaddr, rawsize=rawsize, rawptr=rawptr))

TARGETS = (0x6bedb0, 0x41c250)

# Build off->va only for raw-backed section data
def off2va_sec(off):
    for s in secs:
        if s["rawptr"] <= off < s["rawptr"] + s["rawsize"]:
            return IMGBASE + s["vaddr"] + (off - s["rawptr"]), s["name"]
    return None, None

hits = {t: [] for t in TARGETS}
n_e8 = 0
for i in range(len(data) - 4):
    if data[i] != 0xE8:
        continue
    n_e8 += 1
    va, sname = off2va_sec(i)
    if va is None:
        continue
    rel = struct.unpack_from("<i", data, i+1)[0]
    tgt = (va + 5 + rel) & 0xFFFFFFFF
    if tgt in hits:
        hits[tgt].append((va, sname))

print("whole-file 0xE8 byte count:", n_e8)
for t in TARGETS:
    print(f"whole-file E8 -> target {t:#x}: count={len(hits[t])}")
    for va, sname in hits[t]:
        print(f"   site {va:#x} in {sname}")

# verify decode at each site
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False
def decode_at(va, nbytes=5):
    off = None
    for s in secs:
        base = IMGBASE + s["vaddr"]
        if base <= va < base + s["rawsize"]:
            off = s["rawptr"] + (va - base); break
    if off is None:
        return None
    for ins in md.disasm(data[off:off+nbytes], va):
        return ins
    return None

print("\ndecode verification at each reported site:")
allsites = sorted({va for t in TARGETS for va, _ in hits[t]})
for va, _ in sorted({(va, n) for t in TARGETS for va, n in hits[t]}):
    wi = decode_at(va, 5)
    mark = "OK" if (wi and wi.mnemonic == "call" and wi.op_str in ("0x6bedb0", "0x41c250")) else "MISMATCH"
    print(f"  {va:#x} [{mark}] {wi.mnemonic if wi else '?'} {wi.op_str if wi else '?'}  bytes={data[[s['rawptr']+(va-(IMGBASE+s['vaddr'])) for s in secs if IMGBASE+s['vaddr']<=va<IMGBASE+s['vaddr']+s['rawsize']][0]:][:5].hex()}")

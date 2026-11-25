#!/usr/bin/env python3
# Decode the context of every imm32 0x817bc0 occurrence to confirm each is truly an
# instruction immediate (not an accidental byte match inside other data-in-code).
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
text = [s for s in secs if s["name"] == ".text"][0]
blob = data[text["rawptr"]:text["rawptr"]+text["rawsize"]]
TEXT_VA = IMGBASE + text["vaddr"]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = False

SITES = [0x413dd9, 0x41c272, 0x437f59, 0x517b6c, 0x67d0d1, 0x67e5b5,
         0x6bedd2, 0x6bedfe, 0x6bee20]
print("context window -8..+8 bytes around each imm32 byte offset:")
for s in SITES:
    o = s - TEXT_VA
    lo, hi = max(0, o-8), min(len(blob), o+8)
    # show the 4 bytes and their neighbours
    print(f"  site_va {s:#x} off {text['rawptr']+o:#x}  imm 4 bytes={blob[o:o+4].hex()}  window={blob[lo:hi].hex()}")

print("\ndecode from a few bytes earlier so the containing instruction is visible:")
for s in SITES:
    o = s - TEXT_VA
    start = o - 6
    for ins in md.disasm(blob[start:o+8], TEXT_VA + start):
        b = blob[start + (ins.address - (TEXT_VA+start)) + ins.size - 4: start + (ins.address-(TEXT_VA+start)) + ins.size]
        mark = "  <== imm32 0x817bc0 ends here" if b == struct.pack("<I", 0x817bc0) else ""
        print(f"  {ins.address:#x}  {ins.mnemonic} {ins.op_str}{mark}")
    print("  ---")

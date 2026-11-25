#!/usr/bin/env python3
# Cross-check C3: capstone-based scan (detail=True, streaming per instruction,
# nothing retained) for any instruction whose immediate operand == 0x817bc0.
# Rationale: the raw 4-byte search cannot distinguish a real imm32 from a
# coincidental 4-byte run inside another immediate/displacement.
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
rawlen = len(blob)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True     # per-insn operands, discarded each iteration (no retention)

WANT = 0x817bc0
found = []
pos = 0
while pos < rawlen:
    progressed = False
    end = pos
    for ins in md.disasm(blob[pos:], TEXT_VA + pos):
        progressed = True
        end = ins.address - TEXT_VA + ins.size
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == WANT:
                found.append((ins.address, ins.mnemonic, ins.op_str))
                break
    pos = end if (progressed and end > pos) else pos + 1

print(f"capstone imm==0x817bc0 instruction count in .text: {len(found)}")
for a, m, s in found:
    print(f"  {a:#x}  {m} {s}")

# same for 0x817bb0
WANT = 0x817bb0
found2 = []
pos = 0
while pos < rawlen:
    progressed = False
    end = pos
    for ins in md.disasm(blob[pos:], TEXT_VA + pos):
        progressed = True
        end = ins.address - TEXT_VA + ins.size
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xFFFFFFFF) == WANT:
                found2.append((ins.address, ins.mnemonic, ins.op_str))
                break
    pos = end if (progressed and end > pos) else pos + 1
print(f"capstone imm==0x817bb0 instruction count in .text: {len(found2)}")
for a, m, s in found2:
    print(f"  {a:#x}  {m} {s}")

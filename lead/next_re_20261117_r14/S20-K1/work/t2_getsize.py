"""T2: GetSize two-way cross-check.

Channel A: vtable[12] body `B8 <imm32> C3` (mov eax,imm32; ret) -> size.
Channel B: constructor/factory `push <imm32>` immediately followed by a call to
           an allocator (operator new wrapper) -> size.
Both must independently agree. Also read v[11] WhatAmI as cross-check.
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text, EVID

b = Bin()

# (label, main vtable, slot count) — from T1 RTTI, obj_off=0 tables
CLASSES = [
    ("AnimClass",               0x7E3354, 124),
    ("ParticleClass",           0x7EF954, 123),
    ("ParticleSystemClass",     0x7EFB9C, 122),
    ("VoxelAnimClass",          0x7F6318, 122),
    ("AnimTypeClass",           0x7E3608, 41),
    ("ParticleTypeClass",       0x7F0188, 40),
    ("ParticleSystemTypeClass", 0x7F00A8, 40),
    ("VoxelAnimTypeClass",      0x7F6548, 40),
]

def slot_fn(vt, n):
    return b.u32(vt + 4*n)

def get_imm_ret(fn, maxbytes=64):
    """Disassemble fn, look for B8 imm32 C3 / xor eax,eax;ret / mov eax,imm;ret."""
    ins = disasm_window(b, fn, maxbytes, skipdata=False)
    # prefer first mov eax,imm32 followed by ret
    for k, i in enumerate(ins):
        if i.mnemonic == "mov" and i.op_str.startswith("eax,"):
            arg = i.op_str[4:].strip()
            if arg.startswith("0x"):
                try: imm = int(arg, 16)
                except: continue
                # check next insn is ret
                if k+1 < len(ins) and ins[k+1].mnemonic == "ret":
                    return imm, "mov eax,0x%X; ret" % imm, ins
        if i.mnemonic == "xor" and i.op_str == "eax, eax":
            if k+1 < len(ins) and ins[k+1].mnemonic == "ret":
                return 0, "xor eax,eax; ret", ins
    # fallback: scan bytes for B8 imm32 C3
    data = b.read(fn, 16)
    if len(data) >= 6 and data[0] == 0xB8 and data[5] == 0xC3:
        return struct.unpack("<I", data[1:5])[0], "B8 imm32 C3", []
    return None, "NO_IMM_RET", ins

rows = []
detail = []
for label, vt, nslot in CLASSES:
    wami_fn = slot_fn(vt, 11)
    gsz_fn = slot_fn(vt, 12)
    wami, wami_note, _ = get_imm_ret(wami_fn)
    gsz, gsz_note, ins = get_imm_ret(gsz_fn)
    # raw bytes at GetSize
    raw = b.read(gsz_fn, 12).hex()
    rows.append([label, "%08X" % vt, nslot,
                 "%08X" % wami_fn, (wami if wami is not None else "?"),
                 "%08X" % gsz_fn, (gsz if gsz is not None else "?"),
                 gsz_note, raw])
    detail.append("=== %s vt=%08X slots=%d ===" % (label, vt, nslot))
    detail.append("  v[11] WhatAmI  fn=%08X -> %s" % (wami_fn, wami))
    detail.append("  v[12] GetSize  fn=%08X -> %s   bytes=%s" % (gsz_fn, gsz, raw))
    for i in ins[:8]:
        detail.append("    %08X  %-28s" % (i.address, insn_text(i)))

write_tsv("T2_getsize_channelA.tsv",
          "class\tvtable\tslots\tv11_fn\tWhatAmI\tv12_fn\tGetSize\tform\traw12", rows)
write_text("T2_getsize_channelA.txt", "\n".join(detail) + "\n")

print("\n".join(detail))

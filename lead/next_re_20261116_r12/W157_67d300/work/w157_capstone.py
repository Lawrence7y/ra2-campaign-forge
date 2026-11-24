#!/usr/bin/env python3
# W157 capstone INDEPENDENT channel.
# (A) Linear-disassemble 0x67D300 from its known entry; verify instruction boundaries;
#     count jump back-edges (all jumps, and conditional-only) to reconcile with Ghidra=111.
# (B) Dump key data addresses (IID constants, string table) with file offsets.
# (C) List all absolute global [0xXXXXXXXX] memory refs inside 0x67D300 (array Count/Items).
import pefile, capstone, sys, re

PE_PATH = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
IMAGE_BASE = 0x400000
pe = pefile.PE(PE_PATH, fast_load=True)
data = pe.__data__
BASE = IMAGE_BASE

def va2off(va):
    rva = va - BASE
    return pe.get_offset_from_rva(rva)

def rd(va, n):
    o = va2off(va)
    return data[o:o+n]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

def disasm_range(start_va, size):
    off = va2off(start_va)
    code = data[off:off+size]
    out = list(md.disasm(code, start_va))
    return out

# ---- (A) back-edge count for 0x67D300 ----
FN = 0x67D300
SIZE = 4411
insns = disasm_range(FN, SIZE)
print("=== A) 0x67D300 linear disasm from entry ===")
print(f"instructions={len(insns)} first={insns[0].address:#x} last_end={insns[-1].address+insns[-1].size:#x}")

all_back = []      # any jump whose target <= current address
cond_back = []     # conditional jcc only
for ins in insns:
    if ins.group(capstone.CS_GRP_JUMP):
        # operands[0] is immediate target for direct jmp/jcc
        op = ins.operands[0] if ins.operands else None
        if op and op.type == capstone.CS_OP_IMM:
            tgt = op.imm
            if tgt <= ins.address:
                all_back.append((ins.address, ins.mnemonic, tgt))
                if ins.mnemonic != 'jmp':
                    cond_back.append((ins.address, ins.mnemonic, tgt))
print(f"ALL_JUMP_BACKEDGES={len(all_back)}  CONDITIONAL_JCC_BACKEDGES={len(cond_back)}  UNCOND_JMP_BACKEDGES={len(all_back)-len(cond_back)}")
print("--- back-edge list (address mnemonic -> target) ---")
for a,m,t in all_back:
    print(f"  {a:#010x}  {m:6s} -> {t:#010x}")

# ---- instruction-boundary verification of key byte hits ----
print("\n=== B) key address instruction-boundary check ===")
starts = {i.address: i for i in insns}
# (address, expected bytes)
checks = [
    (0x67D308, '8b0d30b2a800'),
    (0x67D342, 'ff5110'),
    (0x67D351, '8b2df4157e00'),
    (0x67D35D, 'a154418b00'),
    (0x67D36E, '68807c7f00'),
    (0x67D386, 'ffd5'),
    (0x67D3A9, '7cb2'),
]
for a, hx in checks:
    actual = rd(a, 6).hex()
    on_bound = a in starts
    desc = f"{starts[a].mnemonic} {starts[a].op_str}" if on_bound else "(NOT an instruction start)"
    print(f"  {a:#010x} bytes={actual:12s} on_boundary={on_bound}  {desc}")

# ---- (C) absolute global refs inside 0x67D300 ----
print("\n=== C) absolute [0xXXXXXXXX] data refs in 0x67D300 ===")
globals_seen = {}
for ins in insns:
    for op in ins.operands:
        if op.type == capstone.CS_OP_MEM and op.mem.base == 0 and op.mem.index == 0 and op.mem.disp != 0:
            g = op.mem.disp & 0xFFFFFFFF
            if 0x400000 <= g < 0xC00000:
                globals_seen.setdefault(g, []).append(ins.address)
for g in sorted(globals_seen):
    sites = ','.join(f'{x:#x}' for x in globals_seen[g])
    print(f"  {g:#010x}  refs={len(globals_seen[g])}  at={sites}")

# ---- (D) data dumps ----
print("\n=== D) data dumps ===")
def dump(va, n, label):
    b = rd(va, n)
    print(f"--- {label} @ {va:#x} (file off {va2off(va):#x}) ---")
    for i in range(0, n, 16):
        chunk = b[i:i+16]
        hx = ' '.join(f'{x:02x}' for x in chunk)
        dws = ' '.join(f'{int.from_bytes(chunk[j:j+4],"little"):08X}' for j in range(0,len(chunk),4))
        asc = ''.join(chr(x) if 32<=x<127 else '.' for x in chunk)
        print(f"  {va+i:#010x}  {hx:<47s}  {dws:<36s}  {asc}")
dump(0x7F7C60, 0x60, "IID/GUID cluster near 0x7f7c80")
dump(0x83D540, 0xA0, "string/data table used by 0x67CEF0")

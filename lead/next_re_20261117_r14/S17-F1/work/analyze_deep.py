"""
S17-F1: deep analysis of inline vector blocks, Load_Core, Swizzle, gating.
capstone skipdata=True throughout.
"""
import pe_util as P
from capstone import x86_const
import struct

def f(ins):
    return f"0x{ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic:<8s} {ins.op_str}"

# ===== A. Save_Core: count inline vector serializers =====
print("="*100)
print("A. Save_Core inline vector serializers — all 'call [reg+0x10]' IStream::Write sites")
print("="*100)
insns = P.disasm(0x67D300, 0x67E440 - 0x67D300)
# Find any call with memory operand [reg + 0x10]
writes10 = []
call_ebp = []
for ins in insns:
    if ins.mnemonic == 'call':
        if '[ecx + 0x10]' in ins.op_str or '[eax + 0x10]' in ins.op_str or '[edx + 0x10]' in ins.op_str:
            writes10.append(ins)
        if ins.op_str.strip() == 'ebp':
            call_ebp.append(ins)
print(f"call [reg+0x10] count = {len(writes10)}")
for ins in writes10:
    print("   ", f(ins))
print(f"call ebp (OleSaveToStream) total = {len(call_ebp)}")

# Find count-load sites: mov reg,[glob] that feed IStream::Write. Count globals from clue doc.
COUNT_GLOBS = [0x8B4160,0x8B413C,0xA83C9C,0xA8022C,0x8B410C,0xA83CE4,0xA8E34C,
               0xA83DEC,0xA83C6C,0xA8EB44,0xA8B21C,0xA8E394,0xA8E9AC,0xA8E8D4,
               0xA8ECB0,0x8B40EC,0x8B41CC,0x8872B4,0xB0E784,0xB0E724,0x8B417C,
               0xA8EAEC,0xA8B204,0xB0E65C,0xB0F1A4,0xA83D54,0x8B41E4,0x8B41F0]
found = {}
for ins in insns:
    for op in ins.operands:
        if op.type == P.X86_OP_MEM and op.mem.base == 0 and op.mem.disp in COUNT_GLOBS:
            found.setdefault(op.mem.disp, []).append(ins.address)
print(f"\ndistinct Count-globals referenced in Save_Core: {len(found)}/{len(COUNT_GLOBS)}")
for g in COUNT_GLOBS:
    sites = found.get(g, [])
    print(f"   0x{g:08X}: {len(sites)} site(s) {[hex(s) for s in sites[:3]]}")

# ===== B. Load_Core 0x67E440 dispatch order =====
print("\n" + "="*100)
print("B. Load_Core 0x67E440..0x67EC00 — E8 calls + key IStream::Read/OleLoadFromStream")
print("="*100)
lins = P.disasm(0x67E440, 0x67EC00 - 0x67E440)
print(f"decoded {len(lins)} insn")
lc_calls = []
lc_read = []
lc_oleload = 0
for ins in lins:
    if ins.mnemonic == 'call' and ins.bytes[0] == 0xE8:
        for op in ins.operands:
            if op.type == P.X86_OP_IMM:
                lc_calls.append((ins.address, op.imm))
    if ins.mnemonic == 'call' and '0xc]' in ins.op_str:  # [reg+0xC] = IStream::Read
        lc_read.append(ins)
    if ins.mnemonic == 'call' and ins.op_str.strip() in ('edi','ebp','ebx','eax','ecx','edx','esi'):
        pass
print(f"E8 direct calls in Load_Core window: {len(lc_calls)}")
for site, tgt in lc_calls:
    print(f"   0x{site:08X} -> 0x{tgt:08X}")
print(f"call [reg+0xC] (IStream::Read) sites: {len(lc_read)}")
for ins in lc_read[:10]:
    print("   ", f(ins))

# ===== C. Swizzle vtable methods disassembly =====
print("\n" + "="*100)
print("C. SwizzleManagerClass vtable 0x7F4108 slots — size + first insns")
print("="*100)
slots = [0x6CF430,0x6CF4B0,0x6CF4C0,0x6CF230,0x6CF240,0x6CF490,0x6CF2C0,0x6CF4D0,0x6CF4E0,0x6CF410]
for i, s in enumerate(slots):
    ins = P.disasm_insns(s, 6)
    print(f"\n  slot[{i}] 0x{s:08X}:")
    for x in ins[:6]:
        print("     ", f(x))

# Here_I_Am full (0x6CF240..0x6CF2C0)
print("\n--- Here_I_Am 0x6CF240 full ---")
for ins in P.disasm(0x6CF240, 0x6CF2C0-0x6CF240):
    print("   ", f(ins))

# slot6 0x6CF2C0 full
print("\n--- slot6 0x6CF2C0 full (3-arg Here_I_Am) ---")
for ins in P.disasm(0x6CF2C0, 0x6CF350-0x6CF2C0):
    print("   ", f(ins))

# ===== D. Gating chain disassembly with boundaries =====
print("\n" + "="*100)
print("D. gating chain 0x55DBC0..0x55DCA0 (mode==0 && !once) with instruction boundaries")
print("="*100)
for ins in P.disasm(0x55DB90, 0x55DCA0-0x55DB90):
    if 0x55DBCD <= ins.address <= 0x55DC99:
        print("   ", f(ins))

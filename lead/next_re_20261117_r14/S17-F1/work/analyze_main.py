"""
S17-F1 main analysis (Channel 1): independent extraction of
 - Save_Core 0x67D300 dispatch order (35 block calls + 28 inline vectors + scalars)
 - callers of outer/save functions (rel32 scan, atlas-independent)
 - outer save constructor 0x67CEF0 key calls
 - Swizzle manager vtable + methods
All capstone skipdata=True.
"""
import pe_util as P
import struct
from capstone import x86_const

def fmt_ins(ins):
    return f"0x{ins.address:08X}  {ins.bytes.hex():<20s} {ins.mnemonic:<8s} {ins.op_str}"

# ---------- 1. Save_Core direct-call inventory ----------
print("="*100)
print("SECTION 1: Save_Core 0x67D300..0x67E440 direct E8 calls + edx arg tracking")
print("="*100)
insns = P.disasm(0x67D300, 0x67E440 - 0x67D300)
addr_set = set(ins.address for ins in insns)
print(f"decoded {len(insns)} insns; sync-check known sites:")
for ka in (0x67D342, 0x67D386, 0x67DF0F, 0x67E3AA, 0x67DF08):
    print(f"   0x{ka:08X} on_boundary={ka in addr_set}")
pending_edx = None
block_calls = []   # (site, target, edx_arg)
all_calls = []
for ins in insns:
    if ins.mnemonic in ('call','callq') and ins.bytes[0] == 0xE8:
        # get target
        tgt = None
        for op in ins.operands:
            if op.type == P.X86_OP_IMM:
                tgt = op.imm
        if tgt is not None:
            all_calls.append((ins.address, tgt))
            if 0x67FDF0 <= tgt <= 0x680F6F:
                block_calls.append((ins.address, tgt, pending_edx))
        pending_edx = None
    elif ins.mnemonic == 'mov' and len(ins.operands) == 2:
        op0, op1 = ins.operands
        if op0.type == P.X86_OP_REG and op0.reg == x86_const.X86_REG_EDX and op1.type == P.X86_OP_IMM:
            pending_edx = op1.imm

print(f"Total direct E8 calls in Save_Core: {len(all_calls)}")
print(f"Template block calls (target in 0x67FDF0..0x680F6F): {len(block_calls)}")
print("\n-- 35 template block calls in order --")
for i, (site, tgt, arg) in enumerate(block_calls, 1):
    print(f"  #{i:2d} site=0x{site:08X} -> fn=0x{tgt:08X}  edx_arg=0x{arg:08X}" if arg else
          f"  #{i:2d} site=0x{site:08X} -> fn=0x{tgt:08X}  edx_arg=NONE")

# Verify block fn target arithmetic: 0x67FDF0 + 0x80*i
print("\n-- block fn stride check (expect 0x67FDF0 + 0x80*i) --")
for i, (site, tgt, arg) in enumerate(block_calls):
    exp = 0x67FDF0 + 0x80*i
    print(f"  #{i+1:2d} got=0x{tgt:08X} exp=0x{exp:08X} {'OK' if tgt==exp else 'DIFF'}")

# ---------- 2. Inline vector blocks: find IStream::Write count sites ----------
print("\n" + "="*100)
print("SECTION 2: inline vector blocks — 'call [ecx+0x10]' (IStream::Write) sites in Save_Core")
print("="*100)
writes = [ins for ins in insns if ins.mnemonic == 'call' and '[ecx + 0x10]' in ins.op_str]
print(f"  'call [ecx+0x10]' sites: {len(writes)}")
for ins in writes:
    print("   ", fmt_ins(ins))

# OleSaveToStream direct call via ebp
calls_ebp = [ins for ins in insns if ins.mnemonic == 'call' and ins.op_str.strip() == 'ebp']
print(f"  'call ebp' (OleSaveToStream) sites: {len(calls_ebp)}")

# ---------- 3. callers (rel32 + imm32 scan) ----------
print("\n" + "="*100)
print("SECTION 3: callers / refs (atlas-independent rel32 + imm32 scans)")
print("="*100)
for name, tgt in [('Save_Core 0x67D300',0x67D300), ('outer 0x67CEF0',0x67CEF0),
                  ('outer2 0x67D0C0',0x67D0C0), ('Load_Core 0x67E440',0x67E440),
                  ('template 0x67FDF0',0x67FDF0), ('Save_Sides 0x6805F0',0x6805F0),
                  ('scalar_w 0x67F7E0',0x67F7E0), ('scalar_r 0x67F9C0',0x67F9C0),
                  ('HereIAm 0x6CF240',0x6CF240), ('SwizzleMgr vt 0x7F4108',0x7F4108)]:
    rel = P.scan_rel32_calls(tgt)
    imm = P.scan_imm32_refs(tgt)
    print(f"\n{name}: rel32 callers={len(rel)} imm32 refs={len(imm)}")
    if rel:
        print("   rel32:", ', '.join(f"0x{site:08X}({op:02X})" for site,op in rel))
    if imm:
        print("   imm32 (first 15):", ', '.join(f"0x{site:08X}[{sec}]" for site,sec in imm[:15]))

# ---------- 4. outer save constructor 0x67CEF0 key E8 + indirect calls ----------
print("\n" + "="*100)
print("SECTION 4: outer 0x67CEF0..0x67D300 — all E8 calls + indirect calls + strings")
print("="*100)
oins = P.disasm(0x67CEF0, 0x67D300-0x67CEF0)
print(f"instructions decoded: {len(oins)}")
for ins in oins:
    if ins.group(1) or (ins.mnemonic == 'call'):
        for op in ins.operands:
            if op.type == P.X86_OP_IMM:
                print(f"  CALL 0x{ins.address:08X} -> 0x{op.imm:08X}  {fmt_ins(ins)}")
                break
        else:
            # indirect call
            print(f"  ICALL 0x{ins.address:08X}  {fmt_ins(ins)}")

# ---------- 5. Swizzle manager vtable 0x7F4108 ----------
print("\n" + "="*100)
print("SECTION 5: SwizzleManagerClass vtable @ 0x7F4108 (10 slots) + methods")
print("="*100)
for i in range(12):
    v = P.u32(0x7F4108 + i*4)
    print(f"  slot[{i}] @0x{0x7F4108+i*4:08X} = 0x{v:08X}" if v else f"  slot[{i}] = None")

# ---------- 6. boundary_check demonstration ----------
print("\n" + "="*100)
print("SECTION 6: boundary_check (unknown-not-False) key bytes")
print("="*100)
for va, hx in [(0x67D342,'ff5110'), (0x67D386,'ffd5'), (0x67DF0F,'e8dc1e0000'),
               (0x6CF2A8,'c70700000000')]:
    print(f"  0x{va:08X} {hx}: boundary_check={P.boundary_check(va,hx)}")

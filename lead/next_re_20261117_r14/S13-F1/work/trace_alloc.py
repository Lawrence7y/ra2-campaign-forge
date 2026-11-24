"""Trace: (a) BulletClass allocation via class factory in Fire; (b) who calls ctor 0x466380;
(c) weapon selection + target legality (GetWeapon/GetFireError) vtable slots in Fire;
(d) BulletClass::Array remove point (writes to 0xA8ED50 count); (e) GetTotalDamage caller context.
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\work")
import re_lib as R
import capstone
from safe_dis import real_insns

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-F1\EVIDENCE"
out=[]
def p(s=""): out.append(str(s))

p("=== A. Fire around Construct call 0x6FF859 (trace allocation) ===")
p(R.dump_insns(R.disasm(0x6FF740, 0x140)))

p("\n=== B. Who calls BulletClass ctor 0x466380? full .text call sweep ===")
MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); MD.detail=True; MD.skipdata=True
for insn in real_insns(MD, R.read(R.TEXT[1], R.TEXT[2]-R.TEXT[1]), R.TEXT[1]):
    t=R.call_target(insn)
    if t in (0x466380, 0x4664C0):
        p(f"   {R.fmt_insn(insn)}  target=0x{t:08X} parent={R.fn_at(insn.address)}")

p("\n=== C. All indirect calls in Fire with slot numbers ===")
fire = R.disasm_fn(0x6FDD50)
# TechnoClass vtable slot -> name mapping from YRpp header order; print slot index
slotmap = {0x2D8:"GetWeapon", 0x2DC:"?", 0x3CC:"Fire", 0x288:"GetFireError?", 0x28C:"?", 0x290:"SelectWeapon?"}
for insn in fire:
    if insn.mnemonic=="call" and insn.operands and insn.operands[0].type==capstone.x86.X86_OP_MEM:
        m=insn.operands[0].mem
        if m.base!=0 and m.disp is not None:
            slot=m.disp//4
            p(f"   {R.fmt_insn(insn)}  slot={slot} (+0x{m.disp:X}) {slotmap.get(m.disp,'')}")

p("\n=== D. Writes to BulletClass::Array count 0xA8ED50 (absolute + base-loaded) ===")
# absolute: cmp/mov [0xA8ED50]
for insn in real_insns(MD, R.read(R.TEXT[1], R.TEXT[2]-R.TEXT[1]), R.TEXT[1]):
    for op in insn.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.disp==0xA8ED50 and op.mem.base==0:
            p(f"   abs  {R.fmt_insn(insn)}")
# base-loaded: mov reg,0xA8ED40 then [reg+0x10]
prev={}
for insn in real_insns(MD, R.read(R.TEXT[1], R.TEXT[2]-R.TEXT[1]), R.TEXT[1]):
    if insn.mnemonic=="mov" and len(insn.operands)==2:
        dst,src=insn.operands
        if src.type==capstone.x86.X86_OP_IMM and (src.imm&0xFFFFFFFF)==0xA8ED40 and dst.type==capstone.x86.X86_OP_REG:
            prev[insn.reg_name(dst.reg)]=insn.address
    for op in insn.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0 and op.mem.disp==0x10:
            bn=insn.reg_name(op.mem.base)
            if bn in prev:
                p(f"   base {R.fmt_insn(insn)}   (base loaded @0x{prev[bn]:08X})")

p("\n=== E. GetTotalDamage 0x489180 direct callers context (Fire @0x6FDD29, ReceiveDamage @0x701D64) ===")
p("-- Fire @0x6FDD00..0x6FDD50 --")
p(R.dump_insns(R.disasm(0x6FDD00, 0x50)))

txt="\n".join(out)
open(EV+r"\trace_alloc_weapon_array.txt","w",encoding="utf-8").write(txt)
print(txt)

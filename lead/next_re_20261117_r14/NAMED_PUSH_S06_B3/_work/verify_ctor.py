# -*- coding: utf-8 -*-
"""Dump full 5F9720 (beyond atlas), B2's 29B thin-forward 005FEC10, and ctor candidates."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

def dump(va, size, label, filt=None):
    code = R.read_va(va, size)
    insns = R.disasm(va, code)
    print("---- %s @%08X size=%d ----" % (label, va, size))
    for ins in insns:
        raw = code[ins.address-va:ins.address-va+ins.size]
        if filt and not filt(ins): continue
        print("  %08X %-18s %-8s %s" % (ins.address, raw.hex(" "), ins.mnemonic, ins.op_str))

# full 5F9720 to next atlas entry
nxt = min((int(k,16) for k in R.ATLAS if int(k,16) > 0x5F9720), default=0x5F9900)
print("5F9720 atlas size=%s next=%08X" % (R.ATLAS.get("005F9720",{}).get("size"), nxt))
def f9720(ins):
    if ins.id == 0: return False
    if ins.id in (R.X86_INS_RET,) : return True
    if ins.id == R.X86_INS_MOV and ins.operands and ins.operands[0].type==R.X86_OP_REG \
       and ins.operands[0].reg==R.X86_REG_EAX and ins.operands[1].type==R.X86_OP_IMM: return True
    if ins.id in (R.X86_INS_TEST,R.X86_INS_CMP,R.X86_INS_JL,R.X86_INS_JE,R.X86_INS_JGE,R.X86_INS_JG) : return True
    if ins.id == R.X86_INS_CALL: return True
    return False
dump(0x5F9720, nxt-0x5F9720, "5F9720 key-insns", f9720)

# B2 29B thin-forward 005FEC10
print("="*80)
sz = R.ATLAS.get("005FEC10",{}).get("size",29)
dump(0x5FEC10, sz, "B2 005FEC10 29B thin-forward")

# constructor candidates for the 4 vtables
print("="*80)
for va,label in [(0x0071DA80,"TerrainTypeClass ctor"),(0x007216C0,"TiberiumClass ctor A"),
                 (0x00721880,"TiberiumClass ctor B"),(0x00721E80,"TiberiumClass ctor C"),
                 (0x00727FD0,"TubeClass ctor"),(0x00763730,"WaypointPathClass ctor A"),
                 (0x00763810,"WaypointPathClass ctor B"),(0x00763C70,"WaypointPathClass ctor C")]:
    sz = R.ATLAS.get("%08X"%va,{}).get("size",60)
    # only key first insns + vptr write + base-ctor call
    def ctorfilt(ins):
        if ins.id==0: return False
        return ins.id in (R.X86_INS_CALL,R.X86_INS_RET) or (ins.id==R.X86_INS_MOV and ins.operands and ins.operands[0].type==R.X86_OP_MEM and ins.operands[1].type==R.X86_OP_IMM)
    dump(va, min(sz,120), label, ctorfilt)

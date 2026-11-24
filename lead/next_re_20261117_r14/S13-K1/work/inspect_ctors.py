"""S13-K1: dump ctor candidates: prologue, calls, vtable writes, [reg+off] stores."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\work")
from re_lib import *
import capstone

CANDS = {
 "WeaponTypeClass": [0x771C70,0x771F00,0x771F4D,0x7730F0],
 "WarheadTypeClass":[0x75CEC0,0x75D1F0,0x75E0C0,0x75E510],
 "BulletTypeClass": [0x46BBC0,0x46BDF0,0x46C6A0,0x46C890],
 "BulletClass":     [0x466380,0x466560,0x46AE70,0x46B550],
}
lines=[]
def p(x=""): lines.append(str(x))

for cls, cands in CANDS.items():
    p(f"\n######## {cls} ########")
    for fn in cands:
        at = ATLAS_FN.get(fn)
        end = fn + at[0] if at else fn+0x260
        p(f"\n=== cand {hex(fn)} atlas={at} assumed_end={hex(end)} ===")
        n_stores=0; calls=[]; vtwrites=[]
        ins_all = disasm(fn, end-fn)
        for insn in ins_all:
            if insn.mnemonic == "call" and insn.operands and insn.operands[0].type==2:
                calls.append((insn.address, insn.operands[0].imm & 0xFFFFFFFF))
            if insn.mnemonic=="mov" and len(insn.operands)==2:
                d,s=insn.operands
                if d.type==capstone.x86.X86_OP_MEM and s.type==capstone.x86.X86_OP_IMM:
                    imm=s.imm&0xFFFFFFFF
                    if 0x7E0000<=imm<=0x7FA000 and d.mem.disp<0x20:
                        vtwrites.append(insn.address)
                if d.type==capstone.x86.X86_OP_MEM and d.mem.index==0 and 0<=d.mem.disp<0x400:
                    n_stores+=1
        p(f"  stores[0..0x400]={n_stores}; vptr-writes={[hex(x) for x in vtwrites]}")
        p(f"  calls: " + " ".join(f"{hex(a)}->{hex(t)}" for a,t in calls[:20]))
        for i in ins_all[:22]: p("    "+fmt_insn(i))
        p("    ...")
        for i in ins_all[-12:]: p("    "+fmt_insn(i))
open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\ctor_candidates_detail.txt","w",encoding="utf-8").write("\n".join(lines))
print("done", len(lines))

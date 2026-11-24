# -*- coding: utf-8 -*-
import os,sys,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE=os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE,"analysis.json"),encoding="utf-8") as f: A=json.load(f)

for r in A:
    if r["entry"] not in ("0069C9C0","0069CBC0"): continue
    print("="*70);print(r["entry"],r["name"])
    for c in r["ring2"]["cands"]:
        for g in c["global_writes"]:
            f=g.get("in_func"); fx=int(f[1],16) if f else None
            dels=[]; delflag=[]
            if fx:
                sz=R.ATLAS.get(R.hx(fx),{}).get("size") or 512
                for i in R.disasm_body(fx,sz):
                    if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_IMM:
                        t=i.operands[0].imm&0xFFFFFFFF
                        if t in (0x7C8B3D,0x7C93E8): dels.append(R.hx(t))
                    if i.id==X86_INS_TEST and 'byte ptr' in i.op_str and ', 1' in i.op_str: delflag.append(R.hx(i.address))
            print("  write=%s in_func=%s atexit=%s dels=%s delflagtest=%s"%(
                g["write_va"], f[1] if f else None, g.get("atexit"), dels, delflag))

print("\n### call [reg+0xC] 计数")
cnt=0
for i in R.disasm(R.TEXT_VA,R.TEXT_DATA):
    if i.id==X86_INS_CALL and i.operands and i.operands[0].type==X86_OP_MEM:
        m=i.operands[0].mem
        if m.disp==0xC and m.scale==1 and m.base not in (X86_REG_INVALID,0): cnt+=1
print("call [reg+0xC] =",cnt)

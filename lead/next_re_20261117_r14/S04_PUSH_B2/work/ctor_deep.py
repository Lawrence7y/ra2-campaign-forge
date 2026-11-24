# -*- coding: utf-8 -*-
"""对 7 个 self-vt-write 候选：解析体内写入的 vt 的 RTTI 名、写点是否对 this(ecx 派生)、
是否构造器序言；并检查 ③b 形态（③b③ 内存形状 / ③b④ 循环非栈写 / ③b② 调用方分支）。
写 work/ctor_deep_<entry>.txt。只读。
"""
import os, sys, csv, bisect
WORK_B1 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B1\work"
sys.path.insert(0, WORK_B1)
import witness_core as W
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B2"
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_ECX, X86_INS_MOV

ROOT = r"D:\Project\ra2-campaign-forge"
raw = open(os.path.join(ROOT,"ra2youli","gamemd.exe"),"rb").read()
pe = pefile.PE(data=raw, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\0").decode("latin1"), IB+s.VirtualAddress,
                 s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
def va2off(va):
    for n,v,vs,rs,p in secs:
        if v<=va<v+rs: return p+va-v
    return None
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True

ATLAS=os.path.join(ROOT,"lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv")
funcs=[]
with open(ATLAS,encoding="utf-8-sig") as fh:
    fh.readline()
    for ln in fh:
        if not ln.strip(): continue
        p=ln.rstrip("\n").split("\t")
        if len(p)<3: continue
        try: e=int(p[0].strip().upper().replace("0X",""),16); sz=int(p[1])
        except: continue
        funcs.append((e,e+sz,p[0].strip().upper().replace("0X","")))
funcs.sort(); starts=[f[0] for f in funcs]
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    if i>=0 and funcs[i][0]<=site<funcs[i][1]: return funcs[i]
    return None

CAND=["00525430","00525A60","00533D20","005E6520","006418B0","00641B00","00641EE0"]
meta={}
with open(os.path.join(OUT,"work","b2_entries.tsv"),encoding="utf-8") as fh:
    for r in csv.DictReader(fh,delimiter="\t"): meta[r["entry"]]=r

for e in CAND:
    ea=int(e,16); sz=int(meta[e]["size"])
    off=va2off(ea)
    insns=list(md.disasm(raw[off:off+sz],ea))
    lines=["# CTOR DEEP entry=%s name=%s size=%d"%(e,meta[e]["name"],sz)]
    lines.append("## 序言（前 10 条）")
    for i in insns[:10]:
        lines.append("  0x%X %s %s"%(i.address,i.mnemonic,i.op_str))
    # this registers: ecx + regs assigned from ecx
    thisregs={X86_REG_ECX}
    lines.append("## vtable 写入（立即数可解析 RTTI）+ 是否写向 this")
    nvt=0
    for i in insns:
        if i.id==X86_INS_MOV and len(i.operands)==2:
            d,s=i.operands
            if d.type==X86_OP_REG and s.type==X86_OP_REG and s.reg==X86_REG_ECX:
                thisregs.add(d.reg)
            if d.type==X86_OP_MEM and s.type==X86_OP_IMM:
                v=s.imm & 0xFFFFFFFF
                col=W.u32(v-4)
                ci=W.parse_col(col) if col else None
                nm=""
                if ci and ci["sig"]==0:
                    tdi=W.parse_td(ci["td"])
                    if tdi: nm=tdi["name"]
                if nm and ".?AV" in nm:
                    nvt+=1
                    tothis = d.mem.base in thisregs
                    lines.append("  0x%X mov [%s%s],0x%X  vt_rtti=%s  to_this=%s  base_reg=%s disp=%s"%(
                        i.address, md.reg_name(d.mem.base) if d.mem.base else "?",
                        ("+0x%X"%d.mem.disp) if d.mem.disp>=0 else ("-0x%X"%(-d.mem.disp)),
                        v, nm, tothis, d.mem.base, d.mem.disp))
    lines.append("  distinct named vt writes=%d"%nvt)
    # field layout count: writes to [this+off]
    fieldoffs=set()
    for i in insns:
        if i.id==X86_INS_MOV and len(i.operands)==2:
            d,s=i.operands
            if d.type==X86_OP_MEM and d.mem.base in thisregs and d.mem.disp>0:
                fieldoffs.add(d.mem.disp)
    lines.append("  this+field writes (distinct disp>0)=%d %s"%(len(fieldoffs),sorted(fieldoffs)[:20]))
    # backward loops with non-stack writes in loop body
    JCC={"je","jne","jz","jnz","jg","jge","jl","jle","ja","jae","jb","jbe","js","jns"}
    lines.append("## 回边与循环体非栈写")
    for idx,i in enumerate(insns):
        if i.mnemonic in JCC or i.mnemonic=="jmp":
            if i.operands and i.operands[0].type==X86_OP_IMM:
                t=i.operands[0].imm & 0xFFFFFFFF
                if ea<=t<i.address:
                    ti=next((k for k,x in enumerate(insns) if x.address==t),None)
                    if ti is not None:
                        body=insns[ti:idx+1]
                        nstack=0; samples=[]
                        for b in body:
                            if b.id==X86_INS_MOV and len(b.operands)==2 and b.operands[0].type==X86_OP_MEM:
                                m=b.operands[0].mem
                                if m.base not in (4,) and m.base!=0:  # not esp base
                                    nstack+=1
                                    if len(samples)<3: samples.append("0x%X %s %s"%(b.address,b.mnemonic,b.op_str))
                        lines.append("  %s@0x%X->0x%X loop_body_ins=%d nonstack_memwrites=%d %s"%(
                            i.mnemonic,i.address,t,len(body),nstack,samples))
    open(os.path.join(OUT,"work","ctor_deep_%s.txt"%e),"w",encoding="utf-8").write("\n".join(lines))
    print("%s named_vt_writes=%d"% (e,nvt))
print("done")

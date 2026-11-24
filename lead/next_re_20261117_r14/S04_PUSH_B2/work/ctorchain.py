# -*- coding: utf-8 -*-
"""构造链 ring② 分析：对每个 entry 检查
(A) 函数体是否写已知 vt（自身即构造器）
(B) 每个 direct caller 中，call site 前是否对传给本函数的 ecx 对象写了已知 vt（调用者是构造器且 this 同源），
    并解析该 vt 的 RTTI 名（COL=vt-4, TD=[COL+0xC], name=TD+8 内联）。
(C) 调用方是否 test 本函数返回值（③b② caller-branch 条件）。
写 work/ctorchain_<entry>.txt + work/ctorchain_summary.tsv。只读。
"""
import json, csv, bisect
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG, X86_REG_ECX

ROOT = Path(r"D:\Project\ra2-campaign-forge")
EXE = ROOT / "ra2youli" / "gamemd.exe"
OUT = ROOT / "lead/next_re_20261117_r14/S04_PUSH_B2"
ATLAS = ROOT / "lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
raw = EXE.read_bytes()
pe = pefile.PE(data=raw, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\0").decode("latin1"), ib+s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData))
by={s[0]:s for s in secs}
tva=by[".text"][1]; tend=tva+by[".text"][2]
code=raw[by[".text"][4]:by[".text"][4]+by[".text"][2]]

def va2off(va):
    for n,v,vs,rs,ptr in secs:
        if v<=va<v+rs:
            return ptr+va-v
    return None
def u32(va):
    o=va2off(va)
    return int.from_bytes(raw[o:o+4],"little") if o is not None and o+4<=len(raw) else None
def cstr(va,lim=120):
    o=va2off(va)
    if o is None: return ""
    b=raw[o:o+lim]; z=b.find(b"\0")
    if z>=0: b=b[:z]
    try: return b.decode("ascii")
    except: return ""
def rtti_of_vt(vt):
    col=u32(vt-4)
    if col is None: return None
    td=u32(col+0xC)
    if td is None: return None
    nm=cstr(td+8)
    if nm.startswith((".?AV",".?AU")): return (td,nm)
    return None

idx=json.load(open(OUT/"work"/"index.json"))
direct={int(k,16):v for k,v in idx["direct"].items()}
vtables={int(k,16):v for k,v in idx["vtables"].items()}
vtset=set(vtables.keys())

funcs=[]
with open(ATLAS,encoding="utf-8-sig") as fh:
    fh.readline()
    for ln in fh:
        if not ln.strip(): continue
        p=ln.rstrip("\n").split("\t")
        if len(p)<3: continue
        try:
            e=int(p[0].strip().upper().replace("0X",""),16); sz=int(p[1])
        except: continue
        funcs.append((e,e+sz,p[0].strip().upper().replace("0X","")))
funcs.sort(); starts=[f[0] for f in funcs]
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    if i>=0 and funcs[i][0]<=site<funcs[i][1]: return funcs[i]
    return None

md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis(a,b,cap=400):
    o=va2off(a)
    if o is None: return []
    out=[]
    for ins in md.disasm(raw[o:o+(b-a)],a):
        out.append(ins)
        if len(out)>cap: break
    return out

def body_vt_writes(lo,hi):
    hits=[]
    for ins in dis(lo,min(hi,lo+4000)):
        if ins.mnemonic=="mov" and len(ins.operands)==2:
            o0,o1=ins.operands
            if o0.type==X86_OP_MEM and o1.type==X86_OP_IMM and (o1.imm&0xffffffff) in vtset:
                hits.append((ins.address,o1.imm&0xffffffff))
    return hits

def main():
    entries=[]
    with open(OUT/"work"/"b2_entries.tsv",encoding="utf-8") as fh:
        for r in csv.DictReader(fh,delimiter="\t"): entries.append(r)
    summ=[]
    for r in entries:
        e=int(r["entry"],16)
        # (A) self body vt writes
        self_writes=body_vt_writes(e,e+int(r["size"]))
        lines=["# CTORCHAIN entry=%s name=%s"%(r["entry"],r["name"])]
        lines.append("(A) self body writes known vt (self is ctor): count=%d %s"%(len(self_writes),[(hex(a),hex(v)) for a,v in self_writes[:8]]))
        # (B) caller chain
        sites=direct.get(e,[])
        vt_named=0; branch_ret=0
        for s in sites:
            ow=owner(s)
            if not ow:
                lines.append("  site=0x%X NO_OWNER"%s); continue
            pre=dis(max(tva,s-0x120),s)  # instructions before call
            # vt writes to any [reg] among known vt in this window
            vtw=[]
            for ins in pre:
                if ins.mnemonic=="mov" and len(ins.operands)==2:
                    o0,o1=ins.operands
                    if o0.type==X86_OP_MEM and o1.type==X86_OP_IMM and (o1.imm&0xffffffff) in vtset:
                        v=o1.imm&0xffffffff
                        rr=rtti_of_vt(v)
                        vtw.append((ins.address,v,rr[1] if rr else "?"))
            if vtw: vt_named+=1
            # post call: test eax / cmp eax within 5 insns
            post=dis(s+5,s+5+40)
            br=False
            for ins in post[:6]:
                if ins.mnemonic in ("test",) and len(ins.operands)==2 and ins.operands[0].type==X86_OP_REG and ins.operands[0].reg==19 and ins.operands[1].type==X86_OP_REG and ins.operands[1].reg==19:
                    br=True
                if ins.mnemonic in ("cmp",) and len(ins.operands)>0 and ins.operands[0].type==X86_OP_REG and ins.operands[0].reg==19:
                    br=True
            if br: branch_ret+=1
            lines.append("  site=0x%X owner=%s[%X,%X) pre_vt_writes=%d post_test_eax=%s"%(
                s,ow[2],ow[0],ow[1],len(vtw),br))
            for a,v,nm in vtw[:8]:
                lines.append("    vtwrite@0x%X vt=0x%X rtti=%s"%(a,v,nm))
        lines.append("(B) callers with pre-window vt write=%d/%d ; callers branching on eax=%d/%d"%(vt_named,len(sites),branch_ret,len(sites)))
        (OUT/"work"/("ctorchain_%s.txt"%r["entry"])).write_text("\n".join(lines),encoding="utf-8")
        summ.append([r["entry"],len(self_writes),len(sites),vt_named,branch_ret])
    with open(OUT/"work"/"ctorchain_summary.tsv","w",encoding="utf-8",newline="") as fh:
        w=csv.writer(fh,delimiter="\t"); w.writerow(["entry","self_vt_writes","n_direct","caller_with_vtwrite","caller_branch_eax"]); w.writerows(summ)
    for x in summ: print(x)

if __name__=="__main__": main()

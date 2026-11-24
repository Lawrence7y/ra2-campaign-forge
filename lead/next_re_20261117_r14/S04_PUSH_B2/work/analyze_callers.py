# -*- coding: utf-8 -*-
"""S04_PUSH_B2 调用者上下文分析：对每个 entry 的 direct caller，
定位其所属函数（atlas 区间），判断调用者是否为构造器（体内写已知 vtable），
并 dump call site 前后指令（看 ecx=this 来源、返回值是否被 test 分支消费）。
只读。写 work/callers_<entry>.txt 与 work/callers_summary.tsv。
"""
import json, csv
from pathlib import Path
import pefile, capstone
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

ROOT = Path(r"D:\Project\ra2-campaign-forge")
EXE = ROOT / "ra2youli" / "gamemd.exe"
OUT = ROOT / "lead/next_re_20261117_r14/S04_PUSH_B2"
ATLAS = ROOT / "lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv"
raw = EXE.read_bytes()
pe = pefile.PE(data=raw, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
tva = ib + sec.VirtualAddress
tend = tva + sec.Misc_VirtualSize
code = raw[sec.PointerToRawData:sec.PointerToRawData + sec.Misc_VirtualSize]

def va2off(va):
    for s in pe.sections:
        v = ib + s.VirtualAddress
        if v <= va < v + s.SizeOfRawData:
            return s.PointerToRawData + va - v
    return None

def u32(va):
    o = va2off(va)
    return int.from_bytes(raw[o:o+4], "little") if o is not None and o+4 <= len(raw) else None

# atlas
funcs = []
with open(ATLAS, encoding="utf-8-sig") as fh:
    hdr = fh.readline().rstrip("\n").split("\t")
    for ln in fh:
        if not ln.strip(): continue
        p = ln.rstrip("\n").split("\t")
        if len(p) < 3: continue
        try:
            e = int(p[0].strip().upper().replace("0X",""),16)
            sz = int(p[1])
        except ValueError:
            continue
        funcs.append((e, e+sz, p[0].strip().upper().replace("0X","")))
funcs.sort()
starts = [f[0] for f in funcs]
import bisect
def owner(site):
    i = bisect.bisect_right(starts, site) - 1
    if i >= 0 and funcs[i][0] <= site < funcs[i][1]:
        return funcs[i]
    return None

idx = json.load(open(OUT / "work" / "index.json"))
direct = {int(k,16): v for k,v in idx["direct"].items()}
vtables = {int(k,16): v for k,v in idx["vtables"].items()}
# known vt values set (vtable addresses)
vtset = set(vtables.keys())
# all vtable slot values (to recognize C7 05 obj,vt / mov [reg],vt)
slotvals = set()
for v in vtables:
    k=0
    while k<200:
        x=u32(v+4*k)
        if x is None or x==0: break
        slotvals.add(x); k+=1

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail=True; md.skipdata=True

def dis_range(a,b,cap=400):
    off=va2off(a)
    if off is None: return []
    return list(md.disasm(raw[off:off+(b-a)],a))

def body_writes_vt(lo,hi):
    """owner 函数体内是否写已知 vt（构造器标志）"""
    hits=[]
    off=va2off(lo)
    if off is None: return hits
    for ins in md.disasm(raw[off:off+(hi-lo)],lo):
        if ins.mnemonic!="mov" or len(ins.operands)!=2: continue
        o0=ins.operands[0]
        if o0.type!=X86_OP_MEM: continue
        o1=ins.operands[1]
        if o1.type==X86_OP_IMM and (o1.imm & 0xffffffff) in vtset:
            hits.append((ins.address,"mov [mem],vt imm", hex(o1.imm & 0xffffffff)))
        elif o1.type==X86_OP_REG:
            # reg 来源简化：看前 8 条
            pass
    return hits

def main():
    entries=[]
    with open(OUT/"work"/"b2_entries.tsv",encoding="utf-8") as fh:
        for r in csv.DictReader(fh,delimiter="\t"):
            entries.append(r)
    summ=[]
    for r in entries:
        e=int(r["entry"],16)
        sites=direct.get(e,[])
        lines=["# CALLERS entry=%s name=%s"%(r["entry"],r["name"])]
        lines.append("direct sites=%d"%len(sites))
        owner_ctors=0
        for s in sites:
            ow=owner(s)
            owdesc = ("%s [%X,%X)"%(ow[2],ow[0],ow[1])) if ow else "NO_ATLAS_OWNER"
            ctor=[]
            if ow:
                ctor=body_writes_vt(ow[0],min(ow[1],ow[0]+4000))
            if ctor: owner_ctors+=1
            # dump +/- 12 insns around call
            ctx=dis_range(max(tva,s-96),s+16)
            lines.append("  site=0x%X owner=%s ctor_vt_writes=%d"%(s,owdesc,len(ctor)))
            for c in ctor[:6]:
                lines.append("    ctor_write=0x%s %s"%(c[0],c[1]))
            for ins in ctx:
                mark=">>" if ins.address==s else "  "
                lines.append("    %s 0x%X %s %s"%(mark,ins.address,ins.mnemonic,ins.op_str))
        (OUT/"work"/("callers_%s.txt"%r["entry"])).write_text("\n".join(lines),encoding="utf-8")
        summ.append([r["entry"],len(sites),owner_ctors])
    with open(OUT/"work"/"callers_summary.tsv","w",encoding="utf-8",newline="") as fh:
        w=csv.writer(fh,delimiter="\t"); w.writerow(["entry","n_direct","n_owner_ctor"]); w.writerows(summ)
    for x in summ: print(x)

if __name__=="__main__":
    main()

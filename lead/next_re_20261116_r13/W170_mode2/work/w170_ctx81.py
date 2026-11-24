"""Dump +/- N instructions context around each object-field write to [reg+0x81] byte.
Channel A: capstone skipdata=True.  No atlas dependency for the site list itself.
"""
import struct, pefile, capstone, bisect, os

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"

class Bin:
    def __init__(self):
        self.pe = pefile.PE(EXE, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections=[]
        for s in self.pe.sections:
            n=s.Name.decode(errors="replace").rstrip("\x00")
            self.sections.append(dict(name=n, va=self.ib+s.VirtualAddress, raw=s.PointerToRawData, rawsize=s.SizeOfRawData))
    def sec(self,name):
        for s in self.sections:
            if s["name"]==name: return s
        raise KeyError(name)
    def read(self,va,n):
        for s in self.sections:
            if s["va"]<=va and va+n<=s["va"]+s["rawsize"]:
                off=s["raw"]+(va-s["va"]); return self.pe.__data__[off:off+n]
        raise ValueError("VA %08X"%va)

def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True; return m

def load_atlas():
    rows=[]
    with open(ATLAS,"r",encoding="utf-8",errors="replace") as f:
        hdr=f.readline().rstrip("\n").split("\t")
        for line in f:
            p=line.rstrip("\n").split("\t")
            if not p or not p[0]: continue
            try: e=int(p[0],16)
            except: continue
            rows.append((e,dict(zip(hdr,p))))
    rows.sort(key=lambda t:t[0]); return rows

def alookup(rows,va):
    keys=[r[0] for r in rows]
    i=bisect.bisect_right(keys,va)-1
    if i>=0 and va<rows[i][0]+int(rows[i][1].get("size","0")): return rows[i][1]
    return None

def find_writes(b):
    m=md(); t=b.sec(".text")
    data=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
    sites=[]
    for ins in m.disasm(data,t["va"]):
        if ins.id==0: continue
        for op in ins.operands:
            if op.type!=capstone.x86.X86_OP_MEM: continue
            if op.size!=1: continue
            mem=op.mem
            if (mem.disp&0xffffffff)!=0x81: continue
            if mem.base in (capstone.x86.X86_REG_ESP, capstone.x86.X86_REG_EBP) and mem.index==0:
                continue  # stack local
            if op.access & capstone.CS_AC_WRITE:
                sites.append((ins.address,"%s %s"%(ins.mnemonic,ins.op_str),ins.reg_name(mem.base) if mem.base else "ABS"))
                break
    return sites

def context_dump(b,rows,va,before=14,after=16):
    start=va-48
    data=b.read(start,128)
    m=md()
    lines=[]
    for ins in m.disasm(data,start):
        mark=" <<<<" if ins.address==va else ""
        lines.append("  %08X  %-8s %s%s"%(ins.address,ins.mnemonic,ins.op_str,mark))
    a=alookup(rows,va)
    fninfo=("fn entry=%s size=%s"%(a["entry"],a["size"])) if a else "NO_ATLASFN"
    return fninfo,lines

def main():
    b=Bin(); rows=load_atlas()
    sites=find_writes(b)
    lines=[]
    lines.append("Object-field byte writes to [reg+0x81] (stack excluded): %d sites"%len(sites))
    lines.append("")
    for va,text,base in sites:
        fninfo,ctx=context_dump(b,rows,va)
        lines.append("=== %08X  %s   base=%s  [%s] ==="%(va,text,base,fninfo))
        lines.extend(ctx)
        lines.append("")
    path=os.path.join(OUT,"Q2_plus81_write_contexts.txt")
    with open(path,"w",encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")
    print("WROTE",path,"sites=",len(sites))

if __name__=="__main__": main()

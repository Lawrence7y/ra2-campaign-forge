"""Map [+0x81] write-site functions to vtable slot/class; find callers of predicate 0x5F5850.
Channel A byte-level (no Ghidra), capstone skipdata=True.
"""
import struct, pefile, capstone, bisect, os, json, re
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
ATLAS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
VTAB=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json"
CLASS=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\class_atlas_v2.tsv"
OUT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r13\W170_mode2\EVIDENCE"

class Bin:
    def __init__(self):
        self.pe=pefile.PE(EXE,fast_load=True); self.ib=self.pe.OPTIONAL_HEADER.ImageBase; self.sections=[]
        for s in self.pe.sections:
            n=s.Name.decode(errors="replace").rstrip("\x00")
            self.sections.append(dict(name=n,va=self.ib+s.VirtualAddress,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
    def sec(self,n):
        for s in self.sections:
            if s["name"]==n: return s
        raise KeyError(n)
    def read(self,va,n):
        for s in self.sections:
            if s["va"]<=va and va+n<=s["va"]+s["rawsize"]:
                return self.pe.__data__[s["raw"]+(va-s["va"]):s["raw"]+(va-s["va"])+n]
        return b"\x00"*n
    def u32(self,va): return struct.unpack("<I",self.read(va,4))[0]

def md():
    m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); m.detail=True; m.skipdata=True; return m

def load_atlas():
    rows=[]
    with open(ATLAS,"r",encoding="utf-8",errors="replace") as f:
        hdr=f.readline().rstrip("\n").split("\t")
        for line in f:
            p=line.rstrip("\n").split("\t")
            if not p or not p[0]: continue
            try:e=int(p[0],16)
            except:continue
            rows.append((e,dict(zip(hdr,p))))
    rows.sort(key=lambda t:t[0]); return rows

def alookup(rows,va):
    keys=[r[0] for r in rows]; i=bisect.bisect_right(keys,va)-1
    if i>=0 and va<rows[i][0]+int(rows[i][1].get("size","0")): return rows[i][1]
    return None

def load_vtables():
    with open(VTAB,"r",encoding="utf-8",errors="replace") as f:
        try: d=json.load(f)
        except: return []
    # normalize to list of dicts with 'va'/'addr','name','slots'
    out=[]
    if isinstance(d,list):
        for r in d: out.append(r)
    elif isinstance(d,dict):
        for k,v in d.items():
            if isinstance(v,dict):
                v=dict(v); v.setdefault("va",v.get("addr",v.get("vt",k)))
                out.append(v)
    return out

def find_owners(b,fn_entry):
    """scan .rdata dwords equal fn_entry, then for each vt candidate find canonical vtable containing it"""
    hits=[]
    s=b.sec(".rdata")
    data=b.pe.__data__[s["raw"]:s["raw"]+s["rawsize"]]
    pat=struct.pack("<I",fn_entry)
    st=0
    while True:
        i=data.find(pat,st)
        if i<0: break
        va=s["va"]+i
        hits.append(va)
        st=i+1
    return hits

def resolve_vt(vts, slot_va):
    """find canonical vtable whose slot region includes slot_va"""
    res=[]
    for v in vts:
        va=v.get("va") or v.get("addr") or v.get("vt")
        try: va=int(va,16) if isinstance(va,str) else int(va)
        except: continue
        nslot=v.get("n_slots") or v.get("slots") or v.get("count")
        if isinstance(nslot,str):
            try:nslot=int(nslot)
            except:nslot=None
        name=v.get("name") or v.get("class") or v.get("className") or "?"
        # derive slot count by scanning until non-code: simpler: if within 0..0x1000 and multiple of 4
        if va<=slot_va<=va+0x1000 and (slot_va-va)%4==0:
            res.append((va,int((slot_va-va)//4),name))
    return res

def main():
    b=Bin(); rows=load_atlas(); vts=load_vtables()
    # write sites (object-field only), reuse list from earlier script
    m=md(); t=b.sec(".text")
    data=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
    sites=[]
    for ins in m.disasm(data,t["va"]):
        if ins.id==0: continue
        for op in ins.operands:
            if op.type!=capstone.x86.X86_OP_MEM or op.size!=1: continue
            if (op.mem.disp&0xffffffff)!=0x81: continue
            if op.mem.base in (capstone.x86.X86_REG_ESP,capstone.x86.X86_REG_EBP) and op.mem.index==0: continue
            if op.access & capstone.CS_AC_WRITE:
                sites.append(ins.address); break
    # unique containing functions
    fns={}
    for va in sites:
        a=alookup(rows,va)
        key=a["entry"] if a else "ORPHAN@%08X"%va
        fns.setdefault(key,[]).append(va)
    lines=[]
    lines.append("=== [+0x81] write-site functions -> vtable ownership ===")
    for fn,sitelist in sorted(fns.items(), key=lambda x: (x[0] if x[0][:1].isdigit() else "z")):
        if fn.startswith("ORPHAN"):
            lines.append("%s sites=%s"%(fn,[hex(x) for x in sitelist])); continue
        e=int(fn,16)
        hits=find_owners(b,e)
        lines.append("fn %s size=%s sites=%s rdata_dword_hits=%s"%(fn,alookup(rows,e)["size"],[hex(x) for x in sitelist],[hex(x) for x in hits]))
        for h in hits:
            for va,slot,name in resolve_vt(vts,h):
                lines.append("    @%08X -> vt=%08X slot=%d (+0x%X) class=%s"%(h,va,slot,slot*4,name))
    # callers of 0x5F5850
    lines.append("")
    lines.append("=== direct call rel32 sites to 0x5F5850 (capstone) ===")
    for ins in m.disasm(data,t["va"]):
        if ins.id==0: continue
        if ins.mnemonic=="call" and ins.op_str.startswith("0x"):
            if int(ins.op_str,16)==0x5F5850:
                a=alookup(rows,ins.address)
                lines.append("  %08X in fn %s"%(ins.address, ("entry=%s size=%s"%(a["entry"],a["size"])) if a else "NO_ATLASFN"))
    path=os.path.join(OUT,"Q2_plus81_fn_ownership.txt")
    with open(path,"w",encoding="utf-8") as f: f.write("\n".join(lines)+"\n")
    print("WROTE",path)
    print("\n".join(lines[:120]))

if __name__=="__main__": main()

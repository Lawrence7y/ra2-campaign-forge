"""S16-K1 reusable RE primitives.

Rules honoured:
  * all disassembly uses capstone with skipdata=True
  * VA addressed with ImageBase 0x400000; VA->file offset via section table
  * no reliance on function_atlas.tsv for channel B
"""
from __future__ import annotations
import struct
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            self.secs.append(dict(name=name, va=self.base+s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize, raw=s.PointerToRawData,
                                  rawsize=s.SizeOfRawData))
        self.data = self.pe.__data__

    def sec(self, name):
        for s in self.secs:
            if s['name'] == name:
                return s
        raise KeyError(name)

    def off(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va']+s['rawsize']:
                return s['raw'] + (va-s['va'])
        raise ValueError(f"VA {va:08X} not in raw range")

    def read(self, va, n):
        o = self.off(va)
        return self.data[o:o+n]

    def u8(self, va): return self.read(va,1)[0]
    def u16(self, va): return struct.unpack('<H', self.read(va,2))[0]
    def u32(self, va): return struct.unpack('<I', self.read(va,4))[0]
    def i32(self, va): return struct.unpack('<i', self.read(va,4))[0]

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va']+max(s['rawsize'],s['vsize']):
                return s
        return None

def md(detail=True, skipdata=True):
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = detail
    m.skipdata = skipdata
    m.skipdata_setup = (".byte", None, None)
    return m

def disasm_range(b: Bin, start: int, end: int, skipdata=True):
    """Linear disasm [start,end). Returns list of cs insn (id==0 for skipped bytes)."""
    data = b.read(start, end-start)
    return list(md(skipdata=skipdata).disasm(data, start))

def disasm_n(b: Bin, start: int, nbytes: int, skipdata=True):
    return list(md(skipdata=skipdata).disasm(b.read(start,nbytes), start))

def fmt(insn):
    return f"{insn.address:08X}  {insn.bytes.hex():<20} {insn.mnemonic:<8} {insn.op_str}"

def dump(b: Bin, start: int, end: int, skipdata=True):
    return "\n".join(fmt(i) for i in disasm_range(b,start,end,skipdata))

def find_bytes(b: Bin, pattern: bytes, secname=None):
    """Return all VAs matching literal byte pattern in raw sections."""
    out=[]
    secs=[b.sec(secname)] if secname else b.secs
    for s in secs:
        buf=b.data[s['raw']:s['raw']+s['rawsize']]
        pos=0
        while True:
            i=buf.find(pattern,pos)
            if i<0: break
            out.append(s['va']+i)
            pos=i+1
    return out

def cstr(b: Bin, va: int, maxn=200):
    raw=b.read(va,maxn)
    z=raw.find(b'\x00')
    if z<0: z=maxn
    return raw[:z].decode('ascii',errors='replace')

def imm32_refs(b: Bin, value: int, secname='.text'):
    """Find all 4-byte little-endian occurrences of value in a section."""
    return find_bytes(b, struct.pack('<I',value), secname)

def scan_calls(b: Bin, secname='.text'):
    """Full linear sweep, skipdata=True. Returns (calls:dict target->[sites], jmps)."""
    m=md(skipdata=True)
    s=b.sec(secname)
    data=b.data[s['raw']:s['raw']+s['rawsize']]
    calls, jmps = {}, {}
    nins=0; nskip=0
    for ins in m.disasm(data,s['va']):
        if ins.id==0:
            nskip+=ins.size; continue
        nins+=1
        if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
            calls.setdefault(int(ins.op_str,16),[]).append(ins.address)
        elif ins.mnemonic=='jmp' and ins.op_str.startswith('0x'):
            jmps.setdefault(int(ins.op_str,16),[]).append(ins.address)
    return calls, jmps, dict(insns=nins, skipped=nskip, bytes=len(data))

def load_atlas(path=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"):
    rows=[]
    with open(path,encoding='utf-8',errors='replace') as f:
        hdr=f.readline().rstrip('\n').split('\t')
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<len(hdr): continue
            rec=dict(zip(hdr,p))
            try: va=int(rec.get('entry') or rec.get('address') or rec.get('va'),16)
            except Exception: continue
            try: size=int(rec.get('size','0'))
            except Exception: size=0
            rows.append((va,size,rec))
    rows.sort()
    return rows,hdr

def func_containing(rows, va):
    """Channel-A function attribution: true interval containment, never entry_at_or_before."""
    import bisect
    keys=[r[0] for r in rows]
    i=bisect.bisect_right(keys,va)-1
    if i>=0 and va<rows[i][0]+rows[i][1]:
        return rows[i]
    return None

# ---- RTTI ----
def rtti_type_descriptors(b: Bin, name_substr=None):
    """Scan all data sections for MSVC TypeDescriptor:
      +0 pVFTable (points to TypeDescriptor's own vft, commonly 0x7F9594)
      +4 spare (0)
      +8 inline NUL-terminated mangled name  (NOT a pointer -- MSVC layout)
    Returns list of dict(va, name, pvf, spare, sec)."""
    out=[]
    for s in b.secs:
        if s['name'] not in ('.rdata','.data','.idata'): continue
        buf=b.data[s['raw']:s['raw']+s['rawsize']]
        base=s['va']
        for i in range(0,len(buf)-12,4):
            pvf,spare=struct.unpack_from('<II',buf,i)
            va=base+i
            if not (0x400000<=pvf<0xC00000): continue
            if spare!=0: continue
            try: name=cstr(b,va+8,128)
            except Exception: continue
            if not name or (not name.startswith('.?A') and not name.startswith('???')):
                continue
            if name_substr and name_substr not in name: continue
            out.append(dict(va=va,name=name,pvf=pvf,spare=spare,sec=s['name']))
    return out

def rtti_vftables(b: Bin, td_va: int):
    """Find VFTables belonging to a TypeDescriptor via CompleteObjectLocator.
    Returns list of dict(col_va, vftable_va, slots=[...])."""
    out=[]
    # search 4-byte refs to TypeDescriptor in .rdata/.data
    for ref in find_bytes(b, struct.pack('<I',td_va)):
        col=ref-0xC  # pTypeDescriptor at COL+0xC
        try:
            sig,off,cd,ptd,pcd=struct.unpack('<IIIII',b.read(col,20))
        except Exception: continue
        if sig!=0 or ptd!=td_va: continue
        # find pointer to COL => vftable-4
        for p in find_bytes(b,struct.pack('<I',col)):
            vft=p+4
            # read slots until a pointer that is not code or until 200 slots
            slots=[]
            for k in range(300):
                try: val=b.u32(vft+4*k)
                except Exception: break
                if not (0x400000<=val<0xC00000): break
                slots.append(val)
            out.append(dict(col_va=col,vftable_va=vft,slots=slots,
                            type_td=td_va, offset=off, cd=cd, class_td=pcd))
    return out

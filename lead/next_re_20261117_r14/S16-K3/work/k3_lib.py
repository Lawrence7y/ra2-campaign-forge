"""S16-K3 independent RE primitives (written from scratch).
Rules: capstone skipdata=True; VA via ImageBase+sections; RTTI COL+0xC -> TD+8 inline name;
fail-closed if RTTI unreadable. Never rely on atlas for vtable boundary (use .rdata COL/next-table).
"""
from __future__ import annotations
import struct, pefile, capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

class Bin:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.decode(errors="replace").rstrip("\x00")
            self.secs.append(dict(name=nm, va=self.base+s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize, raw=s.PointerToRawData,
                                  rawsize=s.SizeOfRawData))
        self.data = self.pe.__data__

    def sec(self, name):
        for s in self.secs:
            if s['name'] == name: return s
        raise KeyError(name)

    def off(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va']+s['rawsize']:
                return s['raw']+(va-s['va'])
        raise ValueError(f"VA {va:08X} not in any raw range")

    def read(self, va, n):
        o=self.off(va); return self.data[o:o+n]

    def u8(self,va): return self.read(va,1)[0]
    def u16(self,va): return struct.unpack('<H',self.read(va,2))[0]
    def u32(self,va): return struct.unpack('<I',self.read(va,4))[0]
    def i32(self,va): return struct.unpack('<i',self.read(va,4))[0]

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va']+max(s['rawsize'],s['vsize']): return s
        return None

    def in_rdata(self,va):
        s=self.sec('.rdata'); return s['va'] <= va < s['va']+s['rawsize']

    def in_text(self,va):
        s=self.sec('.text'); return s['va'] <= va < s['va']+s['rawsize']


def md(skipdata=True, detail=True):
    m=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail=detail; m.skipdata=skipdata
    m.skipdata_setup=(".byte",None,None)
    return m


def fmt(i): return f"{i.address:08X}  {i.bytes.hex():<20} {i.mnemonic:<8} {i.op_str}"


def disasm_range(b, start, end, skipdata=True):
    return list(md(skipdata=skipdata).disasm(b.read(start,end-start), start))


def disasm_n(b, start, nbytes, skipdata=True):
    return list(md(skipdata=skipdata).disasm(b.read(start,nbytes), start))


def dump_range(b, start, end):
    return "\n".join(fmt(i) for i in disasm_range(b,start,end))


def find_u32(b, value, secs=None):
    """All 4-byte-aligned occurrences of value in given sections (default .rdata/.data)."""
    out=[]
    pat=struct.pack('<I',value)
    for s in (secs or [b.sec('.rdata'),b.sec('.data')]):
        buf=b.data[s['raw']:s['raw']+s['rawsize']]
        pos=0
        while True:
            i=buf.find(pat,pos)
            if i<0: break
            if i%4==0: out.append(s['va']+i)
            pos=i+1
    return out


def cstr(b, va, maxn=200):
    raw=b.read(va,maxn); z=raw.find(b'\x00')
    if z<0: z=maxn
    return raw[:z].decode('ascii',errors='replace')


def rtti_from_col(b, col):
    """COL: sig, offset, cdOffset, pTypeDescriptor(+0xC), pClassDescriptor(+0x10).
    TD: +0 pVFTable, +4 spare, +8 INLINE mangled name.
    fail-closed: returns None if any check fails."""
    try:
        sig,off,cd,ptd,pcd=struct.unpack('<IIIII',b.read(col,20))
    except Exception:
        return None
    if sig!=0: return None
    if not (0x400000<=ptd<0xC00000): return None
    try:
        pvf,spare=struct.unpack('<II',b.read(ptd,8))
        name=cstr(b,ptd+8,128)
    except Exception:
        return None
    if not name.startswith('.?A'): return None
    return dict(col=col,off=off,cd=cd,ptd=ptd,pcd=pcd,name=name,pvf=pvf)


def vftables_for_td(b, td):
    """Find all VFTables whose COL points to td. Returns list of dict(vft, col, off, slots).
    VC6 layout: vftable[-1] = pointer to COL (i.e. [vft-4] == col)."""
    out=[]
    for ref in find_u32(b, td):
        col=ref-0xC
        r=rtti_from_col(b,col)
        if not r or r['ptd']!=td: continue
        # pointer to COL in .rdata or .data -> vft = ref+4
        for pref in find_u32(b, col):
            vft=pref+4
            # collect slots until non-code value (COL ptr / data) or 400 slots
            slots=[]
            for k in range(400):
                try: val=b.u32(vft+4*k)
                except Exception: break
                if not b.in_text(val): break
                slots.append(val)
            out.append(dict(vft=vft,col=col,off=r['off'],slots=slots,name=r['name']))
    return out


def find_vftable_containing_slot(b, vft_base, want_va):
    for k in range(400):
        try: val=b.u32(vft_base+4*k)
        except Exception: break
        if val==want_va: return k
    return None


def find_any_vftable_slot(b, want_va):
    """Scan all .rdata dwords that are COL refs to get candidate vftables, then find slot.
    Returns list of (vft, col, classname, slot_index, off)."""
    res=[]
    seen=set()
    for s in [b.sec('.rdata'),b.sec('.data')]:
        buf=b.data[s['raw']:s['raw']+s['rawsize']]
        for i in range(0,len(buf)-3,4):
            col=struct.unpack_from('<I',buf,i)[0]
            if not (0x7e0000<=col<0xb80000): continue
            r=rtti_from_col(b,col)
            if not r: continue
            pref=s['va']+i
            if (col,pref) in seen: continue
            seen.add((col,pref))
            vft=pref+4
            # find slot
            for k in range(200):
                try: val=b.u32(vft+4*k)
                except Exception: break
                if val==want_va:
                    res.append((vft,col,r['name'],k,r['off']))
                    break
                if not b.in_text(val): break
    return res

"""S10-KPROVED2 own toolkit: PE load + RTTI vtable census.
No import/copy from any other card's work dir. Built from scratch 2026-11-19.
"""
import struct, sys
import pefile

EXE = r'ra2youli\gamemd.exe'
IB = 0x400000

class PE:
    def __init__(self, path=EXE):
        self.pe = pefile.PE(path)
        self.image = self.pe.get_memory_mapped_image()
        self.imgbase = self.pe.OPTIONAL_HEADER.ImageBase
        self.sects = []
        for s in self.pe.sections:
            nm = s.Name.decode('latin1').rstrip('\x00')
            self.sects.append((nm, self.imgbase+s.VirtualAddress,
                               self.imgbase+s.VirtualAddress+s.Misc_VirtualSize,
                               s.PointerToRawData, s.SizeOfRawData))
    def rva2off(self, rva):
        for nm, va0, va1, praw, sz in self.sects:
            v0 = va0 - self.imgbase
            if v0 <= rva < v0 + sz:
                return praw + (rva - v0)
        return None
    def va2off(self, va):
        return self.rva2off(va - self.imgbase)
    def u32va(self, va):
        o = self.va2off(va)
        if o is None or o+4 > len(self.image):
            return None
        return struct.unpack_from('<I', self.image, o)[0]
    def bytesva(self, va, n):
        o = self.va2off(va)
        if o is None:
            return None
        return self.image[o:o+n]
    def sec_of_va(self, va):
        for nm, va0, va1, praw, sz in self.sects:
            if va0 <= va < va1:
                return nm
        return None
    def in_text(self, va):
        return self.sec_of_va(va) == '.text'

def rtti_name(pe, td):
    """TD+8 is inline mangled name string (技术⑦). Fail closed."""
    b = pe.bytesva(td+8, 64)
    if not b:
        return None
    # read until NUL
    end = b.find(b'\x00')
    if end < 0:
        return None
    s = b[:end]
    try:
        name = s.decode('ascii')
    except UnicodeDecodeError:
        return None
    if not (name.startswith('.?AV') or name.startswith('.?AU')):
        return None
    return name

def parse_col(pe, col_va):
    """COL: [+4]=offset(not needed), [+0xC]=pTD, [+0x10]=pClassHierarchy.
    tech⑧: COL is at vt-4, chain COL+0xC -> TD, TD+8 inline name.
    """
    sig = pe.u32va(col_va)
    td = pe.u32va(col_va+0xC)
    if td is None or pe.va2off(td) is None:
        return None
    name = rtti_name(pe, td)
    if name is None:
        return None
    return {'col':col_va,'td':td,'name':name,'sig':sig}

def census_vtables(pe):
    """Scan .rdata 4-aligned positions as vt-4 COL pointers. For each valid COL,
    vtable starts at (pos+4). Walk slots while values land in .text.
    Return list of vtables and a map entry_va -> list[(vt,slot,name,col,td)].
    """
    rdata = [s for s in pe.sects if s[0]=='.rdata'][0]
    _, va0, va1, praw, sz = rdata
    vts = []
    entry_map = {}
    # iterate over 4-aligned VAs in .rdata used range
    start = va0
    end = va1
    va = start
    while va + 4 <= end:
        col = pe.u32va(va)  # candidate COL pointer at this position
        if col is not None and pe.va2off(col) is not None:
            parsed = parse_col(pe, col)
            if parsed:
                vt = va + 4
                slots = []
                s = 0
                while True:
                    val = pe.u32va(vt + 4*s)
                    if val is None or not pe.in_text(val):
                        break
                    # guard against absurd slot count
                    if s > 2000:
                        break
                    slots.append(val)
                    entry_map.setdefault(val, []).append({
                        'vt':vt,'slot':s,'name':parsed['name'],
                        'col':parsed['col'],'td':parsed['td']})
                    s += 1
                vts.append({'vt':vt,'col':col,'td':parsed['td'],
                            'name':parsed['name'],'nslots':len(slots)})
        va += 4
    return vts, entry_map

if __name__ == '__main__':
    pe = PE()
    vts, emap = census_vtables(pe)
    print('vtables found:', len(vts))
    # candidates from classification A set
    cands = []
    with open(r'lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv', encoding='utf-8') as f:
        hdr = f.readline().rstrip('\n').split('\t')
        ii = {h:i for i,h in enumerate(hdr)}
        for line in f:
            c = line.rstrip('\n').split('\t')
            if c[ii['subsystem']]=='S10' and c[ii['has4_strict']]=='1' and c[ii['has2_rtti']]=='1':
                cands.append(int(c[ii['entry']],16))
    print('A-set (has2_rtti=1 & has4_strict=1):', len(cands))
    for e in sorted(cands):
        holds = emap.get(e, [])
        names = sorted(set(h['name'] for h in holds))
        slots = [(hex(h['vt']), h['slot']) for h in holds]
        print(f'{e:08X}  nholds={len(holds)}  names={names}  slots={slots}')

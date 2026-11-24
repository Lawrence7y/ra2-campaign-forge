"""Full RTTI/vftable scan from gamemd.exe (independent of function_atlas.tsv).

MSVC layout: at vftable[-4] lives a pointer to a CompleteObjectLocator (COL).
COL+0x0C -> TypeDescriptor; TypeDescriptor+8 -> ".?AVClass@@" name.
Scan .rdata for every aligned dword that points at a valid COL, treat P+4 as a
vftable, walk consecutive .text pointers as slots.
"""
import os, re, struct, json
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
EXE = os.path.join(PROJECT, 'ra2youli', 'gamemd.exe')
IB = 0x400000
TEXT_LO, TEXT_HI = 0x401000, 0x7E1000
RDATA_LO, RDATA_HI = 0x7E1000, 0x811074
DATA_LO, DATA_HI = 0x812000, 0xB79BE4
STR_LO, STR_HI = RDATA_LO, DATA_HI

with open(EXE, 'rb') as fh:
    D = fh.read()

def u32(va):
    off = va - IB
    if off < 0 or off + 4 > len(D):
        return None
    return struct.unpack_from('<I', D, off)[0]

def cstr(va, cap=96):
    off = va - IB
    if off < 0 or off + cap > len(D):
        return ''
    return D[off:off + cap].split(b'\x00')[0].decode('latin1', 'replace')

def clean_name(raw):
    # .?AVClass@@  or .?AUstruct@@
    m = re.match(r'^\.\?A[UV](.*)@@$', raw)
    if m:
        inner = m.group(1)
        # nested like Foo@Bar -> Bar::Foo
        return inner.replace('@', '::')
    return raw

def valid_col(col):
    if not (RDATA_LO <= col < RDATA_HI):
        return None
    # This binary uses signature=0 (verified on BuildingClass/AbstractClass/TEventClass COLs),
    # so validate structurally via pTypeDescriptor + pClassDescriptor instead of sig==1.
    td = u32(col + 0x0C)
    if td is None or not (STR_LO <= td < STR_HI):
        return None
    raw = cstr(td + 8, 128)
    if not raw.startswith('.?A'):
        return None
    pcd = u32(col + 0x10)
    if pcd is None or not (RDATA_LO <= pcd < RDATA_HI):
        return None
    return clean_name(raw)

def main():
    vtables = []      # (vt_addr, class, [slots])
    func_map = {}     # funcva -> [(class, vt, slot)]
    # scan .rdata aligned dwords for COL pointers
    for P in range(RDATA_LO, RDATA_HI - 4, 4):
        val = u32(P)
        if val is None:
            continue
        cls = valid_col(val)
        if not cls:
            continue
        vt = P + 4
        slots = []
        for slot in range(512):
            f = u32(vt + 4 * slot)
            if f is None or not (TEXT_LO <= f < TEXT_HI):
                break
            slots.append(f)
            func_map.setdefault(f, []).append(dict(cls=cls, vt=vt, slot=slot, plus=4*slot))
        if slots:
            vtables.append(dict(vt=vt, colptr_at=P, col=val, cls=cls, n=len(slots)))
    # dedup func_map entries
    for f in func_map:
        seen = set()
        uniq = []
        for m in func_map[f]:
            k = (m['cls'], m['vt'], m['slot'])
            if k not in seen:
                seen.add(k)
                uniq.append(m)
        func_map[f] = uniq
    with open(os.path.join(HERE, 'rtti_vtables.json'), 'w', encoding='utf-8') as f:
        json.dump(dict(vtables=vtables, func_map={str(k):v for k,v in func_map.items()}), f, ensure_ascii=False, indent=1)
    print('vftables found:', len(vtables))
    print('functions that are vtable slots:', len(func_map), 'memberships:', sum(len(v) for v in func_map.values()))
    # slice coverage
    TAB = chr(9)
    with open(os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv'), encoding='utf-8', errors='replace') as f:
        lines = f.read().splitlines()
    sl = lines[1:1293]
    entries = [int(r.split(TAB)[0],16) for r in sl]
    hit = [e for e in entries if e in func_map]
    print('slice functions that are vtable slots:', len(hit))
    for e in hit[:60]:
        print('%08X' % e, [(m['cls'], m['slot']) for m in func_map[e]])

if __name__ == '__main__':
    main()

import pefile, struct, os

P = os.path.join('D:', os.sep, 'Project', 'ra2-campaign-forge', 'ra2youli', 'gamemd.exe')
pe = pefile.PE(P)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b'\0').decode('ascii', 'replace')
    secs.append((name, s.VirtualAddress + IB, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
_data = open(P, 'rb').read()

def sec_of(va):
    for n, vb, vs, pr, rs in secs:
        if vb <= va < vb + max(vs, rs):
            return n
    return None

def off(va):
    for n, vb, vs, pr, rs in secs:
        if vb <= va < vb + max(vs, rs):
            d = va - vb
            if d < rs:
                return pr + d
    return None

def rd(va):
    o = off(va)
    if o is None or o + 4 > len(_data):
        return None
    return struct.unpack_from('<I', _data, o)[0]

def rdstr(va, n=120):
    o = off(va)
    if o is None:
        return None
    return _data[o:o+n].split(b'\0')[0].decode('ascii', 'replace')

def td_name(td):
    if not td:
        return None
    # TD: +0 = pVFTable (should be 0x7F9594), +8 = name
    return rdstr(td + 8)

# RTTI CompleteObjectLocator: +0 sig, +4 offset, +8 cdOffset, +0xC pTD, +0x10 pCHD
# ClassHierarchyDescriptor (CHD): +0 sig, +4 attributes, +8 numBaseClasses, +0xC pBaseClassArray
# BaseClassArray: array of DWORD -> BaseClassDescriptor
# BaseClassDescriptor: +0 pTD, +4 numContainedBases, +8 mdisp, +0xC pdisp, +0x10 vdisp, +0x14 attributes
def parse_chd(col):
    chd = rd(col + 0x10)
    if not chd or sec_of(chd) not in ('.rdata', '.data'):
        return {'chd': chd, 'ok': False, 'reason': 'bad chd ptr'}
    nbase = rd(chd + 8)
    parr = rd(chd + 0xC)
    out = {'chd': chd, 'nbase': nbase, 'parr': parr, 'bases': [], 'ok': True}
    if nbase is None or parr is None or nbase > 64:
        out['ok'] = False
        out['reason'] = 'bad nbase/parr'
        return out
    for i in range(nbase):
        bcd = rd(parr + 4*i)
        btd = rd(bcd) if bcd else None
        out['bases'].append((bcd, btd, td_name(btd)))
    return out

def slot_count(vt):
    # walk slots from vt[0]; count consecutive dwords that are .text code addrs;
    # stop at first value not in .text (COL pointer in .rdata marks boundary)
    n = 0
    stops = []
    for i in range(2000):
        val = rd(vt + 4*i)
        if val is None:
            stops.append(('none', i)); break
        s = sec_of(val)
        if s == '.text':
            n += 1
        else:
            stops.append((s or 'out', i, '%08X' % val)); break
    return n, stops

targets = [
    ('AbstractClass', 0x7E1F50, 24), ('ObjectClass', 0x7EF060, 122),
    ('TechnoClass', 0x7F4960, 309), ('FootClass', 0x7E8C94, 341),
    ('BuildingClass', 0x7E3EBC, 322), ('UnitClass', 0x7F5C70, 344),
    ('InfantryClass', 0x7EB058, 343), ('AircraftClass', 0x7E22A4, 341),
]
for name, vt, meta_slots in targets:
    col = rd(vt - 4)
    td = rd(col + 0xC) if col else None
    chd = parse_chd(col) if col else None
    sc, stops = slot_count(vt)
    v11 = rd(vt + 11*4)
    v12 = rd(vt + 12*4)
    print('=== %s vt=%08X col=%08X TDname=%s' % (name, vt, col or 0, td_name(td)))
    print('    meta_slots=%d  rdata_scan_slots=%d stop=%s' % (meta_slots, sc, stops[:1]))
    print('    v[11]=%s v[12]=%s' % (('%08X'%v11) if v11 else None, ('%08X'%v12) if v12 else None))
    if chd:
        print('    CHD=%08X nbase=%s parr=%s ok=%s' % (chd['chd'] or 0, chd.get('nbase'), chd.get('parr'), chd['ok']))
        for j,(bcd,btd,bnm) in enumerate(chd['bases']):
            print('      base[%d] bcd=%s btd=%s name=%s' % (j, ('%08X'%bcd) if bcd else None, ('%08X'%btd) if btd else None, bnm))

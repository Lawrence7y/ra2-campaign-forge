"""MSVC6-style RTTI: COL = {sig, offset, cdOffset, pTD(abs), pCD(abs)} (5 dwords, no pSelf).
CHD  = {sig, attributes, numBaseClasses, pBaseClassArray(abs)} (4 dwords)
BCD  = {pTD, numContainedBases, mdisp, pdisp, vdisp, attributes} (6 dwords)
vtable layout: [vtable-4] = COL ptr ; [vtable+0..] = slots
"""
import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
IB = pe.image_base


def cstr(v, maxlen=300):
    off = pe.va_to_off(v)
    if off is None:
        return None
    end = pe.data.find(b'\0', off)
    if end < 0 or end - off > maxlen:
        return None
    return pe.data[off:end].decode('latin-1', 'replace')


def in_rdata(v):
    return v is not None and 0x007E1000 <= v < 0x00812000


def in_data(v):
    return v is not None and 0x00812000 <= v < 0x00B79BE4


def is_col(v):
    if not in_rdata(v):
        return False
    sig, off, cd, ptd, pcd = [pe.dword(v + k * 4) for k in range(5)]
    if sig != 0:
        return False
    if not in_data(ptd):
        return False
    nm = cstr(ptd + 8)
    if not nm or not nm.startswith('.?A'):
        return False
    if not in_rdata(pcd):
        return False
    return True


def col_info(v):
    sig, off, cd, ptd, pcd = [pe.dword(v + k * 4) for k in range(5)]
    return dict(col=v, offset=off, cdOffset=cd, td=ptd, chd=pcd, name=cstr(ptd + 8))


def chd_bases(chd):
    sig, attr, n, arr = [pe.dword(chd + k * 4) for k in range(4)]
    out = []
    for i in range(min(n, 8)):
        bcd = pe.dword(arr + i * 4)
        if bcd is None:
            break
        ptd = pe.dword(bcd)
        nm = cstr(ptd + 8) if ptd else None
        mdisp, pdisp, vdisp = [pe.dword(bcd + 8 + j * 4) for j in range(3)]
        out.append((nm, mdisp, pdisp, vdisp))
    return attr, out


# find all vtable bases: address A such that dword(A) is a COL and A+4 begins slots
print('=== enumerate vtables (COL ptr at A, slots from A+4) ===')
vt = []
for A in range(0x007E1000, 0x00812000 - 4, 4):
    c = pe.dword(A)
    if is_col(c):
        vt.append((A + 4, c))
print('total vtables: %d' % len(vt))

print()
print('=== vtables containing 0054A4F0 ===')
for base, col in vt:
    slots = []
    a = base
    while a < 0x00812000:
        d = pe.dword(a)
        if d is None:
            break
        if pe.is_text(d):
            slots.append((a, d))
            a += 4
            continue
        break
    vals = [d for _, d in slots]
    if 0x0054A4F0 in vals:
        ci = col_info(col)
        attr, bases = chd_bases(ci['chd'])
        print('  vtable base %08X  COL %08X  offset=%d cdOffset=%d' % (base, col, ci['offset'], ci['cdOffset']))
        print('    class   : %s' % ci['name'])
        print('    CHD attr=%d bases=%s' % (attr, bases))
        print('    slot count=%d' % len(slots))
        for i, (a, d) in enumerate(slots):
            tag = '   <== CRASH FN' if d == 0x0054A4F0 else ''
            print('      slot%2d (+0x%02X) @%08X = %08X%s' % (i, i * 4, a, d, tag))
        print()

print('=== vtables containing 0054A3D0 (sibling) ===')
for base, col in vt:
    vals = []
    a = base
    while a < 0x00812000:
        d = pe.dword(a)
        if d is None or not pe.is_text(d):
            break
        vals.append(d)
        a += 4
    if 0x0054A3D0 in vals:
        ci = col_info(col)
        print('  vtable base %08X COL %08X slot%d class=%s' % (base, col, vals.index(0x0054A3D0), ci['name']))

print()
print('=== classes whose vtable has >=1 slot, sample of first 12 vtables near 007ECBE0 ===')
for base, col in vt:
    if 0x007ECB00 <= base <= 0x007ECD00:
        ci = col_info(col)
        attr, bases = chd_bases(ci['chd'])
        print('  base %08X COL %08X off=%d class=%s' % (base, col, ci['offset'], ci['name']))
        print('     bases=%s' % (bases,))

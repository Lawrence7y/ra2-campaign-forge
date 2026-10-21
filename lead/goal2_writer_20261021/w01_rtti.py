"""Proper MSVC RTTI parse for the vtables that contain 0x0054A4F0.

Layout used (MSVC 6 / VC7 style):
  vtable: [-1] = ptr to CompleteObjectLocator (COL), [0..n] = virtual fn ptrs
  COL: signature(+0), offset(+4), cdOffset(+8), pTypeDescriptor(+12 RVA),
       pClassDescriptor(+16 RVA), pSelf(+20 RVA)
  TypeDescriptor: vftable(+0), spare(+4), name[] (+8)
  ClassDescriptor: signature, offset, cdOffset, pTypeDescriptor, pClassDescriptor,
                   pSelf, pCHD, pBaseClassArray, pBaseClassDescriptorArray
"""
import importlib.util, os, struct

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
IB = pe.image_base


def va(rva):
    return (rva + IB) & 0xFFFFFFFF


def cstr(v, maxlen=260):
    off = pe.va_to_off(v)
    if off is None:
        return None
    end = pe.data.find(b'\0', off)
    if end < 0:
        return None
    return pe.data[off:min(end, off + maxlen)].decode('latin-1', 'replace')


def sect(v):
    s = pe.section_of(v)
    return s['name'] if s else '??'


def dump_col(col_va):
    sig, off, cd, ptd, pcd, pself = [pe.dword(col_va + k) for k in (0, 4, 8, 12, 16, 20)]
    out = {}
    out['col'] = col_va
    out['sig'] = sig
    out['offset'] = off
    out['cdOffset'] = cd
    out['td'] = va(ptd) if ptd else 0
    out['cd'] = va(pcd) if pcd else 0
    out['self'] = va(pself) if pself else 0
    out['name'] = cstr(out['td'] + 8) if out['td'] else None
    # ClassDescriptor detail
    if out['cd']:
        cdv = out['cd']
        out['cd_sig'] = pe.dword(cdv)
        out['cd_pchd'] = pe.dword(cdv + 24)
        out['cd_pbase'] = pe.dword(cdv + 28)
        out['cd_pbcd'] = pe.dword(cdv + 32)
    return out


def walk_vtable(start_slot_va, limit=40):
    """start_slot_va = address of slot0 (i.e. vtable base)."""
    slots = []
    v = start_slot_va
    for i in range(limit):
        d = pe.dword(v)
        if d is None:
            break
        slots.append((v, d))
        v += 4
        if d == 0:
            # a null slot is legal in MSVC vtables (pure call handler) -- keep going
            pass
    return slots


# ---- locate vtables by scanning .rdata for COL pointers ----
RD_LO, RD_HI = 0x007E1000, 0x00812000
print('=== scanning .rdata for vtable groups ===')
groups = []
v = RD_LO
while v < RD_HI - 8:
    d = pe.dword(v)
    if d is not None and 0x00800000 <= d < 0x00812000 and (d % 4 == 0):
        # candidate COL ptr at v ; check the COL looks sane
        col = d
        sig = pe.dword(col)
        ptd = pe.dword(col + 12)
        pself = pe.dword(col + 20)
        if sig == 0 and ptd is not None and 0x007E1000 <= ptd < 0x00812000 and pself == (col - IB):
            nm = cstr(va(ptd) + 8)
            if nm and nm.startswith('.?A'):
                groups.append((v, col, nm))
    v += 4

print('found %d candidate vtables' % len(groups))
for gv, col, nm in groups:
    if 0x007ECB00 <= gv <= 0x007ECD00:
        print('  vtablebase=%08X COL=%08X name=%s' % (gv, col, nm))

print()
print('=== detailed dump of the three vtables around 007ECBD8..007ECC20 ===')
for gv, col, nm in groups:
    if 0x007ECB00 <= gv <= 0x007ECD00:
        info = dump_col(col)
        print('--- vtable base %08X (COL %08X) ---' % (gv, col))
        print('    class name      : %s' % nm)
        print('    COL offset=%d cdOffset=%d self=%08X' % (info['offset'], info['cdOffset'], info['self']))
        print('    ClassDescriptor : %08X  pCHD=%s pBaseArray=%s pBCDArray=%s' % (
            info['cd'],
            hex(info.get('cd_pchd') or 0), hex(info.get('cd_pbase') or 0), hex(info.get('cd_pbcd') or 0)))
        slots = walk_vtable(gv, limit=12)
        for i, (a, d) in enumerate(slots):
            tag = ''
            if d == 0x0054A4F0:
                tag = '   <== CRASH FUNCTION (vtable slot %d)' % i
            if not pe.is_text(d) and d != 0:
                tag += '   [not .text: %s]' % sect(d)
            print('    slot%2d @%08X = %08X%s' % (i, a, d, tag))
        print()

print('=== what is at 007ECBC0..007ECBE0 (before first vtable) ===')
for a in range(0x007ECBB8, 0x007ECBE4, 4):
    print('  %08X = %08X  (%s)' % (a, pe.dword(a), sect(pe.dword(a))))

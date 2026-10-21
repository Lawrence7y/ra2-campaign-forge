"""The 89 `mov dword ptr [esi+4], <rdata-band imm>` stores.

These are the ONLY static instruction shape that can put a code-segment-band
address (0x007E1000..0x007EFFFF per the task's ".text" definition) into an
object's +4 field.  Enumerate them all, with their containing function and
the class whose vtable they initialise, to find which could be confused with
VectorClass<PAUTileInsertType>.
"""
import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()
IB = pe.image_base


def cstr(v, maxlen=300):
    off = pe.va_to_off(v)
    if off is None:
        return None
    end = pe.data.find(b'\0', off)
    if end < 0 or end - off > maxlen:
        return None
    return pe.data[off:end].decode('latin-1', 'replace')


def vtable_owner(vt):
    """vt = address of slot0. COL ptr sits at vt-4."""
    col = pe.dword(vt - 4)
    if col is None or not (0x007E1000 <= col < 0x00812000):
        return None
    sig, off, cd, ptd, pcd = [pe.dword(col + k * 4) for k in range(5)]
    if sig != 0:
        return None
    nm = cstr(ptd + 8) if ptd else None
    return (nm, col) if nm else None


ins = pt.disasm_range(pe, md, pe.text_lo, 0x007E1000)

print('=== all `mov dword ptr [REG + 4], <imm in 007E1000..007EFFFF> ===')
rows = []
for i in ins:
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    if dst not in ('dword ptr [esi + 4]', 'dword ptr [eax + 4]', 'dword ptr [ecx + 4]',
                   'dword ptr [edx + 4]', 'dword ptr [edi + 4]', 'dword ptr [ebx + 4]',
                   'dword ptr [ebp + 4]'):
        continue
    if not src.startswith('0x'):
        continue
    try:
        val = int(src, 16)
    except ValueError:
        continue
    if not (0x007E1000 <= val <= 0x007EFFFF):
        continue
    own = vtable_owner(val)
    rows.append((i.address, dst, val, own))

print('  count: %d' % len(rows))
for a, d, v, own in rows:
    nm = own[0] if own else '<not a vtable base>'
    print('  %08X  %-24s = %08X   owner=%s' % (a, d, v, nm))

print()
print('=== grouped by owner class ===')
from collections import Counter
c = Counter((r[3][0] if r[3] else None) for r in rows)
for nm, n in c.most_common():
    print('  %-80s %d' % (nm, n))

print()
print('=== do ANY of these stores write a .TEXT (00401000-007E1000) address into +4? ===')
n = 0
for i in ins:
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    if not dst.endswith('+ 4]'):
        continue
    if not src.startswith('0x'):
        continue
    try:
        val = int(src, 16)
    except ValueError:
        continue
    if 0x00401000 <= val < 0x007E1000:
        n += 1
        print('  %08X  %-26s = %08X' % (i.address, dst, val))
print('  count = %d' % n)

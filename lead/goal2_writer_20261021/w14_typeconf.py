"""Verify the multi-inheritance vptr-fixup mechanism and the owning class layout."""
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


def col_of(vt):
    col = pe.dword(vt - 4)
    if col is None or not (0x007E1000 <= col < 0x00812000):
        return None
    sig, off, cd, ptd, pcd = [pe.dword(col + k * 4) for k in range(5)]
    if sig != 0:
        return None
    return dict(col=col, offset=off, cdOffset=cd, td=ptd, chd=pcd,
                name=cstr(ptd + 8) if ptd else None)


print('=== full list: `mov [REG+4], <imm 007E1000..007EFFFF>` with owner + COL offset ===')
ins = pt.disasm_range(pe, md, pe.text_lo, 0x007E1000)
seen = {}
for i in ins:
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    if not dst.startswith('dword ptr [') or not dst.rstrip().endswith('+ 4]'):
        continue
    if not src.startswith('0x'):
        continue
    try:
        val = int(src, 16)
    except ValueError:
        continue
    if not (0x007E1000 <= val <= 0x007EFFFF):
        continue
    ci = col_of(val)
    key = (val, ci['name'] if ci else None, ci['offset'] if ci else None)
    seen.setdefault(key, []).append(i.address)

for (val, nm, off), addrs in sorted(seen.items(), key=lambda kv: -len(kv[1])):
    print('  vtable %08X  COL offset=%s  class=%-58s  %d sites  e.g. %08X' % (
        val, off, nm, len(addrs), addrs[0]))

print()
print('=== is 007ECBFC / 007ECBDC ever stored at +4 anywhere? ===')
for target in (0x007ECBFC, 0x007ECBDC):
    found = [a for (v, nm, off), addrs in seen.items() if v == target for a in addrs]
    print('  %08X stored at +4: %d sites %s' % (target, len(found), found))

print()
print('=== IsometricTileTypeClass vtable 007ECC1C: COL + full slot list ===')
ci = col_of(0x007ECC1C)
print('  class=%s COL=%08X offset=%d' % (ci['name'], ci['col'], ci['offset']))
a = 0x007ECC1C
for k in range(20):
    d = pe.dword(a + k * 4)
    if d is None:
        break
    if not pe.is_text(d):
        print('  slot%2d %08X = %08X   (not code -- end)' % (k, a + k * 4, d))
        break
    print('  slot%2d %08X = %08X' % (k, a + k * 4, d))

print()
print('=== global initializer for the static VectorClass instance @00AA1078 ===')
print('  vtable 007ECBDC -> DynamicVectorClass<PAUTileInsertType>')
print('  vtable 007ECBFC -> VectorClass<PAUTileInsertType>')
print('  static instance layout observed from 0x00543E70..0x00543EA6:')
print('    [00AA1078] = 007ECBFC  (+0x00 vptr)')
print('    [00AA107C] = 0         (+0x04 element ptr)')
print('    [00AA1080] = 0         (+0x08 count)')
print('    [00AA1084] = 1 (byte)  (+0x0C flag)')
print('    [00AA1085] = 0 (byte)  (+0x0D owns-buffer flag)')
print('    [00AA1088] = 0         (+0x10 active/capacity-used)')
print('    [00AA108C] = 0xA       (+0x14 capacity = 10)')

print()
print('=== does the Resize body read +0x14? (capacity field) ===')
body = pt.disasm_range(pe, md, 0x0054A4F0, 0x0054A58E)
for i in body:
    if '0x14' in i.op_str or '0x10' in i.op_str:
        print('  %08X  %-8s %s' % (i.address, i.mnemonic, i.op_str))

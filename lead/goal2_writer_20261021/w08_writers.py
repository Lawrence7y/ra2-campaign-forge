"""Writer candidate enumeration.

1) Who references the VectorClass<PAUTileInsertType> vtable 0x007ECBFC / 0x007ECBDC
   (constructors that set the vptr) -> tells us the OWNER class + member offset.
2) Every static store whose value is a .text/.rdata address (vptr/fnptr writes),
   grouped by destination displacement, to find who could hit a "+4" field.
3) Store shapes that could put a code address into an object's pointer field:
   memcpy-like loops, indexed stores, rep movs with .text source.
"""
import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()
RD_LO, RD_HI = 0x007E1000, 0x00812000

TEXT = pe.read(0x00401000, 0x3E0000)

print('=== 1) immediate/dword references to the two vtables ===')
for vt in (0x007ECBDC, 0x007ECBFC):
    needle = struct.pack('<I', vt)
    hits = []
    idx = 0
    while True:
        idx = pe.data.find(needle, idx)
        if idx < 0:
            break
        va = None
        for s in pe.sections:
            if s['rawptr'] <= idx < s['rawptr'] + s['rawsize']:
                va = s['va'] + (idx - s['rawptr'])
                sec = s['name']
                break
        hits.append((idx, va, sec))
        idx += 1
    print('  vtable %08X referenced %d times in file' % (vt, len(hits)))
    for off, va, sec in hits:
        print('     file %06X  VA %08X  (%s)' % (off, va, sec))

print()
print('=== 2) disasm around each vtable reference (vptr stores) ===')
ins = pt.disasm_range(pe, md, pe.text_lo, 0x007E1000)
for vt in (0x007ECBDC, 0x007ECBFC):
    pat = '0x%x' % vt
    for i in ins:
        if pat in i.op_str and i.mnemonic == 'mov':
            print('  %08X  %-30s' % (i.address, i.op_str))

print()
print('=== 3) store-shape census: `mov [reg+disp], <code/rdata VA>` grouped by disp ===')
from collections import Counter
by_disp = Counter()
for i in ins:
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    if not (dst.startswith('dword ptr [') and src.startswith('0x')):
        continue
    try:
        val = int(src, 16)
    except ValueError:
        continue
    if not (pe.is_text(val) or RD_LO <= val < RD_HI):
        continue
    if '+' in dst:
        try:
            d = int(dst.split('+')[1].split(']')[0].strip(), 16)
        except ValueError:
            continue
        by_disp[d] += 1
    else:
        by_disp[0] += 1
for d in sorted(by_disp):
    print('   disp=0x%-4X  count=%d' % (d, by_disp[d]))

print()
print('=== 4) stores with disp==4 whose value is a .text (not .rdata) address ===')
for i in ins:
    if i.mnemonic != 'mov':
        continue
    p = i.op_str.split(',')
    if len(p) != 2:
        continue
    dst, src = p[0].strip(), p[1].strip()
    if not dst.endswith('+ 4]'):
        continue
    try:
        val = int(src, 16)
    except ValueError:
        continue
    if pe.is_text(val):
        print('  %08X  %-34s' % (i.address, i.op_str))

print()
print('=== 5) rep movs / rep stos and memcpy-shaped loops copying to a +4 dest ===')
for i in ins:
    if i.mnemonic in ('rep movsb', 'rep movsd', 'rep stosb', 'rep stosd', 'movsb', 'movsd'):
        print('  %08X  %-8s %s' % (i.address, i.mnemonic, i.op_str))

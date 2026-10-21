"""Decisive reachability + band reconciliation checks.

Q1: Is 0x0054A56E reachable other than by entering at 0x0054A4F0?
    -> is it a dword anywhere (fnptr table)?  any branch targets it? (w07 said 0)
Q2: The task's ".text" band is 0x00401000-0x007EFFFF, but real .text ends at
    0x007E1000. 0x007E1000-0x007EFFFF is .rdata = WHERE ALL VTABLE POINTERS LIVE.
    So "a .text address in a pointer field" is most likely a VTABLE POINTER.
Q3: Does the code path to 0x0054A56E write [esi+0xC] first (read-only => would
    fault at 0x0054A506, not 0x0054A56E)?
Q4: Enumerate vptr stores whose immediate value lands in 0x007E1000-0x007EFFFF.
"""
import importlib.util, os, struct
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()

CRASH = 0x0054A56E
FN_LO, FN_HI = 0x0054A4F0, 0x0054A58E

print('=== Q1: raw LE dword 0x0054A56E anywhere in the file? ===')
needle = struct.pack('<I', CRASH)
idx = 0
hits = []
while True:
    idx = pe.data.find(needle, idx)
    if idx < 0:
        break
    va = None
    for s in pe.sections:
        if s['rawptr'] <= idx < s['rawptr'] + s['rawsize']:
            va = s['va'] + (idx - s['rawptr']); sec = s['name']; break
    hits.append((idx, va, sec))
    idx += 1
print('  occurrences: %d' % len(hits))
for off, va, sec in hits:
    print('    file %06X -> VA %08X (%s)' % (off, va, sec))

print()
print('=== Q1b: any dword in .rdata/.data that points INSIDE [0054A4F0,0054A58E)? ===')
inner = []
for v in range(0x007E1000, 0x00B79BE4 - 4, 4):
    d = pe.dword(v)
    if d is not None and FN_LO < d < FN_HI:
        inner.append((v, d))
print('  pointers into the function body (excluding entry): %d' % len(inner))
for v, d in inner[:20]:
    print('    @%08X = %08X' % (v, d))

print()
print('=== Q2: section boundary reconciliation ===')
for s in pe.sections:
    lo, hi = s['va'], s['vend']
    ov = max(0, min(hi, 0x007F0000) - max(lo, 0x00401000))
    if ov:
        print('  %-9s %08X..%08X  overlap with claimed ".text" band 00401000-007EFFFF = 0x%X bytes' % (s['name'], lo, hi, ov))
print('  => real .text ends at %08X; 007E1000..007EFFFF is .rdata (read-only, vtable home)' % pe.text_hi)

print()
print('=== Q3: mandatory writes before the faulting store ===')
ins = pt.disasm_range(pe, md, FN_LO, FN_HI)
for i in ins:
    if FN_LO <= i.address <= CRASH and i.mnemonic == 'mov' and 'ptr [esi' in i.op_str:
        kind = 'WRITE' if i.op_str.split(',')[0].strip().startswith(('byte', 'dword', 'word')) else 'read '
        print('  %08X  %-8s %-26s %s' % (i.address, kind, i.op_str, '<-- FAULT' if i.address == CRASH else ''))
print('  => [esi+0xC] is WRITTEN at 0x0054A506 and 0x0054A526, both BEFORE 0x0054A56E.')
print('     If esi were in a read-only section, the first fault would be 0x0054A506, never 0x0054A56E.')

print()
print('=== Q4: vptr/fnptr immediate stores whose value is in the .rdata band 007E1000-007EFFFF ===')
allins = pt.disasm_range(pe, md, pe.text_lo, 0x007E1000)
band = Counter()
examples = []
for i in allins:
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
    if 0x007E1000 <= val <= 0x007EFFFF:
        band[dst] += 1
        if len(examples) < 12:
            examples.append((i.address, dst, val))
print('  total stores of a .rdata-band immediate: %d' % sum(band.values()))
for a, d, v in examples:
    print('    %08X  %-28s = %08X' % (a, d, v))
print('  distinct destinations: %d' % len(band))
print('  top destinations:')
for d, c in band.most_common(10):
    print('    %-28s %d' % (d, c))

print()
print('=== Q5: this class object layout (from ctor/dtor static analysis) ===')
print('  class  : .?AV?$VectorClass@PAUTileInsertType@IsometricTileTypeClass@@@@')
print('  vtable : 007ECBFC   (+0 = vptr)')
print('  +0x00  vptr          (written by dtor 0054A7B6 / 0054A806 = 0x7ECBFC)')
print('  +0x04  element ptr   (heap buffer; the field at the crash)')
print('  +0x08  count         (ebp = requested count)')
print('  +0x0C  needs-free / owning flag (byte)')
print('  +0x0D  owns-buffer flag (byte)')
print('  +0x10  capacity      (seen at 0054A199 / 0054A1F9 / 0054A46B / 0054A6CB)')
print('  size ~ 0x14 bytes')

import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()

TARGETS = [0x0054A4F0]
print('=== prologue scan backwards from 0x54A4F0 ===')
insns = pt.disasm_range(pe, md, 0x0054A300, 0x0054A4F2)
print(pt.fmt(insns, lo=0x0054A360, hi=0x0054A4F2))

print()
print('=== direct E8/E9 rel32 xrefs in .text ===')
for t in TARGETS:
    hits = []
    text = pe.read(0x00401000, 0x3E0000)
    for i in range(len(text) - 5):
        if text[i] in (0xE8, 0xE9):
            rel = struct.unpack_from('<i', text, i + 1)[0]
            src = 0x00401000 + i
            if (src + 5 + rel) & 0xFFFFFFFF == t:
                hits.append((src, text[i]))
    print('target %08X: %d hits' % (t, len(hits)))
    for a, op in hits:
        print('   %08X %s' % (a, 'call' if op == 0xE8 else 'jmp'))

print()
print('=== dword occurrences of target anywhere in image (vtables etc) ===')
needle = struct.pack('<I', TARGETS[0])
idx = 0
found = []
while True:
    idx = pe.data.find(needle, idx)
    if idx < 0:
        break
    found.append(idx)
    idx += 1
print('raw file offsets:', ['0x%06X' % f for f in found])
for f in found:
    # map back to VA
    for s in pe.sections:
        if s['rawptr'] <= f < s['rawptr'] + s['rawsize']:
            va = s['va'] + (f - s['rawptr'])
            print('  file 0x%06X -> %s VA %08X' % (f, s['name'], va))
            # show surrounding table
            base = va - 0x40
            vals = []
            for k in range(0, 0x80, 4):
                d = pe.dword(base + k)
                vals.append('%08X' % d if d is not None else '--------')
            print('    table ctx %08X:' % base, ' '.join(vals))
            break

"""m0: YRpp address-binding index (② channel 2 source), rebuilt from YRpp\ headers.

binding = a literal `CALL(0x…)/JMP_THIS(0x…)/JMP_STD(0x…)/THISCALL(0x…)/JMP(0x…)` line in YRpp\.
For each binding we also collect every absolute address literal seen inside the enclosing class
block, so the byte-conformance test (`≥2 of them appear as 4-byte immediates in the body`) can
be run per entry.
"""
import sys, json, re, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import core2 as C

YR = C.ROOT/'YRpp'
BIND  = re.compile(r'\b(CALL|JMP_THIS|JMP_STD|THISCALL|JMP)\s*\(\s*(0x[0-9A-Fa-f]{5,8})\s*\)')
CLASS = re.compile(r'^\s*(?:class|struct)\s+(?:\w+\s+)*(?P<n>[A-Za-z_]\w*)')

bindings = collections.defaultdict(list)
class_addrs = collections.defaultdict(set)

files = [p for p in YR.rglob('*')
         if p.is_file() and p.suffix.lower() in ('.h', '.hpp', '.cpp') and '.git' not in p.parts]
nb = 0
for p in files:
    txt = p.read_text(encoding='utf-8', errors='replace').splitlines()
    cur = None
    for i, l in enumerate(txt):
        m = CLASS.match(l)
        if m and not l.strip().startswith('//'): cur = m.group('n')
        for mm in BIND.finditer(l):
            nb += 1
            bindings[int(mm.group(2), 16)].append([str(p.relative_to(C.ROOT)), i+1, mm.group(1), cur])
        if cur:
            for hm in re.finditer(r'0x([0-9A-Fa-f]{5,8})u?', l):
                v = int(hm.group(1), 16)
                if 0x800000 <= v < 0xB80000: class_addrs[cur].add(v)

print('YRpp files        =', len(files))
print('binding lines     =', nb)
print('distinct entries  =', len(bindings))
print('classes w/ addrs  =', len(class_addrs))

(C.OUT/'work'/'yrpp.json').write_text(json.dumps(
    {'bindings': {hex(k): v for k, v in bindings.items()},
     'class_addrs': {k: sorted(v) for k, v in class_addrs.items()}},
    ensure_ascii=False), encoding='utf-8')
print('wrote yrpp.json')

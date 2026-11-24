"""Parse re_atlas/evidence/vtable_slots.txt -> func entry -> [(class, vtable, slot, plus, detail)]."""
import os, re, json
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
VT = os.path.join(PROJECT, 're_atlas','evidence','vtable_slots.txt')
TAB = chr(9)
cls_re = re.compile(r'^===\s+(\S+)\s+vtable\s+0x([0-9A-Fa-f]+)\s*===')
slot_re = re.compile(r'^\s*\[\s*(\d+)\]\s+0x([0-9A-Fa-f]+)\s+0x([0-9A-Fa-f]+)\s+(\S+)\s*(.*)$')
out = {}
cur = None
with open(VT, encoding='utf-8', errors='replace') as f:
    for line in f:
        m = cls_re.match(line)
        if m:
            cur = (m.group(1), int(m.group(2),16))
            continue
        s = slot_re.match(line)
        if s and cur:
            slot = int(s.group(1))
            plus = int(s.group(2),16)
            val = int(s.group(3),16)
            kind = s.group(4)
            detail = s.group(5).strip()
            out.setdefault(val, []).append(dict(cls=cur[0], vt=cur[1], slot=slot, plus=plus, kind=kind, detail=detail))
with open(os.path.join(HERE,'vtable_membership.json'),'w',encoding='utf-8') as f:
    json.dump({str(k):v for k,v in out.items()}, f, ensure_ascii=False, indent=1)
print('functions that are vtable slots:', len(out), 'total memberships:', sum(len(v) for v in out.values()))
with open(os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv'), encoding='utf-8', errors='replace') as f:
    lines=f.read().splitlines()
sl=lines[1:1293]
entries=[int(r.split(TAB)[0],16) for r in sl]
hit=[e for e in entries if e in out]
print('slice functions that are vtable slots:', len(hit))
for e in hit[:40]:
    print('%08X'%e, [(m['cls'],m['slot']) for m in out[e]])

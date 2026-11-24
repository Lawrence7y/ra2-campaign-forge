"""Identify LocomotionClass vtable boundaries precisely via COL pointers.
MSVC layout: [methods...][COLptr] repeated; COLptr = vftable_start - 4.
Use class_atlas vtables_canonical.json to know the COL for each (class,col_offset)."""
from pehelp import *
import json

path = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json'
data = json.load(open(path, encoding='utf-8'))
loco = [v for v in data['vtables'] if 'LocomotionClass' in v['class'] and 'TClassFactory' not in v['class']]
# group by class
from collections import defaultdict
g = defaultdict(list)
for v in loco: g[v['class']].append(v)

for cls, vs in sorted(g.items()):
    print('###', cls)
    for v in sorted(vs, key=lambda x:-x['col_offset']):
        vt, col, off = v['vt'], v['col'], v['col_offset']
        # actual COL ptr at vt-4 must equal col
        cptr = u32(vt-4)
        # scan forward from vt until we hit a dword that is a known COL of any loco vtable, or non-code
        known_cols = {x['col'] for x in loco}
        n = 0
        for i in range(80):
            d = u32(vt+4*i)
            if d in known_cols:  # next COL => end of this vtable
                break
            if not (IMAGE_BASE <= d < 0x10000000 and section_of(d)=='.text'):
                # non-code, potential end (but could be mid-table? MSVC tables are all code)
                break
            n += 1
        print('  off=%-3d vt=%08X col=%08X cptr@vt-4=%08X %s  slots=%d (end@%08X=%08X)' % (
            off, vt, col, cptr, 'OK' if cptr==col else 'MISMATCH', n, vt+4*n, u32(vt+4*n)))
    print()

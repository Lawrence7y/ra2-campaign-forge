# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
for vt in (0x7e1964, 0x7e36d4, 0x7f4108, 0x7ea564):
    c = col_of(vt)
    print('=== vt 0x%08x ===' % vt)
    if not c:
        print('  COL 解不出'); continue
    print('  COL sig=%s class=%s n=%d' % (c['signature'], c['type_desc'], c['n']))
    for b in c['bases']:
        print('    %-46s ncb=%-3s mdisp=%s' % (b['name'], b['ncb'], b['mdisp']))
    print('  slots:', ['0x%08x'%u32(vt+4*i) for i in range(8)])
    print()

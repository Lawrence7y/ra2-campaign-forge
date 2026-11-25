# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
print('IB 0x%08x' % IB)
print('sections:', [(n,hex(lo),hex(hi),'raw 0x%x'%rs,'vsz 0x%x'%vs) for n,lo,hi,ptr,vs,rs in SECS])
print()
def where(va):
    for n,lo,hi,ptr,vs,rs in SECS:
        if lo<=va<hi:
            off=va-lo
            return '%s off 0x%x %s' % (n, off, 'RAW' if off<rs else 'BSS(virtual-only, 静态全 0)')
    return 'NONE'
for va in (0x87f7e8,0x89a29c,0xb0c110,0x7ea6e8,0x7ea564,0x7e36d4,0x7f4108,0x818858,0x820270,0x7f7c70):
    print('0x%08x  %s' % (va, where(va)))
print()
print('BSS 边界: .data raw 结束于 0x%08x, vsz 结束于 0x%08x'
      % (IB+0x812000+0x6c000, IB+0x812000+0x367be4))

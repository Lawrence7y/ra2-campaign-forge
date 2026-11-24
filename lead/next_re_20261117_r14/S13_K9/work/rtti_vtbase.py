# RTTI chain with CORRECT vtable bases (vt-4 = COL, COL+0xC = TD, TD+8 inline name)
import sys,struct
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
VTS=[('F1',0x7e17cc),('F2',0x7e1e84),('F3',0x7e1ed4),('F4',0x7e4678),('F5',0x7ef824),('F6',0x7f07a4),
     ('F1d',0x7e17ec),('F2d',0x7e1ea4),('F3d',0x7e1ef4),('F4d',0x7e4698),('F5d',0x7ef844),('F6d',0x7f07c4)]
for name,vt in VTS:
    col=u32(vt-4)
    td=u32(col+0xC) if col else None
    b=rd(td+8,60) if td else None
    nm=b.split(b'\x00')[0].decode('ascii',errors='replace') if b else None
    print(name,'vt',hex(vt),'COL',hex(col) if col else None,'in',sec_of(col) if col else '-',
          'TD',hex(td) if td else None,'in',sec_of(td) if td else '-','TD+8 name',repr(nm))

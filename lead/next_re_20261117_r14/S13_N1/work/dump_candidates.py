import sys
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
for va in [0x487C70,0x487C80,0x773030,0x46B5C0]:
 print('=====',hex(va),'=====')
 for i in dis(va,0x120 if va!=0x773030 else 0x70): print(fmt(i))
 print('VT',vt_slots_for_entry(va))
 print('XREF',[hex(x) for x in direct_xrefs(va)])

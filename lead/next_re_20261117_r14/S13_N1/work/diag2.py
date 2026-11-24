import sys
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
for va,n in [(0x46B5C0,0x90),(0x4393F0,0x70),(0x77BE0,0x60),(0x8ACE0,0x80),(0x773030,0x60)]:
 print('====',hex(va),'====')
 for i in dis(va,n):
  if i.mnemonic in ('test','call','ret','retf') or 'delete' in i.op_str:
   print(fmt(i))
print('known vt hits',vt_slots_for_entry(0x4393D0))

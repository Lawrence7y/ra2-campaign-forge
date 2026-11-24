import sys
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
for va in [0x81afa0,0x842c2c,0x7e4db8]:
 try: print(hex(va),'cstr',repr(cstr(va,120)),'rtti',rtti_name_from_vt(va))
 except Exception as e: print(hex(va),'ERR',e)
print('== ctor 771C70 tail ==')
for i in dis(0x771E70,0x1a0): print(fmt(i))
print('== refs to 88756c/887578 in ctor ==')
for i in dis(0x771C70,0x400):
 s=fmt(i).lower()
 if '88756c' in s or '887578' in s: print(fmt(i))

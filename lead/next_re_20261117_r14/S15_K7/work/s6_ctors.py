import sys;sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S15_K7\work');import pe_common as p
for ctor,name in [(0x6E5B60,'TagTypeClass'),(0x6F06E0,'TeamTypeClass'),(0x726C80,'TriggerTypeClass')]:
 print('----',name,hex(ctor),'----'); p.dump(ctor,0x60)
 for a,bb,s,i in p.dis(ctor,0x60):
  if 'mov dword ptr [' in s and ', 0x7' in s:
   import re
   m=re.search(r', (0x7[0-9a-f]+)',s)
   if m:
    try: print('  RTTI',m.group(1),p.vtinfo(int(m.group(1),16))['name'])
    except Exception as e: print('  ERR',m.group(1),e)

import sys,struct
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
L=['RTTI checks, COL=vtable-4, TD=COL+0xC, TD+8 inline name']
def chk(vt,nm):
    col=R.u32(vt-4); td=R.u32(col+0xC); raw=R.read(td+8,80); z=raw.find(b'\0'); s=raw[:z if z>=0 else 80]
    L.append(f'{nm} vt={vt:08X} col={col:08X} td={td:08X} name={s!r}')
for vt,nm in [(0x7EB058,'InfantryClass'),(0x7EBEF4,'UnitClass'),(0x7EA540,'TechnoClass'),(0x7E4C64,'FootClass')]:chk(vt,nm)
out=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\EVIDENCE\RTTI_CHECK.txt')
out.write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('\n'.join(L))

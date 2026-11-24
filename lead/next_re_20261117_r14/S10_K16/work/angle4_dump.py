
import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
for a in [0x00754BE0,0x00468090,0x005F5E80]:
 size=next((int(r[1]) for k,r in k16.atl.items() if k==f'{a:08x}'),200)
 print('\n###',hex(a),'cov',k16.row(a),'size',size,'slots',[(x[0],x[3]) for x in k16.cls(a)])
 for i in common.disasm(a,size): print(common.fmt(i))

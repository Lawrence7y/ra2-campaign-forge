
import sys,os
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
addrs=[0x00701410,0x006FB740,0x0070B570,0x006F4EB0,0x006FB010]
for a in addrs:
 r=k16.row(a); size=next((int(rr[1]) for k,rr in k16.atl.items() if k==f'{a:08x}'),200)
 print('\n###',hex(a),'covname',r[2] if r else None,'grade',r[4] if r else None,'size',size,'slots',[(x[0],x[3]) for x in k16.cls(a)])
 ins=common.disasm(a,size)
 for i in ins: print(common.fmt(i))

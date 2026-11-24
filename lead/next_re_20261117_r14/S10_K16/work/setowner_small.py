
import sys,os,collections,re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
small=[0x7010D0,0x701120,0x701140,0x701190,0x7012C0]
callers=k16.callers_of(small)
for a in small:
 size=next((int(r[1]) for k,r in k16.atl.items() if k==f'{a:08x}'),0)
 ins=common.disasm(a,size)
 print('\n###',f'{a:08X}',k16.row(a),'size',size,'slots',[(x[0],x[3]) for x in k16.cls(a)])
 for i in ins: print(common.fmt(i))
 print('direct calls',[(f'{s:08X}',f'{t:08X}',k16.row(t)[4] if k16.row(t) else '?') for s,t in k16.direct_calls_in(a,size)])
 by=collections.defaultdict(list)
 for s,ca in callers.get(a,[]): by[ca].append(s)
 print('direct callers',[(f'{ca:08X}',k16.row(ca)[2] if k16.row(ca) else '?',[f'{s:08X}' for s in ss]) for ca,ss in by.items()])


import sys,os,re,collections
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
targets=[0x00701410,0x006FB740,0x0070B570,0x006F4EB0,0x006FB010,0x006FB170,0x006FB470,0x007014A0]
callers=k16.callers_of(targets)
for a in targets:
 r=k16.row(a); size=next((int(rr[1]) for k,rr in k16.atl.items() if k==f'{a:08x}'),200)
 ins=common.disasm(a,size)
 calls=[(s,t,k16.row(t)[4] if k16.row(t) else '-',k16.row(t)[2] if k16.row(t) else '-') for s,t in k16.direct_calls_in(a,size)]
 vcalls=[(i.address,i.op_str) for i in ins if i.mnemonic=='call' and 'ptr [' in i.op_str]
 writes=[common.fmt(i) for i in ins if re.search(r'mov\s+(byte|word|dword) ptr \[esi \+ 0x',common.fmt(i))]
 cmpimm=[common.fmt(i) for i in ins if i.mnemonic in ('cmp','test') and re.search(r'0x[0-9a-f]+',i.op_str)]
 print('\n###',f'{a:08X}','cov',r[2] if r else None,r[4] if r else None,'size',size,'nins',len(ins))
 print('SLOTS',[(x[0],x[3]) for x in k16.cls(a)])
 print('CALLERS',[(f'{t:08X}' if isinstance(t,int) else t,len(v)) for t,v in []])
 print('DIRECT CALLS',len(calls))
 for s,t,g,n in calls: print(' ',f'{s:08X}','->',f'{t:08X}',g,(n or '')[:70])
 print('VCALLS',len(vcalls))
 for s,o in vcalls: print(' ',f'{s:08X}',o)
 print('SELF FIELD WRITES',len(writes))
 for w in writes[:50]: print(' ',w)
 print('CMP/TESTS',len(cmpimm))
 for c in cmpimm[:30]: print(' ',c)
 print('CALLER FUNCS')
 by=collections.defaultdict(list)
 for site,ca in callers.get(a,[]): by[ca].append(site)
 for ca,sites in sorted(by.items()):
  cr=k16.row(ca); print(' ',f'{ca:08X}',cr[2] if cr else '?',cr[4] if cr else '?',[f'{s:08X}' for s in sites])

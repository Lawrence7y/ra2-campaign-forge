# -*- coding: utf-8 -*-
import sys,re,struct
sys.path.insert(0, __import__('os').path.dirname(__file__))
import pe_common as p
sys.stdout.reconfigure(encoding='utf-8')
blob=p.data[p.TEXT.PointerToRawData:p.TEXT.PointerToRawData+p.TEXT.Misc_VirtualSize]
# f6 44 24 08 01 = test byte ptr [esp+8],1
pat=bytes.fromhex('f644240801')
hits=[];i=0
while True:
 j=blob.find(pat,i)
 if j<0: break
 va=p.TSTART+j
 ins=p.dis(va,0x80)
 txt='\n'.join(s for a,bb,s,_ in ins)
 # bounded until first ret after pattern
 after=[(a,bb,s) for a,bb,s,_ in ins if a>=va]
 calls=re.findall(r'call (0x[0-9a-f]+)', '\n'.join(s for a,bb,s in after[:20]))
 ret4=any(s.split()[0] in ('ret','retn') and '4' in s for a,bb,s in after[:20])
 hits.append((va,calls,ret4,txt))
 i=j+1
print('pattern_count',len(hits))
print('va\tcalls_near\tret4')
for va,calls,ret4,txt in hits[:80]:
 print(f'{va:08X}\t{";".join(calls)}\t{ret4}')
# bounded target bodies full variable up to first ret
TARGETS=['006D0F00','006D6070','006E1830','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','00721270','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
print('\nTARGET_BOUNDED_DTOR')
for hx in TARGETS:
 va=int(hx,16); ins=p.dis(va,0x1000,True)
 txt='\n'.join(s for a,bb,s,_ in ins)
 tb=any('test byte ptr [esp + 8], 1' in s for a,bb,s,_ in ins)
 dc=[x for x in re.findall(r'call (0x[0-9a-f]+)',txt)]
 ret4=any(s.split()[0] in ('ret','retn') and re.search(r'\b4\b',s) for a,bb,s,_ in ins)
 print(hx,'first_ret',f'{ins[-1][0]:08X}','len',len(ins),'tb',tb,'calls',len(dc),'ret4',ret4,'decision','TRUE' if tb and dc and ret4 else 'FALSE')

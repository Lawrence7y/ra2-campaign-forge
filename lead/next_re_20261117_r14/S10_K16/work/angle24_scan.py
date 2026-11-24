
import sys,os,collections,re
sys.path.insert(0,os.path.dirname(__file__)); import common,k16
print('S10 Object/Abstract rows')
for a,r in sorted(k16.cov.items()):
 if r[1]=='S10' and re.search(r'ObjectClass|AbstractClass',r[2]+' '+r[3]): print(a,r[2],r[4],r[3][:100])
print('\nS10 nonproved directly called by Anim/Bullet class functions')
s10np={int(k,16):r for k,r in k16.cov.items() if r[1]=='S10' and r[4]!='[已证]'}
hits=collections.defaultdict(list)
for a,size in k16.FUNCS:
 cr=k16.row(a); nm=(cr[2] if cr else '')+' '+(cr[3] if cr else '')
 if not re.search(r'AnimClass|BulletClass',nm): continue
 for site,t in k16.direct_calls_in(a,size):
  if t in s10np: hits[t].append((site,a,cr[2] if cr else '?',cr[4] if cr else '?'))
for t,h in sorted(hits.items()):
 r=s10np[t]
 print('\n',f'{t:08X}',r[2],r[4],'callers',len(h))
 for site,a,n,g in h: print('  ',f'{site:08X} <- {a:08X}',n,g)

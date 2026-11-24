import os
ROOT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
CARD=ROOT+r'\S17_K5'
NEEDLES=['DebugLogSink','DebugLogSink_behavior']
hits=[]
for dp,dn,fn in os.walk(ROOT):
 if dp.startswith(CARD): continue
 for f in fn:
  p=os.path.join(dp,f)
  try: t=open(p,'r',encoding='utf-8',errors='ignore').read()
  except: continue
  for n in NEEDLES:
   if n in t: hits.append((p,n))
conf=[l for l in open(ROOT+r'\COVERAGE\CONFLICTS.tsv','r',encoding='utf-8',errors='ignore').read().splitlines() if '004068E0' in l]
out=[]
out.append('S17_K5 conflict/grep check (read-only)')
out.append('exact proposed-name hits outside S17_K5: '+str(len(hits)))
for p,n in hits[:30]: out.append('  '+p+' : '+n)
out.append('CONFLICTS.tsv rows containing 004068E0: '+str(len(conf)))
for l in conf: out.append('  '+l)
txt='\n'.join(out)+'\n'
open(CARD+r'\EVIDENCE\conflict_check.txt','w',encoding='utf-8').write(txt)
print(txt)

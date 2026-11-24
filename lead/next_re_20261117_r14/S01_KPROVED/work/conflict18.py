# -*- coding: utf-8 -*-
import os,re
ROOTS=[r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14",r"D:\Project\ra2-campaign-forge\docs",r"D:\Project\ra2-campaign-forge\re_atlas",r"D:\Project\ra2-campaign-forge\YRpp"]
S01=['00409030','00409100','004091C0','004092F0','00409320','00409360','004093F0','00409880','00409C40','00409D90','00430250','0048C8B0','0048CCC0','004E2450','004E2460','004E24A0','004F1AA0','0052FC20','00554400','0055AF60','0055CFD0','0055D360','0055E420','0055F1E0','005A89D0','005B1D90','005B1E40','005CAF70','005CAFC0','005D2410','005D2530','005D5870','005D5880','005D5890','0063D810','00643E80','00646DF0','00647040','006470F0','006471A0','006521C0','006640E0','00697AD0','0069AE90','0069BAB0','006BB9A0','007240B0','007241A0','00724200','00732CA0','00734120','00734210','007CD80F']
pat6=re.compile(r'\b([0-9A-Fa-f]{6})\b')
hits={e:[] for e in S01}; nf=0
for ROOT in ROOTS:
 for root,dirs,files in os.walk(ROOT):
  dirs[:]=[d for d in dirs if d not in {'.git','__pycache__'}]
  for fn in files:
   if not re.search(r'\.(md|tsv|txt|json|h|cpp|ndjson)$',fn,re.I): continue
   fp=os.path.join(root,fn)
   try:
    if os.path.getsize(fp)>4_000_000: continue
    lines=open(fp,encoding='utf8',errors='replace').read().splitlines()
   except: continue
   nf+=1
   for ln,line in enumerate(lines,1):
    for m in pat6.finditer(line):
     h=m.group(1).upper()
     for e in S01:
      if e[-6:]==h: hits[e].append(os.path.relpath(fp,ROOT)+':'+str(ln))
print('files scanned:',nf)
for e in S01:
  u=list(dict.fromkeys(hits[e]))
  if u: print(f'{e}: {len(u)} files {u[:3]}')

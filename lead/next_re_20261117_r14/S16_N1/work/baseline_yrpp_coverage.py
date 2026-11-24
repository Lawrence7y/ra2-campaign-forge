# -*- coding: utf-8 -*-
import os,re
base=r"D:\Project\ra2-campaign-forge"
# collect all 6-hex addresses mentioned anywhere in YRpp source/docs (excluding .mimosa)
bind=set()
for root,dirs,files in os.walk(base+r"\YRpp"):
  dirs[:]=[d for d in dirs if d not in ('.mimosa','.git')]
  for f in files:
    if not f.lower().endswith(('.h','.html','.cpp')):continue
    try:s=open(os.path.join(root,f),encoding='utf8',errors='ignore').read()
    except:continue
    for m in re.finditer(r'0x([0-9A-Fa-f]{6})\b',s): bind.add(int(m.group(1),16))
print("YRpp distinct 6-hex addresses:",len(bind))
cov=open(base+r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv",encoding='utf8').read().splitlines()[1:]
atl=set(x.split('\t')[0].lower() for x in open(base+r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv",encoding='utf8').read().splitlines()[1:] if x.strip())
s16=[]
seen=set()
for l in cov:
  c=l.split('\t')
  if len(c)>=5 and c[1]=='S16' and c[0].lower() in atl:
    a=int(c[0],16)
    if a not in seen: seen.add(a); s16.append((a,c[2]))
bound=[(hex(a),n) for a,n in s16 if a in bind]
print("S16 entries:",len(s16),"YRpp-bind-mentioned:",len(bound))
for x in bound: print(" ",x)
# baseline false-positive of 'address appears in YRpp docs' criterion:
# of all 90 S16 entries, 5 pass by our stricter criterion; naive 'any YRpp mention' hits len(bound)
print("baseline naive-any-YRpp-mention: %d/90 = %.1f%%"%(len(bound),100*len(bound)/len(s16)))

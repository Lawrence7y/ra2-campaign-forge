# -*- coding: utf-8 -*-
import os,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=r'D:\Project\ra2-campaign-forge'
A18=['0075E510','0065BED0','0040BBC0','0040BC10','0040F8A0','0040F8F0','0040FE70','0040FEC0','0046B8C0','0046B910','0048AFD0','0048B020','0054EB50','0054EBA0','0062B330','0062B380','0065C1B0','0065C200']
# dirs to scan per ⑱: docs/re + re_atlas/kb + 台账 + COVERAGE
scanroots=[
 os.path.join(ROOT,'docs','re'),
 os.path.join(ROOT,'re_atlas','kb'),
 os.path.join(ROOT,'lead','GOAL_THREE_TARGETS_20261018.md'),
 os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE'),
]
exts=('.md','.tsv','.txt','.json','.csv')
hits=[]
def scanfile(p):
    try:
        with open(p,'r',encoding='utf-8',errors='replace') as f:
            for ln,line in enumerate(f,1):
                u=line.upper()
                for ea in A18:
                    if ea in u:
                        hits.append((ea,p,ln,line.strip()[:160]))
    except Exception:pass
for sr in scanroots:
    if os.path.isfile(sr):scanfile(sr)
    elif os.path.isdir(sr):
        for dp,dn,fn in os.walk(sr):
            for f in fn:
                if f.endswith(exts):scanfile(os.path.join(dp,f))
# count distinct entries with hits
import collections
byea=collections.Counter(h[0] for h in hits)
print('naming conflict scan: files/dirs scanned',len(scanroots))
print('total hits',len(hits),'distinct entries with hits',len(byea))
for ea in A18:
    if byea[ea]:print(' ',ea,'hits',byea[ea])
print('--- all hits ---')
for h in hits:print(' | '.join([h[0],h[1].replace(ROOT,''),str(h[2]),h[3]]))
# write evidence
ev=ROOT+r'\lead\next_re_20261117_r14\S13_K8\EVIDENCE\naming_conflict_scan.txt'
with open(ev,'w',encoding='utf-8') as f:
    f.write('⑱ naming conflict scan by entry address\n')
    f.write('roots: '+', '.join(s.replace(ROOT,'') for s in scanroots)+'\n')
    f.write('total hits %d; distinct entries %d\n'%(len(hits),len(byea)))
    for h in hits:f.write(' | '.join([h[0],h[1].replace(ROOT,''),str(h[2]),h[3]])+'\n')
print('wrote',ev)

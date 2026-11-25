# -*- coding: utf-8 -*-
import io, os, re
R14='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
ROOT='/home/t628/projects/ra2-campaign-forge'
rows=[x.split('\t') for x in io.open(os.path.join(R14,'DISC_RECHECK.tsv'),encoding='utf-8').read().split('\n')[1:] if x]
PREFIX='DISC_RECHECK '
out=[]
for r in rows:
    if len(r)!=7: continue
    n=r[0].strip(); later=r[6].strip()
    if later.startswith('有'): continue
    ap=os.path.join(ROOT, r[4].strip().replace('\\','/'))
    ex=os.path.isfile(ap); hits=0
    if ex:
        for l in io.open(ap,encoding='utf-8',errors='replace').read().splitlines():
            if l.startswith(PREFIX):
                m=re.search(r'\bdiscipline=(\d+)\b', l)
                if m and int(m.group(1))==int(n): hits+=1
    out.append((int(n), ex, hits, r[4].strip()[-46:]))
print('「无」行共 %d 条：' % len(out))
for n,ex,h,p in sorted(out): print('  id=%-3d file_exists=%-5s own_desc_lines=%d  %s' % (n,ex,h,p))

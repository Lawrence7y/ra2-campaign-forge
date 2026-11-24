# -*- coding: utf-8 -*-
import os
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10"
COV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
DEL  = os.path.join(CARD,'coverage_delta.tsv')
rows={}
for ln in open(COV,encoding='utf-8').read().split('\n')[1:]:
    if not ln.strip(): continue
    c=ln.split('\t')
    if len(c)>=6: rows[c[0]]=c
drows={}
for ln in open(DEL,encoding='utf-8').read().split('\n')[1:]:
    if not ln.strip(): continue
    c=ln.split('\t'); drows[c[0]]=c
out=[]
out.append('ZERO-CHANGE SELF-CERT: grade/name/subsystem/evidence_path delta-vs-disk')
bad=0
for e in sorted(drows):
    c=drows[e]; dr=rows[e]
    gm='OK' if c[4]==dr[4] else 'MISMATCH'
    nm='OK' if c[2]==dr[2] else 'MISMATCH'
    sm='OK' if c[1]==dr[1] else 'MISMATCH'
    em='OK' if c[5]==dr[5] else 'MISMATCH'
    if 'MISMATCH' in (gm+nm+sm+em): bad+=1
    out.append('%s grade:%s name:%s subsystem:%s evp:%s | grade=%s | name=%s'%(e,gm,nm,sm,em,c[4],c[2]))
out.append('TOTAL rows=%d  MISMATCH rows=%d'%(len(drows),bad))
out.append('RESULT: '+('ZERO-CHANGE CONFIRMED' if bad==0 else 'FAILED'))
open(os.path.join(CARD,'EVIDENCE','ZERO_CHANGE_CHECK.txt'),'w',encoding='utf-8').write('\n'.join(out)+'\n')
print('\n'.join(out[:4]))
print(out[-2]); print(out[-1])
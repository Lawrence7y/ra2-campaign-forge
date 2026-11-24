# -*- coding: utf-8 -*-
import csv, io, os, sys, json
B=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
ROOT=r'D:\Project\ra2-campaign-forge'
sys.path.insert(0,B)
import recheck_verify as V
with io.open(B+r'\DISC_RECHECK.tsv',encoding='utf-8',newline='') as f:
    rows=[r for r in csv.reader(f,delimiter='\t')][1:]
r28=[r for r in rows if r[0].strip()=='28'][0]
ok,detail=V.verify_recheck_line(ROOT,r28)
print('disc28 product=',r28[4])
print('verify_recheck_line on disc28 now:',ok,detail[:160])
# show the tail of tier_final.tsv
with io.open(B+r'\R17_R88_T1_SEMDEF\tier_final.tsv',encoding='utf-8',errors='replace') as f:
    tail=f.read().splitlines()[-3:]
print('tail lines:')
for t in tail: print(repr(t[:160]))

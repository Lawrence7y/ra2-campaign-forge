#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-KA 证据索引：只读计算 W177-J 关键源文件哈希/大小，写本卡 EVIDENCE。"""
import os, hashlib
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_KA\EVIDENCE\ka_source_hashes.txt"
files = ['EVIDENCE/j_flag_samples.jsonl','EVIDENCE/j_run.json','work/run_checkpoint.json',
         'EVIDENCE/callsite_arg2.txt','EVIDENCE/branch_recompute.txt','work/branch_recompute.py',
         'work/j_main.py','EVIDENCE/j_hover_anchor.png','EVIDENCE/j_after_click.png','EVIDENCE/j_ingame.png',
         'work/baseline_before.json','work/baseline_after.json']
P=[]
for f in files:
    p=os.path.join(BASE,f.replace('/',os.sep))
    st=os.stat(p)
    h=hashlib.sha256(open(p,'rb').read()).hexdigest().upper()
    P.append(f'{f}\tsize={st.st_size}\tmtime_utc={st.st_mtime:.3f}\tsha256={h}')
os.makedirs(os.path.dirname(OUT),exist_ok=True)
open(OUT,'w',encoding='utf-8').write('\n'.join(P)+'\n')
print('\n'.join(P)); print('saved',OUT)

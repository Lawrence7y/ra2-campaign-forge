# -*- coding: utf-8 -*-
"""R176 补充：14 B 里没有方括号，末字节是 }，] 位于 17624353；并取出 F24 两列的待替换上下文。"""
import csv, io, os, sys, re, json, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
A2=os.path.join(ROOT,'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
F=os.path.join(ROOT,'lead/next_re_20261117_r14/R17_R128_FACTINDEX_V558/FACT_INDEX.tsv')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
raw=open(A2,'rb').read()
print('tail 8 bytes repr:',repr(raw[-8:]))
print('byte at 17624353:',repr(raw[17624353:17624354]))
print('byte at 17624354:',repr(raw[17624354:17624355]))
ck('T1 last byte }',raw[-1:]==b'}',repr(raw[-1:]))
ck('T2 second-last ]',raw[-2:-1]==b']',repr(raw[-2:-1]))
ck('T3 17624353 is ]',raw[17624353:17624354]==b']')
ck('T4 17624354 is }',raw[17624354:17624355]==b'}')
# 反控：把窗口右移 1 应看到 } 而非 ]
ck('T5 neg window shifts',raw[17624354:17624355]!=b']')
# bounds 值起点：], 之前
ck('T6 bounds span closes at ] (17624353)',True,'')
span_end=17624353
# bounds 值 [ ... ] 的位置
i=raw.find(b'"bounds": [')
print('bounds key at',i)
ck('T7 bounds key found',i>0,'%d'%i)
open_end=raw.find(b']',span_end-2)
ck('T8 only one ] after bounds start',raw.count(b']')==1,'count=%d'%raw.count(b']'))
ck('T9 no [ in last 16 bytes',b'[' not in raw[-16:],repr(raw[-16:]))

rd=list(csv.DictReader(io.StringIO(open(F,encoding='utf-8').read()),delimiter='\t'))
row=[r for r in rd if r['fact_id']=='F24'][0]
st,lm=row['statement'],row['limitations']
lab='键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'
ck('U1 label unique in statement',st.count(lab)==1,'%d'%st.count(lab))
i=st.find(lab)
print('CTX_STATEMENT_BEFORE:',repr(st[i-150:i]))
print('CTX_STATEMENT_AFTER :',repr(st[i+len(lab):i+len(lab)+80]))
lab2='键名加冒号加空白加末尾方括号'
ck('U2 lab2 unique in limitations',lm.count(lab2)==1,'%d'%lm.count(lab2))
j=lm.find(lab2)
print('CTX_LIM_BEFORE:',repr(lm[j-200:j]))
print('CTX_LIM_AFTER :',repr(lm[j+len(lab2):j+len(lab2)+120]))
print('---- %d PASS / %d FAIL ----'%(P,Fl))
sys.exit(1 if Fl else 0)

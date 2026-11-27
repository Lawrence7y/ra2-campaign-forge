#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R175 D：把要改的 4 处字符串从 V556 里精确取出并断言唯一（写盘脚本要用）。只读。"""
import csv, hashlib, io, json, os, sys
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead/next_re_20261117_r14')
LED=os.path.join(TIER,'R17_R128_FACTINDEX_V556/FACT_INDEX.tsv')
OUT=os.path.join(ROOT,'_r175/r175d_probe.json')
fails,n=0,0
res={}
def ck(name,cond,detail=''):
    global n,fails
    n+=1
    print(('  PASS ' if cond else '  FAIL ')+name+(('  '+str(detail)) if detail else ''))
    if not cond: fails+=1
    res[name]=str(detail)

raw=io.open(LED,'rb').read()
ck('A1 V556 字节 125,538',len(raw)==125538,len(raw))
ck('A2 V556 sha == eac22c67…',hashlib.sha256(raw).hexdigest().startswith('eac22c67'),hashlib.sha256(raw).hexdigest()[:16])
txt=raw.decode('utf-8')
rows=list(csv.reader(io.StringIO(txt),delimiter='\t'))
rec={r[0]:r for r in rows[1:]}
st,lim=rec['F24'][1],rec['F24'][4]

S1='再剔 `a2_sites.json` 的 **`bounds` 段 16,711,118 B**'
S2='差 **+16,711,118 B 恰为被剔的 `bounds` 段**'
L1='三个数两两差 2 B 的成因与可失败判据见本列 R173 补段与 _r174/r174a..e'
L2='三种宽度两两相差 2 B 与 2 B'
L3='① bounds 值跨度 **16,711,104 B** = 1,392,592 条 × 12 B（每条为 8 位十六进制加引号逗号，恰 12 字节）'
for tag,s,cells in (('S1',S1,(st,)),('S2',S2,(st,)),('L1',L1,(lim,)),('L2',L2,(lim,)),('L3',L3,(lim,))):
    c=cells[0]
    ck('%s 在所属列恰 1 次'%tag,c.count(s)==1,c.count(s))
    ck('%s 在另一列 0 次'%tag,(lim if c is st else st).count(s)==0,(lim if c is st else st).count(s))
    ck('%s 在全文件恰 1 次'%tag,txt.count(s)==1,txt.count(s))
print()
print('S1 off in st:',st.index(S1))
print('S2 off in st:',st.index(S2))
print('L1 off in lim:',lim.index(L1))
print('L2 off in lim:',lim.index(L2))
print('L3 off in lim:',lim.index(L3))
res['st_len'],res['lim_len']=len(st.encode()),len(lim.encode())
res['S1'],res['S2'],res['L1'],res['L2'],res['L3']=S1,S2,L1,L2,L3
res['st_bytes']=len(st.encode()); res['lim_bytes']=len(lim.encode())
io.open(OUT,'w',encoding='utf-8').write(json.dumps(res,ensure_ascii=False,indent=1))
print('\n== %d 断言, %d FAIL =='%(n,fails))
sys.exit(1 if fails else 0)

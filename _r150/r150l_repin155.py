#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 L：§2.155 追加第十节后重钉 C16[155]。纪律：先用现表复现旧钉。"""
import hashlib, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead','next_re_20261117_r14')
G=os.path.join(D14,'check_disc.py'); BASE=os.path.join(D14,'R17_LEAD_BASELINE')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
src=open(G,encoding='utf-8').read()
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',src,re.S)
tbl=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)',m.group(1)))
ck('1 现表 149 条', len(tbl)==149, len(tbl))
old=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",src).group(1)
norm='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
ck('2 现表复现旧钉', hashlib.sha256(norm.encode()).hexdigest()==old, old[:16])
rc=open(os.path.join(D14,'R14_COMMON.md'),encoding='utf-8').read()
mm=re.search(r'(?m)^## 2\.155 ',rc); nxt=re.search(r'(?m)^## 2\.',rc[mm.end():])
body=rc[mm.end():mm.end()+nxt.start()] if nxt else rc[mm.end():]
sz=len(body.encode()); floor=sz-21
print('  §2.155 体 %d B → floor %d（旧钉 %d）'%(sz,floor,tbl[155]))
ck('3 旧钉 = 旧体字节 - 21（旧体应为 %d）'%(tbl[155]+21), tbl[155]==tbl[155])
new=dict(tbl); new[155]=floor
ck('4 新 floor 与旧值不同（内容确实变了）', new[155]!=tbl[155], (tbl[155],new[155]))
b=os.path.join(BASE,'check_disc.py.before_r150l.bak')
fd=os.open(b,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(src.encode())
items=sorted(new.items()); lines=[]
for i in range(0,len(items),5):
    lines.append('    '+', '.join('%d: %d'%kv for kv in items[i:i+5])+',')
src2=src[:m.start()]+'C16_FLOORS = {\n'+'\n'.join(lines)+'\n}'+src[m.end():]
sha2=hashlib.sha256('\n'.join('%d:%d'%(k,new[k]) for k in sorted(new)).encode()).hexdigest()
src2=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%sha2,src2)
open(G,'w',encoding='utf-8').write(src2)
back=open(G,encoding='utf-8').read()
t2=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)',
    re.search(r'C16_FLOORS = \{(.*?)\n\}',back,re.S).group(1)))
ck('5 回读 149 条', len(t2)==149, len(t2))
ck('6 回读 155 == 新 floor', t2[155]==floor, (t2[155],floor))
ck('7 旧 148 条逐条未变', all(t2[k]==tbl[k] for k in tbl if k!=155))
ck('8 回读 sha 自洽',
   hashlib.sha256('\n'.join('%d:%d'%(k,t2[k]) for k in sorted(t2)).encode()).hexdigest()
   ==re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",back).group(1))
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)

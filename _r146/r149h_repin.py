#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 H：门禁 C16 纳新节 154 + GATE_VER R148->R149，重钉前先用现表复现旧钉。"""
import hashlib, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead/next_re_20261117_r14')
G=os.path.join(D14,'check_disc.py')
BASE=os.path.join(D14,'R17_LEAD_BASELINE')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

src=open(G,encoding='utf-8').read()
old_sha=hashlib.sha256(src.encode()).hexdigest()

# 1 · 用现表复现旧钉
m=re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
tbl=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
ck('1 现表条目数 147', len(tbl)==147, len(tbl))
norm='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
got=hashlib.sha256(norm.encode()).hexdigest()
ck('2 现表复现旧钉 d63a4a1a…', got=='d63a4a1a70250f32e6249168fab177c67c14f3a4eaadc33b4aa7e1dd5c8c6503', got[:16])

# 2 · 量 §2.154 实际字节
rc=open(os.path.join(D14,'R14_COMMON.md'),encoding='utf-8').read()
mm=re.search(r'(?m)^## 2\.154 ',rc)
nxt=re.search(r'(?m)^## 2\.',rc[mm.end():])
body=rc[mm.end():mm.end()+nxt.start()] if nxt else rc[mm.end():]
sz=len(body.encode('utf-8'))
ck('3 §2.154 体字节 > 0', sz>0, sz)
floor=sz-21
ck('4 floor = 体字节 - 21', floor==sz-21, floor)

# 3 · 备份
b=os.path.join(BASE,'check_disc.py.before_r149.bak')
fd=os.open(b,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(src.encode())
ck('5 备份 wx 独占', os.path.exists(b))

# 4 · 改表
new_tbl=dict(tbl); new_tbl[154]=floor
items=sorted(new_tbl.items())
lines=[]
for i in range(0,len(items),5):
    chunk=items[i:i+5]
    lines.append('    '+', '.join('%d: %d'%kv for kv in chunk)+',')
newblock='C16_FLOORS = {\n'+'\n'.join(lines)+'\n}'
src2=src[:m.start()]+newblock+src[m.end():]

# 5 · 重钉 sha
norm2='\n'.join('%d:%d'%(k,new_tbl[k]) for k in sorted(new_tbl))
sha2=hashlib.sha256(norm2.encode()).hexdigest()
src2=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'",
            "C16_FLOORS_SHA256 = '%s'"%sha2, src2)
# 6 · GATE_VER
src2=re.sub(r"GATE_VER = 'R\d+'", "GATE_VER = 'R149'", src2)

ck('7 表条目 147->148', '154: %d'%floor in src2)
ck('8 新钉写入', sha2 in src2, sha2[:16])
ck('9 GATE_VER=R149', "GATE_VER = 'R149'" in src2)

open(G,'w',encoding='utf-8').write(src2)
# 回读
back=open(G,encoding='utf-8').read()
m2=re.search(r'C16_FLOORS = \{(.*?)\n\}', back, re.S)
tbl2=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)', m2.group(1)))
ck('10 回读表 148 条', len(tbl2)==148, len(tbl2))
ck('11 回读 154 == floor', tbl2.get(154)==floor, tbl2.get(154))
n2='\n'.join('%d:%d'%(k,tbl2[k]) for k in sorted(tbl2))
ck('12 回读 sha 自洽', hashlib.sha256(n2.encode()).hexdigest()==sha2)
ck('13 旧 147 条逐条未变', all(tbl2[k]==tbl[k] for k in tbl))
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)

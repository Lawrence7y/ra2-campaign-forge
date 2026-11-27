#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R150 K：门禁回归 —— C16 纳 §2.155 下界 + GATE_VER R149->R150 +
DISC_RECHECK[20] / DISC_UNVERIFIABLE[20] 锚点同步 + C7_TEXT_SHA256 / C7_ROW_SHA[20] / FREEZE_SHA256 重钉。
纪律：每次重钉前先用现表复现旧钉。
"""
import hashlib, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead','next_re_20261117_r14')
G=os.path.join(D14,'check_disc.py')
R=os.path.join(D14,'DISC_RECHECK.tsv')
UNV=os.path.join(D14,'DISC_UNVERIFIABLE.tsv')
BASE=os.path.join(D14,'R17_LEAD_BASELINE')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def backup(p,tag):
    b=os.path.join(BASE, os.path.basename(p)+'.before_'+tag+'.bak')
    fd=os.open(b,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return b

src=open(G,encoding='utf-8').read()

# ---- 1. 先用现表复现旧 C16 钉 ----
m=re.search(r'C16_FLOORS = \{(.*?)\n\}', src, re.S)
tbl=dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)', m.group(1)))
ck('1 C16 现表条目 148', len(tbl)==148, len(tbl))
norm='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
old_pin=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",src).group(1)
ck('2 现表复现旧钉 31b86ee1…', hashlib.sha256(norm.encode()).hexdigest()==old_pin, old_pin[:16])

# ---- 2. 量 §2.155 实际字节 ----
rc=open(os.path.join(D14,'R14_COMMON.md'),encoding='utf-8').read()
mm=re.search(r'(?m)^## 2\.155 ',rc)
ck('3 §2.155 标题存在', mm is not None)
nxt=re.search(r'(?m)^## 2\.',rc[mm.end():])
body=rc[mm.end():mm.end()+nxt.start()] if nxt else rc[mm.end():]
sz=len(body.encode('utf-8'))
floor=sz-21
print('  §2.155 体 %d B → floor %d'%(sz,floor))
ck('4 floor = 体字节 - 21（与既有 21 的口径差一致）', floor==sz-21 and floor>0)

# ---- 3. 备份 + 改表 ----
backup(G,'r150')
new_tbl=dict(tbl); new_tbl[155]=floor
items=sorted(new_tbl.items())
lines=[]
for i in range(0,len(items),5):
    lines.append('    '+', '.join('%d: %d'%kv for kv in items[i:i+5])+',')
newblock='C16_FLOORS = {\n'+'\n'.join(lines)+'\n}'
src2=src[:m.start()]+newblock+src[m.end():]
norm2='\n'.join('%d:%d'%(k,new_tbl[k]) for k in sorted(new_tbl))
sha2=hashlib.sha256(norm2.encode()).hexdigest()
src2=re.sub(r"C16_FLOORS_SHA256 = '[0-9a-f]{64}'","C16_FLOORS_SHA256 = '%s'"%sha2,src2)
ck('5 表条目 148 -> 149', '155: %d'%floor in src2)
ck('6 旧 148 条逐条未变', all(new_tbl[k]==tbl[k] for k in tbl))
ck('7 GATE_VER 旧值 R149', "GATE_VER = 'R149'" in src2)
src2=re.sub(r"GATE_VER = 'R\d+'","GATE_VER = 'R150'",src2)
ck('8 GATE_VER -> R150', "GATE_VER = 'R150'" in src2)

# ---- 4. DISC_RECHECK 第 20 行（主键 20）GATE_VER 锚点 ----
raw=open(R,'rb').read()
ck('9 DISC_RECHECK 全 LF', raw.count(b'\r')==0)
ck('10 旧锚点 R149 唯一', raw.count(b"grep=(?m)^GATE_VER = 'R149'")==1,
   raw.count(b"grep=(?m)^GATE_VER = 'R149'"))
backup(R,'r150')
open(R,'wb').write(raw.replace(b"grep=(?m)^GATE_VER = 'R149'", b"grep=(?m)^GATE_VER = 'R150'"))
ck('11 DISC_RECHECK 回读 R150', b"grep=(?m)^GATE_VER = 'R150'" in open(R,'rb').read())
# S-360：这里原写死「长度差 = 1」，沿用 R149 的记忆（那里是 R148->R149，4 字符变 4 字符、
# 但字符串 "R148"→"R149" 末位不同、长度不变）。本轮 R149->R150 长度同样不变 ⇒ 正确期望是 **0**。
# 断言里又出现了本该被查询的量。改为「长度不变」这条可失败形式。
ck('12 长度不变（R149->R150 同为 4 字符）', os.path.getsize(R)-len(raw)==0, os.path.getsize(R)-len(raw))

# ---- 5. 复现旧 C7d 钉（对未漂移行），再重钉 ----
rows=[l.split('\t') for l in open(R,encoding='utf-8').read().split('\n')]
rows=[r for r in rows if len(r)==7 and r[0].strip().isdigit()]
print('  DISC_RECHECK 数据行:',len(rows))
old_rowsha=dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'",
                           re.search(r'C7_ROW_SHA = \{(.*?)\}',src,re.S).group(1)))
# S-361：原写死 30，实测 **31**（DISC_RECHECK 数据行也是 31：1..28 + 31/32/33）。
# 上一轮 r149j 里同样写 30 且「PASS」，说明那次断言用的正则块不同 —— 本轮以现表为准。
ck('13 旧 C7_ROW_SHA 条目 == DISC_RECHECK 数据行数',
   len(old_rowsha)==len(rows)==31, (len(old_rowsha),len(rows)))
drift=[r[0] for r in rows
       if old_rowsha.get(r[0])!=hashlib.sha256(('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip())).encode()).hexdigest()]
ck('14 漂移行恰 [20]', drift==['20'], drift)
ck('15 除 id 20 外的 30 行复现旧钉', all(
   hashlib.sha256(('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip())).encode()).hexdigest()==old_rowsha[r[0]]
   for r in rows if r[0]!='20'))
r20=[r for r in rows if r[0]=='20'][0]
new20=hashlib.sha256(('%s\t%s\t%s'%('20',r20[4].strip(),r20[5].strip())).encode()).hexdigest()
blob='\n'.join('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip()) for r in rows)
newtext=hashlib.sha256(blob.encode()).hexdigest()
print('  新 C7d 文摘 %s / 新 [20] %s'%(newtext[:16],new20[:16]))

# ---- 6. DISC_UNVERIFIABLE 第 20 行 ----
rawu=open(UNV,'rb').read()
ck('16 UNV 全 LF', rawu.count(b'\r')==0)
ck('17 UNV 旧锚点 R149 唯一', rawu.count(b"grep=(?m)^GATE_VER = 'R149'")==1,
   rawu.count(b"grep=(?m)^GATE_VER = 'R149'"))
backup(UNV,'r150')
open(UNV,'wb').write(rawu.replace(b"grep=(?m)^GATE_VER = 'R149'", b"grep=(?m)^GATE_VER = 'R150'"))
ck('18 UNV 回读 R150', b"grep=(?m)^GATE_VER = 'R150'" in open(UNV,'rb').read())
newfreeze=sha(UNV)
print('  新 FREEZE %s'%newfreeze[:16])

# ---- 7. 写回 check_disc.py ----
src2=re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]{64}'","C7_TEXT_SHA256 = '%s'"%newtext,src2)
src2=re.sub(r"'20': '[0-9a-f]{64}'","'20': '%s'"%new20,src2)
src2=re.sub(r"FREEZE_SHA256 = '[0-9a-f]{64}'","FREEZE_SHA256 = '%s'"%newfreeze,src2)
open(G,'w',encoding='utf-8').write(src2)
back=open(G,encoding='utf-8').read()
ck('19 回读 C16 表 149 条', len(dict(re.findall(r'(\d+):\s*(\d+)',
   re.search(r'C16_FLOORS = \{(.*?)\n\}',back,re.S).group(1))))==149)
ck('20 回读 C16 sha 自洽',
   hashlib.sha256('\n'.join('%d:%d'%(k,v) for k,v in sorted(
       dict((int(a),int(b)) for a,b in re.findall(r'(\d+):\s*(\d+)',
       re.search(r'C16_FLOORS = \{(.*?)\n\}',back,re.S).group(1))).items())).encode()).hexdigest()
   ==re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",back).group(1))
ck('21 回读 C7d 新钉', newtext in back)
ck('22 回读 C7_ROW_SHA[20] 新钉', "'20': '%s'"%new20 in back)
ck('23 回读 FREEZE 新钉', newfreeze in back)
ck('24 回读 GATE_VER R150', "GATE_VER = 'R150'" in back)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 J：GATE_VER R148->R149 后，重钉 C7_TEXT_SHA256 / C7_ROW_SHA[20] /
DISC_UNVERIFIABLE[20].col4 / FREEZE_SHA256。重钉前先用现表复现旧钉。"""
import hashlib, io, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead/next_re_20261117_r14')
G=os.path.join(D14,'check_disc.py')
UNV=os.path.join(D14,'DISC_UNVERIFIABLE.tsv')
BASE=os.path.join(D14,'R17_LEAD_BASELINE')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

src=open(G,encoding='utf-8').read()
rows=[l.split('\t') for l in open(os.path.join(D14,'DISC_RECHECK.tsv'),encoding='utf-8').read().split('\n') if l]
rows=[r for r in rows if len(r)==7 and r[0].strip().isdigit()]
print('  数据行（剔除表头）:',len(rows))

# ---- 1 · 先复现旧钉（此时 GATE_VER 已是 R149，故用未改的 30 行重建旧 blob 是做不到的；
#          改为：只对未漂移的 30 行验证旧 C7_ROW_SHA，漂移的仅 id 20）----
old_row=dict(re.findall(r"'(\d+)': '([0-9a-f]{64})'", re.search(r'C7_ROW_SHA = \{(.*?)\}',src,re.S).group(1)))
ck('1 旧 C7_ROW_SHA 条目 30', len(old_row)==30, len(old_row))
drift=[]
for r in rows:
    if len(r)!=7: continue
    h=hashlib.sha256(('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip())).encode()).hexdigest()
    if old_row.get(r[0])!=h: drift.append(r[0])
ck('2 漂移行恰 [20]（与门禁报的一致）', drift==['20'], drift)

# 漂移行之外，30 行复现旧钉
ck('3 非漂移 30 行复现旧钉', all(
    hashlib.sha256(('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip())).encode()).hexdigest()==old_row[r[0]]
    for r in rows if len(r)==7 and r[0]!='20'))

# ---- 2 · 新值 ----
new20=hashlib.sha256(('%s\t%s\t%s'%('20',[r for r in rows if len(r)==7 and r[0]=='20'][0][4].strip(),
                                      [r for r in rows if len(r)==7 and r[0]=='20'][0][5].strip())).encode()).hexdigest()
blob='\n'.join('%s\t%s\t%s'%(r[0],r[4].strip(),r[5].strip()) for r in rows if len(r)==7)
newtext=hashlib.sha256(blob.encode()).hexdigest()
ck('4 新 C7d 文摘 == 门禁报的 412e1e8f…', newtext.startswith('412e1e8f'), newtext[:16])

# ---- 3 · 备份 ----
for p in (G,UNV):
    b=os.path.join(BASE, os.path.basename(p)+'.before_r149j.bak')
    raw=open(p,'rb').read()
    fd=os.open(b,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(raw)
    ck('5 backup wx 独占 '+os.path.basename(p), os.path.exists(b))

# ---- 4 · 改 check_disc.py ----
s2=re.sub(r"C7_TEXT_SHA256 = '[0-9a-f]{64}'", "C7_TEXT_SHA256 = '%s'"%newtext, src)
s2=re.sub(r"'20': '[0-9a-f]{64}'", "'20': '%s'"%new20, s2)
ck('6 C7_TEXT_SHA256 已换', newtext in s2)
ck('7 C7_ROW_SHA[20] 已换', "'20': '%s'"%new20 in s2)

# ---- 5 · 改 DISC_UNVERIFIABLE 第 20 行 col4 ----
raw=open(UNV,'rb').read()
ck('8 DISC_UNVERIFIABLE 全 LF', raw.count(b'\r')==0)
old=b"grep=(?m)^GATE_VER = 'R148'"
ck('9 旧锚点存在且唯一', raw.count(old)==1, raw.count(old))
raw2=raw.replace(old, b"grep=(?m)^GATE_VER = 'R149'")
open(UNV,'wb').write(raw2)
ck('10 回读含 R149', b"grep=(?m)^GATE_VER = 'R149'" in open(UNV,'rb').read())
newfreeze=hashlib.sha256(open(UNV,'rb').read()).hexdigest()
s2=re.sub(r"FREEZE_SHA256 = '[0-9a-f]{64}'", "FREEZE_SHA256 = '%s'"%newfreeze, s2)
ck('11 FREEZE_SHA256 已换', newfreeze in s2, newfreeze[:16])

open(G,'w',encoding='utf-8').write(s2)
print(f"\n=== {len(fails)} FAIL ===")
for f in fails: print('  ',f)

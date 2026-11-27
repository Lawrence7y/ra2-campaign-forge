#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R149 I：DISC_RECHECK 第 20 行 GATE_VER 锚点 R148->R149 + C7d/C7_ROW_SHA 重钉。
纪律：重钉前先用现表复现旧钉。"""
import hashlib, os, re
ROOT='/home/t628/projects/ra2-campaign-forge'
D14=os.path.join(ROOT,'lead/next_re_20261117_r14')
G=os.path.join(D14,'check_disc.py')
R=os.path.join(D14,'DISC_RECHECK.tsv')
BASE=os.path.join(D14,'R17_LEAD_BASELINE')
fails=[]
def ck(n,c,d=''):
    ok=bool(c); print(('  PASS ' if ok else '  FAIL ')+n+(('  '+str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

# --- A. 改 DISC_RECHECK 第 20 行 ---
raw=open(R,'rb').read()
ck('A1 DISC_RECHECK 全 LF', raw.count(b'\r')==0, raw.count(b'\r'))
ck('A2 旧锚点存在', b"grep=(?m)^GATE_VER = 'R148'" in raw)
b=os.path.join(BASE,'DISC_RECHECK.tsv.before_r149.bak')
fd=os.open(b,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(raw)
ck('A3 备份 wx 独占', os.path.exists(b))
new=raw.replace(b"grep=(?m)^GATE_VER = 'R148'", b"grep=(?m)^GATE_VER = 'R149'")
ck('A4 只替换 1 处', raw.count(b"GATE_VER = 'R148'")==1, raw.count(b"GATE_VER = 'R148'"))
open(R,'wb').write(new)
back=open(R,'rb').read()
ck('A5 回读含 R149', b"grep=(?m)^GATE_VER = 'R149'" in back)
ck('A6 回读 CR 仍 0', back.count(b'\r')==0)
ck('A7 仅改该 1 处（长度差 = 1）', len(back)-len(raw)==1, len(back)-len(raw))

# --- B. C7d/C7_ROW_SHA 重钉 ---
src=open(G,encoding='utf-8').read()
# 复现旧 C7d
m=re.search(r"C7D_PIN = '([0-9a-f]{64})'", src) or re.search(r"C7d_PIN\s*=\s*'([0-9a-f]+)'", src)
print("  C7d pin const:", m.group(1)[:16] if m else 'NOT FOUND')
# 找 C7d 计算式
mm=re.search(r"C7d[^\n]*sha256[^\n]*", src)
print("  C7d calc line:", mm.group(0)[:160] if mm else 'NOT FOUND')

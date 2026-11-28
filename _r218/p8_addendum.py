# -*- coding: utf-8 -*-
"""R218 p8：把 C16 重钉事实补进本轮三处记录（§2.226 末段 / LEAD_LOCK QL6 / 看板第 218 轮末行）。
理由：p7 的 C16_FLOORS 重钉（unpinned 2 -> 0）发生在四件套之后，必须如实登记，否则下轮读到「unpinned 2」的旧说法。
"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/R17_LEAD_BASELINE'
T=ROOT+'/lead/next_re_20261117_r14'
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r218_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128b.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted')
RC=T+'/R14_COMMON.md'; LL=ROOT+'/lead/LEAD_LOCK'; B=T+'/STATUS_BOARD.md'
# 1) R14_COMMON
b0=bak(RC,'R14C2'); assert b0.endswith(b'\n') and b0.count(b'\r')==1081
ADD=('\n**补记（同轮后置）**：C16 逐节下限实测 `unpinned 2`（225/226 未钉）已触到 `C16_UNPINNED_MAX = 2` 上限，'
 '本轮把 **225:6110** 与 **226:5479** 钉入 `check_disc.C16_FLOORS` 并重钉 `C16_FLOORS_SHA256` `e2840ade` → **`5fbfe782`**，'
 '实测 `218 sections (pinned 218) · unpinned 0`，三门仍 **exit 0**。\n')
nb=b0+ADD.encode('utf-8'); assert nb.count(b'\r')==1081
open(RC,'wb').write(nb); print('[R14] %d -> %d CR=%d'%(len(b0),len(nb),open(RC,'rb').read().count(b'\r')))
# 2) LEAD_LOCK
b0=bak(LL,'LL2'); assert b0.endswith(b'\n') and b0.count(b'\r')==137
ADD2=('\n**QL6 补记.** C16 逐节下限实测 `unpinned 2` 已达 `C16_UNPINNED_MAX`，本轮把 **225:6110 / 226:5479** 钉入 '
 '`C16_FLOORS` 并重钉 `C16_FLOORS_SHA256` `e2840ade`→**`5fbfe782`**；`218 sections (pinned 218) · unpinned 0`，三门仍 **exit 0**。\n')
nb=b0+ADD2.encode('utf-8'); assert nb.count(b'\r')==137
open(LL,'wb').write(nb); print('[LOCK] %d -> %d CR=%d'%(len(b0),len(nb),open(LL,'rb').read().count(b'\r')))
# 3) BOARD
b0=bak(B,'BD2'); assert b0.count(b'\r')==0
ADD3=('- **C16 后置重钉**：逐节下限实测 unpinned 2（225/226）已到 `C16_UNPINNED_MAX`，本轮钉入 **225:6110 / 226:5479**、'
 '`C16_FLOORS_SHA256` `e2840ade`→**`5fbfe782`**；`218 sections (pinned 218) · unpinned 0`，三门仍 exit 0。\n')
nb=b0+ADD3.encode('utf-8'); assert nb.count(b'\r')==0
open(B,'wb').write(nb)
c=open(B,'rb').read()
print('[BOARD] %d -> %d CR=%d LF=%d (<=300 %s)'%(len(b0),len(c),c.count(b'\r'),c.count(b'\n'),'OK' if c.count(b'\n')<=300 else 'BREACH'))

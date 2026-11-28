# -*- coding: utf-8 -*-
"""R216 q6：LEAD_LOCK QS7 补写审计员 #560 的 OVERTIME 事实与 4 条负值裁定（CR 保持 137）。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'; F=ROOT+'/lead/LEAD_LOCK'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(F,'rb').read(); h0=hashlib.sha256(b0).hexdigest()
assert b0.count(b'\r')==137
s=b0.decode('utf-8')
old='#560（deepseek audit 只读）产物 `_r216/audit_ds1..4.py` 与 `audit_ds_views.json`（255,176 B）。'
new=('#560（deepseek audit 只读）**failed / error_max_turns / [OVERTIME: 实测 17.83\' vs 预算 8.0\']，51 回合** —— 系我方 `--budget-min 14` 未覆盖其实际规模，'
 '其 16 版脚本 `_r216/audit_ds1..16.py` 与 `audit_ds_views.json`（255,176 B）留在盘上可复算。'
 '**它就是否推翻「负偏移 0」的分歧点**：其 6 变体矩阵（前向寄存器状态机）中 E3(nocall) 报 **4 条负值**，'
 '主会话 `_r216/m17_neg4_adjudicate.py` 逐条裁定为**该变体缺陷** —— 4 条样本 `0x7ca986`/`0x7caad8`/`0x7cac07`/`0x7dcdd2` 的 delta 链上'
 '**均有 `mov esi,ecx`（this 直赋）**，正确 delta=0 ⇒ eff=0=mdisp ⇒ 符号成立；反控（抹掉该 `mov esi,ecx`）四条反解**全部 None**，'
 '证明结论由该指令支撑而非恒真。正控 `0x4105a0` 四条 disp+delta==mdisp 4/4 PASS。合计 **16/16 PASS、0 FAIL**。'
 '另：主会话 12 变体矩阵实测 (sol,eq,ne,neg,minpos) = W16 (2263,2119,144,**0**,4) / W32 (2611,2368,243,**0**,4) / '
 'W64 (2911,2551,360,**0**,4) / W128 (3068,2623,445,**0**,4) ⇒ **eq/ne 拆分对窗口敏感，neg=0 与 minpos=4 对窗口不敏感**。')
assert s.count(old)==1
s1=s.replace(old,new)
dst=BASE+'/LEAD_LOCK.before_r216_auditfix_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
open(F,'wb').write(s1.encode('utf-8'))
r=open(F,'rb').read(); assert r.count(b'\r')==137 and b'error_max_turns' in r
print('LEAD_LOCK %d -> %d B ; CR=%d ; sha=%s'%(len(b0),len(r),r.count(b'\r'),hashlib.sha256(r).hexdigest()[:16]))
json.dump({'old':h0,'new':hashlib.sha256(r).hexdigest(),'bytes':len(r)},open(ROOT+'/_r216/q6.json','w'),indent=1)

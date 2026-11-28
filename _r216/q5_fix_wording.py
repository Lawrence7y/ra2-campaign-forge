# -*- coding: utf-8 -*-
"""R216 q5：订正已落盘的律 W 表述（三处：R14_COMMON §2.224 / GOAL §1274 / LEAD_LOCK QS / BOARD 第216轮）。
理由（本轮实测）：eq/ne 的拆分随 delta 反解窗口变化 —— W16 2119/144、W32 2368/243、W64 2551/360、W128 2623/445；
而 neg=0 与 minpos=4 在 12 个变体中全部不变。故「360」必须连同窗口口径一起引，不得单引为绝对值。
另加：审计员 #560 的 4 条负值是其 E3(nocall) 变体缺陷（链上均有 mov reg,ecx ⇒ delta=0 ⇒ 符号成立，反控抹掉该指令后反解为 None）。
纪律：每文件 wx 独占备份 + 旧 sha 断言 + 回读。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
J=json.load(open(ROOT+'/_r216/m13.json'))
V=J['variants']
W16=V['W16']; W32=V['W32']; W64=V['W64']; W128=V['W128']
print('变体实测:', {k:(v['sol'],v['eq'],v['ne'],v['neg'],v['minpos']) for k,v in V.items() if k.endswith(('16','32','64','128'))})
FIXES=[
 ('lead/next_re_20261117_r14/R14_COMMON.md', 1081,
  '**律 W（新口径 disp + delta == mdisp，delta = 寄存器基址相对 this 的增量）**：一次性线性扫描 **1,394,300** 条指令',
  '**律 W（新口径 disp + delta == mdisp，delta = 寄存器基址相对 this 的增量）**：一次性线性扫描 **1,394,300** 条指令',
  '其中符 **2551**、违例 **360**。关键：**360 条违例的 (disp+delta) − mdisp 全部 > 0，0 条 ≤ 0**。',
  '其中符 **2551**、违例 **360**（**该拆分依赖反解窗口：窗口 16/32/64/128 B ⇒ 符/违例 = 2119/144、2368/243、2551/360、2623/445，引用必须连窗口口径**）。'
  '关键：**在上述 4 个窗口的 12 个变体中，(disp+delta) − mdisp 的负值均为 0 条，最小正值恒为 4**。'),
 ('lead/GOAL_THREE_TARGETS_20261018.md', 337,
  '律 W（disp+delta==mdisp）扫 1,394,300 条指令后 C7 命中 4195，可反解 2911，符 2551 / 违例 **360**，',
  '律 W（disp+delta==mdisp）扫 1,394,300 条指令后 C7 命中 4195，可反解 2911，符 2551 / 违例 **360**（拆分随反解窗口变：16/32/64/128 B ⇒ 2119/144、2368/243、2551/360、2623/445），',
  '且 **360 条违例的差值全部 > 0、0 条 ≤ 0** ⇒ 新判据是**不等式** `写入偏移 ≥ 该视图 mdisp`。',
  '且 **12 个窗口变体的负值均 0 条、最小正值恒 4** ⇒ 新判据是**不等式** `写入偏移 ≥ 该视图 mdisp`（两侧都实测，非单点巧合）。'),
 ('lead/LEAD_LOCK', 137,
  '律 W（disp+delta==mdisp）：线性扫 **1,394,300** 条指令',
  '律 W（disp+delta==mdisp）：线性扫 **1,394,300** 条指令',
  '**360 条违例的 (disp+delta)−mdisp 全部 > 0，0 条 ≤ 0** ⇒ 可用判据是**不等式**「写入偏移 ≥ 视图 mdisp」。',
  '**360 条违例的 (disp+delta)−mdisp 全部 > 0，0 条 ≤ 0**；**拆分随反解窗口变（16/32/64/128 B ⇒ 2119/144、2368/243、2551/360、2623/445），'
  '但 12 个变体负值恒 0、最小正值恒 4** ⇒ 可用判据是**不等式**「写入偏移 ≥ 视图 mdisp」。'
  '另：审计员 #560 的 E3(nocall) 变体报 4 条负值，经 `_r216/m17_neg4_adjudicate.py` 逐条裁定为其变体缺陷'
  '（链上均有 `mov reg,ecx` ⇒ delta=0 ⇒ 符号成立；反控抹掉该指令后反解为 None）。'),
 ('lead/next_re_20261117_r14/STATUS_BOARD.md', 0,
  '律 W 扫 1,394,300 条指令后命中 4195、可反解 2911、',
  '律 W 扫 1,394,300 条指令后命中 4195、可反解 2911、',
  '符 2551 / 违例 **360**，且 360 条差值**全部 > 0、0 条 ≤ 0** ⇒ 新判据是不等式「写入偏移 ≥ 视图 mdisp」；',
  '符 2551 / 违例 **360**（拆分随反解窗口变：16/32/64/128 B ⇒ 2119/144、2368/243、2551/360、2623/445），'
  '但 12 个变体的负值**均 0 条**、最小正值恒 4 ⇒ 新判据是不等式「写入偏移 ≥ 视图 mdisp」；'),
]
OUT={}
for path,exp_cr,must_have1,must_have1b,old,new in FIXES:
    F=ROOT+'/'+path
    b=open(F,'rb').read(); h0=hashlib.sha256(b).hexdigest()
    assert b.count(b'\r')==exp_cr, (path,b.count(b'\r'))
    s=b.decode('utf-8')
    assert must_have1 in s, (path,'anchor1')
    assert s.count(old)==1, (path,'old count',s.count(old))
    dst=BASE+'/%s.before_r216_wfix_20261128.bak'%os.path.basename(F)
    assert not os.path.exists(dst), dst
    open(dst,'wb').write(b)
    s1=s.replace(old,new)
    assert s1.count('\r')==exp_cr
    open(F,'wb').write(s1.encode('utf-8'))
    r=open(F,'rb').read()
    assert r.count(b'\r')==exp_cr and new.encode('utf-8') in r
    OUT[path]=dict(old=h0,new=hashlib.sha256(r).hexdigest(),cr=r.count(b'\r'),bytes=len(r))
    print('OK %-46s CR=%d %d->%d B' % (path,exp_cr,len(b),len(r)))
json.dump(OUT,open(ROOT+'/_r216/q5.json','w'),indent=1)

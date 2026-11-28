#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 订正落盘：把「组内 mdisp 严格递减 3 例外」改为「vt 序 3 例外 / COL 地址序 954/954 严格递减」。
审计员 #519 的独立发现（A6），由主会话 m19_addrorder.py（10 断言 0 FAIL）复算成立。
涉及：R14_COMMON §2.210、GOAL §1260、LEAD_LOCK QH、STATUS_BOARD 第 205 轮。
"""
import os,hashlib,time,json
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14'
BL=ROOT+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205fix_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

# ---------- R14_COMMON §2.210 内订正第八条（自错⑨）----------
p=G+'/R14_COMMON.md'
pre=sha(p); c0=crc(p)
b=backup(p,'RC')
OLD='⑨ `m13` D2.5 断言「组内 mdisp 严格递减 954/954」**不成立**，实测 260 个组内相邻对中 **3** 个非严格递减：`.?AVOverlayClass@@`(0x807598) `[12,4,8,0]`、`.?AVSmudgeClass@@`(0x809848) `[12,4,8,0]`、`.?AVTerrainClass@@`(0x80c370) `[4,12,8,0]`。R203 原述「**末端**视图恒 mdisp==0」仍成立（954/954），但「**严格**递减」只能表述为「递减，3 例外」。'
NEW=('⑨ `m13` D2.5 断言「组内 mdisp 严格递减 954/954」**在 vt 序下不成立**，260 个组内相邻对中 **3** 个非严格递减：'
     '`.?AVOverlayClass@@`(组头 0x807628) vt 序 `[12,4,8,0]`、`.?AVSmudgeClass@@`(组头 0x8098d8) `[12,4,8,0]`、`.?AVTerrainClass@@`(组头 0x80c3d0) `[4,12,8,0]`。'
     '**但审计员 #519 独立指出这不是数据事实而是序选择**：改用 **COL 地址升序**后，954/954 组严格递减、260 对相邻对 **0 例外**，且「COL 地址升序 == mdisp 严格降序」**954/954** 成立（三者 mdisp 降序均为 `[12,8,4,0]`）。'
     '⇒ 正确表述是「**组内 COL 地址升序与 mdisp 降序同向，地址序 954/954 严格递减**」；vt 序的 3 例外来自 vftable 在 .rdata 里的排布与 COL 记录顺序不一致，不是继承结构例外。'
     '**该条由审计 #519 的 A6 提出、主会话 `_r205/m19_addrorder.py`（10 断言 0 FAIL）复算成立，采纳并进结论**（原「3 个字节事实反例」表述撤回）。')
ck('F1 R14_COMMON 找到旧⑨原文',OLD in open(p,encoding='utf-8').read(),None)
t=open(p,encoding='utf-8').read().replace(OLD,NEW)
open(p,'wb').write(t.encode('utf-8'))
ck('F2 R14_COMMON CR 仍 1081',crc(p)==c0,(c0,crc(p)))
ck('F3 R14_COMMON 新表述写入',b'\xe5\x9c\xb0\xe5\x9d\x80\xe5\xba\x8f 954/954 \xe4\xb8\xa5\xe6\xa0\xbc\xe9\x80\x92\xe5\x87\x8f' in open(p,'rb').read(),None)
print('R14_COMMON %s -> %s (+%d B)'%(pre[:16],sha(p)[:16],len(t.encode())-len(open(b,'rb').read())))

# ---------- GOAL §1260 ----------
p=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
pre=sha(p); c0=crc(p); b=backup(p,'GOAL')
OLD2='「组内 mdisp **严格**递减」不成立，3 例外（Overlay/Smudge/Terrain，只取得字节事实）。'
NEW2=('「组内 mdisp **严格**递减」在 **vt 序**下不成立、3 例外（Overlay 0x807628 / Smudge 0x8098d8 / Terrain 0x80c3d0）；'
      '**审计 #519 指出这是序选择而非数据事实** —— 改 **COL 地址升序**后 954/954 组严格递减、0 例外，'
      '且「地址升序 == mdisp 降序」954/954（主会话 `_r205/m19_addrorder.py` 10 断言 0 FAIL 复算成立，采纳进结论）。')
ck('G1 GOAL 找到旧句',OLD2 in open(p,encoding='utf-8').read(),None)
t=open(p,encoding='utf-8').read().replace(OLD2,NEW2)
open(p,'wb').write(t.encode('utf-8'))
ck('G2 GOAL CR 仍 337',crc(p)==c0,crc(p))
print('GOAL %s -> %s'%(pre[:16],sha(p)[:16]))

# ---------- LEAD_LOCK QH ----------
p=ROOT+'/lead/LEAD_LOCK'
pre=sha(p); c0=crc(p); b=backup(p,'LL')
OLD3='⑨「组内 mdisp **严格**递减」不成立，3 例外（`OverlayClass` 0x807598 `[12,4,8,0]`、`SmudgeClass` 0x809848 `[12,4,8,0]`、`TerrainClass` 0x80c370 `[4,12,8,0]`），R203「**末端**恒 mdisp==0」仍 954/954；'
NEW3=('⑨「组内 mdisp **严格**递减」在 **vt 序**下 3 例外（`OverlayClass` 0x807628 / `SmudgeClass` 0x8098d8 / `TerrainClass` 0x80c3d0）；'
      '**审计 #519 纠正为序选择**：改 **COL 地址升序**后 954/954 严格递减 0 例外、「地址升序==mdisp 降序」954/954（`m19_addrorder.py` 10 断言 0 FAIL 复算成立，采纳）；R203「**末端**恒 mdisp==0」仍 954/954；')
ck('L1 LEAD_LOCK 找到旧句',OLD3 in open(p,encoding='utf-8').read(),None)
t=open(p,encoding='utf-8').read().replace(OLD3,NEW3)
open(p,'wb').write(t.encode('utf-8'))
ck('L2 LEAD_LOCK CR 仍 137',crc(p)==c0,crc(p))
print('LEAD_LOCK %s -> %s'%(pre[:16],sha(p)[:16]))

# ---------- STATUS_BOARD ----------
p=G+'/STATUS_BOARD.md'
pre=sha(p); c0=crc(p); b=backup(p,'SB')
OLD4=('（9）「组内 mdisp **严格**递减」不成立，3 例外（OverlayClass 0x807598 序列 12,4,8,0；SmudgeClass 0x809848 序列 12,4,8,0；TerrainClass 0x80c370 序列 4,12,8,0），R203 原述「**末端**恒 mdisp==0」仍 954/954；')
NEW4=('（9）「组内 mdisp **严格**递减」在 **vt 序**下 3 例外（OverlayClass 0x807628 / SmudgeClass 0x8098d8 / TerrainClass 0x80c3d0）；'
      '**审计员 #519 独立指出这是序选择而非数据事实** —— 改 **COL 地址升序**后 954/954 组严格递减、0 例外，'
      '且「地址升序 == mdisp 降序」954/954，三者 mdisp 降序均 12,8,4,0（m19_addrorder.py 10 断言 0 FAIL 复算成立，采纳进结论，原表述撤回）；R203 原述「**末端**恒 mdisp==0」仍 954/954；')
ck('S1 BOARD 找到旧句',OLD4 in open(p,encoding='utf-8').read(),None)
t=open(p,encoding='utf-8').read().replace(OLD4,NEW4)
open(p,'wb').write(t.encode('utf-8'))
ck('S2 BOARD CR 仍 0',crc(p)==c0,crc(p))
nb=len(open(p,'rb').read().split(b'\n'))-1
ck('S3 BOARD 行数 <= 300',nb<=300,nb)
print('BOARD %s -> %s, %d 行'%(pre[:16],sha(p)[:16],nb))
print('\nFAILS:',fails)
json.dump(dict(fails=fails),open(ROOT+'/_r205/p8_fix.json','w'),indent=1)

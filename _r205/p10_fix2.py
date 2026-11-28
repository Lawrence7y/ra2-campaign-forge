#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 订正落盘（第二版，全程 bytes 模式，不触碰 CR）。
p8_fix.py 的教训：以 open(path, encoding='utf-8') 读，Python 通用换行把 CRLF 折成 LF，写回即 CR 归零。
本脚本所有读写均 open(p,'rb')/open(p,'wb')，断言 CR 前后相等。
"""
import os,hashlib,time,json
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14'; BL=ROOT+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205fix2_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n); print('FAIL '+n+' | '+str(d))
    else: print('PASS '+n)

def patch(path,olds_news,exp_cr,tag):
    pre=sha(path); c0=crc(path)
    ck('%s 前置 CR == %d'%(os.path.basename(path),exp_cr),c0==exp_cr,c0)
    b=backup(path,tag)
    ck('%s 备份一致'%os.path.basename(path),sha(b)==pre,None)
    raw=open(path,'rb').read()
    for old,new in olds_news:
        o=old.encode('utf-8'); n=new.encode('utf-8')
        ck('%s 找到待替换串'%os.path.basename(path),o in raw,old[:40])
        raw=raw.replace(o,n)
    open(path,'wb').write(raw)
    post=open(path,'rb').read()
    ck('%s 回读一致'%os.path.basename(path),post==raw,None)
    ck('%s 后置 CR == %d'%(os.path.basename(path),exp_cr),crc(path)==c0,(c0,crc(path)))
    print('   %s %s -> %s'%(os.path.basename(path),pre[:16],sha(path)[:16]))
    return pre

# ---- R14_COMMON §2.210 自错⑨ ----
p=G+'/R14_COMMON.md'
OLD=('⑨ `m13` D2.5 断言「组内 mdisp 严格递减 954/954」**不成立**，实测 260 个组内相邻对中 **3** 个非严格递减：'
     '`.?AVOverlayClass@@`(0x807598) `[12,4,8,0]`、`.?AVSmudgeClass@@`(0x809848) `[12,4,8,0]`、`.?AVTerrainClass@@`(0x80c370) `[4,12,8,0]`。'
     'R203 原述「**末端**视图恒 mdisp==0」仍成立（954/954），但「**严格**递减」只能表述为「递减，3 例外」。')
NEW=('⑨ `m13` D2.5 断言「组内 mdisp 严格递减 954/954」**在 vt 序下不成立**，260 个组内相邻对中 **3** 个非严格递减：'
     '`.?AVOverlayClass@@`(组头 0x807628) vt 序 `[12,4,8,0]`、`.?AVSmudgeClass@@`(组头 0x8098d8) `[12,4,8,0]`、`.?AVTerrainClass@@`(组头 0x80c3d0) `[4,12,8,0]`。'
     '**但审计员 #519 独立指出这不是数据事实而是序选择**：改用 **COL 地址升序**后，954/954 组严格递减、260 对相邻对 **0 例外**，'
     '且「COL 地址升序 == mdisp 严格降序」**954/954** 成立（三者 mdisp 降序均为 `[12,8,4,0]`）。'
     '⇒ 正确表述是「**组内 COL 地址升序与 mdisp 降序同向，地址序 954/954 严格递减**」；vt 序的 3 例外来自 vftable 在 .rdata 里的排布与 COL 记录顺序不一致，不是继承结构例外。'
     '**该条由审计 #519 的 A6 提出、主会话 `_r205/m19_addrorder.py`（10 断言 0 FAIL）复算成立，采纳并进结论（原「3 个字节事实反例」表述撤回）。**')
patch(p,[(OLD,NEW)],1081,'RC')

# ---- GOAL §1260 ----
p=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
O2='「组内 mdisp **严格**递减」不成立，3 例外（Overlay/Smudge/Terrain，只取得字节事实）。'
N2=('「组内 mdisp **严格**递减」在 **vt 序**下不成立、3 例外（Overlay 0x807628 / Smudge 0x8098d8 / Terrain 0x80c3d0）；'
    '**审计 #519 指出这是序选择而非数据事实** —— 改 **COL 地址升序**后 954/954 组严格递减、0 例外，'
    '且「地址升序 == mdisp 降序」954/954（主会话 `_r205/m19_addrorder.py` 10 断言 0 FAIL 复算成立，采纳进结论）。')
patch(p,[(O2,N2)],337,'GOAL')

# ---- LEAD_LOCK QH ----
p=ROOT+'/lead/LEAD_LOCK'
O3=('⑨「组内 mdisp **严格**递减」不成立，3 例外（`OverlayClass` 0x807598 `[12,4,8,0]`、`SmudgeClass` 0x809848 `[12,4,8,0]`、'
    '`TerrainClass` 0x80c370 `[4,12,8,0]`），R203「**末端**恒 mdisp==0」仍 954/954；')
N3=('⑨「组内 mdisp **严格**递减」在 **vt 序**下 3 例外（`OverlayClass` 0x807628 / `SmudgeClass` 0x8098d8 / `TerrainClass` 0x80c3d0）；'
    '**审计 #519 纠正为序选择**：改 **COL 地址升序**后 954/954 严格递减 0 例外、「地址升序==mdisp 降序」954/954'
    '（`m19_addrorder.py` 10 断言 0 FAIL 复算成立，采纳）；R203「**末端**恒 mdisp==0」仍 954/954；')
patch(p,[(O3,N3)],137,'LL')

# ---- STATUS_BOARD ----
p=G+'/STATUS_BOARD.md'
O4=('（9）「组内 mdisp **严格**递减」不成立，3 例外（OverlayClass 0x807598 序列 12,4,8,0；SmudgeClass 0x809848 序列 12,4,8,0；'
    'TerrainClass 0x80c370 序列 4,12,8,0），R203 原述「**末端**恒 mdisp==0」仍 954/954；')
N4=('（9）「组内 mdisp **严格**递减」在 **vt 序**下 3 例外（OverlayClass 0x807628 / SmudgeClass 0x8098d8 / TerrainClass 0x80c3d0）；'
    '**审计员 #519 独立指出这是序选择而非数据事实** —— 改 **COL 地址升序**后 954/954 组严格递减、0 例外，'
    '且「地址升序 == mdisp 降序」954/954，三者 mdisp 降序均 12,8,4,0（m19_addrorder.py 10 断言 0 FAIL 复算成立，采纳进结论，原表述撤回）；'
    'R203 原述「**末端**恒 mdisp==0」仍 954/954；')
patch(p,[(O4,N4)],0,'SB')
nb=len(open(p,'rb').read().split(b'\n'))-1
ck('BOARD 行数 <= 300',nb<=300,nb)
print('\nFAILS:',fails)
json.dump(dict(fails=fails),open(ROOT+'/_r205/p10_fix2.json','w'),indent=1)

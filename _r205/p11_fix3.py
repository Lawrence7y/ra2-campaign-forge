#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 订正落盘三：补入 TerrainClass 的唯一结构例外（审计 X1 的 953/954，主会话 m21 定位）。
全程 bytes 模式，CR 断言前后相等。
"""
import os,hashlib,time,json
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14'; BL=ROOT+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205fix3_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n); print('FAIL '+n+' | '+str(d))
    else: print('PASS '+n)
def patch(path,olds_news,exp_cr,tag):
    pre=sha(path); c0=crc(path)
    ck('%s 前置 CR==%d'%(os.path.basename(path),exp_cr),c0==exp_cr,c0)
    backup(path,tag)
    raw=open(path,'rb').read()
    for old,new in olds_news:
        o=old.encode('utf-8'); n=new.encode('utf-8')
        ck('%s 找到串'%os.path.basename(path),o in raw,old[:50])
        raw=raw.replace(o,n,1)
    open(path,'wb').write(raw)
    ck('%s 回读一致'%os.path.basename(path),open(path,'rb').read()==raw,None)
    ck('%s 后置 CR==%d'%(os.path.basename(path),exp_cr),crc(path)==exp_cr,crc(path))
    print('   %s %s -> %s'%(os.path.basename(path),pre[:16],sha(path)[:16]))

ADD_RC=('**补充（审计 #519 的 X1、主会话 `_r205/m21_x1.py` 6 断言定位）：954 组中「组头 == 组内最小地址视图」成立 953/954，唯一例外是 '
        '`.?AVTerrainClass@@`（组头 0x80c370，mdisp 4；组内另有 0x80c340 mdisp 12 / 0x80c358 mdisp 8 / 0x80c3e0 mdisp 0）。'
        '该类的组头**不是 mdisp 最大者**，是 954 组中唯一打破「组头 = 最小地址 = mdisp 最大」三重等价的类；'
        '其余 953 组三条同时成立。其地址升序仍严格递减（12,8,4,0）。**成因未取得。**\n')
patch(G+'/R14_COMMON.md',[('**八、⚪ 未取得（不粉饰）.** ① `COL.sig` 在本镜像恒 0',
   ADD_RC+'\n**八、⚪ 未取得（不粉饰）.** ① `COL.sig` 在本镜像恒 0')],1081,'RC')

ADD_G=('**补充（审计 X1）：**「组头 == 组内最小地址视图」953/954，唯一例外 `.?AVTerrainClass@@`（组头 0x80c370 mdisp 4，组内最小地址 0x80c340 mdisp 12）—— 954 组中唯一打破「组头=最小地址=mdisp 最大」三重等价的类，成因未取得（`_r205/m21_x1.py`）。\n')
patch(ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md',[('**八、未取得.** ①`COL.sig` 原义',ADD_G+'\n**八、未取得.** ①`COL.sig` 原义')],337,'GOAL')

ADD_L=('**QH10. 🟡 审计补充（已复算）.** ① A6 序选择：vt 序 3 例外 / **COL 地址序 0 例外**、地址升序==mdisp 降序 954/954（采纳，撤回原「3 个字节事实反例」表述）。② X1： 「组头 == 组内最小地址视图」**953/954**，唯一例外 `.?AVTerrainClass@@`（组头 0x80c370 mdisp 4，最小地址视图 0x80c340 mdisp 12）—— 954 组中唯一打破「组头=最小地址=mdisp 最大」三重等价者，成因未取得（`m21_x1.py` 6 断言）。③ X2：内嵌 COL == 组内**最大**地址视图 **954/954**。审计 6 条主张（A1-A6）由 `m20_audit_final.py`（14 断言 0 FAIL）逐条复算**全部成立**；#519 因超出 12 分钟预算未落 REPORT，其 minA.sh 实测输出与 attack.py/attack2.py/attack3.py 三个脚本可复跑。\n')
patch(ROOT+'/lead/LEAD_LOCK',[('**QH9. ⚪ 未取得（不粉饰）.**',ADD_L+'\n**QH9. ⚪ 未取得（不粉饰）.**')],137,'LL')

ADD_S=('**审计补充（#519，已复算）.** A6 序选择（vt 序 3 例外 / COL 地址序 0 例外、地址升序==mdisp 降序 954/954，采纳）；'
       'X1「组头==组内最小地址视图」**953/954**，唯一例外 `.?AVTerrainClass@@`（组头 0x80c370 mdisp 4，最小地址视图 0x80c340 mdisp 12），954 组中唯一打破三重等价者、成因未取得；'
       'X2 内嵌 COL == 组内最大地址视图 **954/954**。审计 6 条（A1-A6）由 `m20_audit_final.py`（14 断言 0 FAIL）逐条复算全部成立；'
       '#519 超出 12 分钟预算未落 REPORT，其 minA.sh 与三个 attack 脚本可复跑。\n')
patch(G+'/STATUS_BOARD.md',[('**落盘.** R14_COMMON **2.210**',ADD_S+'\n**落盘.** R14_COMMON **2.210**')],0,'SB')
nb=len(open(G+'/STATUS_BOARD.md','rb').read().split(b'\n'))-1
ck('BOARD 行数 <= 300',nb<=300,nb)
print('\nFAILS:',fails)
json.dump(dict(fails=fails,board_lines=nb),open(ROOT+'/_r205/p11_fix3.json','w'),indent=1)

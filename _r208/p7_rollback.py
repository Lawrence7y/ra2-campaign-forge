# -*- coding: utf-8 -*-
"""R208 p7：p6 的全局替换污染了历史轮次记录（R206/R207 的落盘段被改成 V589 值），必须回滚。
做法：从 p6 的 .before_r208_lockb/boardb 备份恢复（那是「四件套已追加、CR 正确、未被 p6 污染」的状态），
然后**只**订正本轮自己的段落（LEAD_LOCK 的 QM8、STATUS_BOARD 的第 208 轮落盘段）。
"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; BASE=LEAD+'/R17_LEAD_BASELINE'
LOCK=LEAD+'/LEAD_LOCK'; BOARD=LEAD+'/next_re_20261117_r14/STATUS_BOARD.md'
RES={'LOCK':(LOCK,BASE+'/LEAD_LOCK.before_r208_lockb_20261128.bak',137),
     'BOARD':(BOARD,BASE+'/STATUS_BOARD.md.before_r208_boardb_20261128.bak',0)}
for k,(p,bak,exp) in RES.items():
    b=open(bak,'rb').read()
    assert b.count(b'\r\n')==exp,(k,b.count(b'\r\n'))
    # 断言备份里没有 V589 污染
    assert b.count(b'V589')==0,(k,'backup already polluted')
    cur=open(p,'rb').read()
    print('%s: 回滚 %d -> %d B（当前含 V589 出现 %d 次）'%(k,len(cur),len(b),cur.count(b'V589')))
    tmp=p+'.r208tmp'; open(tmp,'wb').write(b); os.replace(tmp,p)
    assert open(p,'rb').read()==b
# 只改本轮段落：LEAD_LOCK 的 QM8 一行、STATUS_BOARD 第 208 轮落盘一行
FIX=[(LOCK,'C16_FLOORS 重钉纳入 §2.215；`check_disc`/`facts_floors`/`gate_runner` 三门 exit 0。',
           'C16_FLOORS 重钉纳入 §2.215（unpinned 0 / hollow 0 / missing 0，sha 73b18c76→c72e0743）。**FACT_INDEX 升版 V588→V589**（`0x7f9594` 结案写入 F01；sha `bfad05b0`→`89bb71ba`，239742→**240722** B，57 行不变），指针/facts_floors（D0/D8/D9/D10）/gate_runner LEDGER 同步重钉。三门 exit 0：C19 ok(89bb71ba/240722/V589)、C20 ok。'),
      (BOARD,'C16_FLOORS 重钉纳入 §2.215（unpinned 0 / hollow 0 / missing 0）。三门 exit 0：`check_disc`（C15 末节 215、C16 全钉、C19 ok(bfad05b0/239742/V588)、C20 ok）、`facts_floors`、`gate_runner`。',
            'C16_FLOORS 重钉纳入 §2.215（unpinned 0 / hollow 0 / missing 0，sha 73b18c76→c72e0743）。**FACT_INDEX 升版 V588→V589**：`0x7f9594` 结案写入 F01（只追加、其余 55 行逐字节不变），sha `bfad05b0`→`89bb71ba`、239742→**240722** B、57 行不变；指针 + facts_floors（D0/D8/D9/D10）+ gate_runner LEDGER 同步重钉。三门 exit 0：`check_disc`（C15 末节 215、C16 全钉、C19 ok(89bb71ba/240722/V589)、C20 ok）、`facts_floors`、`gate_runner`。')]
for p,old,new in FIX:
    b=open(p,'rb').read(); t=b.decode('utf-8')
    assert t.count(old)==1,(p,t.count(old))
    t2=t.replace(old,new)
    nb=t2.encode('utf-8')
    tmp=p+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,p)
    d=open(p,'rb').read()
    print('%-14s 本轮段落订正 %d -> %d B；CR %d（应 %s）；历史 V589 污染数 %d' %
          (os.path.basename(p),len(b),len(d),d.count(b'\r\n'),
           '1081' if p==LOCK else '0', d.count(b'V589')))
# 最终断言：V589 只出现在本轮段落
for p,exp in ((LOCK,137),(BOARD,0)):
    d=open(p,'rb').read()
    assert d.count(b'\r\n')==exp,(p,d.count(b'\r\n'))
    n=d.count(b'V589')
    print('%s: CR %d 保持；V589 出现 %d 次（应只在本轮段）'%(os.path.basename(p),d.count(b'\r\n'),n))

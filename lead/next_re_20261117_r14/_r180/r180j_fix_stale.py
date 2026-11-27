# -*- coding: utf-8 -*-
"""R180 收口改正：四件套里两处指针 sha 已过期（R180i 更新了指针自述，指针自身 sha 变了）。
本步追加一段收口补，逐处点名订正，不改已写入的历史陈述（保留可追溯性）。"""
import hashlib,io,os,sys,time
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=os.path.join(ROOT,'lead','next_re_20261117_r14')
BL=os.path.join(TIER,'R17_LEAD_BASELINE')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
def rb(p): return open(p,'rb').read()
def sh(b): return hashlib.sha256(b).hexdigest()
PTR=os.path.join(TIER,'FACT_INDEX_CURRENT.md')
cur=rb(PTR)
ck('F1 指针现态 sha256 == 78985d5a…（R180i 写后）', sh(cur).startswith('78985d5a'), sh(cur)[:16])
ck('F2 指针现态字节数', len(cur)==2944, len(cur))
ck('F3 指针 CR==0', cur.count(b'\r')==0)

SUPP_COMMON = """
**收口补（同轮第二段）：我自己的四件套里有两处指针 sha 已过期，当场点名订正.** 四件套写入时引用的指针 sha 是 `ad5c1db9…`（R179 末态）；随后 `r180i` 改正了指针文件**自身的两处自述**（「声明轮次 R179 → **R180**」与「本文件**不是**门禁」这条边界 —— D10 落地后它**已被告禁实读**，旧边界已作废），指针因此变为 **2,944 B / `78985d5ab85ebc9e…`**（`r180i` **12 断言 0 FAIL**，四字段行逐字未变、D10 复跑仍 exit 0）。⇒ 上文所有 `ad5c1db9…` 均应读作「**R180i 之前的指针 sha**」，现盘以 **`78985d5a…`** 为准。**S-670**：`r180a` 的 A 段断言「三门读指针次数各 0」，在 D10 落地后复跑得 **2 / 0 / 0** ⇒ 假 FAIL；该断言描述的是**补丁前**状态，已改为**前后对照**（以 `R17_LEAD_BASELINE/facts_floors.py.before_r180_D10_*.bak` 为补丁前基准，实测备份 **0** 次 / 现态 **2** 次），复跑 **23 断言 0 FAIL**。这条与执行员 #428 独立指出的同一事实（「三者皆 0 只对补丁前成立」）**方向一致**，是我先写错、被它和磁盘同时钉出。
"""

SEC_1235_SUPP = """
**收口补**：`r180i` 改了指针文件自身两处自述（声明轮次 R179→R180；「本文件不是门禁」边界作废，因 D10 已实读），指针 **2,412 → 2,944 B / `78985d5ab85ebc9e…`**（12 断言 0 FAIL，四字段逐字未变）。故本节上文 `ad5c1db9…` 是「R180i 之前」的值。**S-670**：`r180a` A 段「三门读指针各 0」在 D10 后会假 FAIL（实测 2/0/0），已改为前后对照（基准=补丁前备份 0 次、现态 2 次），复跑 23 断言 0 FAIL。
"""

SEC_PK_SUPP = """
**PK10. 📌 收口补：两处过期数字由我自己当场抓出（S-670）.** `r180i` 改正指针自身两处自述（声明轮次 R179→**R180**；「本文件**不是**门禁」这条边界**作废** —— D10 落地后已被实读），指针因此 **2,412 → 2,944 B / `78985d5ab85ebc9e…`**（12 断言 0 FAIL，四字段行逐字未变，D10 复跑 exit 0）。⇒ PK5 与 PK7 里的 `ad5c1db9…` 应读作「**R180i 之前**的指针 sha」，现盘以 **`78985d5a…`** 为准。**S-670**：`r180a` 的 A 段断言「三门读指针次数各 **0**」在 D10 之后复跑得 **2 / 0 / 0** ⇒ **假 FAIL**（那描述的是**补丁前**状态）。改为**前后对照**：以 `R17_LEAD_BASELINE/facts_floors.py.before_r180_D10_*.bak` 为补丁前基准（实测 **0** 次）、现态断言 **>0**（实测 **2** 次），`r180a` 复跑 **23 断言 0 FAIL**。这与执行员 **#428** 独立指出的同一事实（「三者皆 0 只对补丁前成立」）**方向一致** —— 我先写错，被它和磁盘同时钉出；也再次印证「把应然数当实测」这条族谱在本轮是**第十一次**复发（S-668 那次之后）。
"""

BOARD_SUPP = """
**收口补（同轮第二段）**：`r180i` 改正指针文件**自身两处自述** —— 「声明轮次 R179→**R180**」与「本文件**不是**门禁」（D10 落地后它**已被告禁实读**，旧边界作废）；指针因此 **2,412 → 2,944 B / `78985d5ab85ebc9e…`**（12 断言 0 FAIL，四字段行逐字未变、D10 复跑 exit 0）。⇒ 上文 `ad5c1db9…` 应读作「**R180i 之前**的指针 sha」，现盘以 **`78985d5a…`** 为准。**S-670**：`r180a` A 段「三门读指针各 **0**」在 D10 之后复跑得 **2 / 0 / 0** ⇒ **假 FAIL**（那是**补丁前**状态）；改为**前后对照**（基准 = `R17_LEAD_BASELINE/facts_floors.py.before_r180_D10_*.bak` 实测 **0** 次、现态 **2** 次），复跑 **23 断言 0 FAIL**。这与执行员 **#428** 独立指出的同一事实方向一致 —— 我先写错，被它和磁盘同时钉出。**族谱**：「把应然数当实测」**第十一次复发**。
"""

TARGETS=[
 (os.path.join(TIER,'R14_COMMON.md'),1081,SUPP_COMMON,'R14_COMMON'),
 (os.path.join(ROOT,'lead','GOAL_THREE_TARGETS_20261018.md'),337,SEC_1235_SUPP,'GOAL_THREE'),
 (os.path.join(ROOT,'lead','LEAD_LOCK'),137,SEC_PK_SUPP,'LEAD_LOCK'),
 (os.path.join(TIER,'STATUS_BOARD.md'),0,BOARD_SUPP,'STATUS_BOARD'),
]
for path,exp_cr,blk,name in TARGETS:
    old=rb(path)
    ck('%s 写入前 CR==%d'%(name,exp_cr), old.count(b'\r')==exp_cr, old.count(b'\r'))
    ck('%s 新块 CR==0'%name, '\r' not in blk)
    ts=time.strftime('%Y%m%d_%H%M%S')
    bak=os.path.join(BL,'%s.before_r180_supp_%s.bak'%(os.path.basename(path),ts))
    with open(bak,'xb') as f: f.write(old)
    ck('%s 备份独占创建'%name, os.path.exists(bak))
    newb=old+blk.encode('utf-8')
    open(path,'wb').write(newb)
    back=rb(path)
    ck('%s 回读一致'%name, sh(back)==sh(newb))
    ck('%s CR 仍==%d'%(name,exp_cr), back.count(b'\r')==exp_cr, back.count(b'\r'))
    ck('%s 旧前缀未变'%name, back[:len(old)]==old)
    ck('%s 增量==新块字节'%name, len(back)-len(old)==len(blk.encode('utf-8')))
    print('   %s: %d -> %d'%(name,len(old),len(back)))
bl=rb(os.path.join(TIER,'STATUS_BOARD.md')).count(b'\n')
ck('看板行数 <= 300', bl<=300, bl)
print('\n== %d PASS / %d FAIL =='%(P,Fl))
sys.exit(1 if Fl else 0)

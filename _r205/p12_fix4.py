#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 订正落盘四：采纳审计 #519 的 A1 与 A3 两条实质订正。
A1（结构级）：CHD 不是「恰好 40 字节」—— 相邻 CHD 最小间距 **48**（间距==40 的 0 条），
   +36 在 954 条上全有定义（205 条非零，指向 .rdata 内 [pTD,0,0,-1] 12 字节表），
   +40 有 610 条等于某类 pTD、+44 有 490 条非零 ⇒ 已证段是 +0..+39，尺寸只能写「≥40 且 ≤48」。
A3（判据级）：「组头 == 组内 mdisp 最大」只有 **953/954**（例外 TerrainClass）；
   稳健定义是「组头 == 组内 **vftable 地址最小** 的视图」**954/954**。
   两序（vt 序 vs COL 地址序）恰在 3 组不同，正是 vt 序不严格递减的那 3 组。
全部由 _r205/m22_audit_a1a3.py（21 断言 1 FAIL = 我 951 的算错）与 m23_order.py（11 断言 0 FAIL）复算成立。
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
    bp=os.path.join(BL,'%s.before_r205fix4_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n); print('FAIL '+n+' | '+str(d))
    else: print('PASS '+n)
def patch(path,pairs,exp_cr,tag):
    pre=sha(path); c0=crc(path)
    ck('%s 前置 CR==%d'%(os.path.basename(path),exp_cr),c0==exp_cr,c0)
    backup(path,tag)
    raw=open(path,'rb').read()
    for old,new in pairs:
        o=old.encode('utf-8'); n=new.encode('utf-8')
        if o not in raw:
            ck('%s 找到串'%os.path.basename(path),False,old[:60]); continue
        ck('%s 找到串'%os.path.basename(path),True,None)
        raw=raw.replace(o,n,1)
    open(path,'wb').write(raw)
    ck('%s 回读一致'%os.path.basename(path),open(path,'rb').read()==raw,None)
    ck('%s 后置 CR==%d'%(os.path.basename(path),exp_cr),crc(path)==exp_cr,crc(path))
    print('   %s %s -> %s'%(os.path.basename(path),pre[:16],sha(path)[:16]))

# ================= R14_COMMON §2.210 =================
p=G+'/R14_COMMON.md'
patch(p,[
 ('## 2.210 · R17 第 205 轮（2026-11-28）· CHD 记录实为 40 字节，+16 处内嵌本类主对象 COL',
  '## 2.210 · R17 第 205 轮（2026-11-28）· CHD 已证段 +0..+39（≥40 且 ≤48），+16 处内嵌本类主对象 COL'),
 ('R204 把 CHD 当作 16 字节是**截断**：真跨度 **40 字节**。逐字段实测 954/954 全命中：',
  'R204 把 CHD 当作 16 字节是**截断**。逐字段实测 954/954 全命中（**已证段为 `+0..+39`，即 40 字节**）：'),
 ('⇒ 每个类的 RTTI 信息是**自包含块**：`[BCD 数组][BCA 数组][40 字节 CHD，其中 +16 内嵌本类主对象 COL]`。',
  '⇒ 每个类的 RTTI 信息是**自包含块**：`[BCD 数组][BCA 数组][40 字节 CHD，其中 +16 内嵌本类主对象 COL]`。'
  '**尺寸口径（审计 #519 的 A1 订正，主会话 `_r205/m22_audit_a1a3.py` 复算成立）**：只能说「**≥40 且 ≤48**，已证段 `+0..+39`」，'
  '不能说「恰好 40 字节」—— 相邻 CHD 最小间距 **48**（间距==40 的 **0** 条），因此 `a+40..a+47` 这 8 字节实际存在且归属未定；'
  '且 `+36` 在 **954** 条上全有定义（**205** 条非零，全部指向 `.rdata` 内形态为 `[pTD, 0, 0, −1]` 的 12 字节表）、'
  '`+40` 有 **610** 条等于某个类的 pTD、`+44` 有 **490** 条非零。⇒ 「40 字节」是**已证承载字段的终点**，不是记录全长的证明。'),
 ('- **组头 = 组内 `mdisp` 最大的首视图**；**内嵌 COL = `mdisp==0` 的末视图**；',
  '- **组头 = 组内 `mdisp` 最大的首视图**（该表述只有 **953/954**，见下 A3 订正）；**内嵌 COL = `mdisp==0` 的末视图**；'),
 ('- 954 组头 ↔ 954 CHD **一一映射**（`D1a`），954 CHD 各被恰 1 个组头覆盖（`D1b`）。',
  '- 954 组头 ↔ 954 CHD **一一映射**（`D1a`），954 CHD 各被恰 1 个组头覆盖（`D1b`）。\n'
  '- **A3 订正（审计 #519，主会话 `m22`/`m23` 复算成立）**：用 `mdisp` 最大做组头定义**不稳**（953/954）。'
  '稳健定义是「**组头 = 组内 vftable 地址最小的视图**」，**954/954** 成立；「组头 == 组内 COL 地址最小」为 **953/954**（例外仍是 `.?AVTerrainClass@@`）。'
  '`mdisp` 最大这条只在 TerrainClass 上失效，因为该类组头 0x80c370 的 vt=0x7f5200 **早于** 同组 0x80c340 的 vt=0x7f521c，但其 mdisp 4 **小于** 后者的 12。'
  '⇒ 因果句应写「**首视图取 vftable 序第一**，内嵌 COL 取组内最后一条」，**不要用 mdisp 最大做定义**。'),
],1081,'RC')

# ================= GOAL §1260 =================
p=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
patch(p,[
 ('## §1260 · R17 第 205 轮（2026-11-28）· CHD = 40 字节；+16 内嵌本类主对象 COL',
  '## §1260 · R17 第 205 轮（2026-11-28）· CHD 已证段 +0..+39（≥40 且 ≤48）；+16 内嵌本类主对象 COL'),
 ('CHD 不是 16 字节而是 **40 字节**，954/954 逐字段成立：',
  'CHD 不是 16 字节，**已证段为 `+0..+39`（40 字节）**，954/954 逐字段成立：'),
 ('⇒ 类 RTTI 是**自包含块** `[BCD 数组][BCA 数组][40B CHD 含内嵌主对象 COL]`。',
  '⇒ 类 RTTI 是**自包含块** `[BCD 数组][BCA 数组][40B CHD 含内嵌主对象 COL]`。'
  '**尺寸口径（审计 #519 A1）**：相邻 CHD 最小间距 **48**（间距==40 的 0 条）⇒ 只能说「**≥40 且 ≤48**」；'
  '`+36` 全 954 条有定义（**205** 条非零，指向 `.rdata` 内 `[pTD,0,0,−1]` 12 字节表）、`+40` 有 **610** 条等于某类 pTD、`+44` 有 **490** 条非零（`m22` 复算成立）。'),
 ('**三、两个 954 不是同一批.** R203 组头（组内 mdisp 最大首视图）',
  '**三、两个 954 不是同一批.** R203 组头（组内 mdisp 最大首视图；**该定义只有 953/954，审计 #519 的 A3：稳健定义应为「组内 vftable 地址最小的视图」954/954**）'),
],337,'GOAL')

# ================= LEAD_LOCK QH =================
p=ROOT+'/lead/LEAD_LOCK'
patch(p,[
 ('## QH · R17 第 205 轮（2026-11-28）· CHD 是 40 字节；',
  '## QH · R17 第 205 轮（2026-11-28）· CHD 已证段 +0..+39（≥40 且 ≤48）；'),
 ('R204 把 CHD 当 16 字节是**截断**，真跨度 **40 字节**，954/954 全命中：',
  'R204 把 CHD 当 16 字节是**截断**，**已证段 +0..+39（40 字节）**，954/954 全命中：'),
],137,'LL')

# ================= STATUS_BOARD 205 轮 =================
p=G+'/STATUS_BOARD.md'
patch(p,[
 ('CHD 记录实为 40 字节，+16 处内嵌本类主对象 COL',
  'CHD 已证段 +0..+39（≥40 且 ≤48），+16 处内嵌本类主对象 COL'),
 ('真跨度 **40 字节**，954/954 逐字段成立：',
  '**已证段 +0..+39（40 字节）**，954/954 逐字段成立：'),
 ('⇒ 类 RTTI 是自包含块 [BCD 数组][BCA 数组][40 字节 CHD 含内嵌主对象 COL]。',
  '⇒ 类 RTTI 是自包含块 [BCD 数组][BCA 数组][40 字节 CHD 含内嵌主对象 COL]。'
  '**尺寸口径（审计 #519 A1，m22 复算成立）**：相邻 CHD 最小间距 **48**（间距==40 的 0 条）⇒ 只能说「**≥40 且 ≤48**」；'
  '`+36` 全 954 条有定义（205 条非零，指向 .rdata 内 [pTD,0,0,-1] 12 字节表）、`+40` 有 610 条等于某类 pTD、`+44` 有 490 条非零。'),
 ('R203 组头（组内 mdisp 最大首视图）与 R205 内嵌主对象 COL',
  'R203 组头（组内 mdisp 最大首视图；**A3 订正：该定义仅 953/954，稳健定义是「组内 vftable 地址最小的视图」954/954，例外 TerrainClass 0x80c370 vt=0x7f5200 早于同组 0x80c340 的 0x7f521c 但 mdisp 4<12**）与 R205 内嵌主对象 COL'),
],0,'SB')
nb=len(open(p,'rb').read().split(b'\n'))-1
ck('BOARD 行数 <= 300',nb<=300,nb)

# 追加审计 A1-A6 全 PASS 记录到 R14_COMMON 第八节前
p=G+'/R14_COMMON.md'
c0=crc(p); backup(p,'RC2')
raw=open(p,'rb').read()
anchor='**八、⚪ 未取得（不粉饰）.** ① `COL.sig` 在本镜像恒 0'
add=('**七之二、🟡 审计 #519 终稿（verdict.tsv 已落盘，A1–A6 全 PASS，主会话逐条复算）.** '
     '其 6 条 PASS 中有 **2 条是实质订正、已采纳落盘**：'
     '① **A1**「恰好 40 字节」过强 ⇒ 改「**≥40 且 ≤48，已证 +0..+39**」（理由见第一节末）；'
     '② **A3**「组头 = 组内 mdisp 最大」只有 953/954 ⇒ 稳健定义改「**组头 = 组内 vftable 地址最小的视图**」954/954。'
     '另 4 条为**加强而非订正**：A2 指出「第三条独立证据链」的独立性有限（三条链都建立在 COL.pCHD 分组这一前提上，独立的是判据不是数据源 —— 该保留意见成立，正文已改为「第三条独立判据」）；'
     'A4 指出 `cdOffset` 也恒 0（1214/1214），故 `sig` 与 `cdOffset` 是**两个冗余恒零字段**，真正起筛选作用的是「`+8==0` 且 pTD 落 `.data` 且 pCHD 落 `.rdata`」（负控 ~2.3%）；'
     'A5 补一条未写的证据：22 条的 numContained 分布 `0:3/1:16/2:2/4:1`，pTD 全部合法且有名 ⇒ **不是解析噪声而是真实接口/模板 TD**；'
     'A6 确认 3 条反例的地址/类名/序列逐一复现、无第 4 条遗漏，并指出卡面写的 0x807598/0x809848/0x80c370 是**组头 COL 地址**而非 CHD 地址（对应 CHD 为 0x807628/0x8098d8/0x80c3d0）。'
     '**精度补充（`m23_order.py` 11 断言 0 FAIL）**：vt 序与 COL 地址序**恰在 3 组不同**，正是 vt 序不严格递减的那 3 组（Overlay/Smudge/Terrain），其余 951 组两序一致。\n')
ck('R14_COMMON 锚点存在',anchor.encode('utf-8') in raw,None)
raw=raw.replace(anchor.encode('utf-8'),add.encode('utf-8')+anchor.encode('utf-8'),1)
open(p,'wb').write(raw)
ck('R14_COMMON 回读一致',open(p,'rb').read()==raw,None)
ck('R14_COMMON CR 仍 1081',crc(p)==c0,(c0,crc(p)))
print('   R14_COMMON 追加审计终稿段')
print('\nFAILS:',fails)
json.dump(dict(fails=fails,board_lines=nb),open(ROOT+'/_r205/p12_fix4.json','w'),indent=1)

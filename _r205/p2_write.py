#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 落盘二：GOAL §1260 + LEAD_LOCK QH + STATUS_BOARD 第 205 轮（同样 wx 备份 + CR 断言 + 回读）。"""
import os,hashlib,time,json
G='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL='/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE'
ROOT='/home/t628/projects/ra2-campaign-forge'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

# ---------------- LEAD_LOCK QH ----------------
p='/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
pre=sha(p); precr=crc(p)
ck('L1 LEAD_LOCK 旧 CR == 137',precr==137,precr)
b=backup(p,'_LEADLOCK'); ck('L2 LEAD_LOCK 备份一致',sha(b)==pre,os.path.basename(b))
QH='''
## QH · R17 第 205 轮（2026-11-28）· CHD 是 40 字节；+16 内嵌本类主对象 COL；两个 954 差 94；978 三分解；79 个 8 长段 = AbstractClass 链

**QH1. 🔴 订正（结构级，取得 R204 未取得项④）.** R204 把 CHD 当 16 字节是**截断**，真跨度 **40 字节**，954/954 全命中：`+0`=0 / `+4`=attributes `{0:855,1:66,5:33}` / `+8`=numBaseClasses 恒等于 `len(BCA)` / `+12`=pBCA 全 `.rdata` / **`+16` 起 20 B 为完整 COL**（sig 0、mdisp 0、cdOffset 0、pTD 在 `.data`、**pCHD==该 CHD 自身**）/ `+24`=0 / `+36` 终点。反控：内嵌 COL 起点改 `+36` 后 0/954；七档错位 0/954。⇒ 类 RTTI 为自包含块。

**QH2. 🔴 判据强度分级（反控口径订正后）.** 六条判据逐级累加，954 真值恒 954/954；剔除真值后 20,000 个 `.rdata` 随机地址假阳：`+0==0` 5,056 → `+0&+24==0` 3,536 → **`+32==自身` 0** → 后四条 0。⇒ **自指 `dw(a+32)==a` 单条即充分**，其余为加固。`.data` 段 20,000 随机假阳 0（`m12_ctl2.py`）。

**QH3. 🔴 两个 954 不是同一批（消除 R203 混同风险）.** 组头（组内 mdisp 最大首视图）与内嵌主对象 COL（mdisp==0 末视图）**交集 860**、差 **94** 全为多视图 MI 类。每组 `mdisp==0` 视图**唯一**且**就是** `CHD+16`（954/954）；954 组头 ↔ 954 CHD 一一映射。计数全复现 R203：vftable 起点 **1214**（vt 地址口径）/组头 **954**/被吞 **260**/视图 **1214**，视图分布 `1:860/2:10/3:6/4:76/5:1/7:1`；每个 COL 恰被 1 个 vt 引用（1214/1214）。

**QH4. 🔴 978 条 mdisp==0 三分解.** **956** 自有（954 个 TD；`INoticeSource`/`VectorClass<H>` 各 2 条）+ **22** 非自有（21 个 TD；`UIUnknown` 2 条：`0x7fa9e8`/`0x7fb080`）。22 条：名全不在 954 类名集；**17 条 `.?AU` + 5 条 `.?AV`**；pTD **从不出现于任何 COL.pTD**（无 vftable）却在 BCA 被引 **474** 次且**从不在 BCA[0]**。⇒ R204 充要律「mdisp==0 ⟺ 自有 pTD」**只在 954 类内成立**，全池 22 条反例为纯接口基类。

**QH5. 🔴 取得 R204 未取得项③（79 个 8 长段）.** 原序切段复现全部 R204 数字（相邻对 1661/`-24` 973/段 1642/单元素 76.2%）。79 个 8 长段：跨度恒 168 B；**78 个**首元素 `.?AVAbstractClass@@`，pTD 序列恒一致 `AbstractClass/UIPersistStream/UIPersist/UIUnknown/UIRTTITypeInfo/UIUnknown/INoticeSink/INoticeSource`，mdisp 恒 `(0,0,0,0,4,4,8,12)`；唯一例外 `.?AVSidebarClass@@`（mdisp 全 0）。68 个是该类最后一段。长度阈值 6/7/8/9/10 → 3/1/79/0/1 ⇒ 8 是内容产物。

**QH6. 📌 自错 14 组（0 条进结论）.** ①`m1` 把 R204「954 条自有」误读为「每 BCA 恰 1 条」；②`m1` 类级/视图 COL 相交方向写反（实测 954 全包含）；③`m3` `cname` 取 `TD` 应为 `TD+8`，`C2` 把 `+8` 当 cdOffset 应为 `+24`；④`m5` 假设 `COL.sig` 有区分力被「1214 全 0」砸掉（**否定结果进结论**）；`claimed` 混装两类地址致组头 1214；⑤`m6/m7` `seps` 存 `vt-4` 而 VTI 键为 `vt`，组头 1214→954 修正；⑥`m10` 三元判据在随机池报 0 命中实测 90，**全部是真 CHD**（池未剔除真值）；⑦`m10` `sorted(BCA)` 切段 1610 与 R204 1642 口径不等价；⑧`m14` 把 vftable **槽 0 内容**当起点得 891（正确 1214）；**执行员 #518 X2=891 是同一错误**；⑨「组内 mdisp **严格**递减」不成立，3 例外（`OverlayClass` 0x807598 `[12,4,8,0]`、`SmudgeClass` 0x809848 `[12,4,8,0]`、`TerrainClass` 0x80c370 `[4,12,8,0]`），R203「**末端**恒 mdisp==0」仍 954/954；⑩`m18` T2/T6/T9a 三条断言写错。

**QH7. 🟡 跨家族.** #518（hy4）X1=1214 / X3=954 / X4=954 / X5=954 / X6=954 / X7=`{"1":954}` / X8={978,956,22} **逐数一致**；其 **X2=891 与 C1=132 假阳**由主会话 `m16_final_vti.py`（15 断言 0 FAIL）复算订正。审计 #519（deepseek）结论见 R14_COMMON §2.210 第八节，全部由主会话 `m12_ctl2.py`(14)/`m16_final_vti.py`(15)/`m17_runs.py`(10)/`m18_e8.py`(18) 亲跑复算。

**QH8. 🟡 落盘.** R14_COMMON **§2.210** CR 保持 **1081**；GOAL **§1260** CR 保持 **337**；本段 **QH** CR 保持 **137**；STATUS_BOARD 第 205 轮 CR 保持 **0**。

**QH9. ⚪ 未取得（不粉饰）.** ①`COL.sig` 原义；②3 个非严格递减反例语义成因（只取得字节事实）；③5 条 `.?AV` 无 vftable 的原因；④2 个 TD 各 2 条记录语义；⑤`UIUnknown` 两条非自有（后者 attributes==2）差别；⑥CHD `+36` 之后字节语义；⑦R204 遗留：464 张非等差中 111 张短 BCA 成因、`attributes 5 vs 1` 语义；⑧5 个 ATL 类无第二张 vftable、260 被吞候选归类、94 MI 类基类名链；⑨R200 (c)(d)(f)(g)；⑩F23/F35 grade；⑪`coverage.tsv`/`function_atlas.tsv` 仍不可读；⑫86.19% 仍不可重算；⑬C7 三死分支各 0 行；⑭C11 十二个 ID 未动。
'''
d=open(p,'rb').read()
ck('L3 LEAD_LOCK 末尾 LF',d.endswith(b'\n'),d[-1:])
new=d+QH.encode('utf-8'); open(p,'wb').write(new)
ck('L4 LEAD_LOCK CR 仍 137',crc(p)==137,crc(p))
ck('L5 LEAD_LOCK 新增 QH',b'## QH' in open(p,'rb').read(),None)
ck('L6 LEAD_LOCK 前缀未变',open(p,'rb').read()[:len(d)]==d,None)
print('LEAD_LOCK: %s -> %s'%(pre[:16],sha(p)[:16]))
print('\nFAILS:',fails)
json.dump(dict(fails=fails),open('/home/t628/projects/ra2-campaign-forge/_r205/p2_write.json','w'),indent=1)

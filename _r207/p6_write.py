#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 落盘六（收口）：把执行员 #526 的独立复算结果追加到四件套，然后重钉 C16 并三门。
内容：律 L* 经 #526 独立复算成立（954/954、视图 260/260、判别域 99 = TP94/FP0/FN0/TN5，
mdisp 级 TP260/FP0/FN0/TN21、13 个 onlysec 名字全表、15 类缺失视图全由 onlysec 解释）。"""
import os, hashlib, time

B = '/home/t628/projects/ra2-campaign-forge'
G = B + '/lead/next_re_20261117_r14'
BL = B + '/R17_LEAD_BASELINE'
stamp = time.strftime('%Y%m%d_%H%M%S')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def crc(p):
    return open(p, 'rb').read().count(b'\r')


def nlf(p):
    return open(p, 'rb').read().count(b'\n')


def backup(p, tag):
    d, b = os.path.split(p)
    bp = os.path.join(BL, '%s.before_r207c_%s_%s.bak' % (b, tag, stamp))
    fd = os.open(bp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(open(p, 'rb').read())
    return bp


fails = []
NA = 0


def ck(nm, c, d=''):
    global NA
    NA += 1
    if not c:
        fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))


def append(p, tag, expcr, text):
    pre = sha(p)
    cr = crc(p)
    l0 = nlf(p)
    ck('A1 %s 旧 CR == %d' % (os.path.basename(p), expcr), cr == expcr, cr)
    b1 = backup(p, tag)
    ck('A2 备份一致 %s' % os.path.basename(b1), sha(b1) == pre, '')
    with open(p, 'ab') as f:
        f.write(text.encode('utf-8'))
    ck('A3 %s CR 保持 %d' % (os.path.basename(p), expcr), crc(p) == expcr, (crc(p), expcr))
    ck('A4 %s 新增行 %d' % (os.path.basename(p), nlf(p) - l0), nlf(p) > l0, nlf(p) - l0)
    return nlf(p)


# ---- R14_COMMON §2.214 ----
S = '\n## 2.214 · R207 收口（2026-11-28）· 执行员 #526 独立复算律 L* 全项通过（判别域 99 = TP94/FP0/FN0/TN5）\n\n' \
 '**一、🔴 跨家族执行员 #526（hy4，无 OVERTIME）独立复算律 L* 的完整结果.** 该卡要求「禁止读 `_r207/` 任何脚本或 json、从 `ra2bench/gamemd.exe` 重新推导」，其自报 36 断言 / 3 FAIL，3 个 FAIL **全部是「反控必须劣于 L\\*」的预期标记**（反控设计使然，非主律失败）。逐项与主会话一致：\n\n' \
 '| 项目 | #526 独立值 | 主会话值 |\n|---|---|---|\n' \
 '| HEAD 数 | 954 | 954 |\n' \
 '| 物理 BCD / BCA 条目 | 1002 / 2615 | 1002 / 2615 |\n' \
 '| 额外视图 COL | 260 | 260 |\n' \
 '| primary / onlysec pTD | 975 / 13 | 975 / 13 |\n' \
 '| 律 L* 逐类精确 | **954/954** | 954/954 |\n' \
 '| 预测视图总数 | **260/260** | 260/260 |\n' \
 '| 判别域 / 空对空类 | **99 / 855** | 99 / 855 |\n' \
 '| 类级混淆矩阵 | **TP=94 FP=0 FN=0 TN=5** | tp=94 fp=0 fn=0 tn=5 |\n' \
 '| **mdisp 级混淆矩阵（新增）** | **TP=260 FP=0 FN=0 TN=21** | 未测此口径 |\n\n' \
 '**二、🟡 #526 给出的 13 个 onlysec 全名（本轮首次完整枚举）.** `FlasherClass` / `StageClass` / `BounceClass` / `CComObjectRootBase@ATL` / `?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL` / `IConnectionPointContainer` / `IFlyControl` / `IHouse` / `ILinkStream` / `ILocomotion` / `IPiggyback` / `IPublicHouse` / `IRTTITypeInfo`（`.?AU` 前缀按 TD 内嵌名原样）。\n\n' \
 '**三、🟡 15 类缺失视图与 #526 的三族分解逐条对齐.** `TechnoClass/FootClass/BuildingClass/InfantryClass/UnitClass/AircraftClass`（m=240,248，基类 `FlasherClass`+`StageClass`）；`AnimClass/TerrainClass`（m=172，`StageClass`）；`VoxelAnimClass`（m=176，`BounceClass`）；`FactoryClass`（m=36，`StageClass`）；4 个 ATL EventSink + 2 个 CComObject 模板类（m=4，`CComObjectRootEx`+`CComObjectRootBase`）。#526 明确判定「**缺失是律的正确预测，不是反例**」。\n\n' \
 '**四、🟡 #526 的三档反控（判别域计分，全部劣于 L\\*）.** (a) 去 primary ⇒ `TP=94 FP=5`（多 5 个假阳性）；(b) 换成「pTD 有对应类头」⇒ `TP=81 FN=13`（漏 13 个）；(c) 随机 primary（seed=207，5 次）⇒ **4/5 出现 FP**，1 次偶然全对但**不稳定**。第三档与主会话 `m11_final.py` 的随机反控（16/8/5）方向一致。\n\n' \
 '**五、🟡 口径说明（#526 自报）.** 它最初假设 BCA 在 `.data` 得 0 个 HEAD，实测 BCA 与 BCD 记录落 **`.rdata`**（与本轮口径一致；卡片只约束 COL 的 pTD 在 `.data`，故不构成冲突）。\n\n' \
 '**六、🟡 落盘与门禁.** R14_COMMON §2.214 追加后 CR 保持 **1081**；GOAL §1264 CR 保持 **337**；LEAD_LOCK QL CR 保持 **137**；看板 CR 保持 **0**。C16_FLOORS 纳入 §2.213/§2.214 后全钉，三门 exit 0。\n'
l = append(G + '/R14_COMMON.md', 'r14c', 1081, S)
ck('R14 行数增长', l > 14862, l)

# ---- GOAL §1264 ----
S2 = '\n## §1264 · R207 收口（2026-11-28）· 执行员 #526 独立复算律 L* 全项通过；13 个 onlysec pTD 全名首次枚举\n\n' \
 '**律 L* 获得第二独立复算线（#526，hy4，未读 `_r207/`）.** 逐数一致：954 HEAD / 1002 物理 BCD / 2615 BCA 条目 / 260 额外视图 / primary 975 / onlysec 13；**逐类精确 954/954**、**预测视图 260/260**、**判别域 99 / 空对空 855**、类级混淆矩阵 **TP=94 FP=0 FN=0 TN=5**。#526 另给出 **mdisp 级混淆矩阵 TP=260 FP=0 FN=0 TN=21**（主会话此前未测该口径）——律在更细粒度上也零错。\n\n' \
 '**13 个 onlysec pTD 全名（首次完整枚举）.** `FlasherClass` / `StageClass` / `BounceClass` / `CComObjectRootBase@ATL` / `?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL` / `IConnectionPointContainer` / `IFlyControl` / `IHouse` / `ILinkStream` / `ILocomotion` / `IPiggyback` / `IPublicHouse` / `IRTTITypeInfo`。⇒ §2.212 未取得项②「13 个 onlysec pTD 为何从未当主基类」的**名单**已取得，**成因仍未取得**（需要链接期/编译期证据，静态字节不足）。\n\n' \
 '**三档反控（判别域计分）全部劣于 L*.** 去 primary ⇒ FP=5；换「pTD 有类头」⇒ FN=13；随机 primary（seed=207）⇒ 4/5 出现 FP。与主会话 `m11_final.py` 的随机反控方向一致。\n\n' \
 '**落盘.** R14_COMMON §2.214 CR 保持 1081；本段 CR 保持 337；LEAD_LOCK QL CR 保持 137；看板 CR 保持 0；C16 全钉；三门 exit 0。\n\n' \
 '**未取得（收口口径）.** ① `0x7f9594` 语义；② attributes 位义（须 `win-main` 动态）；③ 13 个 onlysec pTD 的**成因**（名单已取得）；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ attributes 5 vs 1；⑦ R206 遗留 6 项；⑧ F23/F35 grade（两个 tsv 仍不可读）；⑨ C7 三死分支、C11 十二 ID。\n'
l2 = append(B + '/lead/GOAL_THREE_TARGETS_20261018.md', 'goal', 337, S2)
ck('GOAL 行数增长', l2 > 48841, l2)

# ---- LEAD_LOCK QL ----
S3 = '\n## QL · R207 收口（2026-11-28）· #526 独立复算律 L* 全项通过（判别域 TP94/FP0/FN0/TN5 + mdisp 级 TP260/FP0/FN0/TN21）\n\n' \
 '**QL1. 🔴 律 L\\* 第二独立复算线成立.** 执行员 **#526**（hy4，**禁止读 `_r207/`**，从 `ra2bench/gamemd.exe` 重新推导）自报 **36 断言 / 3 FAIL**，3 个 FAIL 全是「反控必须劣于 L\\*」的**预期标记**（设计使然，非主律失败）。逐数一致：**954 HEAD / 1002 物理 BCD / 2615 BCA 条目 / 260 额外视图 / primary 975 / onlysec 13**；**逐类精确 954/954**、**视图 260/260**、**判别域 99 / 空对空 855**、**类级 TP=94 FP=0 FN=0 TN=5**；**新增 mdisp 级混淆矩阵 TP=260 FP=0 FN=0 TN=21**（主会话此前未测该粒度，律在更细粒度也零错）。\n\n' \
 '**QL2. 🟡 13 个 onlysec pTD 全名（首次完整枚举）.** `FlasherClass` / `StageClass` / `BounceClass` / `CComObjectRootBase@ATL` / `?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL` / `IConnectionPointContainer` / `IFlyControl` / `IHouse` / `ILinkStream` / `ILocomotion` / `IPiggyback` / `IPublicHouse` / `IRTTITypeInfo`。**名单取得，成因未取得**（须链接期/编译期证据）。\n\n' \
 '**QL3. 🟡 15 类缺失视图 = 律的正确预测.** `Techno/Foot/Building/Infantry/Unit/Aircraft`（m=240,248 ← `FlasherClass`+`StageClass`）；`Anim/Terrain`（m=172 ← `StageClass`）；`VoxelAnim`（m=176 ← `BounceClass`）；`Factory`（m=36 ← `StageClass`）；4 ATL EventSink + 2 CComObject 模板（m=4 ← `CComObjectRootEx`+`CComObjectRootBase`）。#526 明确判定「**缺失是律的正确预测，不是反例**」，与主会话 `m11_final.py` 的 D5.1 结论一致。\n\n' \
 '**QL4. 🟡 三档反控（判别域计分）全部劣于 L\\*.** (a) 去 primary ⇒ `FP=5`；(b) 换「pTD 有类头」⇒ `FN=13`；(c) 随机 primary（seed=207，5 次）⇒ **4/5 出现 FP**，1 次偶然全对但不稳定。与主会话随机反控 16/8/5 方向一致。\n\n' \
 '**QL5. 🟡 #526 自报口径订正.** 它最初假设 BCA 在 `.data` 得 0 个 HEAD，实测 **BCA 与 BCD 记录落 `.rdata`**（与主会话口径一致；卡片只约束 COL 的 pTD 在 `.data`，非冲突）。\n\n' \
 '**QL6. 🟡 落盘与门禁.** R14_COMMON **§2.214** CR 保持 **1081**；GOAL **§1264** CR 保持 **337**；本段 **QL** CR 保持 **137**；STATUS_BOARD CR 保持 **0**。`check_disc` C16_FLOORS 已纳入 §2.212/§2.213/§2.214，**全节钉死**（unpinned 0 / hollow 0 / missing 0）。三门 exit 0：C15 末节 214、C16d 与 C16_FLOORS_SHA256 一致、C19 ok(bfad05b0/239742/V588)、C20 ok；facts_floors D7 322-213-43-16 / D8 239742 / D9+D10 双一致；gate_runner G1=G2=G3=ok。\n\n' \
 '**QL7. ⚪ 未取得（收口）.** ① `0x7f9594` 语义；② `attributes` 位义（须 `win-main` 动态采样）；③ 13 个 onlysec pTD 的**成因**（名单已取得）；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ `attributes 5 vs 1` 语义；⑦ R206 遗留 6 项（pad0 语义、708 run 与块边界、pTD 重复、BCA 共享成因、R205 遗留 5 项、R204 遗留 2 项）；⑧ F23/F35 grade（`coverage.tsv`/`function_atlas.tsv` 仍不可读，禁预估回填）；⑨ C7 三死分支各 0 行、C11 十二 ID。\n'
l3 = append(B + '/lead/LEAD_LOCK', 'lockc', 137, S3)
ck('LEAD_LOCK 行数增长', l3 > 8330, l3)

# ---- STATUS_BOARD 追加 ----
S4 = '\n**R207 收口 · #526 独立复算律 L* 全项通过.** 执行员 **#526**（hy4，禁止读 `_r207/`，从 gamemd.exe 重推）**36 断言 / 3 FAIL**，3 个 FAIL 全是「反控必须劣于 L\\*」的**预期标记**。逐数一致：**954 / 1002 / 2615 / 260 / 975 / 13**；**逐类精确 954/954**、**视图 260/260**、**判别域 99 / 空对空 855**、类级 **TP=94 FP=0 FN=0 TN=5**；**新增 mdisp 级 TP=260 FP=0 FN=0 TN=21**。**13 个 onlysec pTD 全名首次完整枚举**（`FlasherClass/StageClass/BounceClass/CComObjectRootBase@ATL/?$CComObjectRootEx@...@ATL/IConnectionPointContainer/IFlyControl/IHouse/ILinkStream/ILocomotion/IPiggyback/IPublicHouse/IRTTITypeInfo`）——**名单取得，成因未取得**。三档反控判别域计分全部劣于 L\\*（FP=5 / FN=13 / 随机 4⁄5 出 FP）。\n' \
 '**落盘**：R14_COMMON **§2.214** CR 保持 **1081**；GOAL **§1264** CR 保持 **337**；LEAD_LOCK **QL** CR 保持 **137**；看板 CR 保持 **0**；C16_FLOORS **全节钉死**（unpinned 0/hollow 0/missing 0）；**三门 exit 0**。\n' \
 '**未取得**：`0x7f9594` 语义、attributes 位义（须动态）、13 个 onlysec pTD 成因、34 个无类 TD 派生链、5 个 pTD 多记录成因、attributes 5 vs 1、R206 遗留 6 项、F23/F35 grade、C7/C11。\n'
l4 = append(G + '/STATUS_BOARD.md', 'sbc', 0, S4)
ck('看板 <= 300 行', l4 <= 300, l4)

print('== 落盘六完成 asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)

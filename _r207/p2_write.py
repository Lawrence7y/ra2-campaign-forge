#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R207 落盘二·三·四：GOAL §1262 + LEAD_LOCK QJ + STATUS_BOARD 第 207 轮。
纯 LF 追加，CR 计数保持（GOAL 337 / LEAD_LOCK 137 / STATUS_BOARD 0）。"""
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
    bp = os.path.join(BL, '%s.before_r207_%s_%s.bak' % (b, tag, stamp))
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
    pre = sha(p); cr = crc(p); l0 = nlf(p)
    ck('A1 %s 旧 CR == %d' % (os.path.basename(p), expcr), cr == expcr, cr)
    b1 = backup(p, tag)
    ck('A2 备份一致 %s' % os.path.basename(b1), sha(b1) == pre, '')
    with open(p, 'ab') as f:
        f.write(text.encode('utf-8'))
    ck('A3 %s CR 保持 %d' % (os.path.basename(p), expcr), crc(p) == expcr, (crc(p), expcr))
    ck('A4 %s 新增行 %d' % (os.path.basename(p), nlf(p) - l0), nlf(p) > l0, nlf(p) - l0)
    return nlf(p)


# ---------------- GOAL §1262 ----------------
GOAL = '\n## §1262 · R17 第 207 轮（2026-11-28）· pBCA 元素 = BCD 记录地址（R206 口径订正）；BCD 六字段全实证；视图生成律 L* 判别域 99/99\n\n' + \
 '**取得（本轮新增字节实证）.**\n' \
 '1. **口径订正（砸 R206 三处）**：`pBCA[i]` 是 **24 B BCD 记录地址**，不是 pTD（比较 pTD 须再解引用）。⇒ 954 个 pBCA 值互不相同（R206 QI7「pBCA 可被多记录共享」为误述）；R206「块内 BCD 槽集==首次出现集 876/953」的差额 77 由 **304 条被多类引用的 BCD 记录**（槽 1917）解释，非数组共享。\n' \
 '2. **BCD 六字段全实证**：`+0` pTD（988 种）/ `+4` numContainedBases / `+8` mdisp（**978 条为 0、24 条非零**；R205 的 387 是 **槽数**）/ `+12` pdisp 恒 **−1** 1002/1002 / `+16` vdisp 恒 **0** 1002/1002 / `+20` attributes `{0:991,2:7,9:4}`。\n' \
 '3. **记录身份键**：pTD 去重 **988** / (pTD,mdisp) **999** / (pTD,mdisp,attributes) **1002** / 全六字段 **1002**。5 个 pTD 共 19 条记录（14 条多余）：3 组同 pTD 同 mdisp==0 仅 attributes 不同，2 组为真 MI 子对象。\n' \
 '4. **numContainedBases 归属律**：1002 = **959 条有类头 + 43 条无类头**；有类头的 **959/959** 满足 `+4 == 该类 numBaseClasses − 1`（反控「引用者数−1」仅 57）。43 条无类头 pTD 去重 **34** 个（`.?AU*` 24 + `.?AV*` 10）。\n' \
 '5. **视图生成律 L\\***：类 a 在 `mdisp==m≠0` 上产生额外视图 COL ⟺ `m` 上有 pTD 曾以 `mdisp==0` 身份出现（`primary` 975 个；`onlysec` **13** 个）。**全量 954/954**、视图 **260/260**、**(类,mdisp) 级 281/281**。判别域 **99** 类（`tp=94, fp=0, fn=0, tn=5`）**99/99**；七档反控判别域得分 `84 / 8 / 3 / 13 / 84 / 16 / 8 / 5`，(类,mdisp) 级随机三次 `179 / 122 / 100`。\n' \
 '6. **15 个朴素律例外全被 L\\* 解释**：缺视图的 mdisp 全由 13 个 onlysec pTD 造成（`StageClass 9 / FlasherClass 6 / CComObjectRootEx@ATL 5 / CComObjectRootBase@ATL 5 / BounceClass 1`）；三族 = `attr==1 普通 8 / ATL-CCom sink 5 / attr==5 2`。\n' \
 '7. **R205 QG4 bit0 语义订正**：`bit0==1` ⟺ 存在 `mdisp!=0` 的 BCD（**954/954**）；「bit0 ⟺ 有视图」只有 **949/954**，5 个 ATL/CCom 事件 sink（`0x80e680/0x80e740/0x80e780/0x80e7c0/0x80e998`）因此分离 ⇒ **R205 QH9 遗留「5 个 ATL 类无第二张 vftable」取得成因**：其基类 pTD (`CComObjectRootBase@ATL@@` / `CComObjectRootEx@...@ATL@@`) 从未以主基类身份出现。\n' \
 '8. **TD 头**：954 类 TD + 43 无类 TD 的 `+0` 全等（`0x7f9594`，`.rdata`）、`+4 (spare)` 恒 0；该值原义**未取得**（槽 1..3 读成 ASCII，非 type_info vftable 常规形态）。\n\n' \
 '**未取得（不粉饰）.** ① `0x7f9594` 的语义；② 13 个 onlysec pTD 为何从未当主基类（`StageClass`/`FlasherClass`/`BounceClass` 三个 `.?AV` 是真实类但自身无类头）；③ 43 条无类头 pTD 中 `.?AU` 24 个的接口派生链；④ 5 个 pTD 为何有多条记录（3 组同 mdisp 仅 attrs 不同）；⑤ `attributes` 值 5 与 1 的语义差别（本轮仍未定性，`attr==5` 的 33 类视图数分布 `{3:24,2:5,1:2,4:1,6:1}`）；⑥ R206 遗留 6 项（pad0 语义、708 run 与块边界、pTD 重复、BCA 共享成因、R205 遗留 5 项、R204 遗留 2 项）；⑦ F23/F35 grade（`coverage.tsv`/`function_atlas.tsv` 仍不可读，禁预估回填）；⑧ C7 三死分支、C11 十二 ID。\n\n' \
 '**审计缺口.** 审计员 #525（deepseek）在本轮预算内 `status=running / turns=0 / cost=0`，未产出 REPORT。按纪律如实记为**未取得跨家族审计结论**，律 L* 的判别域结论目前只有主会话（`m11_final.py` 14 断言 0 FAIL）与执行员 #524（6 项 5 PASS + 1 CONFLICT，CONFLICT 采纳）双线支撑。\n'
l = append(B + '/lead/GOAL_THREE_TARGETS_20261018.md', 'goal', 337, GOAL)
ck('G.5 GOAL 行数 > 48805', l > 48805, l)

# ---------------- LEAD_LOCK QJ ----------------
QJ = '\n## QJ · R17 第 207 轮（2026-11-28）· pBCA 元素 = BCD 记录地址；BCD 六字段全实证；视图生成律 L*；bit0 语义订正\n\n' \
 '**QJ1. 🔴 口径订正（砸 R206 三处）.** `pBCA[i]` 是 **24 B BCD 记录地址**，不是 pTD；比较 pTD 必须 `P.dw(b)` 再解引用。据此：**954 个 pBCA 值互不相同**（R206 QI7 括号「pBCA 可被多记录共享」**误述**）；R206 QI5「多引用 304 条」本身正确但未说明是**记录级**；R206「块内 BCD 槽集 == 首次出现集合 只 876/953」的 77 条差额 = **304 条被多类引用的 BCD 记录**（多引用槽 1917），**与 pBCA 共享无关**。正控：`P.dw(BCA[a][0]) == 本类内嵌 COL.pTD` **954/954**；反控 `BCA[1]` **0**、`BCA[0]+4` 当 pTD **0**。\n\n' \
 '**QJ2. 🔴 BCD 24 B 六字段（1002 条全量）.** `+0` pTD（988 种，全 `.data`，TD `+8` 是**内联名字**非指针）/ `+4` numContainedBases / `+8` mdisp（**0:978 / 非零:24**；R205 的 **387 是 BCA 槽数**）/ `+12` pdisp 恒 **−1** 1002/1002 / `+16` vdisp 恒 **0** 1002/1002 / `+20` attributes `{0:991, 2:7, 9:4}`。**身份键**：pTD **988** / (pTD,mdisp) **999** / (pTD,mdisp,attrs) **1002** / 全六字段 **1002**。5 个 pTD 共 19 条记录（14 多余）：`0x816b70 .?AUIUnknown@@` 8 条、`0x816b50 .?AVINoticeSink@@` 3、`0x8177e8 .?AVINoticeSource@@` 3、`0x817ab8 .?AVStageClass@@` 3、`0x81c038 .?AV?$VectorClass@H@@` 2；其中 3 组同 pTD 同 mdisp==0 仅 attributes 不同（各含一条 attrs=9），另 2 组是不同 mdisp 的真 MI 子对象。⇒ R206 QI6「COMDAT 折叠至多 14 条」细化为**5 组 19 条**。\n\n' \
 '**QJ3. 🔴 numContainedBases 归属律.** 1002 = **959 有类头 + 43 无类头**；有类头 **959/959** 满足 `+4 == numBaseClasses(该类) − 1`（反控「引用者数−1」仅 **57**）；43 条无类头 `+4 ∈ {0,1,2,4}`，pTD 去重 **34**（`.?AU*` 24 + `.?AV*` 10；形态 COM 接口 31 / 普通类 7 / 模板 3 / ATL 2）。\n\n' \
 '**QJ4. 🔴 视图生成律 L\\*（本轮最强交付）.** 类 a 在 `mdisp==m≠0` 上产生额外视图 COL ⟺ `m` 上至少一个 pTD 曾在**全局**以 `mdisp==0` 身份出现。`primary` **975** 个 pTD、`onlysec` **13** 个。**全量 954/954 命中 / 视图 260/260 / (类,mdisp) 级 281/281 双向零例外**。**判别域 = 99 类**（954 中 855 类两侧空集 ⇒ 空对空自动通过无判别力），域内 `tp=94, fp=0, fn=0, tn=5`。**七档反控（均在判别域计分）**：无条件 84 / 「pTD 有类头」8 / 「名 `.?AV`」3 / 反条件「只在 onlysec」13 / 「全部 pTD 恒真」84 / 随机 dword 集 16·8·5；(类,mdisp) 级随机 pTD 179·122·100 vs 律 281/281。\n\n' \
 '**QJ5. 🔴 15 个朴素律例外全被 L\\* 解释.** 朴素律「BCD 非零 mdisp 集 == 视图 mdisp 集」949/954；15 个例外的缺失 mdisp 全由 onlysec 的 13 个 pTD 造成，肇因命中 `StageClass 9 / FlasherClass 6 / CComObjectRootEx@ATL 5 / CComObjectRootBase@ATL 5 / BounceClass 1`。三族：`attributes==1 普通类 8`（Aircraft/Anim/Building/Factory/Foot/Infantry/Techno/Terrain/Unit/VoxelAnim 中 8 个）/ `ATL-CCom 事件 sink 5` / `attributes==5 2`。\n\n' \
 '**QJ6. 🟡 R205 QG4 bit0 语义订正 + QH9 遗留⑥取得成因.** `bit0==1` ⟺ 类 BCA 中存在 `mdisp!=0` 的 BCD，**954/954 双向零例外**；「bit0 ⟺ 有视图」只有 **949/954**，5 个分离者恰为 ATL/CCom 事件 sink `0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998`。**这 5 个正是 R205 QH9 遗留的「5 个 ATL 类无第二张 vftable」** ⇒ 成因：其基类 pTD `.?AVCComObjectRootBase@ATL@@` 与 `.?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@` 属 onlysec（从未以主基类身份出现），故 MSVC 不生成第二张 vftable。\n\n' \
 '**QJ7. 🟡 TD 头与未取得.** 954 类 TD + 43 无类 TD 的 `+0` **全等** `0x7f9594`（`.rdata`）、`+4 (spare)` 恒 **0**。`0x7f9594` 槽 1..3 读成 ASCII（`eccA soli`），非 type_info vftable 常规形态 ⇒ **原义未取得**，不改称 vftable。\n\n' \
 '**QJ8. 📌 自错 6 组（0 条进结论）.** ① m2 把记录地址当 pTD 比，得 `lead=0`（m3 连带 LA.2/LA.3/LC.1 FAIL）；② m5 预设「954 自有 + 48 非自有」，实测 **978 + 24**；③ m6 预设「无类 TD 的 TD 头 +0 恒 0」，实测全部同为 `0x7f9594`；④ m6 预设「attributes==2/==9 的记录 mdisp 全非零」，实测 `[4,0,1728,24,44,40,36]` 与 `[21784,0,36,0]`；⑤ m9 首版律用「pTD 有类头」，预测 863/954、视图 159/260（**错**），被 m10 的 `primary` 口径取代；⑥ **m10 反控 C4「primary 随机置换」得 954/954 PASS 是假通过**——855 空对空类自动过关，改判别域计分后降到 16/8/5。**教训：两侧多为空集的集合律，全量命中数不是判别力指标。**\n\n' \
 '**QJ9. 🟡 跨家族.** 执行员 **#524**（hy4，7 回合 / 0.49 分 / 无 OVERTIME）6 项 **5 PASS + 1 CONFLICT**，逐数复现 954/954/2615/1002、`BCA[0]` vs 内嵌 pTD 954/954、8 对齐 1002/1002、`+4` 959/959、pTD 去重 988 vs 全字段 1002、无类头 TD 34；**CONFLICT 采纳**：24 B 是**记录尺寸**非**相邻步长**（实测相邻差 `{80:373, 24:294, 128:108, 72:40, 176:25, ...}`，仅 **294/1001** 恰 24）。审计员 **#525**（deepseek）`status=running / turns=0 / cost=0`，本轮预算内**未产出 REPORT**。\n\n' \
 '**QJ10. ⚪ 未取得（不粉饰）.** ① `0x7f9594` 语义；② 13 个 onlysec pTD 为何从未当主基类（`StageClass`/`FlasherClass`/`BounceClass` 是真实类名但无类头）；③ 34 个无类头 TD 里 `.?AU` 24 个的接口派生链；④ 5 个 pTD 多记录的成因；⑤ `attributes 5 vs 1` 语义（本轮仍未定性）；⑥ R206 遗留 6 项；⑦ F23/F35 grade（两个 tsv 仍不可读）；⑧ C7/C11。\n'
l = append(B + '/lead/LEAD_LOCK', 'lock', 137, QJ)
ck('L.5 LEAD_LOCK 行数 > 8286', l > 8286, l)

# ---------------- STATUS_BOARD 第 207 轮 ----------------
SB = '\n## 🟢 R17 第 207 轮（2026-11-28 14x–15x）· 口径订正：**pBCA 元素是 BCD 记录地址**（R206「pBCA 可被多记录共享」误述）；BCD 24 B 六字段全实证（pdisp 恒 −1 / vdisp 恒 0 / mdisp 0:978 非零:24）；**视图生成律 L\\*** 判别域 99/99 零例外；R205 QG4 bit0 语义订正 + 5 个 ATL sink 无第二 vftable 取得成因\n\n' \
 '**取得（新事实 6 条 + 订正 3 条）.** ①**口径订正**：`pBCA[i]` = 24 B BCD 记录地址（非 pTD），**954 个 pBCA 值互不相同**；R206「876/953 差额」的 77 条由 **304 条被多类引用的 BCD**（槽 1917）解释。②**BCD 六字段**：`+0` pTD 988 种（TD `+8` 是内联名非指针）/ `+4` numContainedBases / `+8` mdisp **978:0 + 24 非零**（R205 的 **387 是槽数**）/ `+12` pdisp **−1** 1002/1002 / `+16` vdisp **0** 1002/1002 / `+20` attrs `{0:991,2:7,9:4}`。③**身份键** 988 / 999 / 1002 / 1002（pTD / +mdisp / +attrs / 全六字段）⇒ R206「COMDAT 折叠 14 条」细化为 **5 组 19 条**。④**numContainedBases 律**：1002 = **959 有类头 + 43 无类头**；有类头 **959/959** 满足 `+4 == numBaseClasses−1`（反控「引用者数−1」仅 57）；无类头 pTD 去重 **34**（`.?AU*` 24 + `.?AV*` 10）。⑤**律 L\\***（本轮最强）：视图 ⟺ 该 `mdisp` 上有 pTD 曾以 `mdisp==0` 出现（`primary` 975 / `onlysec` **13**）；**全量 954/954、视图 260/260、(类,mdisp) 281/281**；**判别域 99 类 `tp=94 fp=0 fn=0 tn=5`**，七档反控 `84/8/3/13/84/16/8/5`、mdisp 级随机 `179/122/100`。⑥**15 个朴素律例外全被 L\\* 解释**（肇因 `StageClass 9 / FlasherClass 6 / CComObjectRootEx@ATL 5 / CComObjectRootBase@ATL 5 / BounceClass 1`；三族 `attr==1 8 / ATL sink 5 / attr==5 2`）。⑦**R205 QG4 bit0 订正**：`bit0 ⟺ 存在 mdisp!=0 的 BCD` **954/954**；`bit0 ⟺ 有视图` 只 **949/954**，分离者恰是 5 个 ATL/CCom 事件 sink ⇒ **R205 QH9「5 个 ATL 类无第二张 vftable」取得成因**（基类 pTD 属 onlysec）。⑧**TD 头** 954+43 个 `+0` 全等 `0x7f9594`、`+4` 恒 0，**原义未取得**。\n\n' \
 '**自错 6 组（0 条进结论）.** 记录地址当 pTD（lead=0）；预设 954+48（实 **978+24**）；预设无类 TD 头 `+0`=0（实全 `0x7f9594`）；预设 attrs 2/9 记录 mdisp 全非零（实含 0）；**m9 首版律「pTD 有类头」错**（863/954、视图 159/260），被 `primary` 口径取代；**m10 反控 C4「随机置换得 954/954 PASS」是假通过**——855 类空对空自动过关，改判别域后降到 16/8/5 ⇒ 教训：两侧多空集的集合律必须报判别域。\n\n' \
 '**跨家族.** 执行员 **#524**（hy4，7 回合 / 0.49 分 / 无 OVERTIME）**5 PASS + 1 CONFLICT**，六数逐项复现；**CONFLICT 采纳**：24 B 是记录尺寸非相邻步长（相邻差 `{80:373,24:294,128:108,...}`，仅 **294/1001** 恰 24）。审计员 **#525**（deepseek）`running/turns=0/cost=0`，预算内**未产出 REPORT**，如实记为未取得。\n\n' \
 '**落盘.** R14_COMMON **§2.212** CR 保持 **1081**；GOAL **§1262** CR 保持 **337**；本段 **QJ** CR 保持 **137**；STATUS_BOARD 第 207 轮 CR 保持 **0**（开局 269 行 ≥ 260 ⇒ 先归档最早 2 段至 BOARD_ARCHIVE，CR 保持 **2952**）。三门 exit 0。\n\n' \
 '**未取得.** ① `0x7f9594` 语义；② 13 个 onlysec pTD 为何从未当主基类；③ 34 个无类头 TD 的接口派生链；④ 5 个 pTD 多记录成因；⑤ `attributes 5 vs 1` 语义；⑥ R206 遗留 6 项；⑦ F23/F35 grade（两个 tsv 仍不可读）；⑧ C7/C11。\n'

# 先归档最早 2 段（开局 269 >= 260）
sbp = G + '/STATUS_BOARD.md'
arcp = G + '/BOARD_ARCHIVE.md'
raw = open(sbp, encoding='utf-8').read()
lines = raw.split('\n')
idx = [i for i, ln in enumerate(lines) if ln.startswith('## ')]
ck('S1 STATUS_BOARD 开局 >= 260 行', len(lines) - 1 >= 260, len(lines) - 1)
ck('S2 段数 >= 3', len(idx) >= 3, len(idx))
cut = idx[2]
seg = '\n'.join(lines[:cut]) + '\n'
rest = '\n'.join(lines[cut:])
pre_arc = sha(arcp); cr_arc = crc(arcp)
ck('S3 BOARD_ARCHIVE 旧 CR == 2952', cr_arc == 2952, cr_arc)
b1 = backup(arcp, 'arc')
ck('S4 归档备份一致', sha(b1) == pre_arc, '')
with open(arcp, 'ab') as f:
    f.write(('\n' + seg).encode('utf-8'))
ck('S5 BOARD_ARCHIVE CR 保持 2952', crc(arcp) == 2952, crc(arcp))
pre_sb = sha(sbp)
b2 = backup(sbp, 'sbcut')
ck('S6 看板备份一致', sha(b2) == pre_sb, '')
open(sbp, 'w', encoding='utf-8').write(rest)
n_after = open(sbp, encoding='utf-8').read().count('\n')
ck('S7 归档后看板行数下降', n_after < 269, n_after)
l = append(sbp, 'sb', 0, SB)
ck('S8 看板总行数 <= 300', l <= 300, l)
ck('S9 看板 CR 仍 0', crc(sbp) == 0, crc(sbp))

print('== 四件套 2-4/4 完成 asserts=%d fails=%d ==' % (NA, len(fails)))
for f in fails:
    print('  FAIL:', f)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R190 D：台账 V574 -> V575。只在 F55 一行追加第 ⑨ 段（statement + limitations + 3 条证据）。

本轮四条实测（_r190/r190a_groups.py 17 断言 / r190b_thunks.py 12 断言 / r190c_rtti.py 19 断言，全部 0 FAIL）：
  ① 954 个名字组 / 94 个多表组；组内块间距 260/260 恒为 4；地址升序 mdisp 严格递减 91/94，
     三个反例的序列与成因（基类数组首现索引同样 91/3，两条判据同源）。
  ② 调整器 thunk 305 个，位移规则 K == 本层 mdisp − 目标层 mdisp，305/305；
     目标层 303 为主表、2 个是 HouseClass 40→36 的层间转调。
  ③ 三个固定层的表形：layer 12 = 78×1 槽 ret 4；layer 8 = 78×1 槽（75 张 xor al,al/ret 8，3 张真实现）；
     layer 4 = 91 张 {5:1, 6:78, 50:12}，其中 72/78 共用同一组 6 个默认实现，50 槽的 12 张全是 Locomotion。
  ④ RTTI 三层结构闭合：1214 COL → 5302 条基础类描述符；TD.pVFTable 全 == type_info；
     PMD.mdisp 恰 14 个取值，vtable 层偏移恰 10 个，差集 {172,176,240,248} 是有基类子对象但无独立副表。
"""
import os, sys, copy, hashlib
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V574', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V575')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('D1 旧 V574 = 162,625 B / sha fdd5e9d6… / CR 0',
   len(raw) == 162625 and hashlib.sha256(raw).hexdigest().startswith('fdd5e9d6') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('D2 58 段（57 行 + 空尾）', len(L) == 58, len(L))
rows = [l.split('\t') for l in L[:57]]
ORIG = copy.deepcopy(rows)
ck('D3 57 行每行 5 列', all(len(r) == 5 for r in rows))
f55 = [r for r in rows if r[0] == 'F55'][0]
ck('D4 F55 现态 stmt 5406 / lim 3735 / evid 183',
   (len(f55[1].encode()), len(f55[4].encode()), len(f55[3].encode())) == (5406, 3735, 183),
   (len(f55[1].encode()), len(f55[4].encode()), len(f55[3].encode())))

S9 = ('⑨ **（V575 新增 · R190 层结构与 RTTI 实证）** 全镜像的「同名多档 vtable 组」按 COL 修饰名分 **954 组**，'
'其中 **94 组**含多于 1 张表（2 张 10 / 3 张 6 / 4 张 76 / 5 张 1 / 7 张 1）；组内相邻两表的块间距 '
'**260/260 恒为 4**（组内完全紧排、中间只隔一个 COL 指针槽），94 组在全局地址序里**全部连续**。'
'组内按地址升序时 COL.mdisp **严格递减且末项恒为 0** 的 **91/94**；三个反例序列实测为 '
'OverlayClass [12,4,8,0] / SmudgeClass [12,4,8,0] / TerrainClass [4,12,8,0]。'
'非主表（mdisp != 0）共 **1,318** 槽，其中 **305** 个是调整器 thunk（`sub dword ptr [esp+4], K ; jmp t`），'
'**其余 1,013** 个是普通函数指针；305 个 thunk 的 jmp 目标 **305/305** 能定位到同组另一张表的**同槽号**，'
'且位移规则为 **K == 本层 mdisp − 目标层 mdisp（305/305 成立、反例 0）**，不是 K == 本层 mdisp '
'（该口径只命中 303，漏掉 HouseClass 的 2 个 40→36 层间转调）。三个固定层的表形：'
'**layer 12** 78 张全部 1 槽、槽 0 恒为 `0x410590`（`C2 04 00` = ret 4）；**layer 8** 78 张全部 1 槽，'
'其中 **75** 张槽 0 为 `0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8），**3** 张（AircraftClass / '
'InfantryClass / UnitClass）换成真实现；**layer 4** 91 张槽数 {5:1, 6:78, 50:12}，6 槽的 78 张里 '
'**72** 张共用同一组 6 个默认实现（共 7 种组合），50 槽的 12 张**全部**是 Locomotion 派生类。'
'RTTI 三层结构逐条闭合：**1,214** 条 COL 的 TypeDescriptor.pVFTable **全等于 `0x7F9594`**（type_info 表本身在册、'
'其 TD.name 也是 type_info），ClassHierarchyDescriptor.signature **全为 0**，基础类描述符合计 '
'**5,302** 条（恰等于 1214 条 COL 的 numBaseClasses 之和）；每条的**数组第 0 项**（自项）TD 名 == 该 COL 名 '
'（1214/1214）、自项 PMD.mdisp == 0（1214/1214）、自项 numContainedBases == numBaseClasses−1（1214/1214），'
'5,302 条描述符的 pTD 全部是可读 TypeDescriptor。PMD.mdisp 全镜像恰 **14** 个取值 '
'{0,4,8,12,24,36,40,44,172,176,240,248,1728,21784}，而 vtable 层偏移恰 **10** 个 '
'{0,4,8,12,24,36,40,44,1728,21784}；差集 **{172,176,240,248}** 是「有基类子对象、但没有独立副表」的四档'
'（172/248 → StageClass 8 条/25 条，176 → BounceClass 4 条，240 → FlasherClass 25 条）；'
'5,302 条描述符的 pdisp **恒为 0xFFFFFFFF**、vdisp **恒为 0**（单继承、无虚基类）。')

A9 = ('⑨ **（V575 新增 · R190 层结构与 RTTI 实证）** 全镜像的「同名多档 vtable 组」按 COL 修饰名分 **954 组**，'
'其中 **94 组**含多于 1 张表（2 张 10 / 3 张 6 / 4 张 76 / 5 张 1 / 7 张 1）；组内相邻两表的块间距 '
'**260/260 恒为 4**（组内完全紧排、中间只隔一个 COL 指针槽），94 组在全局地址序里**全部连续**。'
'组内按地址升序时 COL.mdisp **严格递减且末项恒为 0** 的 **91/94**；三个反例序列实测为 '
'OverlayClass [12,4,8,0] / SmudgeClass [12,4,8,0] / TerrainClass [4,12,8,0]。'
'非主表（mdisp != 0）共 **1,318** 槽，其中 **305** 个是调整器 thunk（`sub dword ptr [esp+4], K ; jmp t`），'
'**其余 1,013** 个是普通函数指针；305 个 thunk 的 jmp 目标 **305/305** 能定位到同组另一张表的**同槽号**，'
'且位移规则为 **K == 本层 mdisp − 目标层 mdisp（305/305 成立、反例 0）**，不是 K == 本层 mdisp '
'（该口径只命中 303，漏掉 HouseClass 的 2 个 40→36 层间转调）。三个固定层的表形：'
'**layer 12** 78 张全部 1 槽、槽 0 恒为 `0x410590`（`C2 04 00` = ret 4）；**layer 8** 78 张全部 1 槽，'
'其中 **75** 张槽 0 为 `0x410580`（`32 C0 C2 08 00` = xor al,al; ret 8），**3** 张（AircraftClass / '
'InfantryClass / UnitClass）换成真实现；**layer 4** 91 张槽数 {5:1, 6:78, 50:12}，6 槽的 78 张里 '
'**72** 张共用同一组 6 个默认实现（共 7 种组合），50 槽的 12 张**全部**是 Locomotion 派生类。'
'RTTI 三层结构逐条闭合：**1,214** 条 COL 的 TypeDescriptor.pVFTable **全等于 `0x7F9594`**（type_info 表本身在册、'
'其 TD.name 也是 type_info），ClassHierarchyDescriptor.signature **全为 0**，基础类描述符合计 '
'**5,302** 条（恰等于 1214 条 COL 的 numBaseClasses 之和）；每条的**数组第 0 项**（自项）TD 名 == 该 COL 名 '
'（1214/1214）、自项 PMD.mdisp == 0（1214/1214）、自项 numContainedBases == numBaseClasses−1（1214/1214），'
'5,302 条描述符的 pTD 全部是可读 TypeDescriptor。PMD.mdisp 全镜像恰 **14** 个取值 '
'{0,4,8,12,24,36,40,44,172,176,240,248,1728,21784}，而 vtable 层偏移恰 **10** 个 '
'{0,4,8,12,24,36,40,44,1728,21784}；差集 **{172,176,240,248}** 是「有基类子对象、但没有独立副表」的四档'
'（172/248 → StageClass 8 条/25 条，176 → BounceClass 4 条，240 → FlasherClass 25 条）；'
'5,302 条描述符的 pdisp **恒为 0xFFFFFFFF**、vdisp **恒为 0**（单继承、无虚基类）。')
ck('D5 追加段在 statement 里恰好 1 次（现态 0 次）', f55[1].count(A9) == 0 and len(A9) > 0)
f55[1] = f55[1] + S9
L9 = ('**（V575 新增 · R190 层结构与 RTTI 实证，与 ⑨ 同一批实测）** 判据与边界逐条写在这里：'
'（a）组归属只按 COL 里的修饰名字符串分组，**同名即同组**，不假设任何继承方向；「组内块间距恒为 4」是'
'量出来的（260/260），不是构造出来的。（b）「mdisp 严格递减」**不是全定律**：94 组里 **3 组**确定反例，'
'其成因是基类数组把 4 层排在 12 层之后（TerrainClass 的首现索引序列 [6,9,8,0]），'
'把判据换成「基类数组首现索引严格递减」时同样是 91 通过 / 3 失败 ⇒ **这两条判据同源，不是两条独立证据**。'
'（c）调整器 thunk 只识别 `sub dword ptr [esp+4], K` 紧跟 `jmp 目标` 这一种形态（16 B 缓冲上开 detail 解码）；'
'1,013 个非 thunk 的直接槽**没有**同组同序号的匹配（实测 0 个），因此「各层直接槽是各层自己的实现」'
'这一读法只到「无匹配」这一步，**没有**证明它们语义上不同。（d）RTTI 的「自项」身份由**名字判据**确立：'
'`numContainedBases == 0` 在数组**末项**同样恒成立（1214/1214），单靠计数区分不了首末项；'
'只有 `numBaseClasses == 1` 的 256 条首末同项。（e）5,302 条描述符里 **2,111 条**（34 个不同名）指向'
'本镜像 1,214 个类名之外的基类（`IUnknown` 841 / `IPersistStream` 346 / `IPersist` 346 / '
'`IRTTITypeInfo` 316 / `IClassFactory` 78 等 COM 接口），这些**没有**对应的 `.?AV...` 副表，'
'不影响上面的层数统计，但**不得**把 5,302 条读成「5,302 个在本镜像里有 vtable 的类」。'
'（f）三条脚本 `_r190/r190a_groups.py`（17 断言）/ `_r190/r190b_thunks.py`（12 断言）/ '
'`_r190/r190c_rtti.py`（19 断言）全部 0 FAIL；反控逐条：mdisp 随机打乱后严格递减掉到 10 组、'
'改要求严格递增命中 0 组、块间距按「槽数+1」算命中 0、调整器改用 K == 本层 mdisp 只命中 303、'
'改用「本层 − 组内最低地址层」命中 0、pTD 整体 +4 后命中 0。')
f55[4] = f55[4] + L9
ck('D6 statement 新尾含 ⑨ 且以中文句号结尾', f55[1].endswith('。') and '⑨ **（V575 新增' in f55[1])
ck('D7 limitations 新尾含 6 条边界且以中文句号结尾', f55[4].endswith('。') and f55[4].count('（a）') >= 1
   and '**3 组**确定反例' in f55[4])
NEWP = '_r190/r190a_groups.py;_r190/r190b_thunks.py;_r190/r190c_rtti.py'
ck('D8 旧第 4 列不含 _r190', '_r190/' not in f55[3], f55[3])
f55[3] = f55[3] + ';' + NEWP
ck('D9 新第 4 列含三条 _r190 路径', all(x in f55[3] for x in ('r190a_groups.py', 'r190b_thunks.py', 'r190c_rtti.py')))
for nm, s in (('statement', S9), ('limitations', L9)):
    ck('D10 %s 新段无 tab / CR / LF / 半角双引号' % nm,
       '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s)
newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
R2 = [l.split('\t') for l in newtxt.split('\n')[:57]]
ck('D11 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 58 and all(len(x) == 5 for x in R2))
ck('D12 只有 F55 一行变化', [a[0] for a, b in zip(ORIG, R2) if a != b] == ['F55'],
   [a[0] for a, b in zip(ORIG, R2) if a != b])
ck('D13 F55 grade 未动（仍是第 3 列原值）', [r for r in ORIG if r[0] == 'F55'][0][2] == f55[2])
exp = 162625 + len(S9.encode()) + len(L9.encode()) + len(NEWP.encode()) + 1
ck('D14 体量按构造闭合（旧 + 三段 + 1 个分隔符）', len(nb) == exp, (len(nb), exp, len(nb) - exp))
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
ck('D15 回读 sha 一致',
   hashlib.sha256(open(NEW, 'rb').read()).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V575 = %d B / sha %s… / F55 stmt %d B / lim %d B / evid %d B'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(f55[1].encode()),
         len(f55[4].encode()), len(f55[3].encode())))
sys.exit(0)

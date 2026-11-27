#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186 E：V567 -> V568，在 F01 与 F29 两列 limitations 各追加 R186 实测段（statement / grade / evidence 不动）。"""
import hashlib, io, os, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V567', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V568')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('X1 旧 V567 = 140,546 B / sha 2e502b68… / CR 0',
   len(raw) == 140546 and hashlib.sha256(raw).hexdigest().startswith('2e502b68') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
ck('X2 56 段（55 行）/ 每行 5 列', len(L) == 56 and all(len(x.split('\t')) == 5 for x in L[:55]), len(L))
rows = [l.split('\t') for l in L[:55]]
import copy
ORIG = copy.deepcopy(rows)
f01 = [r for r in rows if r[0] == 'F01'][0]
f29 = [r for r in rows if r[0] == 'F29'][0]
ck('X3 F01 limitations 9,651 B / F29 limitations 15,256 B',
   len(f01[4].encode()) == 9651 and len(f29[4].encode()) == 15256,
   (len(f01[4].encode()), len(f29[4].encode())))

APP01 = ('**【R186 实测·对象模型的层结构在代码侧闭合，并撤回 R186b 四个覆盖不足的数字】** '
'① `_r186/r186b_ctor.py`（**28 断言 0 FAIL**）与 `_r186/r186c_descent.py`（**23 断言 0 FAIL**）复算：'
'全镜像 **1,214** 个 COL 按 pTD 分组得 **954** 组，每组内 mdisp **两两不同**且**恰含一个 mdisp==0**；'
'层数直方图 **{1:860, 2:10, 3:6, 4:76, 5:1, 7:1}**，Σ 层数 **= 1,214**（与总 COL 数算术闭合，不靠巧合）；'
'每组内的层就是「同一个类在不同基类子对象位置上的多张 vtable」。'
'② `symbols.json` 的 954 条对层数的选择是规则的：**942 类取 mdisp==0 层、12 类取 mdisp==4 层**，'
'而这 12 类**同时也存在 mdisp==0 层** ⇒ symbols 在这 12 类上**偏离**「取 0 层」规则（12 个全是 Locomotion 系，与 R185 结论一致）。'
'③ **代码侧证据**：`.text` 里 `mov dword ptr [基址+位移], <vtable 立即数>` 的装点中，位移**等于该 vtable 的 COL.mdisp**'
'的有 **3,204/3,666 = 87.40%**（口径 = C7 /0 字节模式 ∩ 递归下降指令边界，且基址非 esp/ebp、无索引）；'
'残差 **411** 条里 **387** 条落在模板/容器类（`?$TypeList@H` 69、`?$DynamicVectorList` 系 12、`GenericList` 11 等），'
'**24** 条落在非模板类；真个例恒为 3 条（**004A8660** LayerClass / 位移 −8、**004F73CA** BaseClass / 22,272、**00632CE0** BlowPipe / 20）。'
'④ **撤回**：`r186b_ctor.py` 首版用「从 `.text` 起点 64 KB 分块线性反汇编」找装点，'
'`_r186/r186d_audit_recheck.py`（**17 断言 0 FAIL**）实测该方式**只消费 3,360,178/4,063,232 = 82.70% 字节**、'
'**53 个块提前终止**（.text 内嵌指针表处），因此首版报的 **4,720 / 4,564 / 3,216 / 3,009** 四个数是**覆盖不足下的下限**，'
'**不得再引**；改用「字节模式 ∩ 递归下降」交叉口径后报 **5,731 / 4,886 / 3,666 / 3,204**，'
'并如实登记字节模式单口径的 **845** 条假命中（落在非指令边界上）。'
'⑤ 另复算一条布局事实：**COL+16 恰等于其配对 vtable 基址的个数 = 0/1214**（gap 全为负、-106,000..-84,760、916 个不同值）'
'⇒ COL 与 vtable 只靠 `dword[vt−4]` 反向引用联系，**不是相邻布局**；「每 COL 恰一张表」是构造性事实、不是独立发现的镜像性质。'
'**边界**：本条只在本列追加；statement 与 grade 不动；④ 里「假命中」与「真装点」的分界依赖递归下降的可达性，'
'不可达但真实存在的构造函数若不在种子集合里仍会漏计，该下限未穷举。')

APP29 = ('**【R186 实测·F29 那条「取 mdisp==0 主虚表的 slot1/slot2」在代码侧被证实，另一条撤回】** '
'① `_r186/r186c_descent.py`（**23 断言 0 FAIL**）复算 12 个含 `mdisp==4` 层的 Locomotion 类：'
'**12/12** 的 `mdisp==4` 表在构造器里被装到对象 **+4**（装点位移集合恒为 {4}，无一张装在其它位移），'
'对应 `mdisp==0` 表 **12/12** 被装到 **+0**（且在 +4 上 **0 次**）⇒ F29 要求的「取 `mdisp==0` 主虚表」在**代码侧被独立证实**，'
'不是从 RTTI 反推的措辞：主表确实装在对象偏移 0。'
'② 其中 6 个类（Drive / DropPod / Jumpjet / Ship / Teleport / Walk）另有 **mdisp==24** 的第三接口表，'
'同样被装到 **+0x18（= 24）**，装点位移集合恒为 {24} ⇒ 装点位移 == COL.mdisp 这条关系在 3 层上同时成立。'
'③ **撤回 R186b 的一句**：首版曾报「FlyLocomotionClass / TunnelLocomotionClass 无 imm32 装点」，'
'`_r186/r186d_audit_recheck.py`（**17 断言 0 FAIL**）复算证明这是**线性扫描覆盖不足的伪影**：'
'这两张表各有 **4 条 / 2 条**标准 imm32 装点（Fly: 004CCA12 / 004CCA76 / 004CFCDE / 004D03A9，Tunnel: 00728A42 / 0072A18C，位移全为 4）。'
'**边界**：装点位移与 mdisp 的相等关系只在**能找到 imm32 装点**的表上可判；'
'全镜像 1,214 张表里 **10** 张找不到任何装点（`?$DynamicVectorClass@PAE` / `?$DynamicVectorClass@PAU_DDSURFACEDESC@@` / '
'`CarryoverClass` / `Dial8Class` / `PKPipe` / `TextButtonClass` / `TriColorGaugeClass` 等），这 10 张如实登记、不补齐。')

for nm, s in (('X4 APP01', APP01), ('X4 APP29', APP29)):
    ck(nm + ' 无 tab / CR / LF / 双引号', '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s)
    ck(nm + ' 以句号结尾、长度 > 800', s.endswith('。') and len(s.encode()) > 800, len(s.encode()))

f01[4] = f01[4] + APP01
f29[4] = f29[4] + APP29
newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('X6 新体量 == 旧 + 两段', len(nb) == 140546 + len(APP01.encode()) + len(APP29.encode()),
   (len(nb), 140546 + len(APP01.encode()) + len(APP29.encode())))
ck('X7 新 CR == 0 / 56 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 56 and all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:55]))
R2 = [l.split('\t') for l in newtxt.split('\n')[:55]]
diff = [a[0] for a, b in zip(ORIG, R2) if a != b]
ck('X8 只有 F01 与 F29 两行变化（其余 52 行逐单元格相同）', diff == ['F01', 'F29'], diff)
ck('X9 两行只有第 5 列变（statement / grade / evidence 三项逐字节未动）',
   all(a[0:4] == b[0:4] for a, b in zip(ORIG, R2)))
nf01 = [r for r in R2 if r[0] == 'F01'][0]
nf29 = [r for r in R2 if r[0] == 'F29'][0]
ck('X10 新 F01 lim / F29 lim 字节数', (len(nf01[4].encode()), len(nf29[4].encode())) ==
   (9651 + len(APP01.encode()), 15256 + len(APP29.encode())), (len(nf01[4].encode()), len(nf29[4].encode())))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f:
    f.write(nb)
back = open(NEW, 'rb').read()
ck('X11 回读 sha 一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(nb).hexdigest())
ck('X12 回读字节数', len(back) == len(nb), len(back))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V568 = %d B / sha %s… / F01 lim %d / F29 lim %d'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(nf01[4].encode()), len(nf29[4].encode())))
sys.exit(0)

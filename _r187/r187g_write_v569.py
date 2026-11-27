#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 G：V568 -> V569，在 F01 与 F29 两列 limitations 各追加 R187 实测段（statement/grade/evidence 不动）。

本轮推翻 R186 的两条**陈述**（不是数字）：
  ① F01 ③ 里的「字节模式单口径的 845 条假命中（落在非指令边界上）」——
     r187e 用不依赖可达性的局部对齐判据实测：5,731 条里 5,730 条局部可对齐、1 条孤立。
     ⇒ 845 这个量级的东西绝大多数是**真指令、只是不可达**；「假命中」一词误称了它们。
  ② F29 边界里的「全镜像 1,214 张表里 10 张找不到任何装点」——
     r187d 逐处结构反查实测：10 张**全部**有可定位的 imm32 装点（7 张 C7 对象寄存器 store、
     1 张 C7 栈 store、2 张 mov r32,imm32 后同寄存器写内存）。

同时用全口径重算 R186 的三层数（撤回不必要的收缩）：全 5,731 → 对象寄存器 4,053
（栈基址 1,337 / 绝对址 341 / 带索引 0）→ disp == COL.mdisp 3,737 = 92.20%；
放宽 3,788 = 93.46%；残差 265（模板 262 / 非模板 3：BaseClass / BlowPipe / LayerClass）。
"""
import hashlib, io, os, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V568', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V569')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('X1 旧 V568 = 144,718 B / sha 335b403d… / CR 0',
   len(raw) == 144718 and hashlib.sha256(raw).hexdigest().startswith('335b403d') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
ck('X2 56 段（55 行）/ 每行 5 列', len(L) == 56 and all(len(x.split('\t')) == 5 for x in L[:55]), len(L))
rows = [l.split('\t') for l in L[:55]]
import copy
ORIG = copy.deepcopy(rows)
f01 = [r for r in rows if r[0] == 'F01'][0]
f29 = [r for r in rows if r[0] == 'F29'][0]
ck('X3 F01 limitations 12,239 B / F29 limitations 16,840 B',
   len(f01[4].encode()) == 12239 and len(f29[4].encode()) == 16840,
   (len(f01[4].encode()), len(f29[4].encode())))

APP01 = ('**【R187 实测·撤回 R186 的一处分类，并撤掉一层不必要的收缩】** '
'① **撤回一个词**：R186 的 ③ 把这轮字节模式单口径里「不在递归下降起点集合」的 845 条叫「假命中（落在非指令边界上）」。'
'`_r187/r187e_align.py`（**13 断言 / 2 FAIL 如实登记**）改用**不依赖可达性**的局部对齐判据'
'（某处是否是一条 C7 /0 指令的立即数字段：按 mod/rm/SIB 的自描述长度反推指令起点，再看起点字节是否为 C7 且 modrm.reg==0）：'
'5,731 条里 **5,730** 条局部可对齐、**仅 1** 条孤立（`00535A60`）⇒ 那 845 条绝大多数是**真指令、只是种子集合没覆盖到入口**，'
'「假命中」这个词把「不可达」误称成了「不是指令」，**不宜再引**。'
'② **撤掉一层收缩**：既然「不可达」不等于「不是指令」，R186 的三层口径（交集 4,886 → 对象寄存器 3,666 → 3,204）'
'就不必要。`_r187/r187f_recount.py`（**14 断言 0 FAIL**）用**全 5,731 条**重算：'
'对象寄存器 store（基址为通用寄存器、非 esp/ebp、无索引）**4,053** 条'
'（构成：对象寄存器 4,053 / 栈基址 1,337 / 绝对址 341 / 带索引 0，四类合计 **= 5,731** 算术闭合）；'
'其中 **disp == COL.mdisp 的 3,737 = 92.20%**，放宽到「disp ∈ 该 TD 在全镜像 CHD 出现过的 mdisp」**3,788 = 93.46%**；'
'残差 **265** 条（模板/容器 **262**：`?$TypeList@H` 70、`?$TypeList@PBVAnimTypeClass@@` 12、`?$VectorClass@H` 11 等；'
'非模板 **3**：BaseClass / BlowPipe / LayerClass，与 R186 的真个例逐名相同）。'
'③ ⇒ **R186 的 87.40% 应改读 92.20%**：两者不是矛盾，是**两个作用域**（交集 vs 全口径）；'
'全口径既更大又更准（它不把真指令当假命中），应作为本条主数字，87.40% 降为「交集作用域下的旧值」。'
'④ 反控四条全真红：disp+1 判相等 **0** 命中、mdisp 换常数 0 得 **2,743 < 3,737**、vtable 集合置空 **0** 命中、'
'命中集合整体平移 +3 字节后局部可对齐比例从 **100.00%** 降到 **25.67%**。'
'**边界**：本条只在本列追加；statement 与 grade 不动；92.20% 与 87.40% 的差额来自作用域，不来自任何字节变化。')

APP29 = ('**【R187 实测·撤回「10 张表找不到任何装点」这条边界】** '
'① R186 的边界写「全镜像 1,214 张表里 **10** 张找不到任何装点 …… 这 10 张如实登记、不补齐」。'
'`_r187/r187d_final.py`（**22 断言 0 FAIL**）逐处结构反查实测：**这 10 张全部有可定位的 imm32 装点**。'
'② 判据（只依赖 x86 编码规则，不依赖可达性、也不从立即数中间盲解）：给定 vtable 地址 4 字节的出现偏移 o，'
'按 C7 操作数的 (mod,rm,SIB,disp) 自描述长度 L 反推起点 o−L，要求该处字节为 C7、modrm.reg==0、且按该 modrm 算出的立即数偏移恰为 o。'
'③ 逐处结果（12 处出现）：**7 张**走 C7 对象寄存器 store（CarryoverClass `00473777 c706044c7e00` / Dial8Class `004A53DA c7063c5e7e00` / '
'`?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@` `004E0A8A c7078c927e00` / '
'TriColorGaugeClass `004E2AD5 c70630947e00` / PKPipe `00632CF9 c700acfd7e00` / TextButtonClass `0071FF65` 与 `0071FFC2` 两处 `c706dc557f00` / '
'`?$DynamicVectorClass@PBVToolTip@@` `0072403A c701c8577f00`）；**1 张**走 C7 栈 store'
'（`?$DynamicVectorClass@PAU_DDSURFACEDESC@@` `004A4937 c74424200c5e7e00`，对象构造在栈上，位移 +0x20）；'
'**2 张**走「mov r32,imm32 再把同一寄存器写进内存」（`?$DynamicVectorClass@PAE` `007B2DBA baec7a7f00` → `mov [esi+0x3F338], edx`；'
'`?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@` `007B19C8 ba1c7a7f00` → `mov [esi+8], edx`）。'
'④ 位移 == COL.mdisp 的有 **7/10**；不等的恰 3 张（B 两张位移 +0x3F338 / +8，栈那张 +0x20）—— 这 3 张**不是异常、是形态不同**。'
'⑤ 口径 P（C7 /0）单口径覆盖 **1,212/1,214** 张表，未覆盖的 2 张恰是上面走 B 形态那 2 张；'
'R186c 的 1,204 = 1,214 − 8（有 C7 但指令起点不可达）− 2（纯 B 形态），算术闭合。'
'⑥ 反控四条全真红：imm 判等改 vt+1 **0** 命中、目标 VA 加 4 做结构反查 **10 张全空**、'
'B 形态改用绝对偏移索引（复刻中间版的 bug）命中表数 **从 2 降到 0**、种子清空 **STARTS == 0**。'
'**边界**：本条只在本列追加；statement 与 grade 不动；「有装点」只说明该表在代码里被装载过，不说明装在哪一层（层归属仍需逐类判）。')

for nm, s in (('X4 APP01', APP01), ('X4 APP29', APP29)):
    ck(nm + ' 无 tab / CR / LF / 双引号', '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s)
    ck(nm + ' 以句号结尾、长度 > 800', s.endswith('。') and len(s.encode()) > 800, len(s.encode()))

f01[4] = f01[4] + APP01
f29[4] = f29[4] + APP29
newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('X6 新体量 == 旧 + 两段', len(nb) == 144718 + len(APP01.encode()) + len(APP29.encode()),
   (len(nb), 144718 + len(APP01.encode()) + len(APP29.encode())))
ck('X7 新 CR == 0 / 56 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 56
   and all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:55]))
R2 = [l.split('\t') for l in newtxt.split('\n')[:55]]
diff = [a[0] for a, b in zip(ORIG, R2) if a != b]
ck('X8 只有 F01 与 F29 两行变化（其余 53 行逐单元格相同）', diff == ['F01', 'F29'], diff)
ck('X9 两行只有第 5 列变（statement / grade / evidence 三项逐字节未动）',
   all(a[0:4] == b[0:4] for a, b in zip(ORIG, R2)))
nf01 = [r for r in R2 if r[0] == 'F01'][0]
nf29 = [r for r in R2 if r[0] == 'F29'][0]
ck('X10 新 F01 lim / F29 lim 字节数',
   (len(nf01[4].encode()), len(nf29[4].encode())) ==
   (12239 + len(APP01.encode()), 16840 + len(APP29.encode())),
   (len(nf01[4].encode()), len(nf29[4].encode())))
ck('X11 F01/F29 statement 与 grade 逐字节未动（改数字属裁定，本轮不改）',
   nf01[1] == f01[1] and nf01[2] == f01[2] and nf29[1] == f29[1] and nf29[2] == f29[2])
ck('X12 追加段里的每个数字都能在本轮 json 里找到',
   all(x in open(os.path.join(ROOT, '_r187/r187f.json')).read() for x in ('3737', '4053', '3788', '265', '262')))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f:
    f.write(nb)
back = open(NEW, 'rb').read()
ck('X13 回读 sha 一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(nb).hexdigest())
ck('X14 回读字节数', len(back) == len(nb), len(back))
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V569 = %d B / sha %s… / F01 lim %d / F29 lim %d'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(nf01[4].encode()), len(nf29[4].encode())))
sys.exit(0)

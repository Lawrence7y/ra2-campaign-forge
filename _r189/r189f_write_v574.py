#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R189 F：台账 V573 -> V574。两处订正 + 一条口径撤销，全部落在 F55 一行。

## 订正一（本轮主攻）：R188 的「979 张表撞到内嵌 COL 指针、前缀不是真实槽数」是错的
实测（_r189/r189c_adjacency.py 24 断言 0 FAIL、r189d_packing.py 21 断言 0 FAIL）：
  .rdata 里 vtable 的布局是 **块紧排** [COL 指针 4B][槽 4×k B] 重复，
  1,214/1,214 张表头前 4 字节都是一条 COL 地址；979/979 张表的「截断点」dword
  **恰等于紧接着那张表自己的 COL 指针**（反例 0，+8/−4 两个方向反控都归 0）。
  ⇒ 前缀长度**就是真实槽数**，14,044 **就是**真实槽位实例总数。
  R188 的「854」也不是内嵌证据：其中 847 张只是「下一张表槽数 >= 2」，
  另 7 张是非紧排组的 +8 巧合。

## 订正二：F55 ⑦「72 张的槽 11 同为 0x410450」是跨块越界读数
76 张 thunk 宿主表的**真实槽数恒为 6**（槽 11 根本不存在），vt+44 落在**块外**，
且 76/76 恰等于**紧邻的同名主表**（vt+28）的槽 4；0x410450 在全镜像**只出现在槽 4**
（77 张表）、在真正的槽 11 上出现 0 次。R188 报的 72/2/1/1 是 vt+44 直方（可复现），
但语义是「紧邻主表的槽 4」。真正的槽 11 直方是 0x4C9150 9 / 其余各 1。

## 做法
只改 F55 一行的第 2/4/5 列；第 3 列（evidence）追加 3 条本轮脚本。
"""
import hashlib, io, os, sys, copy
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V573', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V574')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('F1 旧 V573 = 160,515 B / sha b15201b4… / CR 0',
   len(raw) == 160515 and hashlib.sha256(raw).hexdigest().startswith('b15201b4')
   and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16], raw.count(b'\r')))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('F2 58 段（57 行 + 空尾）', len(L) == 58, len(L))
rows = [l.split('\t') for l in L[:57]]
ORIG = copy.deepcopy(rows)
ck('F3 57 行每行 5 列', all(len(r) == 5 for r in rows), [r[0] for r in rows if len(r) != 5])
f55 = [r for r in rows if r[0] == 'F55'][0]

# ---------------- 订正一：statement 里的槽数口径 ----------------
A1 = ('⑤ 观测槽可达实现去重 6,523 / 全 vfunc 实现去重 6,692 / 全槽位实例 14,044（= 1214 张表槽数求和）；')
ck('F4 锚点 A1 恰 1 次', f55[1].count(A1) == 1, f55[1].count(A1))
N1TXT = ('⑤ 观测槽可达实现去重 6,523 / 全 vfunc 实现去重 6,692 / 全槽位实例 14,044（= 1214 张表槽数求和）；'
'**（V574 订正 · R188 的「前缀不是真实槽数」被逐块实测推翻）** `.rdata` 里虚表是**块紧排**：'
'块 = [COL 指针 4 B][槽 4×k B]，块与块之间无空隙；实测 **1,214/1,214** 张表头前 4 字节都是一条 '
'COL 地址，**979/979** 张表「前缀终点」那个 dword **恰等于紧随其后的那张表自己的 COL 指针**'
'（反例 0；反控：终点+8 命中 0、终点−4 命中 0、把终点 COL 与另一张表的头前 COL 错配命中 0）。'
'⇒ **前缀长度就是真实槽数**，**14,044 就是真实槽位实例总数**，不存在「跳过内嵌 COL 继续数」。'
'R188 记的 **854** 同样不是内嵌证据：其中 **847** 张只是「下一张表槽数 ≥ 2」（紧排组内逐表一致 '
'979/979），另 **7** 张是非紧排组的 +8 巧合；非紧排的 235 张 = 0 填充 186 / `.data` 邻接 4 / 散尾 45，'
'块间空隙恒 > 0（最小 4 B），空隙内是 `.rdata` 其它结构（字符串、浮点常量等），只有 8 张出现落 '
'`.text` 区间的 dword 且逐处核对均为无关数据；')
f55[1] = f55[1].replace(A1, N1TXT, 1)
ck('F5 新 statement 含紧排/真实槽数/847/7/186/45',
   all(x in f55[1] for x in ('.rdata` 里虚表是**块紧排**', '前缀长度就是真实槽数', '**847**', '另 **7** 张',
                             '0 填充 186', '散尾 45')))

# ---------------- 订正二：72/76 槽 11 -> 紧邻主表槽 4 ----------------
A2 = ('其中 72 张的槽 11 同为 0x410450、2 张为 0x410310、各 1 张为 0x512280 与 0x410260（集中度 94.74%）；')
ck('F6 锚点 A2 恰 1 次', f55[1].count(A2) == 1, f55[1].count(A2))
N2TXT = ('**（V574 订正 · R188 这半句是跨块越界读数）** 那 76 张 thunk 宿主表的**真实槽数恒为 6**，'
'槽 11 根本不存在；vt+44 落在**本表块外**，且 **76/76** 恰等于**紧随其后的同名主表**（vt+28，'
'其中 mdisp==0 的 73 张）的**槽 4**。`0x410450` 在全镜像**只出现在槽 4**（77 张表）、在真正的槽 11 上'
'出现 **0** 次（基率检验：槽 4 上 0x410450 占 77/907 = 8.49%，若邻居随机则期望命中 6.5 张，'
'实测 72 ⇒ 是「配对主表的槽 4」这一结构性事实，不是巧合）。真正的槽 11 直方为 '
'`0x4C9150` 9 张、其余各 1 张（可读槽 11 的表共 152 张）。R188 报的 72/2/1/1 作为 vt+44 直方'
'**可复现**，但语义错位有两处：**表错**（本表 → 紧邻的同名主表）、**槽错**（11 → 4）；')
f55[1] = f55[1].replace(A2, N2TXT, 1)
ck('F7 新 statement 含 真实槽数为 6/76-76/槽 4/0 次/8.49%',
   all(x in f55[1] for x in ('真实槽数恒为 6', '**76/76**', '只出现在槽 4', '出现 **0** 次', '8.49%')))

# ---------------- 订正三：limitations 里 V572 那一段 ----------------
A3 = ('**（V572 订正）槽数口径必须写死：本文所称「槽数」= 从 vtable VA 起逐 dword 前进（vt+0 即 slot0）'
'直到取值不再落 .text 文件范围的「.text 连续前缀长度」，不是虚表的真实槽数。**实测 1,214 张表的'
'**截断点**构成为：`.rdata` 且**本身是 COL** 的 **979 张**、其它 `.rdata` 231 张、`.data` 4 张 —— '
'即 979 张表不是「虚表到头」，而是撞到一个**内嵌 COL 指针**（嵌套子对象的 vtable 指针），'
'且实测 **854 张**表在截断点之后第 2 个 dword 又回到 .text。⇒ 全槽位实例 14,044 同样是'
'「前缀内槽位实例数」而非「全部槽位实例数」；任何「每表槽数 / 槽实例总数 / 某槽存在性」的断言'
'都必须带这个限定。（本项由主会话自查发现，跨家族审计 #454 未提；审计提的是槽 2 并列与 '
'0x4C9150 两处。）')
ck('F8 锚点 A3 恰 1 次', f55[4].count(A3) == 1, f55[4].count(A3))
N3TXT = ('**（V574 撤销上面这条 V572 订正）R188 把「`.text` 连续前缀长度」当成「只是前缀、不是真实槽数」'
'是错的，本轮逐块实测推翻：`.rdata` 里虚表是块紧排 [COL 指针][槽 4×k]，1,214/1,214 张表头前 '
'4 字节都是 COL 地址，979/979 张表的终点 dword 恰是紧随那张表自己的 COL 指针（反例 0），'
'故**前缀长度 = 真实槽数、14,044 = 真实槽位实例总数**。V572 的「撞到内嵌 COL 指针（嵌套子对象 '
'vtable 指针）」这一定性**作废**；V572 的「854 张在截断点后第 2 个 dword 又回到 .text」也**不是**'
'内嵌证据 —— 它是「紧排组下一张表槽数 ≥ 2」的 847 张 + 非紧排组 +8 巧合的 7 张。'
'仍成立的部分只有「截断点构成 979 / 其它 `.rdata` 231 / `.data` 4」这组分类本身：'
'这 235 张非紧排表 = 0 填充 186 / `.data` 邻接 4 / 散尾 45，块间空隙恒 > 0。'
'（V572 该条由主会话自查提出、跨家族审计 #454 未提；本轮推翻它同样由主会话自查 + 独立第二实现'
' + 独立执行员三方各自复算，审计员 #457 因回合耗尽未回件，如实登记。）')
f55[4] = f55[4].replace(A3, N3TXT, 1)
ck('F9 新 limits 含撤销/作废/三方复算',
   all(x in f55[4] for x in ('V574 撤销', '这一定性**作废**', '三方各自复算')))
ck('F10 旧 limits 不再含「内嵌 COL 指针」这一断言的肯定式',
   '而是撞到一个**内嵌 COL 指针**' not in f55[4])

# ---------------- 第 4 列：追加三条本轮证据 ----------------
ck('F11 旧第 4 列不含 _r189', '_r189/' not in f55[3], f55[3])
f55[3] = f55[3] + ';_r189/r189c_adjacency.py;_r189/r189d_packing.py;_r189/r189e_thunk_oob.py'
ck('F12 新第 4 列含三条 _r189 路径',
   all(x in f55[3] for x in ('r189c_adjacency.py', 'r189d_packing.py', 'r189e_thunk_oob.py')))

for nm, s in (('statement 订正一', N1TXT), ('statement 订正二', N2TXT), ('limitation 撤销段', N3TXT)):
    ck('F13 %s 无 tab / CR / LF / 半角双引号' % nm,
       '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s, '')
ck('F14 F55 statement 与 limitations 都以中文句号结尾',
   f55[1].endswith('。') and f55[4].endswith('。'))

newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('F15 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 58
   and all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:57]))
R2 = [l.split('\t') for l in newtxt.split('\n')[:57]]
ck('F16 只有 F55 一行变化', [a[0] for a, b in zip(ORIG, R2) if a != b] == ['F55'],
   [a[0] for a, b in zip(ORIG, R2) if a != b])
ck('F17 F55 的第 3 列 grade 未动', ORIG[[r[0] for r in ORIG].index('F55')][2] == f55[2],
   (ORIG[[r[0] for r in ORIG].index('F55')][2], f55[2]))
ck('F18 前 54 行（F01..F54）逐字节未动',
   all(a == b for a, b in zip(ORIG[:55], R2[:55]) if a[0] != 'F55'),
   [a[0] for a, b in zip(ORIG[:55], R2[:55]) if a != b and a[0] != 'F55'][:5])
ck('F19 F56 一字未动', [r for r in R2 if r[0] == 'F56'][0] == [r for r in ORIG if r[0] == 'F56'][0])
exp = 160515 + (len(N1TXT.encode()) - len(A1.encode())) + (len(N2TXT.encode()) - len(A2.encode())) \
    + (len(N3TXT.encode()) - len(A3.encode())) \
    + len(';_r189/r189c_adjacency.py;_r189/r189d_packing.py;_r189/r189e_thunk_oob.py'.encode())
ck('F20 体量按构造逐项闭合', len(nb) == exp, (len(nb), exp, len(nb) - exp))

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
ck('F21 回读 sha 一致',
   hashlib.sha256(open(NEW, 'rb').read()).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V574 = %d B / sha %s… / F55 stmt %d B / lim %d B / evid %d B'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(f55[1].encode()),
         len(f55[4].encode()), len(f55[3].encode())))
sys.exit(0)

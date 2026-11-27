#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 I：V571 -> V572，订正 F55 里**三处**由跨家族审计 #454 与主会话自查共同抓出的错误。

## 被订正的三处
E-A **槽 2 的「top 实现」是并列，我的 max() 静默取了任意一个。**
    实测 slot2 直方：0x410600 **74 表** / 0x410310 **74 表**（并列第一）、0x4E14B0 20 表。
    V571 的 F55 写「槽 2 → 0x410310（74 表）」并把它列进「实现<->槽号 一一」的六组里。
    max() 在并列时返回先遇到的那个，于是「0x410310」这条是从并列里挑出来的，
    **不是唯一事实**。订正：明确写出并列，并把「一一」的作用域收窄到「无并列」的五个槽。
    审计员 #454 报的是 0x410600（它 max() 挑到另一个），**两边都是并列的直接后果**。

E-B **「实现与槽号一一」被反例推翻，而 V571 已经写了「不可外推」，但仍把 6 组列成「一一」。**
    实测有 **1 个**实现跨多个槽号：0x4C9150 出现 **205 次、跨 33 个不同槽号**
    （槽 3 22 次 / 槽 5 10 / 槽 6 11 / 槽 11 13 / 槽 12 13 / 槽 0 5 / 槽 28 2 / 槽 29 3 …）。
    V571 的 F55 limitations 里用「0x410310 同时是槽 2 的 top 实现」当反例，**那条反例本身是错的**
    （0x410310 只出现在槽 2，`IMP[0x410310]` 的槽号直方是 `{2: 74}` 单值）；
    真正的反例是 0x4C9150。订正：换反例、并给出「跨槽号实现恰 1 个、跨 33 个槽号」的实测。

E-C **槽数枚举的「连续前缀长度」不是真实槽数，是口径缺陷（主会话自查，审计未提）。**
    现行槽数 = 从 vt 起逐 dword 前进直到取值不再落 .text。实测 1,214 张表的**截断点**构成：
    `.rdata` 且**本身是 COL** 的 **979 张**、其它 `.rdata` 231 张、`.data` 4 张。
    即 979 张表不是「虚表到头了」，而是**撞到一个内嵌的 COL 指针**（嵌套子对象的 vtable 指针）。
    实测 **854 张**表在截断点之后第 2 个 dword 又回到 .text。
    ⇒ 「槽数」这个词在现行口径下应读作「**.text 连续前缀长度**」，不是虚表的真实槽数；
    全槽位实例 14,044 同样是「前缀内槽位实例数」。V571 的 F55 limitations 未声明这一点。

## 判定：三处都不改 F55 的 statement 主体结论（22,731 / 6,965 / 267 / 326 / 49 等），
只订正 limitations 的三段，并把「一一」与「槽数」两个词的边界写死。
"""
import hashlib, io, os, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V571', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V572')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('Y1 旧 V571 = 157,369 B / sha 9babc771… / CR 0',
   len(raw) == 157369 and hashlib.sha256(raw).hexdigest().startswith('9babc771') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('Y2 58 段（57 行 + 空尾）', len(L) == 58, len(L))
rows = [l.split('\t') for l in L[:57]]
import copy
ORIG = copy.deepcopy(rows)
ck('Y3 每行 5 列', all(len(r) == 5 for r in rows))
f55 = [r for r in rows if r[0] == 'F55'][0]

OLD_A = ('⑥ top6 槽的实现函数在**其出现的全部**虚表里都落在同一槽号（实现与槽号一一）：'
'槽 2 → 0x410310（74 表）、槽 3 → 0x410210（76 表）、槽 4 → 0x410220（78 表）、'
'槽 11 → 0x4E1570（20 表）、槽 18 → 0x4104C0（56 表）、槽 33 → 0x5F6BC0（15 表）；')
NEW_A = ('⑥ **（V572 订正）** top 槽的实现函数在**其出现的全部**虚表里落在同一槽号 —— 但**槽 2 有并列**，'
'不可只报一个：实测 slot2 直方为 **0x410600 74 表 / 0x410310 74 表**（并列第一，交集 0）、0x4E14B0 20 表。'
'V571 写「槽 2 → 0x410310（74 表）」是把并列里的一个当唯一事实（我的 max() 在并列时返回先遇到的，'
'审计员 #454 的 max() 返回另一个 ⇒ 它报 0x410600，**两边都不算算错，错在没写并列**）。'
'无并列的五个槽为：槽 3 → 0x410210（76 表）、槽 4 → 0x410220（78 表）、槽 11 → 0x4E1570（20 表）、'
'槽 18 → 0x4104C0（56 表）、槽 33 → 0x5F6BC0（15 表）；')
OLD_B = ('⑦ 的槽 11 取值有 4 个不同值，其中 0x410310 同时是槽 2 的 top 实现 —— '
'同一函数出现在两个不同槽号（槽 2 与槽 11）**确有其例**，故 ⑥ 的「一一」只对 ⑥ 列出的 top6 '
'（其 top 实现）成立，**不得外推为「全镜像实现与槽号一一」**。')
NEW_B = ('**（V572 订正）** V571 在这里用的反例**是错的**：它说「0x410310 同时是槽 2 与槽 11 的 top 实现」，'
'实测 `0x410310` 出现在 **74 张表的槽 2、0 张表的槽 11**（槽号直方 `{2: 74}` 单值）。'
'**真正的反例是 0x4C9150**：它在全镜像出现 **205 次、跨 33 个不同槽号**'
'（槽 3 22 次 / 槽 5 10 / 槽 6 11 / 槽 11 13 / 槽 12 13 / 槽 0 5 / 槽 28 2 / 槽 29 3 / 其余零散）。'
'全镜像**跨槽号的实现恰 1 个**（就是 0x4C9150），其余 6,691 个实现都只出现在单槽号。'
'故 ⑥ 的「一一」只对 ⑥ 列出的那五/六个 top 实现成立，**不得外推为「全镜像实现与槽号一一」**——'
'该命题有一个确切反例。')
OLD_C = ('槽数 = 从 vtable VA 起逐 dword 前进（vt+0 即 slot0）直到取值不再落 .text 文件范围。')
NEW_C = ('**（V572 订正）槽数口径必须写死：本文所称「槽数」= 从 vtable VA 起逐 dword 前进'
'（vt+0 即 slot0）直到取值不再落 .text 文件范围的「.text 连续前缀长度」，不是虚表的真实槽数。**'
'实测 1,214 张表的**截断点**构成为：`.rdata` 且**本身是 COL** 的 **979 张**、其它 `.rdata` 231 张、'
'`.data` 4 张 —— 即 979 张表不是「虚表到头」，而是撞到一个**内嵌 COL 指针**（嵌套子对象的 vtable 指针），'
'且实测 **854 张**表在截断点之后第 2 个 dword 又回到 .text。'
'⇒ 全槽位实例 14,044 同样是「前缀内槽位实例数」而非「全部槽位实例数」；'
'任何「每表槽数 / 槽实例总数 / 某槽存在性」的断言都必须带这个限定。'
'（本项由主会话自查发现，跨家族审计 #454 未提；审计提的是槽 2 并列与 0x4C9150 两处。）')

st = f55[1]
ck('Y4a 旧 A 串在 F55 **statement** 里恰 1 次（⑥ 在 statement 列，不在 limitation 列）',
   st.count(OLD_A) == 1, st.count(OLD_A))
for nm, a in (('Y4b 旧 B 串', OLD_B), ('Y4c 旧 C 串', OLD_C)):
    ck(nm + ' 在 F55 limitations 里恰 1 次', f55[4].count(a) == 1, f55[4].count(a))
st = st.replace(OLD_A, NEW_A, 1)
lim = f55[4]
lim = lim.replace(OLD_B, NEW_B, 1).replace(OLD_C, NEW_C, 1)
ck('Y4d statement 里旧 A 串已不在、新 A 串已入', OLD_A not in st and NEW_A in st)
for nm, s in (('Y5a 新 A', NEW_A), ('Y5b 新 B', NEW_B), ('Y5c 新 C', NEW_C)):
    ck(nm + ' 无 tab / CR / LF / 半角双引号',
       '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s)
ck('Y6 三个旧串都已不在各自应改的列里',
   OLD_A not in st and all(x not in lim for x in (OLD_B, OLD_C)))
ck('Y7 新 statement + 新 limitation 合计含三处订正标记',
   st.count('V572 订正') + lim.count('V572 订正') == 3,
   (st.count('V572 订正'), lim.count('V572 订正')))
ck('Y7b 新 A 串含并列实测', all(x in st for x in ('0x410600 74 表', '0x410310 74 表', '并列')))
ck('Y7c 新 B 串含真反例', all(x in lim for x in ('0x4C9150', '205 次、跨 33 个不同槽号', '恰 1 个')))
ck('Y7d 新 C 串含槽数口径与 979/854', all(x in lim for x in ('979 张', '854 张', '14,044', '连续前缀长度')))
ck('Y8 新 limitation 以句号结尾且 > 2,800 B', lim.endswith('。') and len(lim.encode()) > 2800,
   len(lim.encode()))
ck('Y8b 新 statement 变大', len(st.encode()) > len(f55[1].encode()), len(st.encode()))

f55[1] = st
f55[4] = lim
newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('Y9 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 58
   and all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:57]))
R2 = [l.split('\t') for l in newtxt.split('\n')[:57]]
ck('Y10 只有 F55 一行变化', [a[0] for a, b in zip(ORIG, R2) if a != b] == ['F55'],
   [a[0] for a, b in zip(ORIG, R2) if a != b])
ck('Y11 F55 只有第 2 列与第 5 列变（grade / evidence 逐字节未动）',
   all(a[2:4] == b[2:4] for a, b in zip(ORIG, R2)))
ck('Y12 F56 一字未动', [r for r in R2 if r[0] == 'F56'][0] == [r for r in ORIG if r[0] == 'F56'][0])
ck('Y13 体量 = 旧 + 三处替换差额',
   len(nb) == 157369 + sum(len(x.encode()) - len(y.encode()) for x, y in
   ((NEW_A, OLD_A), (NEW_B, OLD_B), (NEW_C, OLD_C))),
   (len(nb), 157369, len(nb) - 157369))
_origf55 = [r for r in ORIG if r[0] == 'F55'][0]
ck('Y13b F55 statement 只改 ⑥ 一处（前 5 项与 ⑦⑧ 原样）',
   st.replace(NEW_A, OLD_A, 1) == _origf55[1])
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
ck('Y14 回读 sha 一致', hashlib.sha256(open(NEW, 'rb').read()).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V572 = %d B / sha %s… / F55 stmt %d B / F55 lim %d B'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(st.encode()), len(lim.encode())))
sys.exit(0)

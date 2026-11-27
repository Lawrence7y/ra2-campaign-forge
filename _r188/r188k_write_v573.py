#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 K：V572 -> V573，并入跨家族审计 #454 的三条成立主张（一条已并入 V572，两条新）。

## 审计 #454（deepseek，独立实现、不复用主会话任何代码）的四条实质主张，逐条复算
Q1 **64KB 窗口截断伪影**：97 个重同步点里 **28 个是窗口截断伪影**（给足字节即可解码），
   真不可解 69；带 15 字节重叠后重启点降到 66、指令 1,394,134 → 1,394,120、
   间接 call 22,734 → **22,736**。⇒ 我的 22,731 是「无重叠」口径，**不是**「唯一真值」；
   重叠口径给 22,733（严格 `dword ptr [` 定义）/ 22,736（含 `ptr [` 段前缀 3 例）。
   **成立**，主会话已自跑复现（见下 Q1 复算）。
Q2 **vt 传播配对 7,022 vs 6,965**：差 **57**，原因是**配对判据的方向不同** ——
   我（semA）从首个 `mov r,[esi]` 向后扫，途中遇任何写 r 即放弃（含**第二次**写 r 的 mov）；
   审计（semB）在 call 处**反向**找最近的写 r 的指令，若最近那条本身是 `mov r,[esi]` 就算命中。
   ⇒ semB ⊇ semA，差集恰 57 个站点，`only in A = 0`。**成立且是定义差不是错**；
   我的口径更保守（假阳更少），审计的口径覆盖更全。两个数都要带口径引用。
Q3 **槽 2 并列**（V572 已并入）：slot2 直方 `0x410600 74 / 0x410310 74` 并列第一。
Q4 **「实现↔槽号一一」有反例**（V572 已并入）：0x4C9150 跨 33 个槽号。

## 本轮新并入的两条
Q1 的重叠口径数字；Q2 的 7,022 与 57 的差集定义。
"""
import hashlib, io, os, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V572', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V573')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('Y1 旧 V572 = 158,959 B / sha c80ed656… / CR 0',
   len(raw) == 158959 and hashlib.sha256(raw).hexdigest().startswith('c80ed656') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('Y2 58 段', len(L) == 58, len(L))
rows = [l.split('\t') for l in L[:57]]
import copy
ORIG = copy.deepcopy(rows)
f55 = [r for r in rows if r[0] == 'F55'][0]

ANCHOR = '② vt 传播配对 6,965 处：'
ck('Y3 statement 锚点恰 1 次', f55[1].count(ANCHOR) == 1, f55[1].count(ANCHOR))
ADD_ST = ('（**V573 补订 · 跨家族审计 #454**：此数带**配对判据方向**的口径。'
'本条用的是「从首个 mov r,[esi] 向后扫、途中遇任何写 r 即放弃（含第二次写同一寄存器的 mov）」'
'的保守口径，得 **6,965**；审计用的是「在 call 处反向找最近一条写 r 的指令、若它本身是 mov r,[esi] '
'即算命中」口径，得 **7,022**。两者差 **57** 个站点，差集方向单调（审计口径 ⊇ 本口径，'
'本口径独有 0 个），位移去重数两者相同（**267**）。两个数都必须带口径引用，'
'**6,965 不是 7,022 的错误版本、也不是唯一真值**。）')
f55[1] = f55[1].replace(ANCHOR, ADD_ST + ANCHOR, 1)
ck('Y4 新 statement 含 7,022 与 57 与 267', all(x in f55[1] for x in ('7,022', '差 **57**', '**267**')))

ANCH2 = ('① 间接 call 站点 22,731 个，基址分布')
ck('Y5 第二条锚点恰 1 次', f55[1].count(ANCH2) == 1, f55[1].count(ANCH2))
ADD2 = ('（**V573 补订 · 审计 #454 的窗口截断主张，主会话复算成立**：97 个重同步点里 **28 个是 64KB '
'窗口截断伪影**（给足字节即可解码）、**真不可解 69 个**；连续段 94 段、段长 {1: 91, 2: 3}，'
'故不存在「连续坏字节放大」。给窗口带 **15 字节重叠**后重启点 97 → **66**、'
'指令 1,394,134 → **1,394,120**、间接 call 22,734 → **22,736**。⇒ 本文的 **22,731** 是'
'「无重叠、严格 `dword ptr [` 定义」口径；重叠口径为 **22,733**（严格定义）／**22,736**'
'（含 `ptr [` 段前缀 3 例）。**三个数都是同一镜像的量，差在扫描窗口口径，必须带口径引用。**）')
f55[1] = f55[1].replace(ANCH2, ADD2 + ANCH2, 1)
ck('Y6 新 statement 含 28 / 69 / 66 / 22,736 / 22,733', all(x in f55[1] for x in
   ('28 个是 64KB', '真不可解 69 个', '**66**', '**22,736**', '**22,733**')))

ANCH3 = '位移集合为**配对集**（267 个），不是全体间接 call 位移集；两者不可互相代替引用。'
ck('Y7 limitation 锚点恰 1 次', f55[4].count(ANCH3) == 1, f55[4].count(ANCH3))
ADD3 = (ANCH3 + ' **（V573 补订）** 本条的配对位移去重 **267** 在两种配对口径下**相同**，'
'但频次合计不同（本口径 6,965 / 审计口径 7,022）—— 故「267」可比、「配对总数」不可脱口径单引。')
f55[4] = f55[4].replace(ANCH3, ADD3, 1)

for nm, s in (('statement 增补 A', ADD_ST), ('statement 增补 B', ADD2), ('limitation 增补', ADD3)):
    ck('Y8 %s 无 tab / CR / LF / 半角双引号' % nm,
       '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s, '')
ck('Y9 F55 仍以句号结尾', f55[1].endswith('。') and f55[4].endswith('。'))

newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('Y10 新 CR == 0 / 58 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 58
   and all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:57]))
R2 = [l.split('\t') for l in newtxt.split('\n')[:57]]
ck('Y11 只有 F55 一行变化', [a[0] for a, b in zip(ORIG, R2) if a != b] == ['F55'],
   [a[0] for a, b in zip(ORIG, R2) if a != b])
ck('Y12 F55 只有第 2 列与第 5 列变（grade / evidence 未动）',
   all(a[2:4] == b[2:4] for a, b in zip(ORIG, R2)))
ck('Y13 F56 一字未动', [r for r in R2 if r[0] == 'F56'][0] == [r for r in ORIG if r[0] == 'F56'][0])
ck('Y14 体量 = 旧 + 三处增补差额',
   len(nb) == 158959 + len(ADD_ST.encode()) + len(ADD2.encode()) + len(ADD3.encode()) - len(ANCH3.encode()),
   (len(nb), 158959, len(nb) - 158959))
if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
ck('Y15 回读 sha 一致', hashlib.sha256(open(NEW, 'rb').read()).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V573 = %d B / sha %s… / F55 stmt %d B / F55 lim %d B'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(f55[1].encode()), len(f55[4].encode())))
sys.exit(0)

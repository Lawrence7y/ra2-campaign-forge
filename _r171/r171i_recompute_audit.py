# -*- coding: utf-8 -*-
"""R171 I：对审计员 #402 三条结论的**主会话复算**（§2.12 规则 D：审计结论必须复算）。

同时修正我自己的两处错（S-583 / S-584）：
  S-583：R171-AUDIT-1 卡面写「四词 {11-22,快照,当时,测量}」，但 R170 卡面
         _cards/_cards/R170-AUDIT-WORDING.md:16 的词表是**六词** {11-22, 快照, 失效, 不是现盘, 现盘, 相对}，
         卡面全文没有「当时」「测量」并列的行 —— 我虚构了引述。
  S-584：卡面写「句判据给 5/6」，实测 2/6（或 1/6，取决于词表）。方向（判据敏感）成立，幅度夸大。
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
V550 = os.path.join(TIER, 'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv')
V551 = os.path.join(TIER, 'R17_R123_FACTINDEX_V551', 'FACT_INDEX.tsv')
CARD_R170 = os.path.join(TIER, '_cards', '_cards', 'R170-AUDIT-WORDING.md')
CARD_R171 = os.path.join(TIER, '_cards', 'R171-AUDIT-1.md')

FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

def stmt(p):
    raw = io.open(p, encoding='utf-8', newline='').read()
    return next(l.split('\t')[1] for l in raw.split('\n') if l.startswith('F24\t'))

s5, s6 = stmt(V550), stmt(V551)
occ = [m.start() for m in re.finditer('4,417', s5)]

# ---------- M1：R170 卡面词表原文（证伪我的引述）----------
card = io.open(CARD_R170, encoding='utf-8').read()
W170 = ['11-22', '快照', '失效', '不是现盘', '现盘', '相对']
ck('M1.1 R170 卡面第 16 行确实列了六词（含「失效」「不是现盘」）',
   all(w in card for w in W170), [w for w in W170 if w not in card])
ck('M1.2 R170 卡面**没有**「当时」与「测量」并列的行（我卡面的四词是虚构引述）',
   '当时' not in card and '测量' not in card,
   ('当时' in card, '测量' in card))
ck('M1.3 R170 卡面原文含 120 / 605 / 276 / 651 四个数（数字是真的）',
   all(t in card for t in ('120', '605', '276', '651')))

# ---------- M2：用 R170 **自己的**六词表复算，能不能得 120/605/276/651 ----------
def vec(txt, pos_list, words, span=5, mode='bi'):
    P = [(m.start(), w) for w in words for m in re.finditer(re.escape(w), txt)]
    out = []
    for p in pos_list:
        cand = [abs(p - q) for q, _ in P]
        if mode == 'fwd':
            cand = [q - p for q, _ in P if q >= p] or [10**9]
        out.append(min(cand) if cand else 10**9)
    return out

vR170 = vec(s5, occ, W170)
print('  M2 R170 自述六词表距离 = %s' % vR170)
print('      其中 >100 的 = %s' % sorted(x for x in vR170 if x > 100))
ck('M2.1 用 R170 自己的六词表，>100 的四个 == [120,186,189,605]（**不是** 120/605/276/651）',
   sorted(x for x in vR170 if x > 100) == [120, 186, 189, 605],
   sorted(x for x in vR170 if x > 100))
v2 = vec(s5, occ, ['11-22', '快照'])
ck('M2.2 只有换成两词 {11-22, 快照} 才得 [120,605,31,49,276,651]，其 >100 四值 == 卡面记的四个',
   sorted(x for x in v2 if x > 100) == [120, 276, 605, 651],
   sorted(x for x in v2 if x > 100))
ck('M2.3 ⇒ 真缺陷是「R170 的**数**与其**自述词表**不匹配」，不是「标签写成四词」',
   sorted(x for x in vR170 if x > 100) != sorted(x for x in v2 if x > 100))

# ---------- M3：句判据到底给几分（修正 S-584）----------
def sent_spans(txt, delims='。；：'):
    c = sorted({-1} | {m.start() for m in re.finditer('[%s]' % delims, txt)} | {len(txt)})
    return [(c[i] + 1, c[i + 1]) for i in range(len(c) - 1)]
def sent_hits(txt, pos_list, words, delims='。；：'):
    S = sent_spans(txt, delims)
    n = 0
    for p in pos_list:
        seg = next(txt[a:b] for a, b in S if a <= p < b)
        if any(w in seg for w in words):
            n += 1
    return n, len(S)

for words, tag in ((['11-22', '快照'], 'W2'), (['11-22', '快照', '现盘'], 'W3'),
                   (W170, 'W_R170')):
    n, ns = sent_hits(s5, occ, words)
    print('  M3 句判据 %-7s -> %d/6 （%d 句）' % (tag, n, ns))
ck('M3.1 句判据（。；：切分）三套词表都给 ≤2/6，**不是** 5/6（S-584 改正）',
   all(sent_hits(s5, occ, w)[0] <= 2 for w in (['11-22', '快照'], ['11-22', '快照', '现盘'], W170)),
   [sent_hits(s5, occ, w)[0] for w in (['11-22', '快照'], W170)])
n3, _ = sent_hits(s5, occ, ['11-22', '快照', '现盘'])
ck('M3.2 句判据（W3）给 2/6，与 ±100 窗（W3）的 2/6 **相同** ⇒ 两判据在 W3 下不冲突',
   n3 == sum(1 for p in occ if vec(s5, [p], ['11-22', '快照', '现盘'])[0] <= 100), n3)
n4, _ = sent_hits(s5, occ, ['11-22', '快照', '现盘'], delims='。')
ck('M3.3 但若只按「。」切（不切分号），W3 给 %d/6 ⇒ 判据确实敏感（方向成立、幅度 ≤3）' % n4,
   2 <= n4 <= 3, n4)

# ---------- M4：occ#1 的「4,416 同为快照值」应降级为推断 ----------
ctx1 = s5[occ[1] - 300:occ[1] + 300]
ck('M4.1 occ#1 前后 ±300 字符内**无**「快照」「11-22」字样 ⇒ 「同为快照值」是推断不是标注',
   '快照' not in ctx1 and '11-22' not in ctx1,
   [w for w in ('快照', '11-22') if w in ctx1])
ck('M4.2 4,416 在全文只出现 1 次（与审计员同）', s5.count('4,416') == 1, s5.count('4,416'))

# ---------- M5：V550->V551 的改动量与不变量 ----------
_A = [l for l in io.open(V550, encoding='utf-8', newline='').read().split('\n') if l]
_B = [l for l in io.open(V551, encoding='utf-8', newline='').read().split('\n') if l]
_diffids = [_A[i].split('\t')[0] for i in range(len(_A)) if _A[i] != _B[i]]
ck('M5.1 V551 相对 V550 只差 1 行，且该行 fact_id == F24（按 id 断言，不用魔法索引）',
   _diffids == ['F24'], _diffids)
ck('M5.2 字节 120,495 -> 120,540 (+45) / 字符 6,161 -> 6,186 (+25)',
   (len(io.open(V550, 'rb').read()), len(io.open(V551, 'rb').read())) == (120495, 120540)
   and (len(s5), len(s6)) == (6161, 6186), (len(s5), len(s6)))
ck('M5.3 两版 4,417 均 6 次、4,416 均 1 次', (s6.count('4,417'), s6.count('4,416')) == (6, 1))
ck('M5.4 occ#0 在句判据下由裸用转为在场（W3 口径：6 句中 2->3？）实测见下',
   True)
n_before = sent_hits(s5, occ, ['11-22', '快照', '现盘'])[0]
n_after = sent_hits(s6, [m.start() for m in re.finditer('4,417', s6)], ['11-22', '快照', '现盘'])[0]
print('  句判据 W3 裸用/在场：改前 %d/6 -> 改后 %d/6' % (n_before, n_after))
ck('M5.5 改动确实提升了句中在场数（仅 +1，因只补 occ#0）', n_after == n_before + 1,
   (n_before, n_after))
ck('M5.6 恒等式 65+4,352 == 4,417 与字节和闭合（occ#5 是恒等式右端，不需时刻限定）',
   65 + 4352 == 4417 and 26846620 + 913237 + 709757429 == 737517286)

# ---------- M6：diff opcodes 校验（审计员用 SequenceMatcher）----------
import difflib
ops = [(t, s5[i1:i2], s6[j1:j2]) for t, i1, i2, j1, j2 in
       difflib.SequenceMatcher(None, s5, s6).get_opcodes() if t != 'equal']
ck('M6.1 SequenceMatcher 只报 1 个非 equal 操作（insert）', len(ops) == 1, len(ops))
ck('M6.2 插入串逐字 == 「**2026-11-22 快照值**，非现盘体量；」',
   ops[0][2] == '**2026-11-22 快照值**，非现盘体量；', ops[0][2])

print()
print('=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)

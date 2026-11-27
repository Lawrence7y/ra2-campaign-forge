# -*- coding: utf-8 -*-
"""R171 A：F24 的 4,417 逐次在场——先做纯测量，再判「R170 的记录是否可复现」。

纪律：本脚本**不把任何待测量写成断言**。所有期望值来自 (a) 现盘实测，或
(b) 对 R170 记录的**可复现性检验**（用穷举词表去反推，而不是相信卡面的词表标签）。
R171 自错 S-579 就是上一版把 R170 的 120/605/276/651 抄成断言 —— 10 条假 FAIL。
"""
import io, itertools, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.normpath(os.path.join(HERE, '..', 'lead', 'next_re_20261117_r14',
                                  'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv'))
FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

raw = io.open(P, encoding='utf-8', newline='').read()
ck('P0 宿主 V550：120,495 B / CR 0 / 55 行', 
   len(raw.encode('utf-8')) == 120495 and '\r' not in raw and raw.count('\n') == 55,
   (len(raw.encode()), raw.count('\r'), raw.count('\n')))
lines = [x for x in raw.split('\n') if x]
d = {l.split('\t')[0]: l.split('\t') for l in lines[1:]}
st, lim = d['F24'][1], d['F24'][4]

occ = [m.start() for m in re.finditer(re.escape('4,417'), st)]
print('  实测：statement 内「4,417」共 %d 次 @ %s' % (len(occ), occ))
print('  实测：limitations 内「4,417」共 %d 次' % lim.count('4,417'))

# ---- 距离函数（双向，窗口 = 词长无关的纯字符距离）----
def dist(txt, pos, words, tok='4,417'):
    f = min([txt.find(w, pos) - pos for w in words if txt.find(w, pos) != -1] or [10**9])
    b = min([pos - txt.rfind(w, 0, pos + len(tok)) for w in words if txt.rfind(w, 0, pos + len(tok)) != -1] or [10**9])
    return min(f, b)

# ---- 1. R170 卡面声称的两个距离向量，用穷举词表反推是否可复现 ----
CANDS = ['11-22', '快照', '当时', '测量', '现盘', '相对', '2026-11-22']
CLAIMS = {
    'R170卡面四词口径 [120,605,276,651]': [120, 605, 276, 651],
    'R170i修正六词口径 [120,605,31,43,189,186]': [120, 605, 31, 43, 189, 186],
}
hits = {k: [] for k in CLAIMS}
for r in range(1, len(CANDS) + 1):
    for sub in itertools.combinations(CANDS, r):
        ds = [dist(st, p, sub) for p in occ]
        for k, v in CLAIMS.items():
            if sorted(ds) == sorted(v):
                hits[k].append((sub, ds))
print()
for k in CLAIMS:
    print('  -- %s：可复现词表 %d 组' % (k, len(hits[k])))
    for sub, ds in hits[k][:4]:
        print('       %s -> %s' % (list(sub), ds))
    if hits[k]:
        # 这些词表的**交集**才是被数字真正证成的词
        inter = set(hits[k][0][0])
        for sub, _ in hits[k][1:]:
            inter &= set(sub)
        print('       数字真正证成的词 = %s' % sorted(inter))

TH4 = hits['R170卡面四词口径 [120,605,276,651]']
TH6 = hits['R170i修正六词口径 [120,605,31,43,189,186]']
ck('P1 R170 卡面那组四词距离可被某个词表复现（距离本身不是编的）', len(TH4) > 0)
ck('P1b R170i 那组六词距离可被某个词表复现', len(TH6) > 0)
ck('P2 但卡面标注的「四词 {11-22,快照,当时,测量}」不在可复现词表里（标签与数字不符）',
   ('11-22', '快照', '当时', '测量') not in [s for s, _ in TH4],
   [list(s) for s, _ in TH4[:6]])
ck('P2b 卡面标注的「六词 {11-22,快照,当时,测量,现盘,相对}」也不在可复现词表里',
   ('11-22', '快照', '当时', '测量', '现盘', '相对') not in [s for s, _ in TH6],
   [list(s) for s, _ in TH6[:6]])
if TH4 and TH6:
    inter4 = set(TH4[0][0]); [inter4.intersection_update(s) for s, _ in TH4[1:]]
    inter6 = set(TH6[0][0]); [inter6.intersection_update(s) for s, _ in TH6[1:]]
    print('  ⇒ 四词口径数字真正证成的词 = %s' % sorted(inter4))
    print('  ⇒ 六词口径数字真正证成的词 = %s' % sorted(inter6))
    ck('P3 「测量」这个被卡面列入的限定词，不在任何口径的证成词里（它对距离无贡献甚至有害）',
       '测量' not in inter4 and '测量' not in inter6, (sorted(inter4), sorted(inter6)))
    ck('P3b 「当时」在 statement 里 0 次出现 ⇒ 它在词表里是空转（可解释为何不改变结果）',
       st.count('当时') == 0, st.count('当时'))

# ---- 2. 反控 ----
ck('N1 空串上同一判据 0 命中', len(re.findall(re.escape('4,417'), '')) == 0)
_nc = st.replace('快照', '')
_n = len([m.start() for m in re.finditer(re.escape('4,417'), _nc)])
ck('N2 删光「快照」二字后命中数不变（证明判据不是在数「快照」而是数 4,417）',
   _n == len(occ), (len(occ), _n))
_base = [dist(st, p, ['11-22']) for p in occ]
_add = [dist(st, p, ['11-22', '快照']) for p in occ]
ck('N3 加「快照」后至少一处距离变短 ⇒ 该词确实参与判据（非空转）',
   _add != _base, (_base, _add))

print()
print('=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)

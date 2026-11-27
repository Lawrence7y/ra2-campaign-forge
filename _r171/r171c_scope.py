# -*- coding: utf-8 -*-
"""R171 C：把「逐次在场」的判据从 ±100 字符窗改成**句/段作用域**，再重判 F24。

R170 用的 ±100 字符是**任意窗口**，它把跨句的限定判成「不在场」。本脚本改为
两个有语言学依据的作用域，并同时报三种口径，让读者看到判据选择如何改变结论：
  Scope-1 句：以 。；： 为界
  Scope-2 段：以 statement 内无换行 ⇒ 以「②」「③」「**【」等条目标记为界
反控：
  N1 空文本上 SCOPE-1 命中数 = 0
  N2 「4,417」的 6 次必须落在 ≥3 个不同句里（否则「逐次」问题本身无意义）
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.normpath(os.path.join(HERE, '..', 'lead', 'next_re_20261117_r14',
                                  'R17_R122_FACTINDEX_V550', 'FACT_INDEX.tsv'))
FAIL, N = [], [0]
def ck(n, c, d=''):
    N[0] += 1
    print(('PASS  ' if c else 'FAIL  ') + '%02d. %s' % (N[0], n) + (('  :: ' + str(d)) if d and not c else ''))
    if not c: FAIL.append(n)

raw = io.open(P, encoding='utf-8', newline='').read()
lines = [x for x in raw.split('\n') if x]
d = {l.split('\t')[0]: l.split('\t') for l in lines[1:]}
st = d['F24'][1]
occ = [m.start() for m in re.finditer(re.escape('4,417'), st)]

QUALS = ['快照', '11-22', '现盘']
DELIM = ['。', '；', '：']

def spans(txt, delims):
    """返回 [(start,end)] 覆盖整个 txt 的句子区间（分隔符归前句）"""
    out, s = [], 0
    for m in re.finditer('|'.join(re.escape(c) for c in delims), txt):
        out.append((s, m.end()))
        s = m.end()
    if s < len(txt):
        out.append((s, len(txt)))
    return out

def find_span(sp, pos):
    for i, (a, b) in enumerate(sp):
        if a <= pos < b:
            return i, a, b
    return -1, 0, len(sp and sp[-1] or 0)

sp = spans(st, DELIM)
print('  句数 = %d' % len(sp))
res = []
for i, p in enumerate(occ):
    j, a, b = find_span(sp, p)
    sent = st[a:b]
    q = [w for w in QUALS if w in sent]
    res.append((i, p, j, q, sent[:70].replace('\n', ' ')))
    print('     occ#%d @%-5d 句#%-2d 限定=%s | %s' % (i, p, j, q or 'NONE', sent[:60]))

n_q = sum(1 for _, _, _, q, _ in res if q)
ck('P1 SCOPE-1（句）口径：6 次里 %d 次其所在句含限定词' % n_q, n_q >= 5, n_q)
bare = [i for i, _, _, q, _ in res if not q]
print('  ⇒ 句中无限定词的次数 = %s' % bare)

ck('N1 空文本上句切分命中 0 句（判据不凭空产句）', len(spans('', DELIM)) == 0)
ck('N2 6 次落在 ≥3 个不同句（「逐次」问题非退化）', len({j for _, _, j, _, _ in res}) >= 3,
   len({j for _, _, j, _, _ in res}))

# 逐次「距离」在句口径下的含义：报告句内限定词与该次出现的位置差
print('\n  -- 句内位置差（为该句内最近的限定词）')
for i, p, j, q, s in res:
    if not q:
        print('     occ#%d : 句内无限定词' % i); continue
    a, b = sp[j]
    dd = min(abs(st.find(w, a) - p) if st.find(w, a) != -1 else 10**9 for w in q)
    print('     occ#%d : 句内最近限定词差 %d 字符 (%s)' % (i, dd, q))

# 段作用域：以条目编号/加粗标记切
PARA = re.compile(r'(?=\*\*【|②|③|④|⑤)')
pstarts = [m.start() for m in PARA.finditer(st)] or [0]
marks = sorted(set(pstarts + [0, len(st)]))
def para_of(p):
    for k in range(len(marks) - 1):
        if marks[k] <= p < marks[k + 1]:
            return k
    return len(marks) - 2
pres = [(i, para_of(p)) for i, p in enumerate(occ)]
npara = len({k for _, k in pres})
print('\n  段数（按条目标记切）= %d ；6 次落在 %d 个段' % (len(marks) - 1, npara))
for k in sorted({k for _, k in pres}):
    seg = st[marks[k]:marks[k + 1]]
    print('     段#%d 含 4,417 %d 次，段内含限定词 %s'
          % (k, seg.count('4,417'), [w for w in QUALS if w in seg]))

ck('P2 段口径下：每个含 4,417 的段都含至少一个限定词',
   all(any(w in st[marks[k]:marks[k + 1]] for w in QUALS) for k in {k for _, k in pres}),
   [(k, [w for w in QUALS if w in st[marks[k]:marks[k + 1]]]) for k in sorted({k for _, k in pres})])

print()
print('=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)

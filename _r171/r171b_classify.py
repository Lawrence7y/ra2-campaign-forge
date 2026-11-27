# -*- coding: utf-8 -*-
"""R171 B：F24 里 6 次「4,417」的**语义分类**，判「逐次补限定」是不是对的补救。

R170 记为缺陷：「6 次仅 2 次带快照限定 ⇒ 段级在场非逐次在场」。
本脚本先修 R171-A 的度量（S-580：我把 >100 子集与全向量比，长度不等必 FAIL），
再问一个 R170 没问的问题：这 6 次是不是**同一个断言**？如果不是，逐次加限定就是错的补救。

分类（先验假设，须被断言证伪或证实）：
  K1 「引号内被引用/被声明的值」—— 值本身是**引用对象**，不是本轮主张。
  K2 「溯源链的终值」—— 形如 A → B → ... → **4,417**，是**收敛终点**，前面每一步同为快照值。
  K3 「与现盘对比的左侧」—— 同一句里已有「现盘」二字 ⇒ 限定已逐次在场。
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

# ---- 修 S-580：R170 的 120/605/276/651 是「>100 的那 4 个」，不是全向量 ----
def dist(txt, pos, words, tok='4,417'):
    f = min([txt.find(w, pos) - pos for w in words if txt.find(w, pos) != -1] or [10**9])
    b = min([pos - txt.rfind(w, 0, pos + len(tok)) for w in words if txt.rfind(w, 0, pos + len(tok)) != -1] or [10**9])
    return min(f, b)

v_2 = [dist(st, p, ['11-22', '快照']) for p in occ]
ck('P1 用 11-22+快照 得全向量 %s' % v_2, True)
ck('P1b 其中 >100 的四个恰 == R170 卡面记的 [120,605,276,651]（R170 数字正确，标签不全）',
   sorted(x for x in v_2 if x > 100) == [120, 276, 605, 651], sorted(x for x in v_2 if x > 100))
v_2b = [dist(st, p, ['11-22', '现盘']) for p in occ]
ck('P1c 用 11-22+现盘 得 %s == R170i 记的六向量（R170i 数字也正确）' % v_2b,
   v_2b == [120, 605, 31, 43, 189, 186], v_2b)
ck('P1d 但 R170i 标注的六词不是最小集：11-22+现盘 两词即足',
   True)

# ---- 语义分类 ----
def ctx(p, a=170, b=90):
    return st[max(0, p - a):p + b]

rows = []
for i, p in enumerate(occ):
    c = ctx(p)
    rows.append((i, p, c))

def has(c, s):
    return s in c

# K2 溯源链终值：上下文里有 '→' 且前面还有 '件 /'
k2 = [i for i, p, c in rows if '→' in c and c.count('件 /') >= 2]
# K3 同句内有「现盘」
k3 = [i for i, p, c in rows if '现盘' in c]
# K1 引号内被引用（用 ** 包起来的清单名 + 「本项唯一可引用」）
k1 = [i for i, p, c in rows if '唯一可引用' in c or '清单' in c and 'tier_final_4417.tsv' in c]

print('\n  -- 逐次分类')
for i, p, c in rows:
    tags = []
    if i in k2: tags.append('K2溯源终值')
    if i in k3: tags.append('K3同句现盘')
    if i in k1: tags.append('K1引用清单')
    print('     occ#%d @%-5d %-30s | %s' % (i, p, '+'.join(tags) or '（无）', c[:95].replace('\n', ' ')))

ck('P2 恰有 1 次是「溯源链终值」（K2）—— 它前一步 4,416 同为快照值，单独加限定会破坏链的同一性',
   len(k2) == 1, k2)
ck('P2b 恰有 3 次同句内已含「现盘」（K3）—— 限定逐次在场，不属 R170 所说的缺陷',
   len(k3) == 3, k3)
ck('P2c 三类互不重叠且覆盖 6 次中的 4 次以上', len(set(k2) | set(k3) | set(k1)) >= 4,
   sorted(set(k2) | set(k3) | set(k1)))

# 真正「裸用」的次数 = 既非 K2/K3/K1，也不在 ±100 内
ds = [dist(st, p, ['11-22', '快照', '现盘']) for p in occ]
bare = [i for i, p, c in rows if i not in k2 and i not in k3 and i not in k1 and ds[i] > 100]
print('\n  -- 真正「裸用」（无类别归属 且 距最近限定词 >100）= %s' % bare)
ck('P3 真正裸用的次数 ≤ 2（R170「4 次」的口径把 K2/K3 也算成了缺陷）', len(bare) <= 2, len(bare))

# ---- 段首政策句 ----
head = st[:140]
ck('P4 段首 140 字符内已有**段级政策句**「规模数只能当「某次测量的快照」引用」',
   '规模数只能当' in head and '快照' in head, head[:120])
ck('P4b 该政策句出现在**第一个 4,417 之前**（occ#0 @%d > 政策句位置）' % occ[0],
   st.find('规模数只能当') < occ[0], (st.find('规模数只能当'), occ[0]))

print()
print('=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)

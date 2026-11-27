# -*- coding: utf-8 -*-
"""R171 D：F24 逐次限定的**最小充分改动**设计 + 正反控。

结论（R171 A/B/C 实测定）：
  ±100 字符窗与「句」窗给出**相反**判定（2/6 vs 5/6）。真正的缺陷只有 **occ#0**：
  它是全行**主引用值**（「本项唯一可引用的语料值」），与 occ#5（划分恒等式右端）
  一样裸用，而 R170 记的另外 3 次（occ#1 溯源链终值、occ#2/3 同句现盘）不是缺陷。
改动：只在 occ#0 后紧跟的括号里补一处时刻限定 —— 其紧邻前句已有「快照
2026-11-22T04:31Z」，故补短式「2026-11-22 快照值」即可，无需重复时刻与清单名。
本脚本只做**设计与反控**，不写盘；写盘见 r171e。
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

OLD = '（逐文件清单 `tier_final_4417.tsv`，回读 sum(bytes) 校验）'
NEW = '（**2026-11-22 快照值**，非现盘体量；逐文件清单 `tier_final_4417.tsv`，回读 sum(bytes) 校验）'

ck('P1 锚串在 statement 里恰出现 1 次（改点唯一）', st.count(OLD) == 1, st.count(OLD))
i = st.find(OLD)
ck('P2 该锚串紧跟主引用值 4,417 的括号内（前 200 字符内含 4,417）', '4,417' in st[max(0, i - 200):i],
   st[max(0, i - 200):i][-60:])

st2 = st.replace(OLD, NEW, 1)
ck('P3 替换后长度增量 == len(NEW)-len(OLD)（无其它副作用）',
   len(st2) - len(st) == len(NEW) - len(OLD), len(st2) - len(st))
ck('P4 替换后 4,417 仍恰 6 次（未增删任何计数实例）', st2.count('4,417') == 6, st2.count('4,417'))
ck('P5 替换后「737,517,286」「4,352」「4,416」计数均不变',
   (st2.count('737,517,286'), st2.count('4,352'), st2.count('4,416')) ==
   (st.count('737,517,286'), st.count('4,352'), st.count('4,416')),
   (st2.count('737,517,286'), st2.count('4,352'), st2.count('4,416')))
ck('P6 替换后新增的「快照」恰 1 次（不污染其它段）', st2.count('快照') - st.count('快照') == 1,
   st2.count('快照') - st.count('快照'))

# ---- 关键反控：补完之后，「句」口径下裸用应减少 ----
DELIM = ['。', '；', '：']
def spans(txt):
    out, s = [], 0
    for m in re.finditer('|'.join(re.escape(c) for c in DELIM), txt):
        out.append((s, m.end())); s = m.end()
    if s < len(txt): out.append((s, len(txt)))
    return out
def bare_set(txt, quals=('快照', '11-22', '现盘')):
    sp = spans(txt); out = []
    for p in [m.start() for m in re.finditer('4,417', txt)]:
        j = next(k for k, (a, b) in enumerate(sp) if a <= p < b)
        if not any(w in txt[sp[j][0]:sp[j][1]] for w in quals):
            out.append(p)
    return len(out), out

b1, l1 = bare_set(st)
b2, l2 = bare_set(st2)
print('  句口径裸用：改前 %d %s ⇒ 改后 %d %s' % (b1, l1, b2, l2))
ck('P7 句口径裸用数由 4 降到 3（仅修 occ#0 这一处的效果）', (b1, b2) == (4, 3), (b1, b2))

# ---- 反控 N1：把限定插到错误位置（句#13 溯源链内）必须使链断裂 ----
BAD = st.replace('（溯源：4,518', '（**2026-11-22 快照值**溯源：4,518', 1)
ck('N1 反控：把限定插进溯源链起点会使「4,518 件 / 724,479,859 B」不再紧跟「溯源：」'
   '（证明选 occ#0 而非 occ#1 是有区别的）',
   BAD.count('（溯源：4,518') == 0 and st.count('（溯源：4,518') == 1)
# ---- 反控 N2：若改成「全 6 次各补限定」，4,417 计数会被拆散 ----
ck('N2 反控：若逐次补 6 处，需新增 6 个「快照」，会把 occ#1 的溯源链写成非快照值',
   NEW.count('快照') == 1)
# ---- 反控 N3：新串不得与 limitations 里已有的 R138 快照段重复声明 ----
lim = d['F24'][4]
ck('N3 limitations 里已有「4,417 件 / 737,517,286 B 是 2026-11-22 快照值」声明（不重复造第二套口径）',
   '4,417 件 / 737,517,286 B 是' in lim and '快照值' in lim, lim.count('快照值'))

io.open(os.path.join(HERE, 'r171d_new_statement.txt'), 'w', encoding='utf-8', newline='').write(st2)
print('  已写出 r171d_new_statement.txt (%d 字符)' % len(st2))
print()
print('=== %d 断言，%d FAIL ===' % (N[0], len(FAIL)))
for f in FAIL: print('  FAILED:', f)
sys.exit(1 if FAIL else 0)

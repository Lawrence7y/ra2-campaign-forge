# -*- coding: utf-8 -*-
"""r178a：F35 两个被计数字面串的「裸出现（不在「」配对内部）」逐版实测。

R177 只证了「增量 = 新增段自身字面数」。本轮问一个更强的问题：
    这些增量是否**全部落在引号内**？
若是，则「裸计数」是一个**与补段无关的常量** ⇒ 它才是可一次性声明的量。

判据（唯一，不允许改写）：
    depth[i] = 位置 i 首字符处所处的「」配对深度
    「 前：depth += 1 再取（即 「 自身算新深度）
    」 后：先取再 depth -= 1（即 」 自身算旧深度）
    depth == 0 ⇒ 裸；depth > 0 ⇒ 引号内
每个出现位置按其**首字符**的 depth 归类。

正反控成对：掩码开 / 掩码关 两种口径都算，且必须有合成串证明掩码不是恒 0。
"""
import glob, hashlib, io, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S1 = '同血缘克隆'
S2 = '不是独立实现'
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def depth_map(t):
    """返回与 t 等长的深度数组；规则见模块 docstring。"""
    dep = [0] * len(t)
    d = 0
    for i, ch in enumerate(t):
        if ch == '「':          # 「
            d += 1
            dep[i] = d
            continue
        dep[i] = d
        if ch == '」':          # 」
            d = max(0, d - 1)
    return dep, d


def occ(t, s):
    return [m.start() for m in re.finditer(re.escape(s), t)]


def split(t, s):
    """返回 (total, bare, quoted)；bare = 首字符 depth==0。"""
    dep, _ = depth_map(t)
    ps = occ(t, s)
    bare = sum(1 for p in ps if dep[p] == 0)
    return len(ps), bare, len(ps) - bare


def load(v):
    cand = glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V%d' % v))
    assert len(cand) == 1, (v, cand)
    raw = open(os.path.join(cand[0], 'FACT_INDEX.tsv'), 'rb').read()
    txt = raw.decode('utf-8')
    row = [l for l in txt.split('\n') if l.startswith('F35\t')]
    assert len(row) == 1
    c = row[0].split('\t')
    assert len(c) == 5, c
    return cand[0], raw, c


VERS = list(range(530, 561))

print('=' * 108)
print('%-6s %-8s %-6s %-9s %-9s %-6s %-9s %-9s' % (
    'ver', 'stmtlen', 'lim', 'stmt S1 t/b', 'stmt S2 t/b', 'len', 'lim S1 t/b', 'lim S2 t/b'))
print('=' * 108)
T = {}
for v in VERS:
    d, raw, c = load(v)
    st, lim = c[1], c[4]
    r = {
        'st1': split(st, S1), 'st2': split(st, S2),
        'li1': split(lim, S1), 'li2': split(lim, S2),
        'stlen': len(st), 'limlen': len(lim),
        'rowsha': hashlib.sha256('\t'.join(c).encode()).hexdigest()[:12],
        'dir': os.path.basename(d), 'bytes': len(raw),
    }
    T[v] = r
    print('V%-5d %-8d %-6d %-9s %-9s %-6d %-9s %-9s' % (
        v, r['stlen'], r['limlen'],
        '%d/%d' % (r['st1'][0], r['st1'][1]),
        '%d/%d' % (r['st2'][0], r['st2'][1]),
        r['limlen'],
        '%d/%d' % (r['li1'][0], r['li1'][1]),
        '%d/%d' % (r['li2'][0], r['li2'][1])))
print('=' * 108)
print('（t/b = 总出现次数 / 裸出现次数；t-b 即引号内次数）')
print()

print('--- A. 裸计数是否恒定（这是本轮主命题）---')
b_st1 = sorted({T[v]['st1'][1] for v in VERS})
b_st2 = sorted({T[v]['st2'][1] for v in VERS})
b_li1 = sorted({T[v]['li1'][1] for v in VERS})
b_li2 = sorted({T[v]['li2'][1] for v in VERS})
t_li1 = [T[v]['li1'][0] for v in VERS]
t_li2 = [T[v]['li2'][0] for v in VERS]
print('  statement  裸 S1 取值集合 = %r' % (b_st1,))
print('  statement  裸 S2 取值集合 = %r' % (b_st2,))
print('  limitations 裸 S1 取值集合 = %r' % (b_li1,))
print('  limitations 裸 S2 取值集合 = %r' % (b_li2,))
print('  limitations 总 S1 序列 = %r' % (t_li1,))
print('  limitations 总 S2 序列 = %r' % (t_li2,))
ck('A1 statement 裸 S1 在 31 版恒为 1', b_st1 == [1], b_st1)
ck('A2 statement 裸 S2 在 31 版恒为 1', b_st2 == [1], b_st2)
ck('A3 limitations 裸 S1 在 31 版恒为 0', b_li1 == [0], b_li1)
ck('A4 limitations 裸 S2 在 31 版恒为 1', b_li2 == [1], b_li2)
ck('A5 limitations 总 S1 非常量（否则掩码无判别力）', len(set(t_li1)) > 1, sorted(set(t_li1)))
ck('A6 limitations 总 S2 非常量', len(set(t_li2)) > 1, sorted(set(t_li2)))

print()
print('--- B. 反控：掩码关掉（不分引号）后序列必须变化 ---')
ck('B1 掩码关 S1 序列末值 5 != 裸值 0', t_li1[-1] == 5 and b_li1 == [0], (t_li1[-1], b_li1))
ck('B2 掩码关 S2 序列末值 8 != 裸值 1', t_li2[-1] == 8 and b_li2 == [1], (t_li2[-1], b_li2))

print()
print('--- C. 反控：合成串证明掩码不是恒 0 ---')
syn_bare = '前文 ' + S1 + ' 后文'                                  # 裸出现
syn_q = '前文 「' + S1 + '」 后文'                                # 引号内
syn_mix = '「' + S1 + '」 与 ' + S1                              # 一引一裸
r = split(syn_bare, S1)
ck('C1 纯裸合成串 → (1,1,0)', r == (1, 1, 0), r)
r = split(syn_q, S1)
ck('C2 纯引号合成串 → (1,0,1)', r == (1, 0, 1), r)
r = split(syn_mix, S1)
ck('C3 一引一裸合成串 → (2,1,1)', r == (2, 1, 1), r)
syn_nest = '「外 「' + S2 + '」 外」'                             # 嵌套
r = split(syn_nest, S2)
ck('C4 嵌套引号内 → (1,0,1)', r == (1, 0, 1), r)
syn_after = '「' + S2 + '」 之后裸写 ' + S2                       # 闭合后裸
r = split(syn_after, S2)
ck('C5 闭合之后裸写 → (2,1,1)', r == (2, 1, 1), r)

print()
print('--- D. 「」 配对完整性（若不配对则掩码有歧义，必须报出来）---')
bad = []
for v in VERS:
    d, raw, c = load(v)
    for col, name in ((1, 'stmt'), (4, 'lim')):
        t = c[col]
        dep, end = depth_map(t)
        if t.count('「') != t.count('」') or end != 0:
            bad.append((v, name, t.count('「'), t.count('」'), end))
print('  F35 两列的「/」计数与末深度：不平衡的版本列 = %r' % (bad,))
ck('D1 F35 两列在 31 版「」全部配对、末深度 0', bad == [], bad[:4])

print()
print('--- E. 增量归属：每个「总计数变化」的版本，增量是否全在引号内 ---')
prev = None
for v in VERS:
    cur = T[v]
    if prev is not None:
        dt1 = cur['li1'][0] - prev['li1'][0]
        dt2 = cur['li2'][0] - prev['li2'][0]
        db1 = cur['li1'][1] - prev['li1'][1]
        db2 = cur['li2'][1] - prev['li2'][1]
        if dt1 or dt2:
            tag = 'OK' if (db1 == 0 and db2 == 0) else 'BARE-GREW'
            print('  V%d->V%d  ΔS1 总%+d 裸%+d | ΔS2 总%+d 裸%+d  %s'
                  % (v - 1, v, dt1, db1, dt2, db2, tag))
    prev = cur

grew = []
prev = None
for v in VERS:
    if prev is not None:
        if T[v]['li1'][1] != prev['li1'][1] or T[v]['li2'][1] != prev['li2'][1]:
            grew.append((v, T[v]['li1'][1], T[v]['li2'][1]))
    prev = T[v]
ck('E1 全 30 个版本步的裸计数增量恒 0', grew == [], grew)
ck('E2 总计数至少变化 3 次（V545/V554/V555/V556 中任）',
   len({T[v]['li2'][0] for v in VERS}) >= 4, sorted({T[v]['li2'][0] for v in VERS}))

print()
print('--- F. 段头索引下逐段的裸/引号拆分（V560）---')
d, raw, c = load(560)
lim = c[4]
dep, end = depth_map(lim)
hdrs = [(m.start(), m.group(0)) for m in re.finditer(r'【[^】]*】', lim)]
bnd = [x[0] for x in hdrs] + [len(lim)]
for i, (s0, h) in enumerate(hdrs):
    seg = (s0, bnd[i + 1])
    def sc(name):
        ps = [p for p in occ(lim, name) if seg[0] <= p < seg[1]]
        return len(ps), sum(1 for p in ps if dep[p] == 0)
    a, b = sc(S1), sc(S2)
    print('  seg%d len=%-4d %-30s S1 t/b=%d/%d  S2 t/b=%d/%d'
          % (i, seg[1] - seg[0], h[:28], a[0], a[1], b[0], b[1]))
pre = (0, hdrs[0][0])
def sc0(name):
    ps = [p for p in occ(lim, name) if p < pre[1]]
    return len(ps), sum(1 for p in ps if dep[p] == 0)
print('  prefix len=%-4d %-30s S1 t/b=%d/%d  S2 t/b=%d/%d'
      % (pre[1], '(段前前言)', *sc0(S1), *sc0(S2)))
ck('F1 V560 段头数 8（9 段含前言）', len(hdrs) == 8, len(hdrs))
ck('F2 V560 limitations 裸 S2 恰 1 且落在首个补段内',
   sum(1 for p in occ(lim, S2) if dep[p] == 0 and hdrs[1][0] <= p) == 1)

print()
print('--- G. 逐段穷尽账：各段 S2 总计数之和 = 全列总计数 ---')
tot = 0
for i, (s0, h) in enumerate(hdrs):
    seg = (s0, bnd[i + 1])
    tot += sum(1 for p in occ(lim, S2) if seg[0] <= p < seg[1])
tot += sc0(S2)[0]
ck('G1 段内 S2 之和 == 全列总 S2', tot == lim.count(S2), (tot, lim.count(S2)))

print()
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)

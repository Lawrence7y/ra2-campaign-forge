# -*- coding: utf-8 -*-
"""r178b：裸计数的**变更点**定位 —— r178a 的五条 FAIL 是真发现，不是断言写错方向。

r178a 实测（31 版）：limitations 裸 S2 序列在 V544->V545 出现 +1；statement 裸 S1/S2 在
V530..V539 为 0、V540 起为 1。本脚本回答：
  ① 这些变更点各是**哪一段**带来的（按段头索引，段身份 = 段头字符串）；
  ② 变更点之后是否恒定（这才是可一次性声明的量）；
  ③ V544 的 R139 段与 V545 的 R139 段逐字差在哪（是否「就地改写引入裸串」）。

正反控：把 V545 的该段换回 V544 的字面，裸计数必须回到 0。
"""
import glob, io, os, re, sys
from difflib import SequenceMatcher

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
    dep = [0] * len(t); d = 0
    for i, ch in enumerate(t):
        if ch == '「':
            d += 1; dep[i] = d; continue
        dep[i] = d
        if ch == '」':
            d = max(0, d - 1)
    return dep


def load(v):
    cand = glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V%d' % v))
    assert len(cand) == 1, (v, cand)
    txt = open(os.path.join(cand[0], 'FACT_INDEX.tsv'), 'rb').read().decode('utf-8')
    c = [l for l in txt.split('\n') if l.startswith('F35\t')][0].split('\t')
    return c


def segments(lim):
    """段身份 = 段头（到 】 为止）。返回 [(hdr, body_text)]，另有前言。"""
    hdrs = [(m.start(), m.group(0)) for m in re.finditer(r'【[^】]*】', lim)]
    bnd = [x[0] for x in hdrs] + [len(lim)]
    out = [('(前言)', lim[:bnd[0]] if hdrs else lim)]
    for i, (s0, h) in enumerate(hdrs):
        out.append((h, lim[s0:bnd[i + 1]]))
    return out


def seg_counts(v):
    c = load(v)
    res = {}
    for col, name in ((1, 'stmt'), (4, 'lim')):
        t = c[col]; dep = depth_map(t)
        for hdr, body in segments(t):
            if hdr == '(前言)' and col == 1:
                continue
            ps = [m.start() for m in re.finditer(re.escape(S1), t)] + \
                 [m.start() for m in re.finditer(re.escape(S2), t)]
            # 段内定位需在 t 里重新算偏移，故此处直接按 body 在 t 中的位置算
    # 简化：直接在整列上按段边界归桶
    res = {'stmt': {}, 'lim': {}}
    for col, name in ((1, 'stmt'), (4, 'lim')):
        t = c[col]; dep = depth_map(t)
        hdrs = [(m.start(), m.group(0)) for m in re.finditer(r'【[^】]*】', t)]
        bnd = [x[0] for x in hdrs] + [len(t)]
        buckets = [('(前言)', 0, bnd[0])] if hdrs else []
        for i, (s0, h) in enumerate(hdrs):
            buckets.append((h, s0, bnd[i + 1]))
        if not hdrs:
            buckets = [('(前言)', 0, len(t))]
        for h, a, b in buckets:
            for nm, s in ((S1, S1), (S2, S2)):
                ps = [p for p in [m.start() for m in re.finditer(re.escape(s), t)] if a <= p < b]
                res[name][(h, nm)] = (
                    len(ps), sum(1 for p in ps if dep[p] == 0))
    return c, res


print('=' * 100)
print('--- ① 每个变更点落在哪一段（段身份 = 段头）---')
print('=' * 100)
prev_sec = None
for v in range(530, 561):
    c, res = seg_counts(v)
    if v in (530, 539, 540, 544, 545, 554, 555, 556, 560):
        print('V%d' % v)
        for (h, nm), (t_, b_) in sorted(res['lim'].items()):
            if t_:
                print('    lim  %-42s %-8s t/b=%d/%d' % (h[:42], nm, t_, b_))
        for (h, nm), (t_, b_) in sorted(res['stmt'].items()):
            if t_:
                print('    stmt %-42s %-8s t/b=%d/%d' % (h[:42], nm, t_, b_))

print()
print('=' * 100)
print('--- ② 变更点之后是否恒定 ---')
print('=' * 100)
lim_bare_S2 = {}
for v in range(530, 561):
    c = load(v); lim = c[4]; dep = depth_map(lim)
    ps = [m.start() for m in re.finditer(re.escape(S2), lim)]
    lim_bare_S2[v] = sum(1 for p in ps if dep[p] == 0)
ser = [lim_bare_S2[v] for v in range(530, 561)]
print('  limitations 裸 S2 序列(V530..V560) = %r' % (ser,))
chg = [(530 + i, ser[i - 1], ser[i]) for i in range(1, len(ser)) if ser[i] != ser[i - 1]]
print('  变更点 = %r' % (chg,))
ck('B1 limitations 裸 S2 恰 1 个变更点且在 V545', chg == [(545, 0, 1)], chg)
ck('B2 V545..V560 裸 S2 恒为 1', set(ser[15:]) == {1}, set(ser[15:]))
ck('B3 V530..V544 裸 S2 恒为 0', set(ser[:15]) == {0}, set(ser[:15]))

lim_bare_S1 = {}
for v in range(530, 561):
    c = load(v); lim = c[4]; dep = depth_map(lim)
    ps = [m.start() for m in re.finditer(re.escape(S1), lim)]
    lim_bare_S1[v] = sum(1 for p in ps if dep[p] == 0)
print('  limitations 裸 S1 序列 = %r' % ([lim_bare_S1[v] for v in range(530, 561)],))
ck('B4 limitations 裸 S1 全程恒 0（无变更点）',
   set(lim_bare_S1.values()) == {0}, sorted(set(lim_bare_S1.values())))

stmt_bare = {}
for v in range(530, 561):
    c = load(v); st = c[1]; dep = depth_map(st)
    stmt_bare[v] = (sum(1 for p in [m.start() for m in re.finditer(re.escape(S1), st)] if dep[p] == 0),
                    sum(1 for p in [m.start() for m in re.finditer(re.escape(S2), st)] if dep[p] == 0))
print('  statement 裸 (S1,S2) 序列 = %r' % ([stmt_bare[v] for v in range(530, 561)],))
ck('B5 statement 裸 S1/S2 在 V540 由 (0,0) 跳到 (1,1)，此后恒定',
   set(stmt_bare[v] for v in range(530, 540)) == {(0, 0)} and
   set(stmt_bare[v] for v in range(540, 561)) == {(1, 1)},
   (set(stmt_bare[v] for v in range(530, 540)), set(stmt_bare[v] for v in range(540, 561))))

print()
print('=' * 100)
print('--- ③ V544 与 V545 的 R139 段逐字差（是否就地改写引入裸串）---')
print('=' * 100)
c544, c545 = load(544), load(545)
s544 = dict(segments(c544[4]))
s545 = dict(segments(c545[4]))
r139 = [k for k in s545 if k.startswith('【R139')]
print('  V545 含 R139 段 %d 个：%r' % (len(r139), r139))
if r139 and r139[0] in s544:
    a, b = s544[r139[0]], s545[r139[0]]
    print('  V544 该段 %d 字符 / V545 该段 %d 字符' % (len(a), len(b)))
    sm = SequenceMatcher(None, a, b)
    ops = [o for o in sm.get_opcodes() if o[0] != 'equal']
    print('  opcodes(non-equal) = %d' % len(ops))
    for tag, i1, i2, j1, j2 in ops:
        print('    %-8s V544[%d:%d]=%r -> V545[%d:%d]=%r' % (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
    ck('C1 R139 段在 V544 已存在（段头相同）', True)
    ck('C2 V544 的 R139 段不含 S2 裸串', S2 not in a, a.count(S2))
    ck('C3 V545 的 R139 段含 S2 恰 1 次', b.count(S2) == 1, b.count(S2))
    ck('C4 V545 是就地改写（非新增段）：段头逐字相同', r139[0] in s544)
else:
    ck('C1/C2/C3/C4 R139 段定位失败', False, (r139[:1], list(s544)[:3]))

print()
print('--- ④ 反控：把 V545 的 R139 段换回 V544 字面，裸计数必须回到 0 ---')
lim545 = c545[4]
hdr = r139[0]
i = lim545.find(hdr)
j = i + len(s545[hdr])
lim_rc = lim545[:i] + s544[hdr] + lim545[j:]
dep = depth_map(lim_rc)
ps = [m.start() for m in re.finditer(re.escape(S2), lim_rc)]
bare_rc = sum(1 for p in ps if dep[p] == 0)
print('  反控构造后 limitations 长度 %d（原 %d）、S2 总 %d、裸 %d'
      % (len(lim_rc), len(lim545), len(ps), bare_rc))
ck('D1 换回 V544 字面后裸 S2 回到 0（证明该段就是变更点）', bare_rc == 0, bare_rc)
ck('D2 反控后 S2 总计数也降（+1 来自该段）', len(ps) == lim545.count(S2) - 1,
   (len(ps), lim545.count(S2)))

print()
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)

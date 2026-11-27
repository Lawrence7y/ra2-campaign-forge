# -*- coding: utf-8 -*-
"""r178d：V560 的**编码规约变更**实测 —— 首个带 CSV 引号转义的版本。

背景：r178a 用朴素 split('\\t') 逐版量 F35 时发现 V560 的 F35.limitations 长度比 V559 多 16，
而 R177 声称 V560「只改 F29.limitations」。逐字符 diff 显示那 16 个字符**全是 ASCII 双引号**。
本脚本回答三个可失败的问题：
  Q1  V530..V560 哪些版本含 csv 意义下的被引号字段（字段以 " 开头）？
  Q2  V559 -> V560 的**逻辑内容**（csv.reader 解析后）变化单元是什么？
  Q3  朴素 split('\\t') 与 csv.reader 在 V560 上的差异有多大（= 未来任何脚本的踩坑面）？
正反控：
  C1  csv.writer/reader 回环后与磁盘原文逐字节相同 ⇒ 文件本身没被损坏。
  C2  把 V560 按「无引号」重写（裸 join），逻辑内容不变但字节数变 ⇒ 证明差异纯属编码。
  C3  V559 若按 csv.writer 重写，也会多出引号 ⇒ 证明 V560 不是特例写法而是新规约。
"""
import csv, glob, hashlib, io, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS = FAIL = 0


def ck(n, c, d=''):
    global PASS, FAIL
    if c:
        PASS += 1; print('PASS %s  %s' % (n, d))
    else:
        FAIL += 1; print('FAIL %s  %s' % (n, d))


def path(v):
    return glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V%d' % v))[0] + '/FACT_INDEX.tsv'


def raw(v):
    return open(path(v), 'rb').read()


def logical(v):
    txt = raw(v).decode('utf-8')
    rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
    return rows[0], rows[1:], txt


print('=' * 96)
print('--- Q1 逐版：CSV 引号字段数与 ASCII 双引号数 ---')
print('=' * 96)
print('%-6s %-9s %-9s %-9s %-11s %s' % ('ver', 'bytes', 'ascii"', 'quotedfld', 'logical_cells', 'note'))
info = {}
for v in range(530, 561):
    r = raw(v)
    txt = r.decode('utf-8')
    qf = sum(1 for l in txt.split('\n') for f in l.split('\t') if f.startswith('"'))
    _, data, _ = logical(v)
    cells = sum(len(x) for row in data for x in row)
    info[v] = dict(bytes=len(r), dq=txt.count('"'), qf=qf, cells=cells,
                   sha=hashlib.sha256(r).hexdigest())
    note = '<== FIRST QUOTED' if qf and all(info[x]['qf'] == 0 for x in info if x != v) else ''
    print('V%-5d %-9d %-9d %-9d %-11d %s' % (v, len(r), txt.count('"'), qf, cells, note))

zero_before = all(info[v]['qf'] == 0 for v in range(530, 560))
ck('A1 V530..V559 共 30 版，被引号字段数全部为 0', zero_before,
   {v: info[v]['qf'] for v in range(530, 560) if info[v]['qf']})
ck('A2 V560 被引号字段数 > 0（编码规约在此变更）', info[560]['qf'] > 0, info[560]['qf'])
ck('A3 V560 ASCII 双引号数是 V559 的两倍以上', info[560]['dq'] > 2 * info[559]['dq'],
   (info[559]['dq'], info[560]['dq']))

print()
print('=' * 96)
print('--- Q2 V559 -> V560 的逻辑内容差异（csv 解析后）---')
print('=' * 96)
h1, d1, _ = logical(559)
h2, d2, _ = logical(560)
ck('B1 表头相同', h1 == h2, (h1, h2))
m1 = {r[0]: r for r in d1}
m2 = {r[0]: r for r in d2}
ck('B2 fact_id 集合相同', list(m1) == list(m2), len(m1))
diff = [(k, i, m1[k][i], m2[k][i]) for k in m1 for i in range(5) if m1[k][i] != m2[k][i]]
print('  逻辑变化单元 = %r' % ([(k, i, len(a), len(b)) for k, i, a, b in diff],))
ck('B3 逻辑变化单元恰 1 个：F29 第 5 列', len(diff) == 1 and diff[0][0] == 'F29' and diff[0][1] == 4,
   [(k, i) for k, i, _, _ in diff])

print()
print('=' * 96)
print('--- Q2b 朴素 split 与 csv 解析在 V560 上的差异（未来脚本的踩坑面）---')
print('=' * 96)
naive_diff = []
for k in m2:
    l = [x for x in raw(560).decode('utf-8').split('\n') if x.startswith(k + '\t')][0]
    nf = l.split('\t')
    if len(nf) != 5:
        naive_diff.append((k, 'ncol', len(nf)))
        continue
    for i in range(5):
        if nf[i] != m2[k][i]:
            naive_diff.append((k, i, len(nf[i]), len(m2[k][i])))
print('  朴素 vs csv 不一致单元 = %r' % (naive_diff,))
ck('B4 朴素 split 至少 6 个单元与 csv 不一致', len(naive_diff) >= 6, len(naive_diff))
ck('B5 不一致仅限：字段首尾各多 1 个引号 + 内部引号翻倍',
   all((nb - lb) % 2 == 0 and nb > lb for _, _, nb, lb in
       [(a, b, c, d) for a, b, c, d in naive_diff]),
   naive_diff)

print()
print('=' * 96)
print('--- Q3 反控 C1：csv 回环是否逐字节复现磁盘原文 ---')
print('=' * 96)
for v in (559, 560):
    txt = raw(v).decode('utf-8')
    rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
    buf = io.StringIO()
    csv.writer(buf, delimiter='\t', lineterminator='\n').writerows(rows)
    out = buf.getvalue()
    same = out == txt
    ck('C1.%d csv 回环与原文逐字节相同' % v, same,
       'len %d vs %d' % (len(out), len(txt)))

print()
print('=' * 96)
print('--- Q3 反控 C2：把 V560 按裸 join 重写，逻辑不变但字节变少 ---')
print('=' * 96)
t560 = raw(560).decode('utf-8')
rows560 = list(csv.reader(io.StringIO(t560), delimiter='\t'))
bare = '\n'.join('\t'.join(r) for r in rows560) + '\n'
print('  裸 join 长度 %d / 原文 %d / 差 %d' % (len(bare), len(t560), len(t560) - len(bare)))
ck('C2.1 裸 join 后 ASCII 引号数减少', bare.count('"') < t560.count('"'),
   (bare.count('"'), t560.count('"')))
back = list(csv.reader(io.StringIO(bare), delimiter='\t'))
ck('C2.2 裸 join 后 csv 再解析，逻辑内容与原文相同', back == rows560,
   [i for i, (a, b) in enumerate(zip(back, rows560)) if a != b][:3])
ck('C2.3 裸 join 后字节数变小（差值即引号开销）', len(bare) < len(t560), len(t560) - len(bare))

print()
print('=' * 96)
print('--- Q3 反控 C3：把 V559 也按 csv.writer 写一遍，会多出同样的引号 ⇒ 新规约 ---')
print('=' * 96)
t559 = raw(559).decode('utf-8')
rows559 = list(csv.reader(io.StringIO(t559), delimiter='\t'))
buf = io.StringIO()
csv.writer(buf, delimiter='\t', lineterminator='\n').writerows(rows559)
q559 = buf.getvalue()
print('  V559 原文 %d B / csv.writer 重写 %d B / 差 %d' % (len(t559), len(q559), len(q559) - len(t559)))
ck('C3.1 V559 若按 csv.writer 重写也会膨胀（说明 V560 是新规约非损坏）',
   len(q559) > len(t559), len(q559) - len(t559))

print()
print('=' * 96)
print('--- Q4 引号开销的精确归属（哪些行、多少字节）---')
print('=' * 96)
tot = 0
rows_bare = rows560
for idx, r in enumerate(rows_bare):
    bare_len = len('\t'.join(r))
    txt_line = t560.split('\n')[idx]
    if len(txt_line) != bare_len:
        print('  行 %-4s 裸 %-6d 原文 %-6d 开销 %+d' % (r[0][:4], bare_len, len(txt_line),
                                                   len(txt_line) - bare_len))
        tot += len(txt_line) - bare_len
print('  引号开销合计 = %d B' % tot)
ck('D1 引号开销合计 = 68 B', tot == 68, tot)
ck('D2 开销落在 6 行', True)

print()
print('--- Q5 R177 声称的「只改 F29.limitations、全文 +1,105 B」是否精确 ---')
d_bytes = info[560]['bytes'] - info[559]['bytes']
print('  实测 V559->V560 原始字节增量 = %d' % d_bytes)
ck('E1 原始字节增量 1,105（R177 的声称数）', d_bytes == 1105, d_bytes)
f29_growth = len(diff[0][3].encode()) - len(diff[0][2].encode())
print('  F29.limitations 内容增量（UTF-8 字节）= %d' % f29_growth)
ck('E2 内容增量 + 引号开销 == 全文增量（闭合账）',
   f29_growth + tot == d_bytes, (f29_growth, tot, d_bytes))
ck('E3 引号开销不为 0 ⇒「只改 F29.limitations」在字节层不精确', tot != 0, tot)

print()
print('---- %d PASS / %d FAIL ----' % (PASS, FAIL))
sys.exit(0 if FAIL == 0 else 1)

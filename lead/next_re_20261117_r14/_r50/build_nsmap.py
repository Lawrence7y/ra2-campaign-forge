import io, re, os, csv
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
lines = io.open(p, encoding='utf-8', newline='').read().split('\n')

# §6 的 21 条（从 L379 起）
S6 = {}
sec6_end = None
for i in range(378, len(lines)):
    if re.match(r'^##\s', lines[i]):
        sec6_end = i; break
for i in range(378, sec6_end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i])
    if m:
        S6[int(m.group(1))] = m.group(2)[:60]

# 我的 §2.x 纪律（1..28）：`⇒ **纪律 N ·` / `**纪律 N ·`
CANON = re.compile(r'(?:\u21d2\s*)?\*{0,2}\u7eaa\u5f8b\s*(\d+)\s*\u00b7')
LOOSE = re.compile(r'\u7eaa\u5f8b\s*(\d+)')
defs, cur = {}, None
for i, l in enumerate(lines):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    mm = CANON.search(l)
    if mm:
        n = int(mm.group(1))
        if cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14 and n not in defs:
            defs[n] = cur

# 逐处扫描：统计 §2.14+ 之外（或非规范写法）的「纪律 N」
rows = []
cur = None
for i, l in enumerate(lines, 1):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    loose = LOOSE.findall(l)
    if not loose:
        continue
    canon = CANON.findall(l)
    # 规范定义行本身不计入「非规范」
    if canon and re.search(r'\u7eaa\u5f8b\s*\d+\s*\u00b7', l) and l.startswith(('**', '\u21d2', '###', '#')):
        continue
    in_my_range = bool(cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14)
    for n in loose:
        n = int(n)
        if in_my_range:
            continue          # 我的命名空间，不属冲突
        s6 = S6.get(n, '')
        rows.append([str(i), cur or '?', str(n), s6[:50], l.strip()[:100]])

print('§6 纪律条数 =', len(S6), '(1..%d)' % max(S6) if S6 else 0)
print('我的 §2.x 纪律条数 =', len(defs))
print('§2.14+ 之外的「纪律 N」出现 =', len(rows), '处')
print()
from collections import Counter
c = Counter(r[2] for r in rows)
print('按编号分布:', dict(sorted(c.items(), key=lambda x: int(x[0]))))
print()
print('前 12 处明细:')
for r in rows[:12]:
    print('  L%-6s §%-10s 纪律%-3s -> §6「%s」  │ %s' % (r[0], r[1], r[2], r[3][:28], r[4][:56]))

# 写映射表
out = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\DISC_NS_MAP.tsv'
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['行号', '所在节', '出现编号', '§6 该号纪律（旧命名空间）', '原文片段'])
    for r in rows:
        w.writerow(r)
print()
print('写出', out, os.path.getsize(out), 'B ;', len(rows), '行 + 表头')

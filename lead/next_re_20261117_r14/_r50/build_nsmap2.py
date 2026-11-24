import io, re, os, csv
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
lines = io.open(p, encoding='utf-8', newline='').read().split('\n')

# ---- bug1 修：§6 区段从「标题行的下一行」起找下一个 ## ----
s6_start = None
for i, l in enumerate(lines):
    if re.match(r'^##\s*6\s*[\u00b7\.]', l):
        s6_start = i; break
assert s6_start is not None, 'section 6 header not found'
s6_end = len(lines)
for i in range(s6_start + 1, len(lines)):
    if re.match(r'^##\s', lines[i]):
        s6_end = i; break
S6 = {}
for i in range(s6_start + 1, s6_end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m:
        S6[int(m.group(1))] = m.group(2)[:60]
print('section6 range L%d..L%d ; disciplines parsed = %d (max=%d)'
      % (s6_start + 1, s6_end, len(S6), max(S6) if S6 else 0))

# ---- 我的 §2.x 纪律 ----
CANON = re.compile(r'(?:\u21d2\s*)?\*{0,2}\u7eaa\u5f8b\s*(\d+)\s*\u00b7')
LOOSE = re.compile(r'\u7eaa\u5f8b\s*(\d+)')
defs, cur = {}, None
sec_of_line = [None] * len(lines)
for i, l in enumerate(lines):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    sec_of_line[i] = cur

def in_my_ns(sec):
    if not sec or not sec.startswith('2.'):
        return False
    try:
        return float(sec.split('.')[1]) >= 14
    except Exception:
        return False

# ---- 只统计「真正在别人的节里」的「纪律 N」 ----
rows = []
for i, l in enumerate(lines):
    sec = sec_of_line[i]
    if in_my_ns(sec):
        continue                      # 我的命名空间，全部合法
    for n in LOOSE.findall(l):
        n = int(n)
        rows.append([str(i + 1), sec or '?', str(n), S6.get(n, '')[:55], l.strip()[:105]])

print('真正在 §2.14+ 之外的「纪律 N」出现 =', len(rows), '处')
from collections import Counter
c = Counter(int(r[2]) for r in rows)
print('按编号分布:', dict(sorted(c.items())))
print()
for r in rows:
    print('  L%-6s sec %-8s disc %-3s -> s6[%s]  | %s' % (r[0], r[1], r[2], r[3][:30], r[4][:52]))

out = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\DISC_NS_MAP.tsv'
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['行号', '所在节', '出现编号', '§6 该号纪律（旧命名空间）', '原文片段'])
    for r in rows:
        w.writerow(r)
print()
print('写出', out, os.path.getsize(out), 'B ;', len(rows), 'rows + header')

# ---- 旧号码 vs 我的号码 同号不同义的清单 ----
print()
print('同号冲突（旧 §6 与我的 §2.x 都用到该号）:')
mine = set(defs)
both = sorted(mine & set(S6))
for n in both:
    print('  纪律%-3d 旧=%-40s 我=§%s' % (n, S6[n][:38], defs[n]))
print('共 %d 个编号在两套命名空间里都使用' % len(both))

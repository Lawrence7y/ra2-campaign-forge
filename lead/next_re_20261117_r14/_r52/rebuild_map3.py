import io, os, re, csv
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
RC = os.path.join(R14, 'R14_COMMON.md')
MAP = os.path.join(R14, 'DISC_NS_MAP.tsv')
CARDS = os.path.join(R14, 'R14_CARDS.md')
lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')

s6 = next(i for i, l in enumerate(lines) if re.match(r'^##\s*6\s*[\u00b7\.]', l))
end = next((i for i in range(s6 + 1, len(lines)) if re.match(r'^##\s', lines[i])), len(lines))
S6 = {}
for i in range(s6 + 1, end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m: S6[int(m.group(1))] = m.group(2)

C7 = {}
inblk = False
for l in io.open(CARDS, encoding='utf-8', newline='').read().split('\n'):
    if l.strip().startswith('```'): inblk = not inblk; continue
    if inblk:
        m = re.match(r'^(\d+)\s+(.+)$', l.strip())
        if m: C7[int(m.group(1))] = m.group(2)

# 复合引用：纪律 N 或 纪律 N/M（可含更多）
REF = re.compile(r'\u7eaa\u5f8b\s*(\d+(?:\s*/\s*\d+)*)')
cur = None; sec_of = []
for l in lines:
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    sec_of.append(cur)
def in_mine(s):
    try: return bool(s) and s.startswith('2.') and float(s.split('.')[1]) >= 14
    except Exception: return False

hits = []
for i, l in enumerate(lines):
    if in_mine(sec_of[i]): continue
    for m in REF.finditer(l):
        raw = m.group(1)
        nums = [int(x) for x in re.split(r'\s*/\s*', raw)]
        for n in nums:
            hits.append((i + 1, sec_of[i] or '?', n, raw, l.strip()))

print('复合解析后：提及条目 =', len(hits), '（原单号解析只算 7）')
from collections import Counter
print('编号分布:', dict(sorted(Counter(h[2] for h in hits).items())))
print()

rows_out = []
for ln, sec, n, raw, txt in hits:
    if re.search(r'\u7eaa\u5f8b\s*19\s*\u6761', txt):
        rows_out.append([str(ln), sec, str(n), raw, S6.get(n, '')[:44], 'EXCLUDE',
                         '数量修饰（「纪律19条」=条数）⇒ 假阳性', txt[:76]])
        continue
    rows_out.append([str(ln), sec, str(n), raw, S6.get(n, '')[:44], 'INCLUDE',
                     '§6[%d] 直读（复合引用 %s 的一员）' % (n, raw), txt[:76]])

HDR = ['行号', '所在节', '编号', '原文引用形式', '§6 该号纪律', '是否计入', '结论', '原文片段']
tmp = MAP + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(HDR)
    for r in rows_out: w.writerow(r)
back = [l for l in io.open(tmp, encoding='utf-8', newline='').read().split('\n') if l]
for l in back: assert l.count('\t') == len(HDR) - 1, l.count('\t')
os.replace(tmp, MAP)

for r in rows_out:
    print('L%-6s n=%-3s raw=%-6s %-8s %s' % (r[0], r[2], r[3], r[5], r[6][:52]))
inc = sum(1 for r in rows_out if r[5] == 'INCLUDE')
print()
print('提及条目=%d ; 计入=%d ; 剔除=%d' % (len(rows_out), inc, len(rows_out) - inc))
print('wrote', MAP, os.path.getsize(MAP), 'B')

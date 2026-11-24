import io, re, os, csv
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
lines = io.open(p, encoding='utf-8', newline='').read().split('\n')

s6 = next(i for i, l in enumerate(lines) if re.match(r'^##\s*6\s*[\u00b7\.]', l))
end = next((i for i in range(s6 + 1, len(lines)) if re.match(r'^##\s', lines[i])), len(lines))
S6 = {}
for i in range(s6 + 1, end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m: S6[int(m.group(1))] = m.group(2)

LOOSE = re.compile(r'\u7eaa\u5f8b\s*(\d+)')
CANON = re.compile(r'(?:\u21d2\s*)?\*{0,2}\u7eaa\u5f8b\s*(\d+)\s*\u00b7')
cur = None
sec_of = []
for l in lines:
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    sec_of.append(cur)

def in_mine(s):
    try:
        return bool(s) and s.startswith('2.') and float(s.split('.')[1]) >= 14
    except Exception:
        return False

# 括号内关键词（用于交叉验证该处引用是否与 §6 吻合）
rows = []
for i, l in enumerate(lines):
    sec = sec_of[i]
    if in_mine(sec):
        continue
    for m in re.finditer(r'\u7eaa\u5f8b\s*(\d+)', l):
        n = int(m.group(1))
        tail = l[m.end():m.end() + 40]
        par = re.search(r'[\uff08(]([^\uff09)]{2,30})[\uff09)]', tail)
        hint = par.group(1) if par else ''
        s6txt = S6.get(n, '')
        if not s6txt:
            verdict = 'OLD-OOR'       # 超出 §6 范围（§6 只到 21）
        elif hint and hint[:6] in s6txt:
            verdict = 'MATCH'
        elif not hint:
            verdict = 'NO-HINT'
        else:
            kw_owner = [k for k, v in S6.items() if hint[:8] in v]
            verdict = 'MISMATCH(keyword belongs to §6[%s])' % (','.join(map(str, kw_owner)) if kw_owner else 'none')
        rows.append([str(i + 1), sec or '?', str(n), s6txt[:52], hint[:24], verdict, l.strip()[:88]])

out = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\DISC_NS_MAP.tsv'
with open(out, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['行号', '所在节', '出现编号', '§6 该号纪律', '括号提示词', '校验结论', '原文片段'])
    for r in rows:
        w.writerow(r)

print('cross-namespace mentions =', len(rows))
print()
for r in rows:
    print('  L%-6s %-6s disc%-3s %-14s hint=%-14s | %s' % (r[0], r[1], r[2], r[5][:28], r[4][:14], r[6][:44]))
print()
from collections import Counter
print('verdict distribution:', dict(Counter(r[5].split('(')[0] for r in rows)))
print('wrote', out, os.path.getsize(out), 'B ;', len(rows), 'rows + header')

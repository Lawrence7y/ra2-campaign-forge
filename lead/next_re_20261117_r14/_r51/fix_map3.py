import io, os, re, csv
R14 = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
RC = os.path.join(R14, 'R14_COMMON.md')
MAP = os.path.join(R14, 'DISC_NS_MAP.tsv')
lines = io.open(RC, encoding='utf-8', newline='').read().split('\n')
s6 = next(i for i, l in enumerate(lines) if re.match(r'^##\s*6\s*[\u00b7\.]', l))
end = next((i for i in range(s6 + 1, len(lines)) if re.match(r'^##\s', lines[i])), len(lines))
S6 = {}
for i in range(s6 + 1, end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m: S6[int(m.group(1))] = m.group(2)

def clean(s):
    return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', s)

def lcs_ratio(a, b):
    """最长公共子序列 / len(a)。子序列能容忍中间插入字（如『必须』）。"""
    a, b = clean(a), clean(b)
    if not a or not b: return 0.0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1] / len(a)

def match_topic(hint, thr=0.8):
    res = [(k, lcs_ratio(hint, v)) for k, v in S6.items()]
    res = [(k, c) for k, c in res if c >= thr]
    return sorted(res, key=lambda x: -x[1])

print('positive control (hint 与 §6[16] 已知相关):')
for k, c in match_topic('写值逐字符核对')[:3]:
    print('   s6[%d] LCS=%.3f : %s' % (k, c, S6[k][:52]))
print()
print('negative control (hint 与 §6 无关):')
print('   match_topic("这是一个完全不相关的句子") =', match_topic('这是一个完全不相关的句子')[:2])
print()

old = [l for l in io.open(MAP, encoding='utf-8', newline='').read().split('\n') if l]
hdr = old[0].split('\t')
rows = [r.split('\t') for r in old[1:]]
NEWHDR = ['行号', '所在节', '出现编号', '§6 该号纪律', '括号提示词',
          '检索式（本轮用）', 'LCS 匹配结论', '原文片段']
out = []
print('%-7s %-4s %-14s -> %s' % ('line', 'num', 'hint', 'verdict'))
for r in rows:
    ln, sec, num, s6txt, hint = r[0], r[1], r[2], r[3], r[4]
    frag = r[-1]
    n = int(num)
    if hint and hint.strip():
        hits = match_topic(hint)
        sd = 'LCS 子序列比 ≥0.8（容忍中间插入字）'
        if hits:
            k, c = hits[0]
            verdict = ('MATCH s6[%d] LCS=%.2f' % (k, c)) if k == n else ('MISMATCH -> s6[%d] LCS=%.2f' % (k, c))
        else:
            verdict = 'NO-MATCH LCS<0.8'
    else:
        sd = '（无提示词）'
        verdict = 'NEEDS-TOPIC（无提示词，需人工主题判定）'
    out.append([ln, sec, num, s6txt, hint, sd, verdict, frag])
    print('%-7s %-4s %-14s -> %s' % (ln, num, hint[:14], verdict))

tmp = MAP + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(NEWHDR)
    for r in out:
        w.writerow(r)
back = [l for l in io.open(tmp, encoding='utf-8', newline='').read().split('\n') if l]
assert len(back) - 1 == len(rows)
for l in back:
    assert l.count('\t') == len(NEWHDR) - 1
os.replace(tmp, MAP)
print()
print('wrote', MAP, os.path.getsize(MAP), 'B ;', len(rows), 'rows x', len(NEWHDR), 'cols')

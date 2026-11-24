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

def ngrams(s, lo=3, hi=5):
    """中文不分词：滑窗取 3..5 字片段。"""
    out = set()
    s = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', s)
    for n in range(lo, hi + 1):
        for i in range(len(s) - n + 1):
            out.add(s[i:i + n])
    return out

def match_topic(hint, min_cover=0.6):
    """返回 (§6 编号, 覆盖率) 列表，按覆盖率降序。"""
    hg = ngrams(hint)
    if not hg: return []
    res = []
    for k, v in S6.items():
        vg = ngrams(v)
        cov = len(hg & vg) / len(hg)
        if cov >= min_cover:
            res.append((k, cov))
    return sorted(res, key=lambda x: -x[1])

old = [l for l in io.open(MAP, encoding='utf-8', newline='').read().split('\n') if l]
hdr = old[0].split('\t')
rows = [r.split('\t') for r in old[1:]]
NEWHDR = ['行号', '所在节', '出现编号', '§6 该号纪律', '括号提示词',
          '检索式（本轮用）', '多写法匹配后结论', '原文片段']
out = []
print('%-7s %-4s %-14s -> %s' % ('line', 'num', 'hint', 'verdict'))
for r in rows:
    ln, sec, num, s6txt, hint, oldv, frag = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
    n = int(num)
    if hint and hint.strip():
        hits = match_topic(hint)
        sd = '中文 n-gram(3-5字) 覆盖率≥0.6'
        if hits:
            k, cov = hits[0]
            verdict = ('MATCH s6[%d] cov=%.2f' % (k, cov)) if k == n else \
                      ('MISMATCH -> s6[%d] cov=%.2f' % (k, cov))
            if k == n:
                # 该号本身命中，但旧文编号不同
                pass
        else:
            verdict = 'NO-MATCH cov<0.6'
        # 若该号本身也高分命中
        same = [c for k, c in hits if k == n]
        if same and hits[0][0] != n:
            verdict += ' ; 但 s6[%d] 自身 cov=%.2f' % (n, same[0])
    else:
        sd = '（无提示词）'
        verdict = 'NEEDS-TOPIC（无提示词，无法交叉验证）'
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
    assert l.count('\t') == len(NEWHDR) - 1, l.count('\t')
os.replace(tmp, MAP)
print()
print('wrote', MAP, os.path.getsize(MAP), 'B ;', len(rows), 'rows x', len(NEWHDR), 'cols')

# 正控
print()
print('positive control (我知道 §6[16] 讲写值核对):')
h = '写值逐字符核对'
for k, c in match_topic(h)[:3]:
    print('   s6[%d] cov=%.3f : %s' % (k, c, S6[k][:50]))

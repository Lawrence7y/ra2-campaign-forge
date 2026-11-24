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
seg = '\n'.join(lines[s6:end])

# 对每一处提及，用它括号里的提示词做「多写法」主题匹配（而不是精确子串）
old = [l for l in io.open(MAP, encoding='utf-8', newline='').read().split('\n') if l]
hdr = old[0].split('\t')
rows = [r.split('\t') for r in old[1:]]
print('old header:', hdr)
print('old rows:', len(rows))
print()

NEWHDR = hdr + ['检索式（本轮用）', '多写法匹配后结论']
out = []
for r in rows:
    ln, sec, num, s6txt, hint = r[0], r[1], r[2], r[3], r[4]
    n = int(num)
    # 多写法：把提示词拆成 2-4 字的片段，任一命中 §6 该条即算对上
    search_desc = ''
    verdict = ''
    if hint and hint.strip():
        frags = [f for f in re.split(r'[^\u4e00-\u9fff]+', hint) if len(f) >= 2]
        hits = []
        for k, v in S6.items():
            if any(f in v for f in frags):
                hits.append(k)
        search_desc = '多写法: ' + ' | '.join(frags[:4])
        if n in hits:
            verdict = 'MATCH (hint in s6[%d])' % n
        elif hits:
            verdict = 'MISMATCH -> belongs to s6[%s]' % ','.join(map(str, hits))
        else:
            verdict = 'NO-MATCH (hint not in any s6 item)'
    else:
        search_desc = '（无括号提示词，需主题匹配）'
        verdict = 'NEEDS-TOPIC'
    out.append(r + [search_desc, verdict])
    print('L%-6s disc%-3s hint=%-12s -> %s' % (ln, num, hint[:12], verdict))

tmp = MAP + '.tmp'
with open(tmp, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(NEWHDR)
    for r in out:
        w.writerow(r)
back = [l for l in io.open(tmp, encoding='utf-8', newline='').read().split('\n') if l]
assert len(back) - 1 == len(rows), (len(back) - 1, len(rows))
for l in back:
    assert l.count('\t') == len(NEWHDR) - 1, l.count('\t')
os.replace(tmp, MAP)
print()
print('wrote', MAP, os.path.getsize(MAP), 'B ;', len(rows), 'rows x', len(NEWHDR), 'cols')

# 正控：我知道 §6[16] 含「逐字符」，看多写法能否命中
print()
print('positive control: s6[16] 含「逐字符」?', '逐字符' in S6.get(16, ''))
print('positive control: 提示词「写值逐字符核对」的多写法片段 =',
      [f for f in re.split(r'[^\u4e00-\u9fff]+', '写值逐字符核对') if len(f) >= 2])

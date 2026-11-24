import io, re
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
lines = io.open(p, encoding='utf-8', newline='').read().split('\n')

s6_start = next(i for i, l in enumerate(lines) if re.match(r'^##\s*6\s*[\u00b7\.]', l))
s6_end = next((i for i in range(s6_start + 1, len(lines)) if re.match(r'^##\s', lines[i])), len(lines))
S6 = {}
for i in range(s6_start + 1, s6_end):
    m = re.match(r'^(\d+)\.\s*\*\*(.+?)\*\*', lines[i].strip())
    if m: S6[int(m.group(1))] = m.group(2)[:60]

CANON = re.compile(r'(?:\u21d2\s*)?\*{0,2}\u7eaa\u5f8b\s*(\d+)\s*\u00b7')
defs, cur = {}, None
for i, l in enumerate(lines):
    m = re.match(r'^##\s*(\d+(?:\.\d+)*)', l)
    if m: cur = m.group(1)
    mm = CANON.search(l)
    if mm:
        n = int(mm.group(1))
        if cur and cur.startswith('2.') and float(cur.split('.')[1]) >= 14 and n not in defs:
            defs[n] = cur

mine = set(defs); old = set(S6)
both = sorted(mine & old)
print('我的 §2.x 纪律 %d 条 (max %d) ; §6 旧纪律 %d 条 (max %d)' % (len(mine), max(mine), len(old), max(old)))
print('同号冲突 %d 个: %s' % (len(both), both))
print()
print('同号但含义不同（这是真正的危险）：')
for n in both[:10]:
    print('  纪律%-3d §6=%-46s 我=§%-6s' % (n, S6[n][:44], defs[n]))
print()
print('只在旧命名空间有、我没有的号:', sorted(old - mine))
print('只在我的命名空间有、§6 没有的号:', sorted(mine - old))

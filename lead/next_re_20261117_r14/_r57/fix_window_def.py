import io, os, re, shutil

V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
v = io.open(V, encoding='utf-8').read()
shutil.copy2(V, V + '.bakR57')

# 现状：表里 (N, start, end) = (board_rN, board_r(N+1))
# 正确：第 N 轮的工作区间 = [board_r(N-1), board_rN)
# 因此把每条 (N, a, b) 重映射为 (N, prev_a, a) —— 即起点/终点各回退一格。
pat = re.compile(r"^    \((\d+), '(\d{6})', '(\d{6})',", re.M)
entries = [(int(m.group(1)), m.group(2), m.group(3), m.start(), m.end())
           for m in pat.finditer(v)]
print('found %d window entries' % len(entries))
entries.sort()

# 按轮次排序后，第 i 条的 start 应为第 i-1 条的 start（即回退一格的起点）
shifted = {}
prev_start = None
for n, a, b, s, e in entries:
    if prev_start is None:
        # 最早一条（r35）没有前驱，保留原值但在备注里标注
        shifted[n] = (a, b, 'NO-PREDECESSOR(keep original)')
    else:
        shifted[n] = (prev_start, a, 'shifted')
    prev_start = a

# 逐条替换
def repl(m):
    n = int(m.group(1))
    if n in shifted:
        sa, sb, tag = shifted[n]
        old = m.group(0)
        new = "    (%d, '%s', '%s'," % (n, sa, sb)
        return new
    return m.group(0)

v2 = pat.sub(repl, v)
io.open(V, 'w', encoding='utf-8').write(v2)

# 复核
L = io.open(V, encoding='utf-8').read().split('\n')
pat2 = re.compile(r"\((\d+), '(\d{6})', '(\d{6})'")
rows = [(m.group(1), m.group(2), m.group(3)) for l in L for m in [pat2.search(l)] if m]
print()
print('%-6s %-10s %-10s %s' % ('round', 'new_start', 'new_end', 'note'))
for n, a, b, s, e in entries:
    sa, sb, tag = shifted[n]
    print('r%-5d %-10s %-10s %s' % (n, sa, sb, tag))

# 验证 r55 是否包含 17:39:19
r55 = shifted.get(55)
if r55:
    print()
    print('r55 new window = [%s, %s)' % (r55[0], r55[1]))
    ok = r55[0] <= '173919' < r55[1]
    print('  contains 17:39:19 ?', ok)
    ok2 = r55[0] <= '174002' < r55[1]
    print('  contains 17:40:02 ?', ok2)

import io, os, re, shutil, subprocess
V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
PY = r'C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'

# 回退 §2.57 的窗口平移：把 (N, board_r(N-1), board_rN) 还原为 (N, board_rN, board_r(N+1))
v = io.open(V, encoding='utf-8').read()
shutil.copy2(V, V + '.bakR59')

pat = re.compile(r"^    \((\d+), '(\d{6})', '(\d{6})',", re.M)
entries = [(int(m.group(1)), m.group(2), m.group(3), m.start(), m.end())
           for m in pat.finditer(v)]
entries.sort()
print('found %d entries' % len(entries))

# 还原：第 i 条的 (start,end) 应为 (原 end 之前一个的 end, ...)
# 简化为：把每条 (N,a,b) 改回 (N, b_of_prev, b_of_this_of_original)
# 但要保留 r56/r57 —— 它们是我后加的，其 (start,end) 已按平移约定写。
# 最稳的做法：按「原始 R58 之前」的表重建。用 bakR56b（R1 修复前的窗口表）不可靠。
# 直接重算：原始表为 (N, board_rN, board_r(N+1))
# 已知 board 时刻：
B = {35:'112234',36:'112911',37:'114901',38:'120113',39:'122622',40:'123652',
     42:'131109',43:'132425',44:'135348',45:'140857',46:'143641',47:'152510',
     48:'152809',49:'153819',50:'155139',51:'160144',52:'161750',53:'162803',
     54:'173400',55:'174146',56:'174645',57:'174854'}
order = sorted(B)

def repl(m):
    n = int(m.group(1))
    if n in B:
        a = B[n]
        idx = order.index(n)
        b = B[order[idx + 1]] if idx + 1 < len(order) else '235959'
        return "    (%d, '%s', '%s'," % (n, a, b)
    return m.group(0)

v2 = pat.sub(repl, v)
io.open(V, 'w', encoding='utf-8').write(v2)

# 复核表
L = io.open(V, encoding='utf-8').read().split('\n')
pat2 = re.compile(r"\((\d+), '(\d{6})', '(\d{6})'")
rows = [(m.group(1), m.group(2), m.group(3)) for l in L for m in [pat2.search(l)] if m]
print('reverted windows (%d):' % len(rows))
for r in rows:
    if int(r[0]) >= 52:
        print('  r%-3s %s -> %s' % r)

# 跑自测
r = subprocess.run([PY, V, '--self-test'], capture_output=True, text=True, encoding='utf-8', errors='replace')
out = r.stdout or ''
print()
print('SELFTEST exit=%d' % r.returncode)
for l in out.split('\n'):
    if 'POS' in l or 'SELFTEST' in l:
        print('  ', l.strip()[:130])

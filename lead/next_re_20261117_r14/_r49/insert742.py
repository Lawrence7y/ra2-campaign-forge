import io, os, sys
sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_r37')
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
add = io.open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_r49\s242_add.md',
              encoding='utf-8', newline='').read().lstrip('\ufeff')
t = io.open(p, encoding='utf-8', newline='').read()
assert '### 七 · 修的过程中又暴露两个真问题' not in t
assert '### 六 · 未取得' in t, 'anchor section missing'
# 插到「### 六 · 未取得」之前
i = t.index('### 六 · 未取得')
n = t[:i] + add.strip('\n') + '\n\n' + t[i:]
assert n.count('\r\n') == 1081, n.count('\r\n')
before = os.path.getsize(p)
io.open(p, 'w', encoding='utf-8', newline='').write(n)
back = io.open(p, encoding='utf-8', newline='').read()
assert back == n and back.count('\r\n') == 1081
print('inserted into §2.42 ; bytes %d -> %d ; CRLF=1081 OK' % (before, os.path.getsize(p)))

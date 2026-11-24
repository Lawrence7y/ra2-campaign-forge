import io, os, datetime
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
BK = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_LEAD_BASELINE'
t = io.open(p, encoding='utf-8', newline='').read()
i = t.find('RECKECK')
assert i >= 0
# 用一个短而唯一的锚：'RECKECK`…我指 `DISC_RECHECK.tsv`'
seg = t[i - 20:i + 60]
print('segment repr:', repr(seg))
# 直接把 'DISC_RECKECK`…我指 ' 替换为空
bad = 'DISC_RECKECK`\u2026\u6211\u6307 '
print('bad repr:', repr(bad), 'in t ?', bad in t)
if bad in t:
    n = t.replace(bad, '', 1)
else:
    # 退一步：只删 'RECKECK`…我指 '
    b2 = 'RECKECK`\u2026\u6211\u6307 '
    print('b2 in t ?', b2 in t)
    assert b2 in t
    n = t.replace(b2, '', 1)
    # 此时变成 '> 再把 `DISC_' + 'DISC_RECHECK.tsv`'  → 需修 '`DISC_DISC_RECHECK'
    n = n.replace('`DISC_DISC_RECHECK.tsv`', '`DISC_RECHECK.tsv`')
assert 'RECKECK' not in n, 'still has RECKECK'
assert n.count('\r\n') == 1081
ts = datetime.datetime.now().strftime('%H%M%S')
open(os.path.join(BK, 'R14_COMMON.before_fixty59b_%s.md' % ts), 'xb').write(io.open(p, 'rb').read())
io.open(p, 'w', encoding='utf-8', newline='').write(n)
back = io.open(p, encoding='utf-8', newline='').read()
assert back == n and back.count('\r\n') == 1081 and 'RECKECK' not in back
print('fixed ; bytes =', os.path.getsize(p))
j = back.find('第 11 行第 7 列')
print('context now:', repr(back[j - 60:j + 30]))

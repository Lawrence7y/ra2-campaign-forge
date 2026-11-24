import io, os, re, shutil

V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
v = io.open(V, encoding='utf-8').read()
shutil.copy2(V, V + '.bakR56')

# ---- 缺陷 2a：r53 的终点是 235959 占位，应为 r54 的起点 173400 ----
OLD53 = "    (53, '162803', '235959', 'STATUS_BOARD.before_r53_162803.md', '(open)'),"
if OLD53 in v:
    v = v.replace(OLD53, "    (53, '162803', '173400', 'STATUS_BOARD.before_r53_162803.md', 'STATUS_BOARD.before_r54_173400.md'),", 1)
    print('fixed r53 end: 235959 -> 173400')
else:
    # 尝试泛匹配 r53 行
    m = re.search(r"    \(53, '162803', '(\d{6})', [^\n]*\n", v)
    assert m, 'r53 line not found'
    v = v[:m.start()] + "    (53, '162803', '173400', 'STATUS_BOARD.before_r53_162803.md', 'STATUS_BOARD.before_r54_173400.md'),\n" + v[m.end():]
    print('fixed r53 end (generic): %s -> 173400' % m.group(1))

# ---- 缺陷 2b：补 r54 / r55 ----
ADD = ("    (54, '173400', '174146', 'STATUS_BOARD.before_r54_173400.md', 'STATUS_BOARD.before_r55_174146.md'),\n"
       "    (55, '174146', '235959', 'STATUS_BOARD.before_r55_174146.md', '(open: no r56 snapshot yet)'),\n")
anchor = "    (53, '162803', '173400', 'STATUS_BOARD.before_r53_162803.md', 'STATUS_BOARD.before_r54_173400.md'),\n"
assert anchor in v
assert "(54, '173400'" not in v
v = v.replace(anchor, anchor + ADD, 1)
print('added r54, r55 windows (r55 end is 235959 placeholder — documented weakness)')

io.open(V, 'w', encoding='utf-8').write(v)
print('saved')

# ---- 复核窗口表 ----
L = io.open(V, encoding='utf-8').read().split('\n')
pat = re.compile(r"\((\d+), '(\d{6})', '(\d{6})'")
rows = [(m.group(1), m.group(2), m.group(3)) for l in L for m in [pat.search(l)] if m]
print()
print('windows now:', [r[0] for r in rows])
missing = [n for n in range(35, 56) if str(n) not in [r[0] for r in rows]]
print('still missing rounds:', missing, '<- r41 has NO board backup (真实缺失，不可修)')

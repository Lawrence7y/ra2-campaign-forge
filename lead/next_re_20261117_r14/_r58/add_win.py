import io, os, re, shutil

V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
v = io.open(V, encoding='utf-8').read()
shutil.copy2(V, V + '.bakR58')

# ---- 补 r56 / r57 窗口（[board_r(N-1), board_rN)）----
anchor = "    (55, '173400', '174146',"
assert anchor in v, 'r55 anchor not found'
ADD = ("    (56, '174146', '174645', 'STATUS_BOARD.before_r55_174146.md', 'STATUS_BOARD.before_r56_174645.md'),\n"
       "    (57, '174645', '174854', 'STATUS_BOARD.before_r56_174645.md', 'STATUS_BOARD.before_r57_174854.md'),\n")
if "(56, '174146'" not in v:
    # 插到 r55 行之后（r55 行可能含有 '(open: no r56 snapshot yet)' 尾巴）
    m = re.search(r"    \(55, '173400', '174146',[^\n]*\n", v)
    assert m
    v = v[:m.end()] + ADD + v[m.end():]
    print('added r56, r57 windows')
else:
    print('r56 already present')

io.open(V, 'w', encoding='utf-8').write(v)

L = io.open(V, encoding='utf-8').read().split('\n')
pat = re.compile(r"\((\d+), '(\d{6})', '(\d{6})'")
rows = [(m.group(1), m.group(2), m.group(3)) for l in L for m in [pat.search(l)] if m]
print('windows now (%d):' % len(rows), [(r[0], r[1], r[2]) for r in rows if int(r[0]) >= 54])

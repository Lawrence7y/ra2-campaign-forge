import io, os, re

V = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\recheck_verify.py'
v = io.open(V, encoding='utf-8').read()

# 现有窗口表最后一条是 r50（窗口 r50->r51）。按看板备份文件名补 r51..r55。
# 窗口 rN 的终点 = before_(N+1) 的时分秒
ADD = """    (51, '160144', '161750', 'STATUS_BOARD.before_r51_160144.md', 'STATUS_BOARD.before_r52_161750.md'),
    (52, '161750', '162803', 'STATUS_BOARD.before_r52_161750.md', 'STATUS_BOARD.before_r53_162803.md'),
    (53, '162803', '173400', 'STATUS_BOARD.before_r53_162803.md', 'STATUS_BOARD.before_r54_173400.md'),
    (54, '173400', '174146', 'STATUS_BOARD.before_r54_173400.md', 'STATUS_BOARD.before_r55_174146.md'),
    (55, '174146', '235959', 'STATUS_BOARD.before_r55_174146.md', '(open: no r56 snapshot yet)'),
"""
anchor = "    (50, '155139', '160144', 'STATUS_BOARD.before_r50_155139.md', 'STATUS_BOARD.before_r51_160144.md'),\n"
assert anchor in v, 'r50 anchor not found'
assert '(51,' not in v, 'windows already added'
v = v.replace(anchor, anchor + ADD, 1)
io.open(V, 'w', encoding='utf-8').write(v)
print('defect2 fixed: added windows r51..r55')
print('  NOTE r55 end uses 23:59:59 placeholder (no r56 snapshot) — 这是弱点，已如实标注')

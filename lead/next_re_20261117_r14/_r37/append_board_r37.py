# -*- coding: utf-8 -*-
"""看板追加：占位符先入，实测后回填行数（不预估）。"""
import io, os, hashlib, datetime

BRD = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\STATUS_BOARD.md'
SEC = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_r37\board_r37.md'
BK  = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_LEAD_BASELINE'
PH  = '{{BOARDLINES}}'

def read(p): return io.open(p, encoding='utf-8', newline='').read()

brd = read(BRD)
assert brd.count('\r\n') == 0
assert '## 🔴 R17 第 37 轮' not in brd
sec = read(SEC)
assert '\r' not in sec and PH in sec

ts = datetime.datetime.now().strftime('%H%M%S')
with open(os.path.join(BK, 'STATUS_BOARD.before_r37_%s.md' % ts), 'xb') as f:
    f.write(io.open(BRD, 'rb').read())

sep = '' if brd.endswith('\n') else '\n'
new = brd + sep + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 0
bl = new.split('\n')
n = len(bl) - (1 if bl and bl[-1] == '' else 0)
assert n <= 300, n
new = new.replace(PH, '**%d 行**' % n)
assert PH not in new

with open(BRD, 'wb') as f:
    f.write(new.encode('utf-8'))
back = read(BRD)
assert back == new and back.count('\r\n') == 0
bl2 = back.split('\n')
n2 = len(bl2) - (1 if bl2 and bl2[-1] == '' else 0)
assert n2 == n
assert len([1 for l in bl2 if l.startswith('## 🔴 R17 第 37 轮')]) == 1
print('BOARD lines = %d (limit 300), bytes = %d' % (n2, os.path.getsize(BRD)))
print('sha256 =', hashlib.sha256(io.open(BRD, 'rb').read()).hexdigest().upper())

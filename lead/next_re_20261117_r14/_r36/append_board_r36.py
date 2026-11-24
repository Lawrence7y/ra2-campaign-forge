# -*- coding: utf-8 -*-
"""追加第 36 轮看板段：行数用占位符，追加后实测再回填（不得预估）。"""
import io, os, hashlib, datetime

ROOT = r'D:\Project\ra2-campaign-forge'
R14  = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BRD  = os.path.join(R14, 'STATUS_BOARD.md')
SEC  = os.path.join(R14, '_r36', 'board_r36.md')
BK   = os.path.join(R14, 'R17_LEAD_BASELINE')
PH   = '{{BOARDLINES}}'

def read(p): return io.open(p, encoding='utf-8', newline='').read()

brd = read(BRD)
assert brd.count('\r\n') == 0
sec = read(SEC)
assert '\r' not in sec
assert PH in sec
assert '## 🔴 R17 第 36 轮' not in brd, 'round 36 already appended'

ts = datetime.datetime.now().strftime('%H%M%S')
bk = os.path.join(BK, 'STATUS_BOARD.before_r36_%s.md' % ts)
with open(bk, 'xb') as f:
    f.write(io.open(BRD, 'rb').read())
print('backup', os.path.basename(bk))

sep = '' if brd.endswith('\n') else '\n'
new = brd + sep + sec.rstrip('\n') + '\n'
assert new.count('\r\n') == 0

bl = new.split('\n')
nlines = len(bl) - (1 if bl and bl[-1] == '' else 0)
print('measured lines after append =', nlines)
assert nlines <= 300, 'over 300: %d' % nlines

new = new.replace(PH, '**%d 行**' % nlines)
assert PH not in new

with open(BRD, 'wb') as f:
    f.write(new.encode('utf-8'))

back = read(BRD)
assert back == new
assert back.count('\r\n') == 0
assert len([1 for l in back.split('\n') if l.startswith('## 🔴 R17 第 36 轮')]) == 1
bl2 = back.split('\n')
n2 = len(bl2) - (1 if bl2 and bl2[-1] == '' else 0)
assert n2 == nlines
print('BOARD bytes =', os.path.getsize(BRD), 'lines =', n2, '(limit 300)')
print('sha256 =', hashlib.sha256(io.open(BRD, 'rb').read()).hexdigest().upper())
print('OK')
